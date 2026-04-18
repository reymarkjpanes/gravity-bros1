"""
Boss entrance cinematic — dramatic title card + HP bar fill animation.
Plays when the player first enters the boss zone.
"""
import pygame
import math

from config import WIDTH, HEIGHT

# Dramatic display names for each boss type
BOSS_DISPLAY_NAMES = {
    'igorot':     ('IGOROT WARRIOR',    'Guardian of the Terraces',   (200, 150, 80)),
    'carabao':    ('CARABAO TITAN',     'Beast of the Hills',         (120, 80, 40)),
    'bakunawa':   ('BAKUNAWA',          'Serpent of the Deep',        (0, 180, 220)),
    'sirena':     ('SIRENA',            'Enchantress of the Waves',   (0, 200, 180)),
    'mayon':      ('MAYON SPIRIT',      'Wrath of the Volcano',       (255, 80, 0)),
    'tikbalang':  ('TIKBALANG LORD',    'Terror of the Mountains',    (100, 70, 30)),
    'dambuhala':  ('DAMBUHALA',         'The Colossus',               (80, 80, 120)),
    'diwata':     ('DIWATA',            'Spirit of the Forest',       (100, 255, 150)),
    'kutsero':    ('KUTSERO',           'Phantom of Calle Crisologo', (200, 150, 50)),
    'haring_ibon':('HARING IBON',       'King of the Skies',          (255, 215, 0)),
}


class BossIntro:
    """120-frame (2 second) boss entrance cinematic."""

    def __init__(self):
        self.active = False
        self.timer = 0
        self.max_frames = 120
        self.boss_name = ''
        self.boss_subtitle = ''
        self.boss_color = (255, 255, 255)
        self.boss_x = 0           # world-space x of boss for camera pan
        self.player_cam_x = 0     # original camera_x to return to
        self.boss_max_hp = 0
        self._font_title = None
        self._font_sub = None

    def _ensure_fonts(self):
        if self._font_title is None:
            self._font_title = pygame.font.SysFont("Impact", 48, bold=True)
            self._font_sub = pygame.font.SysFont("Georgia", 22, italic=True)

    def start(self, boss):
        """Trigger intro for a Boss entity."""
        self.active = True
        self.timer = 0
        self.boss_x = boss.rect.centerx
        self.boss_max_hp = boss.health

        info = BOSS_DISPLAY_NAMES.get(boss.boss_type, (boss.boss_type.upper(), 'Unknown', (200,200,200)))
        self.boss_name = info[0]
        self.boss_subtitle = info[1]
        self.boss_color = info[2]

    def get_camera_override(self, normal_camera_x):
        """Returns the camera_x to use during the intro (smooth pan)."""
        if not self.active:
            return normal_camera_x

        self.player_cam_x = normal_camera_x

        if self.timer <= 20:
            # Pan toward boss
            t = self.timer / 20
            t = t * t * (3 - 2 * t)  # smoothstep
            target = max(0, self.boss_x - WIDTH // 2)
            return int(self.player_cam_x + (target - self.player_cam_x) * t)
        elif self.timer <= 100:
            # Hold on boss
            return max(0, self.boss_x - WIDTH // 2)
        else:
            # Pan back to player
            t = (self.timer - 100) / 20
            t = t * t * (3 - 2 * t)
            target = max(0, self.boss_x - WIDTH // 2)
            return int(target + (self.player_cam_x - target) * t)

    def update(self):
        """Advance by one frame. Returns True while active."""
        if not self.active:
            return False
        self.timer += 1
        if self.timer >= self.max_frames:
            self.active = False
        return self.active

    def draw(self, screen):
        """Render the current frame of the boss intro."""
        if not self.active:
            return
        self._ensure_fonts()
        t = self.timer

        # ── Letterbox bars ──
        bar_h = 0
        if t <= 20:
            bar_h = int(50 * (t / 20))
        elif t <= 100:
            bar_h = 50
        else:
            bar_h = int(50 * (1.0 - (t - 100) / 20))

        if bar_h > 0:
            pygame.draw.rect(screen, (0, 0, 0), (0, 0, WIDTH, bar_h))
            pygame.draw.rect(screen, (0, 0, 0), (0, HEIGHT - bar_h, WIDTH, bar_h))
            # Gold trim
            pygame.draw.line(screen, self.boss_color, (0, bar_h), (WIDTH, bar_h), 2)
            pygame.draw.line(screen, self.boss_color, (0, HEIGHT - bar_h), (WIDTH, HEIGHT - bar_h), 2)

        # ── Title card (frames 40-90) ──
        if 40 <= t <= 90:
            phase_t = (t - 40) / 50

            # Dark vignette behind title
            vignette = pygame.Surface((WIDTH, 100), pygame.SRCALPHA)
            vignette.fill((0, 0, 0, 140))
            screen.blit(vignette, (0, HEIGHT // 2 - 50))

            # ⚔ decorative line
            line_w = int(WIDTH * 0.6 * min(1.0, phase_t * 2))
            cx = WIDTH // 2
            cy = HEIGHT // 2 - 30
            pygame.draw.line(screen, self.boss_color, (cx - line_w // 2, cy - 25), (cx + line_w // 2, cy - 25), 2)
            pygame.draw.line(screen, self.boss_color, (cx - line_w // 2, cy + 45), (cx + line_w // 2, cy + 45), 2)

            # Sword icons ⚔
            sword = "⚔"
            try:
                sw_font = pygame.font.SysFont("Segoe UI Symbol", 24)
                sw_surf = sw_font.render(sword, True, self.boss_color)
                screen.blit(sw_surf, (cx - line_w // 2 - 25, cy - 32))
                screen.blit(sw_surf, (cx + line_w // 2 + 5, cy - 32))
            except Exception:
                pass

            # Boss name slams in
            if phase_t < 0.3:
                # Slide from left
                slide_t = phase_t / 0.3
                text_x = int(-400 + (cx + 400) * slide_t * slide_t)
            else:
                text_x = cx

            title_surf = self._font_title.render(self.boss_name, True, self.boss_color)
            # Shadow
            shadow = self._font_title.render(self.boss_name, True, (0, 0, 0))
            screen.blit(shadow, (text_x - title_surf.get_width() // 2 + 3, cy + 3))
            screen.blit(title_surf, (text_x - title_surf.get_width() // 2, cy))

            # Subtitle fades in
            if phase_t > 0.3:
                sub_alpha = min(255, int(255 * ((phase_t - 0.3) / 0.3)))
                sub_surf = self._font_sub.render(self.boss_subtitle, True, (220, 220, 220))
                sub_surf.set_alpha(sub_alpha)
                screen.blit(sub_surf, (cx - sub_surf.get_width() // 2, cy + 50))

        # ── HP bar fill animation (frames 70-95) ──
        if 70 <= t <= 95:
            fill_t = (t - 70) / 25
            bar_w = 300
            bar_h_px = 16
            bx = WIDTH // 2 - bar_w // 2
            by = HEIGHT // 2 + 85

            # Background
            pygame.draw.rect(screen, (40, 0, 0), (bx - 2, by - 2, bar_w + 4, bar_h_px + 4))
            # Fill
            filled = int(bar_w * min(1.0, fill_t))
            pygame.draw.rect(screen, (200, 0, 0), (bx, by, filled, bar_h_px))
            # Shine sweep
            if fill_t < 1.0:
                shine_x = bx + filled
                pygame.draw.rect(screen, (255, 255, 255), (shine_x - 3, by, 3, bar_h_px))
            # Border
            pygame.draw.rect(screen, self.boss_color, (bx - 2, by - 2, bar_w + 4, bar_h_px + 4), 2)
            # Label
            hp_label = self._font_sub.render("BOSS", True, (255, 200, 200))
            screen.blit(hp_label, (bx - hp_label.get_width() - 10, by - 2))
