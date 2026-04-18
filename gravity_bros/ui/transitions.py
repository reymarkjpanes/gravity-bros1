"""
Screen transition effects — fade, diamond wipe, iris circle.
Used between game states for polish.
"""
import pygame
import math

from config import WIDTH, HEIGHT


class Transition:
    """Screen transition manager. Only one transition at a time."""

    def __init__(self):
        self.active = False
        self.timer = 0
        self.max_frames = 40
        self.phase = 'out'   # 'out' = fading out, 'in' = fading in
        self.effect = 'fade'  # 'fade', 'diamond', 'iris'
        self.callback = None  # Called at midpoint (phase switch)
        self._midpoint_fired = False

    def start(self, effect='fade', duration=40, on_midpoint=None):
        """Start a transition. on_midpoint is called at the halfway point."""
        self.active = True
        self.timer = 0
        self.max_frames = duration
        self.effect = effect
        self.phase = 'out'
        self.callback = on_midpoint
        self._midpoint_fired = False

    def update(self):
        """Advance by one frame. Returns True while active."""
        if not self.active:
            return False
        self.timer += 1

        # Midpoint: switch from 'out' to 'in'
        half = self.max_frames // 2
        if self.timer >= half and not self._midpoint_fired:
            self._midpoint_fired = True
            self.phase = 'in'
            if self.callback:
                self.callback()

        if self.timer >= self.max_frames:
            self.active = False
        return self.active

    def draw(self, screen):
        """Render the current transition frame."""
        if not self.active:
            return

        half = self.max_frames // 2
        if self.phase == 'out':
            # Going dark: 0.0 → 1.0
            t = min(1.0, self.timer / max(1, half))
        else:
            # Coming back: 1.0 → 0.0
            t = max(0.0, 1.0 - (self.timer - half) / max(1, half))

        if self.effect == 'fade':
            self._draw_fade(screen, t)
        elif self.effect == 'diamond':
            self._draw_diamond(screen, t)
        elif self.effect == 'iris':
            self._draw_iris(screen, t)

    def _draw_fade(self, screen, t):
        """Simple fade to black."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(255 * t)))
        screen.blit(overlay, (0, 0))

    def _draw_diamond(self, screen, t):
        """Diamond shape expands from center to cover screen."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 255))

        # Cut out a diamond-shaped hole that shrinks as t increases
        diag = max(WIDTH, HEIGHT) * 1.5
        size = int(diag * (1.0 - t))
        if size > 0:
            cx, cy = WIDTH // 2, HEIGHT // 2
            points = [
                (cx, cy - size), (cx + size, cy),
                (cx, cy + size), (cx - size, cy)
            ]
            pygame.draw.polygon(overlay, (0, 0, 0, 0), points)
            # We need to use a mask approach — draw black, then punch hole
            # Simpler: draw a scaled diamond of transparency
            mask = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            mask.fill((0, 0, 0, 255))
            pygame.draw.polygon(mask, (0, 0, 0, 0), points)
            # Blend: black everywhere except inside diamond
            screen.blit(mask, (0, 0))
        else:
            screen.blit(overlay, (0, 0))

    def _draw_iris(self, screen, t):
        """Classic Mario-style iris circle that closes to center."""
        max_r = int(math.hypot(WIDTH, HEIGHT) * 0.55)
        radius = int(max_r * (1.0 - t))
        cx, cy = WIDTH // 2, HEIGHT // 2

        # Draw black overlay with circular cutout
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 255))
        if radius > 0:
            pygame.draw.circle(overlay, (0, 0, 0, 0), (cx, cy), radius)
        screen.blit(overlay, (0, 0))
