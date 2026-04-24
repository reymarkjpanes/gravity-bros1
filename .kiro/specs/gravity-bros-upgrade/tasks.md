# Implementation Plan: Gravity Bros Upgrade

## Overview

Implementation proceeds in dependency order: infrastructure and data-model changes first, then new game-mode sessions, then GameEngine decomposition, then UI/HUD integration, then the test suite. Each task builds directly on the previous ones so no code is left orphaned.

All code is Python. Tests use **pytest** + **Hypothesis**.

---

## Tasks

- [x] 1. Upgrade StateManager with validated states and transition enforcement
  - Add `VALID_STATES` frozenset and `ALLOWED_TRANSITIONS` dict to `core/state_manager.py` exactly as specified in the design
  - Rewrite `set_state` to validate the new state against `VALID_STATES` and the current→new pair against `ALLOWED_TRANSITIONS`, raising `ValueError` on failure
  - Add `previous_state: str | None = None` attribute; record it on every successful transition
  - Add `GAME_SURVIVAL` and `GAME_CHALLENGE` to the valid set and their transition entries
  - Keep `get_state()` unchanged
  - _Requirements: 4.1, 4.2, 4.3_

- [x] 2. Fix Save System error handling
  - In `core/save_system.py`, change `print(...)` in `save_game` and `load_game` to `print(..., file=sys.stderr)`
  - Add `import sys` at the top
  - Ensure neither function re-raises any exception (both already swallow; verify the `except` blocks return/return `{}` correctly)
  - _Requirements: 10.1, 10.2_

- [x] 3. Add sprite fallback error handling to Player and Enemy
  - In `Player.__init__`, replace the `if os.path.exists(path):` guard with an else branch that creates a magenta `pygame.Surface((24, 32))` placeholder and logs `f"[WARNING] Sprite not found: {path}"` to `sys.stderr`
  - Apply the same pattern in `Enemy.__init__` (placeholder size `(24, 24)`)
  - _Requirements: 10.3, 10.4_

- [x] 4. Add unknown-sound warning to SoundManager
  - In `SoundManager.play`, before the existing `if name in self.sounds` check, add: if `name` is not in `self._sounds` (or `self.sounds` after `_init_sounds`), print `f"[WARNING] Sound not loaded: {name!r}"` to `sys.stderr` and return
  - Adjust the guard so it covers the case where `_init_sounds` has not yet populated the dict
  - _Requirements: 10.5_

- [x] 5. Implement ObjectPool generic class
  - Create `core/object_pool.py` with the `ObjectPool[T]` class exactly as specified in the design (Generic, `factory`, `max_size=200`, `_available` list, `acquire()`, `release()`, `available_count` property)
  - _Requirements: ObjectPool design constraint_

- [x] 6. Implement GameSession abstract base class
  - Create `core/session.py` with the `GameSession` ABC exactly as specified in the design
  - Include all shared concrete methods (`pause`, `resume`, `add_score`, `add_coins`, `tick_time`) and all four abstract methods (`start`, `update`, `reset`, `end`)
  - _Requirements: 1.x, 2.x (shared session infrastructure)_

- [x] 7. Implement EnemyFactory
  - Create `entities/enemy_factory.py` with the `EnemyFactory` class
  - `create(enemy_type, x, y, hp, speed) -> Enemy` constructs an `Enemy`, overrides `max_hp`, `hp`, and `vx` as specified in the design
  - _Requirements: 8.3 (centralised enemy creation)_

- [x] 8. Add Enemy.reset_position and eliminate external rect assignments
  - Add `reset_position(self, x: int, y: int) -> None` to `Enemy` in `entities/enemy.py`
  - Search the entire codebase for `enemy.rect.x =`, `enemy.rect.y =`, `boss.rect.x =`, `boss.rect.y =` patterns outside `enemy.py` and `boss.py`; replace each with the appropriate `reset_position` call
  - _Requirements: 8.3, 8.4_

- [x] 9. Implement SurvivalSession
  - Create `core/survival.py` with `SurvivalSession(GameSession)` exactly as specified in the design
  - Include `__init__` (with optional `rng` parameter), `start`, `update`, `reset`, `end`, `build_arena`, `spawn_wave`, `compute_wave_stats` (static), `compute_skill_point_reward` (static)
  - `spawn_wave` uses `ObjectPool[Enemy]` and `EnemyFactory`; `build_arena` uses the injected `rng`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.7_

- [x] 10. Implement ChallengeSession
  - Create `core/challenge.py` with `RoundDefinition` dataclass, `ROUND_DEFINITIONS` list (all 5 rounds), and `ChallengeSession(GameSession)` exactly as specified in the design
  - Include `__init__` (with optional `rng`), `start`, `update`, `reset`, `end`, `compute_star_rating` (static), `compute_coin_reward` (static)
  - _Requirements: 2.1, 2.2, 2.4, 2.6_

- [x] 11. Add Player.respawn atomic method
  - Add `respawn(self, x: int, y: int) -> None` to `Player` in `entities/player.py` exactly as specified in the design (resets HP, all timers, flags, gravity_dir, position, velocity, invincibility_timer=120)
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 12. Decompose Player.update into focused sub-methods
  - Extract `_apply_physics(self, platforms, blocks)` — gravity, velocity integration, wall slide, coyote time, jump buffer; no combat or score logic
  - Extract `_resolve_collisions(self, vel_x, vel_y, platforms, blocks)` — AABB resolution, `on_ground` flag; no score or combat
  - Extract `_collect_items(self, coins, gems, stars, power_ups, particles)` — item pickup and score/coin updates; no physics or combat
  - Extract `_handle_enemy_contact(self, enemies, bosses, is_invuln, particles, effects)` — stomp, dash hit, melee, boss contact; no physics or item logic
  - Refactor `update()` to call `pygame.key.get_pressed()` exactly once at the top, then delegate to the four methods in order
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 9.1_

- [x] 13. Refactor Level_Loader — extract _build_bonus_room and add _clamp_endless_chunk
  - Extract `_build_bonus_room(base_x, base_y, platforms, coins, gems, hidden_portals)` from the duplicated bonus-room blocks in `build_tutorial_level` and `build_level`; replace both call sites
  - Add `_clamp_endless_chunk(last_x, last_y, gap, width, y) -> tuple[int, int, int]` with `MAX_H_GAP=240`, `MAX_V_DIFF=180`, `Y_MIN=150`, `Y_MAX=500` constants
  - Wire `_clamp_endless_chunk` into the Endless chunk generation path in `engine.py`
  - _Requirements: 3.1, 3.2, 3.3, 8.2_

- [x] 14. Implement GameEngine._build_save_dict and deduplicate save calls
  - Add `_build_save_dict(self) -> dict` to `GameEngine` with `save_version=1` and all fields listed in the design
  - Rewrite `_save_current_state` to call `save_game(self._build_save_dict())`
  - Rewrite `reset_game_data` to reset all fields then call `save_game(self._build_save_dict())`
  - Remove the duplicated inline dict from the old `_save_current_state`
  - _Requirements: 8.1_

- [x] 15. Integrate StateManager into GameEngine — remove app_state
  - In `GameEngine.__init__`, add `self.state_manager = StateManager()` and remove `self.app_state`
  - Replace every `self.app_state = '...'` write with `self.state_manager.set_state('...')` (or `self.state_manager._state = '...'` for the initial bootstrap only)
  - Replace every `self.app_state` read with `self.state_manager.get_state()`
  - Add `GAME_SURVIVAL` and `GAME_CHALLENGE` branches to the `run()` dispatcher
  - _Requirements: 4.1, 4.2_

- [x] 16. Decompose GameEngine.run_game into focused sub-methods
  - Extract `_handle_gameplay_input(self, event, player, is_paused, ...)` — all `KEYDOWN` and `JOYBUTTONDOWN` handling; no rendering or entity updates
  - Extract `_update_player(self, player, platforms, blocks, ...)` — `player.update()`, camera tracking, hit-stop decrement
  - Extract `_update_enemies(self, enemies, bosses, platforms, blocks, projectiles, players)` — `enemy.update()` and `boss.update()` calls
  - Extract `_update_projectiles(self, projectiles, platforms, blocks, ...)` — projectile movement, wall collision, lifetime expiry
  - Extract `_update_collisions(self, player, enemies, bosses, projectiles, ...)` — player↔enemy, projectile↔enemy, projectile↔player hit resolution
  - Extract `_update_powerups(self, player, power_ups, particles, ...)` — power-up pickup detection and effect application
  - Extract `_update_entities(self, player, ...)` as a pure orchestrator calling the five sub-methods in order; no direct game logic
  - Extract `_render_game(self, player, camera_x, camera_y, ...)` — all `draw_*` calls, background, HUD, overlays
  - Reduce `run_game` to ≤80 lines (init + loop shell only)
  - Replace all inline respawn blocks with `player.respawn(global_respawn_x, global_respawn_y)`
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 9.3_

- [x] 17. Wire Survival mode into GameEngine
  - Add `GAME_SURVIVAL` handling in `run()` that calls `run_game(game_mode='SURVIVAL')`
  - Inside `run_game`, when `game_mode == 'SURVIVAL'`: instantiate `SurvivalSession`, call `build_arena`, skip Portal placement, manage wave countdown (3-second inter-wave timer), call `spawn_wave` when countdown expires
  - Award skill points via `compute_skill_point_reward` when the session ends
  - Persist high score via `_save_current_state` if session score exceeds `self.high_scores.get('survival', 0)`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.7, 1.8_

- [x] 18. Wire Challenge mode into GameEngine
  - Add `GAME_CHALLENGE` handling in `run()` that calls `run_game(game_mode='CHALLENGE')`
  - Inside `run_game`, when `game_mode == 'CHALLENGE'`: instantiate `ChallengeSession`, present round selection screen, load the selected `RoundDefinition`, enforce `disable_horizontal_movement` modifier in `_handle_gameplay_input` for the `gravity_flip_only` round
  - On round completion call `compute_star_rating` and `compute_coin_reward`; persist result via `_save_current_state`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [x] 19. Survival mode HUD integration
  - In `ui/hud.py`, add a `draw_survival_hud(screen, font, wave_number, enemies_remaining, countdown_timer)` function that renders the current wave number and enemy count remaining
  - Call it from `_render_game` when `game_mode == 'SURVIVAL'`
  - _Requirements: 1.6_

- [x] 20. Challenge mode HUD integration
  - In `ui/hud.py`, add a `draw_challenge_hud(screen, font, objective, time_remaining, progress, target)` function that renders the round objective, countdown timer, and progress
  - Call it from `_render_game` when `game_mode == 'CHALLENGE'`
  - _Requirements: 2.3_

- [x] 21. Survival mode game over screen
  - In `ui/hud.py`, add a `draw_survival_game_over(screen, font, big_font, wave_number, score)` function that displays the final wave number, total score, and a "Play Again" option
  - Wire it into `run_game` for `GAME_SURVIVAL` when `session.is_lost` is True
  - _Requirements: 1.5_

- [x] 22. Challenge mode result screen
  - In `ui/hud.py`, add a `draw_challenge_result(screen, font, big_font, stars, coins_earned, failed)` function that shows stars earned (or "Failed"), coins awarded, and retry/back options
  - Wire it into `run_game` for `GAME_CHALLENGE` on round completion or failure
  - _Requirements: 2.4, 2.5, 2.6_

- [x] 23. High score persistence for Survival and Challenge
  - Extend `_build_save_dict` to include `high_scores` entries for `'survival'` and all five `'challenge_<id>'` keys
  - In `init_game_data`, load these keys from `saved_data` with sensible defaults (0 for survival score, 0 for challenge stars)
  - Update high scores at session end in `run_game` for both modes before calling `_save_current_state`
  - _Requirements: 1.8, 2.6, 2.7_

- [x] 24. Checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 25. Set up test suite infrastructure
  - Create `tests/` directory at the project root
  - Create `tests/conftest.py` with the `headless_pygame` session-scoped autouse fixture (sets `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy`, calls `pygame.init()`, `pygame.display.set_mode((1,1))`)
  - Add a `tmp_save_path` fixture that patches `core.save_system.SAVE_FILE` to a `tmp_path`-based location
  - Verify `pytest` can discover and run an empty test file without errors
  - _Requirements: 11.x, 12.x, 13.x, 14.x_

- [x] 26. Write test_state_manager.py — StateManager unit and property tests
  - [x] 26.1 Unit: valid transition succeeds and `previous_state` is recorded
    - _Requirements: 4.1, 4.2_
  - [x] 26.2 Unit: `set_state` with unknown string raises `ValueError`
    - _Requirements: 4.3_
  - [x] 26.3 Unit: forbidden transition (e.g. `GAME_OVER` → `SETTINGS`) raises `ValueError`
    - _Requirements: 4.3_
  - [ ]* 26.4 Property test for Property 6: StateManager rejects all invalid state strings
    - **Property 6: StateManager rejects all invalid state strings**
    - **Validates: Requirements 4.3**
    - Strategy: `text()` filtered to exclude `VALID_STATES`
  - [ ]* 26.5 Property test for Property 7: StateManager records previous state on every transition
    - **Property 7: StateManager records previous state on every transition**
    - **Validates: Requirements 4.2**
    - Strategy: `sampled_from(list(VALID_STATES))` for A and B; assume A ≠ B and A→B is in `ALLOWED_TRANSITIONS`
  - [ ]* 26.6 Property test for Property 12: StateManager rejects invalid transitions
    - **Property 12: StateManager rejects invalid transitions**
    - **Validates: Requirements 4.3**
    - Strategy: `sampled_from(list(VALID_STATES))` for A and B, filtered to pairs not in `ALLOWED_TRANSITIONS`

- [x] 27. Write test_physics.py — Player physics unit and property tests
  - [x] 27.1 Unit: Player lands on platform after `update()` — `on_ground` becomes `True`
    - _Requirements: 11.1_
  - [x] 27.2 Unit: Player `vel_y` is negative immediately after `jump()` call
    - _Requirements: 11.2_
  - [x] 27.3 Unit: inverted gravity (`gravity_dir=-1`) — Player lands on ceiling, `on_ground` becomes `True`
    - _Requirements: 11.3_
  - [x] 27.4 Unit: Player `dead` becomes `True` when HP reaches 0
    - _Requirements: 11.5_
  - [x] 27.5 Unit: `player.invincibility_timer == 120` immediately after `respawn()`
    - _Requirements: 5.3_
  - [ ]* 27.6 Property test for Property 8: Player respawn is a position round-trip
    - **Property 8: Player respawn is a position round-trip**
    - **Validates: Requirements 5.1, 5.2, 11.4**
    - Strategy: `integers(0, 8000)` for x, `integers(0, 600)` for y

- [x] 28. Write test_enemy_ai.py — Enemy AI unit and property tests
  - [x] 28.1 Unit: walker Enemy reverses direction at platform edge
    - _Requirements: 12.1_
  - [x] 28.2 Unit: shielded Enemy `hp` unchanged when `take_damage` called with `shield_hp > 0`
    - _Requirements: 12.2_
  - [x] 28.3 Unit: Enemy `dead` becomes `True` when `take_damage(max_hp)` called
    - _Requirements: 12.3_
  - [ ]* 28.4 Property test for Property 9: Enemy take_damage reduces HP or kills
    - **Property 9: Enemy take_damage reduces HP or kills**
    - **Validates: Requirements 12.4**
    - Strategy: `integers(1, 100)` for damage value `d`

- [x] 29. Write test_save_system.py — Save/load unit and property tests
  - [x] 29.1 Unit: `load_game()` returns `{}` when save file does not exist
    - _Requirements: 13.2_
  - [x] 29.2 Unit: `load_game()` returns `{}` when save file contains invalid JSON
    - _Requirements: 13.3_
  - [x] 29.3 Unit: `save_game` I/O failure does not raise (mock `open` to raise `OSError`)
    - _Requirements: 10.1_
  - [x] 29.4 Unit: `load_game` I/O failure returns `{}` (mock `open` to raise `OSError`)
    - _Requirements: 10.2_
  - [ ]* 29.5 Property test for Property 10: Save/load round-trip preserves all data
    - **Property 10: Save/load round-trip preserves all data**
    - **Validates: Requirements 13.1, 13.4**
    - Strategy: `fixed_dictionaries` with JSON-serializable leaf strategies (text, integers, booleans, lists)

- [x] 30. Write test_mode_logic.py — Survival and Challenge unit and property tests
  - [x] 30.1 Unit: Wave N spawns `BASE_COUNT + N * 2` enemies
    - _Requirements: 14.1_
  - [x] 30.2 Unit: Wave N+1 enemy HP is 10% higher than Wave N enemy HP
    - _Requirements: 14.2_
  - [x] 30.3 Unit: `coin_rush` round with >66% time remaining → 3 stars
    - _Requirements: 14.3_
  - [x] 30.4 Unit: `no_damage` round with 1 hit taken → result is "Failed"
    - _Requirements: 14.4_
  - [ ]* 30.5 Property test for Property 1: Wave enemy count is strictly increasing
    - **Property 1: Wave enemy count is strictly increasing**
    - **Validates: Requirements 1.2, 14.5**
    - Strategy: `integers(min_value=1, max_value=50)` for n
  - [ ]* 30.6 Property test for Property 2: Wave HP and speed scaling stays within bounds
    - **Property 2: Wave HP and speed scaling stays within bounds**
    - **Validates: Requirements 1.4**
    - Strategy: `integers(1,50)` for n, `integers(5,30)` for base_hp, `floats(1.0,5.0)` for base_speed
  - [ ]* 30.7 Property test for Property 3: Challenge star rating covers all ratios
    - **Property 3: Challenge star rating covers all ratios**
    - **Validates: Requirements 2.4**
    - Strategy: `integers(0, 10000)` for time_remaining, `integers(1, 10000)` for time_limit; assume remaining ≤ limit
  - [ ]* 30.8 Property test for Property 4: Challenge coin reward is proportional to stars
    - **Property 4: Challenge coin reward is proportional to stars**
    - **Validates: Requirements 2.6**
    - Strategy: `sampled_from([1, 2, 3])` for stars
  - [ ]* 30.9 Property test for Property 11: Survival skill point reward formula
    - **Property 11: Survival skill point reward formula**
    - **Validates: Requirements 1.7**
    - Strategy: `integers(1, 100)` for wave_number
  - [ ]* 30.10 Property test for Property 13: compute_wave_stats output is bounded for any multipliers
    - **Property 13: compute_wave_stats output is bounded for any multipliers**
    - **Validates: Requirements 1.4**
    - Strategy: `integers(1,100)` for n, `integers(1,1000)` for base_hp, `floats(0.1,20.0)` for base_speed, `floats(1.0,2.0)` for hp_mult and speed_mult
  - [ ]* 30.11 Property test for Property 14: ObjectPool acquire-release-acquire returns same instance
    - **Property 14: ObjectPool acquire-release-acquire returns same instance**
    - **Validates: ObjectPool design constraint**
    - Strategy: create pool with a simple factory; acquire, release, acquire; assert `obj1 is obj2`

- [x] 31. Write test_terrain.py — terrain clamping property tests
  - [x] 31.1 Unit: `_clamp_endless_chunk` clamps gap to ≤ 240
    - _Requirements: 3.1_
  - [x] 31.2 Unit: `_clamp_endless_chunk` clamps y to [150, 500]
    - _Requirements: 3.3_
  - [x] 31.3 Unit: `_clamp_endless_chunk` clamps vertical diff to ≤ 180
    - _Requirements: 3.2_
  - [ ]* 31.4 Property test for Property 5: Endless terrain gap and height are always clamped
    - **Property 5: Endless terrain gap and height are always clamped**
    - **Validates: Requirements 3.1, 3.2, 3.3**
    - Strategy: `integers(-500, 2000)` for gap and y, `integers(50, 800)` for width, `integers(150, 500)` for last_y

- [x] 32. Final checkpoint — ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP; all non-starred tasks must be completed
- Each task references specific requirements for traceability
- Checkpoints (tasks 24 and 32) are integration gates — do not proceed past them with failing tests
- Property tests use `@settings(max_examples=100)` minimum; pure-function properties (P1, P3, P4, P5, P11) can safely use 500+
- The `headless_pygame` fixture in `conftest.py` is required for any test that instantiates `Player` or `Enemy`
- `save_version=1` in `_build_save_dict` must be incremented on any backward-incompatible schema change
