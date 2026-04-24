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
