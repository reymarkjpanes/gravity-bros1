VALID_STATES = frozenset({
    'MAIN_MENU', 'LEVEL_SELECT', 'STORE', 'MISSION_BRIEFING',
    'MODES', 'SETTINGS', 'SKILL_TREE', 'SKILL_CODEX',
    'GAME', 'GAME_ENDLESS', 'GAME_TIME_ATTACK', 'GAME_BOSS_RUSH',
    'GAME_SURVIVAL', 'GAME_CHALLENGE',
    'GAME_OVER', 'LEVEL_CLEARED',
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
        self.save_data = {}

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
