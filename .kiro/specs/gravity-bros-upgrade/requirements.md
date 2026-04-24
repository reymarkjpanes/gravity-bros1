# Requirements Document

## Introduction

This document covers the upgrade of Gravity Bros: Philippine Adventure — a Python/pygame 2D platformer with Filipino-themed characters. The upgrade targets four areas:

1. **New game modes** — Survival and Challenge modes with complete, solid logic
2. **Bug fixes** — Identified issues in collision, state management, and game-mode logic
3. **Code quality refactoring** — Small focused functions, no duplication, no deep nesting, single-responsibility classes
4. **Test coverage** — Automated tests for core game logic

The existing modes (Story, Endless, Time Attack, Boss Rush) are preserved. New modes are added alongside them.

---

## Glossary

- **Game_Engine**: The `GameEngine` class in `core/engine.py` — the top-level coordinator
- **Player**: The `Player` class in `entities/player.py` — the player-controlled character
- **Enemy**: The `Enemy` class in `entities/enemy.py` — standard AI-controlled opponents
- **Boss**: The `Boss` class in `entities/boss.py` — large AI-controlled boss opponents
- **State_Manager**: The `StateManager` class in `core/state_manager.py` — tracks the current application state
- **Save_System**: The `save_game`/`load_game` functions in `core/save_system.py`
- **Level_Loader**: The `build_level` function in `levels/level_loader.py`
- **HUD**: The heads-up display drawn by `ui/hud.py`
- **Wave**: A discrete group of enemies spawned together in Survival mode
- **Round**: A single timed challenge segment in Challenge mode
- **Difficulty**: One of `easy`, `normal`, or `hard` — affects enemy HP, speed, and spawn rate
- **Respawn_Point**: The last activated checkpoint position, or the level start if none activated
- **Combo**: A sequence of aerial kills without touching the ground
- **Skill_Point**: Currency earned by completing levels and killing bosses, spent in the Skill Tree
- **Projectile**: A `Projectile` instance in `entities/items.py` — a moving damaging object
- **Particle**: A `Particle` instance in `entities/items.py` — a visual-only effect object
- **Camera**: The `camera_x`/`camera_y` offset applied during rendering in `run_game`
- **Portal**: The exit object that ends a Story level when all bosses are defeated

---

## Requirements

---

### Requirement 1: Survival Mode

**User Story:** As a player, I want a Survival mode where I defend against endless waves of increasingly difficult enemies, so that I can test how long I can last and compete for a high score.

#### Acceptance Criteria

1. WHEN the player selects Survival from the Modes menu, THE Game_Engine SHALL start a Survival session on a procedurally generated arena with a flat base floor, at least 4 elevated platforms at varying heights, and no Portal.
2. THE Game_Engine SHALL spawn enemies in discrete Waves, where each Wave contains `base_count + (wave_number * 2)` enemies distributed across the arena.
3. WHEN all enemies in the current Wave are defeated, THE Game_Engine SHALL begin the next Wave after a 3-second countdown displayed on the HUD.
4. WHEN a new Wave begins, THE Game_Engine SHALL increase enemy HP by 10% and enemy speed by 5% relative to the previous Wave's values, capped at 300% of the base values.
5. WHEN the player's HP reaches 0 in Survival mode, THE Game_Engine SHALL display the final wave number, total score, and a "Play Again" option without returning to the main menu automatically.
6. THE Game_Engine SHALL display the current wave number and enemy count remaining on the HUD during Survival mode.
7. WHEN the player completes Wave 10 or higher, THE Game_Engine SHALL award 1 Skill_Point per 5 waves completed beyond Wave 9.
8. IF the player's score in Survival mode exceeds the stored high score for Survival, THEN THE Save_System SHALL persist the new high score.

---

### Requirement 2: Challenge Mode

**User Story:** As a player, I want a Challenge mode with a series of timed rounds each with a specific objective, so that I can test different skills and earn bonus rewards.

#### Acceptance Criteria

1. WHEN the player selects Challenge from the Modes menu, THE Game_Engine SHALL present a list of available Rounds and allow the player to select one.
2. THE Game_Engine SHALL define at least 5 distinct Round types: `coin_rush` (collect N coins before time expires), `enemy_clear` (defeat all enemies before time expires), `no_damage` (reach the Portal without taking any damage), `gravity_flip_only` (reach the Portal using only gravity-flip movement — horizontal movement keys are disabled), and `boss_rush_timed` (defeat all bosses before time expires).
3. WHEN a Round starts, THE Game_Engine SHALL display the Round objective, time limit, and current progress on the HUD.
4. WHEN the player completes a Round's objective within the time limit, THE Game_Engine SHALL award a star rating of 1–3 stars based on time remaining: 3 stars for more than 66% time remaining, 2 stars for 33–66%, and 1 star for less than 33%.
5. IF the time limit expires before the objective is met, THEN THE Game_Engine SHALL end the Round and display a "Failed" result screen with the option to retry.
6. WHEN a Round is completed with at least 1 star, THE Game_Engine SHALL award coins equal to `100 * stars_earned` and persist the result via the Save_System.
7. WHERE a Round has been previously completed, THE Game_Engine SHALL display the player's best star rating next to that Round in the selection list.

---

### Requirement 3: Bug Fix — Endless Mode Terrain Generation

**User Story:** As a player, I want Endless mode to generate terrain that is always reachable, so that I am never blocked by an impossible gap.

#### Acceptance Criteria

1. WHEN the Level_Loader generates a new platform chunk in Endless mode, THE Level_Loader SHALL ensure the horizontal gap between consecutive platforms does not exceed the player's maximum horizontal jump distance of 240 pixels (5 speed × 1.6 boost × 30 frames).
2. WHEN the Level_Loader generates a new platform chunk, THE Level_Loader SHALL ensure the vertical difference between consecutive platforms does not exceed 180 pixels (jump_power 14 × gravity 0.6 × ~21 frames).
3. THE Level_Loader SHALL clamp generated platform Y positions to the range [150, 500] to prevent platforms from spawning off-screen.

---

### Requirement 4: Bug Fix — State Manager Integration

**User Story:** As a developer, I want the State_Manager to be the single source of truth for application state, so that state transitions are consistent and debuggable.

#### Acceptance Criteria

1. THE Game_Engine SHALL use the State_Manager to read and write the current application state instead of maintaining a separate `app_state` string attribute.
2. WHEN the Game_Engine transitions between states, THE State_Manager SHALL record the previous state so that the transition can be reversed if needed.
3. THE State_Manager SHALL raise a `ValueError` if `set_state` is called with a state string not in the defined set of valid states: `MAIN_MENU`, `LEVEL_SELECT`, `STORE`, `MISSION_BRIEFING`, `MODES`, `SETTINGS`, `SKILL_TREE`, `SKILL_CODEX`, `GAME`, `GAME_ENDLESS`, `GAME_TIME_ATTACK`, `GAME_BOSS_RUSH`, `GAME_SURVIVAL`, `GAME_CHALLENGE`.

---

### Requirement 5: Bug Fix — Player Death and Respawn Consistency

**User Story:** As a player, I want dying and respawning to always restore my character to a consistent, playable state, so that I am never stuck in a broken state after death.

#### Acceptance Criteria

1. WHEN the Player respawns, THE Player SHALL have HP restored to `max_hp`, all active timers reset to 0, `is_dashing` set to `False`, `is_mounted` set to `False`, `shield_active` set to `False`, and `gravity_dir` reset to 1.
2. WHEN the Player respawns, THE Player SHALL be placed at the Respawn_Point with `vel_x` and `vel_y` both set to 0.
3. WHEN the Player respawns, THE Player SHALL receive 120 frames of invincibility.
4. THE Player SHALL expose a single `respawn(x, y)` method that performs all of the above steps atomically, so that no respawn logic is duplicated across the codebase.

---

### Requirement 6: Refactoring — Function Decomposition in GameEngine

**User Story:** As a developer, I want `run_game` and `run_menu` to be decomposed into small, named functions, so that each function has a single clear responsibility and the code is easy to read and maintain.

#### Acceptance Criteria

1. THE Game_Engine SHALL extract all input-handling logic from `run_game` into a dedicated `_handle_gameplay_input(event, player, ...)` method.
2. THE Game_Engine SHALL extract all rendering logic from `run_game` into a dedicated `_render_game(player, ...)` method.
3. THE Game_Engine SHALL extract all entity-update logic from `run_game` into a dedicated `_update_entities(player, ...)` method.
4. WHEN any extracted method is called, THE Game_Engine SHALL not modify state that belongs to a different extracted method's responsibility (no cross-cutting side effects between input, update, and render phases).
5. THE Game_Engine SHALL contain no function longer than 80 lines after refactoring.

---

### Requirement 7: Refactoring — Player Class Decomposition

**User Story:** As a developer, I want the Player class to be split into focused components, so that movement, combat, and ability logic are each independently readable and testable.

#### Acceptance Criteria

1. THE Player SHALL delegate all gravity and physics integration to a `_apply_physics(platforms, blocks)` method that contains no combat or ability logic.
2. THE Player SHALL delegate all collision resolution to a `_resolve_collisions(vel_x, vel_y, platforms, blocks)` method that returns only collision results and does not modify score or coins.
3. THE Player SHALL delegate all item pickup logic to a `_collect_items(coins, gems, stars, power_ups, particles)` method that contains no physics or combat logic.
4. THE Player SHALL delegate all enemy contact logic to a `_handle_enemy_contact(enemies, bosses, is_invuln, particles, effects)` method that contains no physics or item logic.
5. WHEN any Player method is called, THE Player SHALL not call `pygame.key.get_pressed()` more than once per `update()` call.

---

### Requirement 8: Refactoring — Eliminate Code Duplication

**User Story:** As a developer, I want duplicated patterns extracted into shared utilities, so that fixing a bug in one place fixes it everywhere.

#### Acceptance Criteria

1. THE Game_Engine SHALL extract the save-state dictionary construction into a single `_build_save_dict()` method that is called by both `_save_current_state()` and `reset_game_data()`.
2. THE Level_Loader SHALL extract the bonus room generation into a `_build_bonus_room(base_x, base_y)` function called by both `build_tutorial_level` and `build_level`.
3. THE Enemy SHALL expose a `reset_position(x, y)` method used by all code that repositions an enemy, replacing inline `rect.x = ...` assignments scattered across the codebase.
4. WHEN the codebase is scanned for the pattern `rect.x = ` or `rect.y = ` applied to Enemy or Boss instances outside of their own class files, THE codebase SHALL contain 0 such occurrences after refactoring.

---

### Requirement 9: Refactoring — Reduce Nesting Depth

**User Story:** As a developer, I want no function to have more than 3 levels of indentation, so that logic is easy to follow without mental stack tracking.

#### Acceptance Criteria

1. THE Player.update method SHALL contain no code block nested deeper than 3 levels of indentation (12 spaces in Python).
2. THE Boss.update method SHALL contain no code block nested deeper than 3 levels of indentation.
3. THE Game_Engine.run_game method SHALL contain no code block nested deeper than 3 levels of indentation after refactoring.
4. WHERE deep nesting is reduced, THE refactored code SHALL use early-return guards or extracted helper methods rather than inverting all conditions into a flat chain of `elif` statements.

---

### Requirement 10: Error Handling

**User Story:** As a developer, I want all I/O and asset-loading operations to handle errors gracefully, so that a missing file or corrupt save does not crash the game.

#### Acceptance Criteria

1. WHEN the Save_System fails to write a save file, THE Save_System SHALL log the error to stderr and return without raising an exception to the caller.
2. WHEN the Save_System fails to read a save file, THE Save_System SHALL log the error to stderr and return an empty dict.
3. WHEN the Player loads a sprite image that does not exist on disk, THE Player SHALL substitute a colored rectangle surface of the correct dimensions and log a warning to stderr.
4. WHEN the Enemy loads a sprite image that does not exist on disk, THE Enemy SHALL substitute a colored rectangle surface and log a warning to stderr.
5. WHEN `sounds.play(name)` is called with a sound name that has not been loaded, THE Sound_Manager SHALL log a warning to stderr and return without raising an exception.

---

### Requirement 11: Test Coverage — Core Physics

**User Story:** As a developer, I want automated tests for the Player's physics and collision logic, so that regressions are caught before they reach players.

#### Acceptance Criteria

1. THE test suite SHALL include a test that verifies WHEN a Player is placed above a platform and `update()` is called, THE Player lands on the platform and `on_ground` becomes `True`.
2. THE test suite SHALL include a test that verifies WHEN a Player jumps, THE Player's `vel_y` becomes negative (upward) immediately after the jump call.
3. THE test suite SHALL include a test that verifies WHEN `gravity_dir` is -1 and the Player is below a ceiling platform, THE Player lands on the ceiling and `on_ground` becomes `True`.
4. THE test suite SHALL include a property-based test that verifies FOR ALL valid `(x, y)` spawn positions within the level bounds, calling `Player.respawn(x, y)` followed by reading `player.rect.topleft` returns `(x, y)` (round-trip property).
5. THE test suite SHALL include a test that verifies WHEN a Player's HP reaches 0, `player.dead` becomes `True`.

---

### Requirement 12: Test Coverage — Enemy AI

**User Story:** As a developer, I want automated tests for enemy behavior, so that AI changes do not silently break existing patterns.

#### Acceptance Criteria

1. THE test suite SHALL include a test that verifies WHEN a walker Enemy reaches the edge of a platform, THE Enemy reverses its horizontal direction.
2. THE test suite SHALL include a test that verifies WHEN `take_damage` is called on a shielded Enemy with `shield_hp > 0`, THE Enemy's `hp` does not decrease.
3. THE test suite SHALL include a test that verifies WHEN `take_damage` is called on any Enemy with damage equal to `max_hp`, THE Enemy's `dead` attribute becomes `True`.
4. THE test suite SHALL include a property-based test that verifies FOR ALL damage values `d` in range `[1, 100]`, calling `take_damage(d)` on a fresh Enemy reduces `hp` by exactly `d` (when no shield is active), or sets `dead = True` if `hp - d <= 0`.

---

### Requirement 13: Test Coverage — Save System

**User Story:** As a developer, I want automated tests for the save/load cycle, so that player progress is never silently lost.

#### Acceptance Criteria

1. THE test suite SHALL include a round-trip test that verifies FOR ALL valid save dictionaries `d`, `load_game()` after `save_game(d)` returns a dictionary equal to `d`.
2. THE test suite SHALL include a test that verifies WHEN `load_game()` is called and the save file does not exist, THE Save_System returns an empty dict without raising an exception.
3. THE test suite SHALL include a test that verifies WHEN `load_game()` is called and the save file contains invalid JSON, THE Save_System returns an empty dict without raising an exception.
4. THE test suite SHALL include a property-based test that verifies FOR ALL save dictionaries containing only JSON-serializable values, the round-trip `load_game(save_game(d))` produces a dictionary equal to `d`.

---

### Requirement 14: Test Coverage — Game Mode Logic

**User Story:** As a developer, I want automated tests for the new Survival and Challenge mode logic, so that wave progression and round scoring are correct.

#### Acceptance Criteria

1. THE test suite SHALL include a test that verifies WHEN Wave N ends in Survival mode, the next Wave spawns `base_count + (N * 2)` enemies.
2. THE test suite SHALL include a test that verifies WHEN Wave N+1 enemies are created, their HP is 10% higher than Wave N enemies' HP.
3. THE test suite SHALL include a test that verifies WHEN a `coin_rush` Round ends with more than 66% time remaining, the star rating is 3.
4. THE test suite SHALL include a test that verifies WHEN a `no_damage` Round ends and the player took at least 1 hit, the Round result is "Failed".
5. THE test suite SHALL include a property-based test that verifies FOR ALL wave numbers `n` in range `[1, 50]`, the enemy count formula `base_count + (n * 2)` is strictly increasing.
