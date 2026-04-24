# Design Document — Gravity Bros Upgrade

## Overview

This document describes the technical design for upgrading Gravity Bros: Philippine Adventure. The upgrade covers four areas:

1. **New game modes** — Survival (wave-based arena defense) and Challenge (5 timed round types)
2. **Bug fixes** — Endless terrain gap clamping, StateManager as single source of truth, atomic player respawn
3. **Code quality refactoring** — GameEngine and Player decomposition, duplication elimination, nesting reduction
4. **Test coverage** — pytest + Hypothesis property-based tests for physics, AI, save system, and mode logic

The existing modes (Story, Endless, Time Attack, Boss Rush) are preserved unchanged. All new code is additive or replaces existing code in-place without changing the public API surface visible to `main.py`.

---

## Architecture

### Current Architecture

```
main.py
  └── GameEngine (core/engine.py)
        ├── run()          — top-level loop dispatcher
        ├── run_menu()     — all menu states in one large method
        └── run_game()     — monolithic ~500-line game loop
              ├── Player (entities/player.py)   — ~1500 lines, all logic mixed
              ├── Enemy  (entities/enemy.py)
              ├── Boss   (entities/boss.py)
              ├── Level  (levels/level_loader.py)
              ├── SaveSystem (core/save_system.py)
              └── StateManager (core/state_manager.py) — currently unused
```

### Target Architecture

```
run_game()               → orchestration only
_handle_gameplay_input() → input only
_update_entities()       → game logic orchestration
  _update_player()
  _update_enemies()
  _update_projectiles()
  _update_collisions()
  _update_powerups()
_render_game()           → rendering only
GameSession              → shared mode behavior (abstract base)
SurvivalSession          → wave defense mode
ChallengeSession         → timed challenge mode
EnemyFactory             → enemy creation
ObjectPool[T]            → object recycling
StateManager             → validated state + transition enforcement
_build_save_dict()       → single save source with versioning
```

```
main.py
  └── GameEngine (core/engine.py)
        ├── run()
        ├── run_menu()
        ├── run_game(game_mode)          — thin orchestrator, ≤80 lines
        │     ├── _handle_gameplay_input(event, player, ...)
        │     ├── _update_entities(player, ...)   — orchestrator only
        │     │     ├── _update_player(player, ...)
        │     │     ├── _update_enemies(enemies, ...)
        │     │     ├── _update_projectiles(projectiles, ...)
        │     │     ├── _update_collisions(player, enemies, ...)
        │     │     └── _update_powerups(player, power_ups, ...)
        │     └── _render_game(player, ...)
        ├── _build_save_dict()           — single save dict builder (versioned)
        ├── _save_current_state()        — calls _build_save_dict()
        └── reset_game_data()            — calls _build_save_dict()

  StateManager (core/state_manager.py)  — single source of truth
        ├── VALID_STATES                 — frozenset of valid state strings
        ├── ALLOWED_TRANSITIONS          — dict mapping state → allowed next states
        ├── set_state(state)             — validates state + transition, records previous
        ├── get_state()
        └── previous_state

  GameSession (core/session.py)         — abstract base class
        ├── score, coins, elapsed_time   — shared tracking
        ├── is_paused, is_won, is_lost   — shared state flags
        ├── player, enemies              — shared references
        ├── reset()                      — shared reset logic
        ├── start()                      — abstract
        ├── update()                     — abstract
        ├── reset()                      — abstract
        └── end()                        — abstract

  SurvivalSession (core/survival.py)    — extends GameSession
        ├── build_arena(rng)
        ├── spawn_wave(wave_number, rng)
        └── compute_wave_stats(wave_number, base_hp, base_speed,
                               hp_multiplier, speed_multiplier)

  ChallengeSession (core/challenge.py)  — extends GameSession
        ├── ROUND_DEFINITIONS            — list[RoundDefinition]
        ├── compute_star_rating(time_remaining, time_limit)
        └── compute_coin_reward(stars)

  EnemyFactory (entities/enemy_factory.py)  — new
        └── create(enemy_type, x, y, hp, speed) → Enemy

  ObjectPool[T] (core/object_pool.py)   — new generic pool
        ├── acquire() → T
        └── release(obj: T) → None

  Player (entities/player.py)           — decomposed
        ├── respawn(x, y)               — atomic reset
        ├── _apply_physics(platforms, blocks)
        ├── _resolve_collisions(vel_x, vel_y, platforms, blocks)
        ├── _collect_items(coins, gems, stars, power_ups, particles)
        └── _handle_enemy_contact(enemies, bosses, is_invuln, particles, effects)

  Level_Loader (levels/level_loader.py)
        ├── build_level(level, difficulty)
        ├── build_tutorial_level(difficulty)
        ├── _build_bonus_room(base_x, base_y)  — extracted helper
        └── _clamp_endless_chunk(last_x, last_y, gap, width, y)  — new
```

---

## Components and Interfaces

### 1. StateManager (core/state_manager.py)

**Current state:** Stores `state` and `save_data` but `set_state` does no validation and `previous_state` is not tracked.

**Changes:**

```python
VALID_STATES = frozenset({
    'MAIN_MENU', 'LEVEL_SELECT', 'STORE', 'MISSION_BRIEFING',
    'MODES', 'SETTINGS', 'SKILL_TREE', 'SKILL_CODEX',
    'GAME', 'GAME_ENDLESS', 'GAME_TIME_ATTACK', 'GAME_BOSS_RUSH',
    'GAME_SURVIVAL', 'GAME_CHALLENGE',
})

# Maps each state to the set of states it is allowed to transition into.
# Any transition not listed here is forbidden and raises ValueError.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    # From menus — can navigate to other menus or start a game
    'MAIN_MENU':        frozenset({'LEVEL_SELECT', 'MODES', 'STORE', 'SETTINGS'}),
    'LEVEL_SELECT':     frozenset({'MAIN_MENU', 'MISSION_BRIEFING', 'STORE',
                                   'SKILL_TREE', 'SKILL_CODEX'}),
    'MISSION_BRIEFING': frozenset({'GAME', 'LEVEL_SELECT'}),
    'MODES':            frozenset({'MAIN_MENU', 'GAME_ENDLESS', 'GAME_TIME_ATTACK',
                                   'GAME_BOSS_RUSH', 'GAME_SURVIVAL', 'GAME_CHALLENGE'}),
    'STORE':            frozenset({'LEVEL_SELECT', 'MAIN_MENU'}),
    'SETTINGS':         frozenset({'MAIN_MENU'}),
    'SKILL_TREE':       frozenset({'LEVEL_SELECT'}),
    'SKILL_CODEX':      frozenset({'LEVEL_SELECT'}),
    # From active game states — can pause (return to menu) or reach game-over/cleared
    'GAME':             frozenset({'MAIN_MENU', 'LEVEL_SELECT', 'GAME_OVER',
                                   'LEVEL_CLEARED'}),
    'GAME_ENDLESS':     frozenset({'MAIN_MENU', 'GAME_OVER'}),
    'GAME_TIME_ATTACK': frozenset({'MAIN_MENU', 'GAME_OVER', 'LEVEL_CLEARED'}),
    'GAME_BOSS_RUSH':   frozenset({'MAIN_MENU', 'GAME_OVER', 'LEVEL_CLEARED'}),
    'GAME_SURVIVAL':    frozenset({'MAIN_MENU', 'GAME_OVER'}),
    'GAME_CHALLENGE':   frozenset({'MAIN_MENU', 'GAME_OVER', 'LEVEL_CLEARED'}),
    # Terminal states — only return to menu or retry
    'GAME_OVER':        frozenset({'MAIN_MENU', 'GAME', 'GAME_ENDLESS',
                                   'GAME_TIME_ATTACK', 'GAME_BOSS_RUSH',
                                   'GAME_SURVIVAL', 'GAME_CHALLENGE'}),
    'LEVEL_CLEARED':    frozenset({'MAIN_MENU', 'LEVEL_SELECT', 'GAME'}),
}

class StateManager:
    def __init__(self):
        self._state = 'MAIN_MENU'
        self.previous_state: str | None = None

    def set_state(self, new_state: str) -> None:
        if new_state not in VALID_STATES:
            raise ValueError(f"Invalid state: {new_state!r}")
        allowed = ALLOWED_TRANSITIONS.get(self._state, frozenset())
        if new_state not in allowed:
            raise ValueError(
                f"Invalid transition: {self._state!r} → {new_state!r}"
            )
        self.previous_state = self._state
        self._state = new_state

    def get_state(self) -> str:
        return self._state
```

**Forbidden transition examples** (raises `ValueError`):
- `PAUSE` → `CHARACTER_SELECT` (neither is a valid state)
- `GAME_OVER` → `SETTINGS` (not in `ALLOWED_TRANSITIONS['GAME_OVER']`)
- `MAIN_MENU` → `GAME` (must go through `LEVEL_SELECT` → `MISSION_BRIEFING` → `GAME`)

**GameEngine integration:** `GameEngine.__init__` creates `self.state_manager = StateManager()`. All reads of `self.app_state` become `self.state_manager.get_state()`. All writes become `self.state_manager.set_state(...)`. The `self.app_state` attribute is removed.

---

### 2. Player.respawn (entities/player.py)

**Current state:** Respawn logic is duplicated in at least two places in `engine.py` (keyboard `K_r` handler and controller `A` button handler), each setting a different subset of fields.

**New method:**

```python
def respawn(self, x: int, y: int) -> None:
    """Atomically reset the player to a clean playable state at (x, y)."""
    self.rect.x = x
    self.rect.y = y
    self.vel_x = 0.0
    self.vel_y = 0.0
    self.hp = self.max_hp
    self.dead = False
    self.invincibility_timer = 120
    self.is_dashing = False
    self.is_mounted = False
    self.shield_active = False
    self.gravity_dir = 1
    # Reset all active timers
    for attr in ('speed_boost_timer', 'ability_cooldown', 'ability_timer',
                 'dash_timer', 'dash_cooldown', 'melee_timer', 'attack_cooldown',
                 'combo_timer', 'awaken_cooldown', 'awaken_timer',
                 'wall_jump_lockout', 'jump_buffer_timer', 'tongue_drain_timer'):
        setattr(self, attr, 0)
    self.tongue_target = None
```

All existing respawn call sites in `engine.py` are replaced with `player.respawn(global_respawn_x, global_respawn_y)`.

---

### 3. Player Decomposition (entities/player.py)

The `update()` method currently mixes physics, collision, item collection, and combat. Four private methods are extracted:

| Method | Responsibility | Must NOT touch |
|---|---|---|
| `_apply_physics(platforms, blocks)` | gravity, velocity integration, wall slide | score, coins, combat |
| `_resolve_collisions(vel_x, vel_y, platforms, blocks)` | AABB resolution, on_ground flag | score, coins, combat |
| `_collect_items(coins, gems, stars, power_ups, particles)` | item pickup, score/coin updates | physics, combat |
| `_handle_enemy_contact(enemies, bosses, is_invuln, particles, effects)` | stomp, dash hit, melee, boss contact | physics, item pickup |

`update()` becomes an orchestrator that calls these four methods in order and merges their `effects` dicts. `pygame.key.get_pressed()` is called once at the top of `update()` and the result is passed down.

---

### 4. GameEngine Decomposition (core/engine.py)

`run_game()` is refactored into three extracted methods plus a thin orchestrator:

```python
def run_game(self, game_mode='STORY'):
    # ~30 lines: initialise session state, enter loop
    while running:
        for event in pygame.event.get():
            self._handle_gameplay_input(event, player, ...)
        self._update_entities(player, ...)
        self._render_game(player, ...)
        self.clock.tick(FPS)

def _handle_gameplay_input(self, event, player, is_paused, ...):
    # All KEYDOWN / JOYBUTTONDOWN handling

def _update_entities(self, player, platforms, enemies, bosses, ...):
    """Orchestrator only — calls sub-methods in order, no direct logic."""
    self._update_player(player, platforms, blocks, ...)
    self._update_enemies(enemies, platforms, blocks, projectiles, ...)
    self._update_projectiles(projectiles, platforms, blocks, ...)
    self._update_collisions(player, enemies, bosses, projectiles, ...)
    self._update_powerups(player, power_ups, particles, ...)

def _update_player(self, player, platforms, blocks, ...):
    # player.update(), camera tracking, hit-stop decrement

def _update_enemies(self, enemies, platforms, blocks, projectiles, players):
    # enemy.update() and boss.update() calls

def _update_projectiles(self, projectiles, platforms, blocks, ...):
    # projectile movement, wall collision, lifetime expiry

def _update_collisions(self, player, enemies, bosses, projectiles, ...):
    # player↔enemy, projectile↔enemy, projectile↔player hit resolution

def _update_powerups(self, player, power_ups, particles, ...):
    # power-up pickup detection and effect application

def _render_game(self, player, camera_x, camera_y, ...):
    # All draw_* calls, background, HUD, overlays
```

Each extracted method must be ≤80 lines. `_update_entities` is a pure orchestrator — it contains no game logic itself, only ordered calls to the five sub-methods. Cross-cutting state (camera, screen_shake, hit_stop) is passed as parameters or returned as a small dataclass.

---

### 4a. GameSession Abstract Base Class (core/session.py)

Shared logic that both `SurvivalSession` and `ChallengeSession` need is lifted into an abstract base class:

```python
from abc import ABC, abstractmethod
import pygame

class GameSession(ABC):
    """Abstract base for all game mode sessions."""

    def __init__(self, player, difficulty: str):
        self.player = player
        self.enemies: list = []
        self.difficulty = difficulty

        # Shared tracking
        self.score: int = 0
        self.coins: int = 0
        self.elapsed_time: int = 0   # frames

        # Shared state flags
        self.is_paused: bool = False
        self.is_won: bool = False
        self.is_lost: bool = False

    # ── Shared concrete logic ──────────────────────────────────────────────

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def add_score(self, amount: int) -> None:
        self.score += amount

    def add_coins(self, amount: int) -> None:
        self.coins += amount

    def tick_time(self) -> None:
        """Advance elapsed_time by one frame (only when not paused)."""
        if not self.is_paused:
            self.elapsed_time += 1

    # ── Abstract interface — subclasses implement mode-specific logic ──────

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def update(self) -> None: ...

    @abstractmethod
    def reset(self) -> None: ...

    @abstractmethod
    def end(self) -> None: ...
```

`SurvivalSession` and `ChallengeSession` inherit from `GameSession` and only implement mode-specific logic in their abstract method overrides.

---

### 5. SurvivalSession (core/survival.py)

New module encapsulating all Survival mode logic so `run_game` stays thin. Inherits from `GameSession`.

```python
import random
from core.session import GameSession
from core.object_pool import ObjectPool
from entities.enemy_factory import EnemyFactory

BASE_COUNT = 5  # enemies in wave 1

class SurvivalSession(GameSession):
    def __init__(self, player, difficulty: str, rng: random.Random | None = None):
        super().__init__(player, difficulty)
        self.wave_number = 0
        self.base_hp: int = 10       # set from EnemyFactory defaults
        self.base_speed: float = 2.0
        self._rng = rng or random.Random()
        self._enemy_pool: ObjectPool[Enemy] = ObjectPool(factory=self._make_enemy)
        self._factory = EnemyFactory()

    def _make_enemy(self):
        from entities.enemy import Enemy
        return Enemy(0, 0, difficulty=self.difficulty)

    def start(self) -> None:
        self.wave_number = 0
        self.is_lost = False
        self.is_won = False

    def end(self) -> None:
        self.is_lost = True

    def reset(self) -> None:
        self.score = 0
        self.coins = 0
        self.elapsed_time = 0
        self.wave_number = 0
        self.is_lost = False
        self.is_won = False
        self.enemies.clear()

    def update(self) -> None:
        if self.is_paused:
            return
        self.tick_time()
        # Mode-specific wave logic handled by spawn_wave / wave countdown

    def build_arena(self, rng: random.Random) -> tuple[list, list, None]:
        """Return (platforms, blocks, None) — no portal.
        Uses injected rng for reproducible arena generation."""

    def spawn_wave(self, wave_number: int, rng: random.Random) -> list[Enemy]:
        """Return a list of Enemy instances for the given wave.
        Uses ObjectPool[Enemy] to recycle instances instead of allocating new ones.
        Only determines count, positions, and scaling — delegates type/sprite/behavior
        to EnemyFactory."""
        count = BASE_COUNT + wave_number * 2
        hp, speed = self.compute_wave_stats(
            wave_number, self.base_hp, self.base_speed
        )
        enemies = []
        for i in range(count):
            x = rng.randint(100, 1500)
            y = 400
            enemy_type = rng.choice(['walker', 'hopper', 'archer'])
            # Acquire from pool (recycles dead instances)
            e = self._enemy_pool.acquire()
            # Re-initialise via factory (sets type, sprite, behavior)
            e = self._factory.create(enemy_type, x, y, hp=hp, speed=speed)
            enemies.append(e)
        return enemies

    @staticmethod
    def compute_wave_stats(
        wave_number: int,
        base_hp: int,
        base_speed: float,
        hp_multiplier: float = 1.10,
        speed_multiplier: float = 1.05,
    ) -> tuple[int, float]:
        """Return (scaled_hp, scaled_speed) for the given wave.

        Fully pure — no global state. All scaling parameters are explicit,
        making balancing and testing straightforward.
        """
        hp    = round(base_hp    * min(3.0, hp_multiplier    ** (wave_number - 1)))
        speed = base_speed * min(3.0, speed_multiplier ** (wave_number - 1))
        return hp, speed

    @staticmethod
    def compute_skill_point_reward(wave_number: int) -> int:
        """Return SP awarded for completing wave_number (0 if < 10)."""
        if wave_number < 10:
            return 0
        return (wave_number - 9) // 5
```

The Survival arena is a fixed-width flat floor (Platform at y=450, width=1600) plus 4 elevated platforms at y values [300, 250, 320, 280] spread across the arena. No Portal is placed.

---

### 6. ChallengeSession (core/challenge.py)

Inherits from `GameSession`. Uses structured `RoundDefinition` dataclasses instead of raw dicts/tuples.

```python
from dataclasses import dataclass, field
from core.session import GameSession
import random

@dataclass
class RoundDefinition:
    id: str
    time_limit: int                  # seconds
    objective: str
    enemy_count: int
    map_type: str
    reward_coins: int
    special_modifiers: list[str] = field(default_factory=list)

ROUND_DEFINITIONS: list[RoundDefinition] = [
    RoundDefinition(
        id='coin_rush', time_limit=60, objective='Collect 20 coins',
        enemy_count=0, map_type='flat', reward_coins=100,
    ),
    RoundDefinition(
        id='enemy_clear', time_limit=90, objective='Defeat all enemies',
        enemy_count=10, map_type='standard', reward_coins=200,
    ),
    RoundDefinition(
        id='no_damage', time_limit=120, objective='Reach the portal without taking damage',
        enemy_count=5, map_type='standard', reward_coins=300,
    ),
    RoundDefinition(
        id='gravity_flip_only', time_limit=90,
        objective='Reach the portal using only gravity flips',
        enemy_count=3, map_type='vertical', reward_coins=300,
        special_modifiers=['disable_horizontal_movement'],
    ),
    RoundDefinition(
        id='boss_rush_timed', time_limit=180, objective='Defeat all bosses',
        enemy_count=0, map_type='boss_arena', reward_coins=500,
    ),
]

class ChallengeSession(GameSession):
    def __init__(self, player, difficulty: str, rng: random.Random | None = None):
        super().__init__(player, difficulty)
        self._rng = rng or random.Random()

    def start(self) -> None:
        self.is_lost = False
        self.is_won = False

    def update(self) -> None:
        if self.is_paused:
            return
        self.tick_time()

    def reset(self) -> None:
        self.score = 0
        self.coins = 0
        self.elapsed_time = 0
        self.is_lost = False
        self.is_won = False

    def end(self) -> None:
        self.is_won = True

    @staticmethod
    def compute_star_rating(time_remaining: int, time_limit: int) -> int:
        ratio = time_remaining / time_limit
        if ratio > 0.66: return 3
        if ratio >= 0.33: return 2
        return 1

    @staticmethod
    def compute_coin_reward(stars: int) -> int:
        return 100 * stars
```

The `gravity_flip_only` round's `special_modifiers=['disable_horizontal_movement']` flag is read by `_handle_gameplay_input`, which skips `K_LEFT`, `K_RIGHT`, `K_a`, `K_d` processing for the duration of the round.

---

### 7. EnemyFactory (entities/enemy_factory.py)

`EnemyFactory` centralises all enemy creation logic — type selection, sprite assignment, behavior configuration, and variant setup. `spawn_wave` in `SurvivalSession` only decides *how many* enemies to spawn, *where* to place them, and *what scaling parameters* to use; it delegates the actual construction to `EnemyFactory`.

```python
from entities.enemy import Enemy

class EnemyFactory:
    """Creates fully initialised Enemy instances from typed parameters.

    Separates enemy construction (type, sprite, behavior, variants) from
    wave-level concerns (count, positions, difficulty scaling).
    """

    def create(
        self,
        enemy_type: str,
        x: int,
        y: int,
        hp: int,
        speed: float,
    ) -> Enemy:
        """Return a new Enemy of the given type placed at (x, y) with
        the specified hp and speed overrides applied after construction."""
        enemy = Enemy(x, y, type=enemy_type)
        enemy.max_hp = hp
        enemy.hp = hp
        enemy.vx = -speed if enemy.vx < 0 else speed
        return enemy
```

**Rationale:** Keeping creation logic in one place means adding a new enemy variant (e.g. `'elite_walker'`) only requires a change in `EnemyFactory`, not in every wave-spawning call site.

---

### 7a. ObjectPool (core/object_pool.py)

A generic object pool for recycling short-lived game objects (enemies, projectiles, particles, effects) to avoid per-frame allocation pressure in Survival mode.

```python
from typing import TypeVar, Generic, Callable

T = TypeVar('T')

class ObjectPool(Generic[T]):
    """Generic pool that recycles instances instead of allocating new ones.

    Usage:
        pool = ObjectPool(factory=lambda: Enemy(0, 0))
        obj = pool.acquire()   # get a recycled or new instance
        pool.release(obj)      # return it for future reuse
    """

    def __init__(self, factory: Callable[[], T], max_size: int = 200):
        self._factory = factory
        self._max_size = max_size
        self._available: list[T] = []

    def acquire(self) -> T:
        """Return a pooled instance, or create a new one if the pool is empty."""
        if self._available:
            return self._available.pop()
        return self._factory()

    def release(self, obj: T) -> None:
        """Return obj to the pool for future reuse.
        Silently discards if the pool is already at max_size."""
        if len(self._available) < self._max_size:
            self._available.append(obj)

    @property
    def available_count(self) -> int:
        return len(self._available)
```

`SurvivalSession` holds an `ObjectPool[Enemy]` instance. When a wave ends and enemies are marked dead, `spawn_wave` calls `pool.release(e)` for each dead enemy before acquiring fresh instances for the next wave.

---

### 8. Level_Loader Refactoring (levels/level_loader.py)

**Bonus room extraction:**

```python
def _build_bonus_room(base_x: int, base_y: int,
                      platforms: list, coins: list, gems: list,
                      hidden_portals: list) -> None:
    """Append bonus room objects into the provided lists in-place."""
    platforms.append(Platform(base_x, base_y + 400, 800, 600))
    for i in range(10):
        coins.append(Coin(base_x + 100 + i * 50, base_y + 300))
        if i % 3 == 0:
            gems.append(Gem(base_x + 100 + i * 50, base_y + 200))
    hidden_portals.append(HiddenPortal(base_x + 700, base_y + 320))
```

**Endless chunk clamping:**

```python
MAX_H_GAP = 240   # pixels — player max horizontal jump distance
MAX_V_DIFF = 180  # pixels — player max vertical jump height
Y_MIN, Y_MAX = 150, 500

def _clamp_endless_chunk(last_x: int, last_y: int,
                          gap: int, width: int, y: int
                          ) -> tuple[int, int, int]:
    """Return (clamped_gap, clamped_width, clamped_y)."""
    gap   = min(gap, MAX_H_GAP)
    y     = max(Y_MIN, min(Y_MAX, y))
    y     = max(last_y - MAX_V_DIFF, min(last_y + MAX_V_DIFF, y))
    return gap, width, y
```

The existing Endless chunk generation in `engine.py` calls `_clamp_endless_chunk` before appending the new Platform.

---

### 9. Save System Error Handling (core/save_system.py)

The existing `save_game` / `load_game` already have `try/except` blocks that print to stdout. The change is to redirect to `sys.stderr` and ensure the functions never re-raise:

```python
import sys

def save_game(data: dict) -> None:
    os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[save_game] Error: {e}", file=sys.stderr)

def load_game() -> dict:
    if not os.path.exists(SAVE_FILE):
        return {}
    try:
        with open(SAVE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"[load_game] Error: {e}", file=sys.stderr)
        return {}
```

---

### 10. Sprite / Sound Fallback Error Handling

**Player and Enemy sprite loading:**

```python
# In Player.__init__ and Enemy.__init__
if os.path.exists(path):
    self.images[key] = pygame.image.load(path).convert_alpha()
else:
    print(f"[WARNING] Sprite not found: {path}", file=sys.stderr)
    surf = pygame.Surface((24, 32))
    surf.fill((200, 100, 200))   # magenta placeholder
    self.images[key] = surf
```

**SoundManager:**

```python
def play(self, name: str) -> None:
    if name not in self._sounds:
        print(f"[WARNING] Sound not loaded: {name!r}", file=sys.stderr)
        return
    ...
```

---

### 11. Enemy.reset_position (entities/enemy.py)

```python
def reset_position(self, x: int, y: int) -> None:
    """Move this enemy to (x, y). Use instead of direct rect assignment."""
    self.rect.x = x
    self.rect.y = y
```

All external `enemy.rect.x = ...` and `boss.rect.x = ...` assignments outside their own class files are replaced with `reset_position(x, y)` calls.

---

### 12. GameEngine._build_save_dict (core/engine.py)

```python
def _build_save_dict(self) -> dict:
    return {
        'save_version':       1,                        # bump on breaking schema changes
        'unlocked_levels':    self.unlocked_levels,
        'current_level':      self.selected_level,
        'score':              self.total_score,
        'coins':              self.total_coins,
        'gems':               self.total_gems,
        'stars':              self.total_stars,
        'global_xp':          self.global_xp,
        'global_level':       self.global_level,
        'unlocked_skins':     self.unlocked_skins,
        'selected_skin':      self.selected_skin,
        'unlocked_characters':self.unlocked_characters,
        'selected_character': self.selected_character,
        'unlocked_powerups':  self.unlocked_powerups,
        'selected_powerup':   self.selected_powerup,
        'unlocked_pets':      self.unlocked_pets,
        'selected_pet':       self.selected_pet,
        'unlocked_upgrades':  self.unlocked_upgrades,
        'unlocked_evolutions':self.unlocked_evolutions,
        'unlocked_skills':    self.unlocked_skills,
        'skill_points':       self.skill_points,
        'achievements_unlocked': self.achievements.unlocked,
        'high_scores':        self.high_scores,
        'screen_shake_enabled': self.screen_shake_enabled,
    }

def _save_current_state(self) -> None:
    save_game(self._build_save_dict())

def reset_game_data(self) -> None:
    # ... reset all fields ...
    save_game(self._build_save_dict())
```

`save_version` is a top-level key set to `1`. It must be incremented whenever the save schema changes in a backward-incompatible way, allowing `load_game` to detect and migrate old saves.

---

## Data Models

### SurvivalState (in-memory, not persisted mid-session)

```python
@dataclass
class SurvivalState:
    wave_number: int = 0
    enemies_remaining: int = 0
    countdown_timer: int = 0   # frames until next wave (180 = 3 s)
    session_score: int = 0
    is_game_over: bool = False
```

### ChallengeState (in-memory)

```python
@dataclass
class ChallengeState:
    round_id: str = ''
    time_remaining: int = 0    # frames
    time_limit: int = 0        # frames
    objective_progress: int = 0
    objective_target: int = 0
    hits_taken: int = 0
    is_complete: bool = False
    is_failed: bool = False
    stars_earned: int = 0
```

### High Score Persistence

Survival and Challenge best results are stored in the existing `high_scores` dict inside `save.json`:

```json
{
  "high_scores": {
    "survival": 42000,
    "challenge_coin_rush": 3,
    "challenge_enemy_clear": 2,
    "challenge_no_damage": 1,
    "challenge_gravity_flip_only": 0,
    "challenge_boss_rush_timed": 3
  }
}
```

Challenge values are the best star rating (0 = never completed).

### Wave Enemy Stats

Wave scaling is purely computed — not stored. The formula is:

```
hp(n)    = round(base_hp    × min(3.0, 1.10^(n-1)))
speed(n) = base_speed × min(3.0, 1.05^(n-1))
```

where `n` is 1-indexed wave number and `base_hp` / `base_speed` come from `Enemy.BASE_HP` and the difficulty multiplier.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Wave enemy count is strictly increasing

*For any* wave number `n` in the range [1, 50], the enemy count for wave `n+1` must be strictly greater than the enemy count for wave `n`.

Formally: `enemy_count(n+1) > enemy_count(n)` where `enemy_count(n) = BASE_COUNT + n * 2`.

**Validates: Requirements 1.2, 14.5**

---

### Property 2: Wave HP and speed scaling stays within bounds

*For any* wave number `n` in the range [1, 100], any `base_hp`, any `base_speed`, any `hp_multiplier` in [1.0, 2.0], and any `speed_multiplier` in [1.0, 2.0], the scaled HP and speed returned by `SurvivalSession.compute_wave_stats(n, base_hp, base_speed, hp_multiplier, speed_multiplier)` must be in the range `[base_value, base_value * 3.0]`.

The function is fully pure — no global state is read. All parameters are explicit.

**Validates: Requirements 1.4**

---

### Property 3: Challenge star rating covers all ratios

*For any* `time_remaining` in `[0, time_limit]` and any positive `time_limit`, `compute_star_rating` must return exactly 3 when `ratio > 0.66`, exactly 2 when `0.33 ≤ ratio ≤ 0.66`, and exactly 1 when `ratio < 0.33`.

**Validates: Requirements 2.4**

---

### Property 4: Challenge coin reward is proportional to stars

*For any* star rating `s` in `{1, 2, 3}`, `compute_coin_reward(s)` must equal `100 * s`.

**Validates: Requirements 2.6**

---

### Property 5: Endless terrain gap and height are always clamped

*For any* randomly generated gap, width, and y values passed to `_clamp_endless_chunk`, the returned gap must be ≤ 240, the returned y must be in [150, 500], and the vertical difference from `last_y` must be ≤ 180.

**Validates: Requirements 3.1, 3.2, 3.3**

---

### Property 6: StateManager rejects all invalid state strings

*For any* string not in `VALID_STATES`, calling `StateManager.set_state` must raise `ValueError`.

**Validates: Requirements 4.3**

---

### Property 7: StateManager records previous state on every transition

*For any* two valid states A and B where A ≠ B, after calling `set_state(A)` then `set_state(B)`, `previous_state` must equal A.

**Validates: Requirements 4.2**

---

### Property 8: Player respawn is a position round-trip

*For any* `(x, y)` within level bounds, calling `player.respawn(x, y)` must result in `player.rect.topleft == (x, y)`, `player.vel_x == 0`, and `player.vel_y == 0`.

**Validates: Requirements 5.1, 5.2, 11.4**

---

### Property 9: Enemy take_damage reduces HP or kills

*For any* damage value `d` in [1, 100] applied to a fresh unshielded Enemy, either `enemy.hp` decreases by exactly `d` (if `hp - d > 0`) or `enemy.dead` becomes `True` (if `hp - d ≤ 0`).

**Validates: Requirements 12.4**

---

### Property 10: Save/load round-trip preserves all data

*For any* dictionary containing only JSON-serializable values, calling `save_game(d)` followed by `load_game()` must return a dictionary equal to `d`.

**Validates: Requirements 13.1, 13.4**

---

### Property 11: Survival skill point reward formula

*For any* wave number `n` ≥ 10, `compute_skill_point_reward(n)` must equal `(n - 9) // 5`, and for any `n < 10` it must equal 0.

**Validates: Requirements 1.7**

---

### Property 12: StateManager rejects invalid transitions

*For any* pair of valid states (A, B) where the transition A → B is not present in `ALLOWED_TRANSITIONS`, calling `set_state(B)` from state A must raise `ValueError`.

This is distinct from Property 6 (which tests invalid state *strings*): Property 12 tests that even valid state strings are rejected when the transition itself is forbidden (e.g. `GAME_OVER` → `SETTINGS`).

**Validates: Requirements 4.3**

---

### Property 13: compute_wave_stats output is bounded for any multipliers

*For any* `wave_number` in [1, 100], `base_hp` in [1, 1000], `base_speed` in [0.1, 20.0], `hp_multiplier` in [1.0, 2.0], and `speed_multiplier` in [1.0, 2.0], the values returned by `compute_wave_stats` must satisfy:

- `base_hp ≤ scaled_hp ≤ base_hp * 3.0`
- `base_speed ≤ scaled_speed ≤ base_speed * 3.0`

**Validates: Requirements 1.4**

---

### Property 14: ObjectPool acquire-release-acquire returns same instance

*For any* `ObjectPool[T]` with at least one object, calling `acquire()` to get `obj1`, then `release(obj1)`, then `acquire()` again to get `obj2`, must satisfy `obj1 is obj2` (same object identity — the pool recycled the instance).

**Validates: Requirements (object pooling design constraint)**

---

**Property Reflection — Redundancy Check (updated):**

- Properties 8 (respawn round-trip) subsumes the position check in Requirement 5.2 and the explicit test in Requirement 11.4 — they are unified into one property.
- Properties 1 (wave count increasing) and 11 (SP reward formula) are distinct: one tests the enemy count formula, the other tests the SP formula. No redundancy.
- Properties 9 (damage reduces HP or kills) covers both the "reduce by d" and "set dead" cases in a single property, making separate "kills at max_hp" and "reduces by d" properties redundant.
- Properties 10 (save/load round-trip) covers both Requirement 13.1 and 13.4 — they are the same property stated twice in the requirements.
- Properties 2 and 13 both test wave stat bounds. Property 13 is the more precise formulation (explicit multiplier parameters); Property 2 is retained as a higher-level statement. Together they are complementary, not redundant.
- Property 6 (invalid state strings) and Property 12 (invalid transitions) are distinct: one tests the state name validation, the other tests the transition graph. No redundancy.

---

## Error Handling

### Save System

- `save_game` catches all `Exception` subclasses, logs to `sys.stderr`, and returns `None`. The caller never sees an exception.
- `load_game` catches all `Exception` subclasses (including `json.JSONDecodeError`), logs to `sys.stderr`, and returns `{}`. Missing file returns `{}` without logging.
- Both functions are tested with mocked I/O failures (see Testing Strategy).

### Sprite Loading

- Player and Enemy constructors iterate over all expected sprite paths. Missing paths produce a magenta `pygame.Surface` placeholder and a `sys.stderr` warning. The game continues normally.
- The fallback surface dimensions match the expected sprite dimensions so layout is unaffected.

### Sound Manager

- `sounds.play(name)` checks `name in self._sounds` before playing. Unknown names log a warning to `sys.stderr` and return immediately. No exception propagates.

### StateManager

- `set_state` raises `ValueError` for unknown states. This is intentional — it is a programming error, not a runtime I/O error, so it should surface loudly during development.

### Endless Terrain

- `_clamp_endless_chunk` uses `max`/`min` clamping — it cannot raise an exception. Invalid inputs produce valid clamped outputs.

---

## Testing Strategy

### Framework

- **pytest** for all tests
- **Hypothesis** for property-based tests (minimum 100 iterations per property via `@settings(max_examples=100)`)
- Test files live in `tests/` at the project root

### Test File Layout

```
tests/
  conftest.py              — shared fixtures (headless pygame init, tmp save path)
  test_physics.py          — Requirement 11 (Player physics)
  test_enemy_ai.py         — Requirement 12 (Enemy AI)
  test_save_system.py      — Requirement 13 (Save/load)
  test_mode_logic.py       — Requirements 1, 2, 14 (Survival + Challenge)
  test_state_manager.py    — Requirement 4 (StateManager)
  test_terrain.py          — Requirement 3 (Endless terrain clamping)
```

### Headless Pygame

All tests that instantiate `Player` or `Enemy` require a pygame display. `conftest.py` initialises pygame in headless mode:

```python
import os, pygame, pytest

@pytest.fixture(autouse=True, scope='session')
def headless_pygame():
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()
```

### Unit Tests (example-based)

| Test | Requirement |
|---|---|
| Player lands on platform after `update()` | 11.1 |
| Player `vel_y < 0` immediately after `jump()` | 11.2 |
| Inverted gravity: player lands on ceiling | 11.3 |
| Player `dead = True` when HP reaches 0 | 11.5 |
| Walker enemy reverses direction at platform edge | 12.1 |
| Shielded enemy HP unchanged when `shield_hp > 0` | 12.2 |
| Enemy `dead = True` when `take_damage(max_hp)` | 12.3 |
| `load_game()` returns `{}` when file missing | 13.2 |
| `load_game()` returns `{}` on invalid JSON | 13.3 |
| Wave N spawns `BASE_COUNT + N * 2` enemies | 14.1 |
| Wave N+1 enemy HP is 10% higher than wave N | 14.2 |
| `coin_rush` with >66% time remaining → 3 stars | 14.3 |
| `no_damage` round with 1 hit → "Failed" | 14.4 |
| `save_game` I/O failure does not raise | 10.1 |
| `load_game` I/O failure returns `{}` | 10.2 |
| `_update_entities()` does not advance game state when `is_paused=True` (pause state freeze) | 6.3 |
| `player.invincibility_timer == 120` immediately after `respawn()` (respawn invincibility) | 5.3 |
| Running 50 waves with object pooling does not increase live object count beyond a fixed threshold (survival memory/performance stress) | ObjectPool design constraint |

### Property-Based Tests (Hypothesis)

Each property test references its design document property via a comment tag:

```python
# Feature: gravity-bros-upgrade, Property N: <property text>
```

| Property | Hypothesis Strategy |
|---|---|
| P1: Wave count strictly increasing | `integers(min_value=1, max_value=50)` for n |
| P2: Wave HP/speed within bounds | `integers(1,50)` for n, `integers(5,30)` for base_hp, `floats(1.0,5.0)` for base_speed |
| P3: Star rating covers all ratios | `integers(0, 10000)` for time_remaining, `integers(1, 10000)` for time_limit, assume remaining ≤ limit |
| P4: Coin reward proportional | `sampled_from([1, 2, 3])` for stars |
| P5: Terrain clamping | `integers(-500, 2000)` for gap/y, `integers(50, 800)` for width |
| P6: StateManager rejects invalid states | `text()` filtered to exclude VALID_STATES |
| P7: StateManager records previous state | `sampled_from(list(VALID_STATES))` for A and B |
| P8: Respawn round-trip | `integers(0, 8000)` for x, `integers(0, 600)` for y |
| P9: Enemy damage reduces HP or kills | `integers(1, 100)` for d |
| P10: Save/load round-trip | `fixed_dictionaries` with JSON-serializable leaf strategies |
| P11: SP reward formula | `integers(1, 100)` for wave_number |
| P12: StateManager rejects invalid transitions | `sampled_from(list(VALID_STATES))` for A, `sampled_from(list(VALID_STATES))` for B, filtered to pairs not in ALLOWED_TRANSITIONS |
| P13: compute_wave_stats bounded for any multipliers | `integers(1,100)` for n, `integers(1,1000)` for base_hp, `floats(0.1,20.0)` for base_speed, `floats(1.0,2.0)` for hp_mult and speed_mult |
| P14: ObjectPool acquire-release-acquire identity | Create pool with factory, acquire, release, acquire; assert `obj1 is obj2` |

### Dual Testing Balance

Unit tests cover specific examples and error conditions. Property tests cover universal invariants. The two are complementary: unit tests catch concrete regressions, property tests verify general correctness across the input space.

Property tests are configured with `@settings(max_examples=100)` as a minimum. Pure-function properties (P1, P3, P4, P5, P11) can safely run 500+ examples with negligible cost.
