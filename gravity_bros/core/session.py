from abc import ABC, abstractmethod


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
