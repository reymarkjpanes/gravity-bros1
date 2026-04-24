from dataclasses import dataclass, field
import random
from core.session import GameSession


@dataclass
class RoundDefinition:
    id: str
    time_limit: int          # seconds
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
        id='no_damage', time_limit=120,
        objective='Reach the portal without taking damage',
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
        if ratio > 0.66:
            return 3
        if ratio >= 0.33:
            return 2
        return 1

    @staticmethod
    def compute_coin_reward(stars: int) -> int:
        return 100 * stars
