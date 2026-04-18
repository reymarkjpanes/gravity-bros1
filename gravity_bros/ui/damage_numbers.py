"""
Floating damage numbers that pop up on hit
and drift upward while fading out.
"""
import pygame
import math

_FONT = None


def _get_font():
    global _FONT
    if _FONT is None:
        pygame.font.init()
        _FONT = pygame.font.SysFont("Impact", 22, bold=True)
    return _FONT


class DamageNumber:
    """A single floating number."""
    __slots__ = ('x', 'y', 'text', 'color', 'timer', 'max_timer', 'scale', 'is_crit')

    def __init__(self, x, y, amount, dmg_type='normal'):
        self.x = x
        self.y = y
        self.timer = 0
        self.max_timer = 45

        if isinstance(amount, (int, float)):
            self.is_crit = amount >= 3
        else:
            self.is_crit = False

        if dmg_type == 'heal':
            self.text = f"+{amount}"
            self.color = (0, 255, 80)
        elif dmg_type == 'boss':
            self.text = f"-{amount}" + ("!" if self.is_crit else "")
            self.color = (255, 60, 60)
        elif self.is_crit:
            self.text = f"{amount}!"
            self.color = (255, 215, 0)
        else:
            self.text = str(amount)
            self.color = (255, 255, 255)

        self.scale = 1.5 if self.is_crit else 1.0

    @property
    def alive(self):
        return self.timer < self.max_timer

    def update(self):
        self.timer += 1
        # Rise upward, decelerate
        self.y -= max(0.5, 2.5 - self.timer * 0.05)
        # Scale pop: start big then settle
        if self.timer < 8:
            self.scale = 1.0 + 0.6 * (1.0 - self.timer / 8)
        else:
            self.scale = 1.0

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        font = _get_font()
        # Alpha fade in last 15 frames
        alpha = 255
        if self.timer > self.max_timer - 15:
            alpha = int(255 * ((self.max_timer - self.timer) / 15))

        txt = font.render(self.text, True, self.color)
        if self.scale != 1.0:
            w, h = txt.get_size()
            nw = max(1, int(w * self.scale))
            nh = max(1, int(h * self.scale))
            txt = pygame.transform.scale(txt, (nw, nh))

        txt.set_alpha(alpha)

        # Shadow
        shadow = font.render(self.text, True, (0, 0, 0))
        if self.scale != 1.0:
            shadow = pygame.transform.scale(shadow, txt.get_size())
        shadow.set_alpha(alpha)

        dx = int(self.x - camera_x - txt.get_width() // 2)
        dy = int(self.y - txt.get_height() // 2)
        surface.blit(shadow, (dx + 2, dy + 2))
        surface.blit(txt, (dx, dy))


class DamageNumberManager:
    """Manages all floating damage numbers."""
    def __init__(self):
        self.numbers = []

    def spawn(self, x, y, amount, dmg_type='normal'):
        """Spawn a new damage number."""
        self.numbers.append(DamageNumber(x, y, amount, dmg_type))

    def update(self):
        for n in self.numbers:
            n.update()
        self.numbers = [n for n in self.numbers if n.alive]

    def draw(self, surface, camera_x):
        for n in self.numbers:
            n.draw(surface, camera_x)
