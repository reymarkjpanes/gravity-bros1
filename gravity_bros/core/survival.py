import random
import pygame

from core.session import GameSession
from core.object_pool import ObjectPool
from entities.enemy_factory import EnemyFactory
from entities.enemy import Enemy

BASE_COUNT = 5  # enemies in wave 1


class SurvivalSession(GameSession):
    """Wave-based arena defense game mode session."""

    def __init__(self, player, difficulty: str, rng: random.Random | None = None):
        super().__init__(player, difficulty)
        self.wave_number: int = 0
        self.base_hp: int = 10
        self.base_speed: float = 2.0
        self._rng = rng or random.Random()
        self._enemy_pool: ObjectPool = ObjectPool(factory=self._make_enemy)
        self._factory = EnemyFactory()

    def _make_enemy(self) -> Enemy:
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

    def build_arena(self, rng: random.Random) -> tuple[list, list, None]:
        """Return (platforms, blocks, None) — no portal.

        Builds a flat arena with one wide floor platform and 4 elevated platforms.
        Uses pygame.Rect objects as placeholders.
        """
        platforms = []

        # Wide floor platform at y=450, width=1600
        platforms.append(pygame.Rect(0, 450, 1600, 20))

        # 4 elevated platforms at varying heights spread across the arena
        elevated_heights = [300, 250, 320, 280]
        elevated_x_positions = [200, 500, 900, 1300]
        for x, y in zip(elevated_x_positions, elevated_heights):
            platforms.append(pygame.Rect(x, y, 200, 20))

        return (platforms, [], None)

    def spawn_wave(self, wave_number: int, rng: random.Random) -> list:
        """Return a list of Enemy instances for the given wave.

        Uses EnemyFactory to create enemies with scaled hp and speed.
        """
        count = BASE_COUNT + wave_number * 2
        hp, speed = self.compute_wave_stats(
            wave_number, self.base_hp, self.base_speed
        )
        enemies = []
        for _ in range(count):
            x = rng.randint(100, 1500)
            y = 400
            enemy_type = rng.choice(['walker', 'hopper', 'archer'])
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
        hp = round(base_hp * min(3.0, hp_multiplier ** (wave_number - 1)))
        speed = base_speed * min(3.0, speed_multiplier ** (wave_number - 1))
        return hp, speed

    @staticmethod
    def compute_skill_point_reward(wave_number: int) -> int:
        """Return SP awarded for completing wave_number (0 if < 10)."""
        if wave_number < 10:
            return 0
        return (wave_number - 9) // 5
