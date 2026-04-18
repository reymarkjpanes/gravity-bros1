"""
Tekken / Persona-style skill cut-in animation.
Plays a dramatic 60-frame cinematic when a unique skill is triggered.
"""
import pygame
import math
import os
import glob

from config import WIDTH, HEIGHT

# Character signature colors (matches SKILL_CODEX)
_CHAR_COLORS = {
    'Juan':        (255, 215, 0),
    'Maria':       (255, 150, 180),
    'LapuLapu':    (255, 140, 0),
    'Jose':        (75, 0, 130),
    'Andres':      (220, 20, 60),
    'Aswang':      (139, 0, 0),
    'Tikbalang':   (101, 67, 33),
    'Kapre':       (255, 100, 0),
    'Manananggal': (148, 0, 211),
    'Datu':        (218, 165, 32),
    'Sorbetero':   (135, 206, 235),
    'Taho':        (160, 82, 45),
    'Malunggay':   (50, 205, 50),
    'Batak':       (34, 139, 34),
    'Jeepney':     (255, 215, 0),
}

_SKILL_NAMES = {
    'Juan':        'BAYANIHAN SPIRIT',
    'Maria':       'FILIPINA GRACE',
    'LapuLapu':    'BATTLE OF MACTAN',
    'Jose':        'NOLI ME TANGERE',
    'Andres':      'SIGAW NG PUGAD LAWIN',
    'Aswang':      'HIGOP NG DUGO',
    'Tikbalang':   'WILD STAMPEDE',
    'Kapre':       'TABAHOY NG KAPRE',
    'Manananggal': 'HATAW NG MANANANGGAL',
    'Datu':        'HUSGADO NG DATU',
    'Sorbetero':   'DIRTY KITCHEN BLIZZARD',
    'Taho':        'ARNIBAL GROUND SLAM',
    'Malunggay':   'SUPERFOOD SURGE',
    'Batak':       'PANA AT TABAK',
    'Jeepney':     'KONTING TIYAGA',
}


class SkillCutIn:
    def __init__(self):
        self.active = False
        self.timer = 0
        self.max_frames = 60
        self.character = ''
        self.color = (255, 255, 255)
        self.skill_name = ''
        self.portrait = None
        self._font_big = None
        self._font_skill = None

    def _ensure_fonts(self):
        if self._font_big is None:
            self._font_big = pygame.font.SysFont("Impact", 52, bold=True)
            self._font_skill = pygame.font.SysFont("Impact", 28)

    def start(self, character_name):
        """Trigger the cut-in animation for a character."""
        self.active = True
        self.timer = 0
        self.character = character_name
        self.color = _CHAR_COLORS.get(character_name, (255, 255, 255))
        self.skill_name = _SKILL_NAMES.get(character_name, 'SUPER ART')

        # Try to load portrait
        self.portrait = None
        art_dir = os.path.join(os.path.dirname(__file__), '..', 'concept_art')
        pattern = os.path.join(art_dir, f"{character_name.lower()}_concept_*.png")
        matches = glob.glob(pattern)
        if matches:
            try:
                img = pygame.image.load(matches[0]).convert_alpha()
                w, h = img.get_size()
                ratio = (HEIGHT * 0.7) / h
                self.portrait = pygame.transform.smoothscale(img, (int(w * ratio), int(h * ratio)))
            except Exception:
                pass

    def update(self):
        """Advance the animation by one frame. Returns True while active."""
        if not self.active:
            return False
        self.timer += 1
        if self.timer >= self.max_frames:
            self.active = False
        return self.active

    def draw(self, screen):
        """Render the current frame of the cut-in animation."""
        if not self.active:
            return
        self._ensure_fonts()
        t = self.timer
        progress = t / self.max_frames  # 0.0 → 1.0

        # ── Phase 1 (0-10): Screen darkens + diagonal slash ──
        if t <= 10:
            fade = int(200 * (t / 10))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, fade))
            screen.blit(overlay, (0, 0))

            # Diagonal slash line
            slash_progress = t / 10
            sx = int(WIDTH * slash_progress)
            sy = int(HEIGHT * slash_progress)
            pygame.draw.line(screen, self.color, (0, 0), (sx, sy), 4)
            # Glow around slash
            glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(glow, (*self.color, 80), (0, 0), (sx, sy), 20)
            screen.blit(glow, (0, 0))

        # ── Phase 2 (10-25): Dark BG + portrait slides in + speed lines ──
        elif t <= 25:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            # Speed lines (horizontal)
            phase_t = (t - 10) / 15
            for i in range(20):
                ly = int(i * (HEIGHT / 20)) + 10
                lw = int(WIDTH * 0.3 * phase_t + i * 7) % WIDTH
                alpha = int(60 + 40 * math.sin(i + t * 0.5))
                line_surf = pygame.Surface((lw, 2), pygame.SRCALPHA)
                line_surf.fill((*self.color, alpha))
                screen.blit(line_surf, (0, ly))

            # Character band (horizontal colored stripe)
            band_h = 220
            band_y = HEIGHT // 2 - band_h // 2
            band = pygame.Surface((WIDTH, band_h), pygame.SRCALPHA)
            band.fill((*self.color, 40))
            screen.blit(band, (0, band_y))
            # Border lines
            pygame.draw.line(screen, self.color, (0, band_y), (WIDTH, band_y), 3)
            pygame.draw.line(screen, self.color, (0, band_y + band_h), (WIDTH, band_y + band_h), 3)

            # Portrait slides from left
            if self.portrait:
                slide_x = int(-300 + 350 * min(1.0, phase_t * 1.3))
                screen.blit(self.portrait, (slide_x, HEIGHT // 2 - self.portrait.get_height() // 2))

        # ── Phase 3 (25-45): Skill name slams in + shockwave ring ──
        elif t <= 45:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            phase_t = (t - 25) / 20

            # Band
            band_h = 220
            band_y = HEIGHT // 2 - band_h // 2
            band = pygame.Surface((WIDTH, band_h), pygame.SRCALPHA)
            band.fill((*self.color, 40))
            screen.blit(band, (0, band_y))
            pygame.draw.line(screen, self.color, (0, band_y), (WIDTH, band_y), 3)
            pygame.draw.line(screen, self.color, (0, band_y + band_h), (WIDTH, band_y + band_h), 3)

            # Portrait (now fully visible)
            if self.portrait:
                screen.blit(self.portrait, (50, HEIGHT // 2 - self.portrait.get_height() // 2))

            # Skill name text slams from right
            name_surf = self._font_big.render(self.skill_name, True, self.color)
            char_surf = self._font_skill.render(f"— {self.character.upper()} —", True, (255, 255, 255))

            text_x = int(WIDTH + 200 - (WIDTH * 0.6 + 200) * min(1.0, phase_t * 1.5))
            text_y = HEIGHT // 2 - 30

            # Text shadow
            shadow = self._font_big.render(self.skill_name, True, (0, 0, 0))
            screen.blit(shadow, (text_x + 3, text_y + 3))
            screen.blit(name_surf, (text_x, text_y))
            screen.blit(char_surf, (text_x + 10, text_y + 55))

            # Shockwave ring expanding from center
            ring_r = int(50 * phase_t)
            if ring_r > 0:
                ring_surf = pygame.Surface((ring_r * 4, ring_r * 4), pygame.SRCALPHA)
                alpha = int(200 * (1.0 - phase_t))
                pygame.draw.circle(ring_surf, (*self.color, alpha), (ring_r * 2, ring_r * 2), ring_r, 3)
                screen.blit(ring_surf, (WIDTH // 2 - ring_r * 2, HEIGHT // 2 - ring_r * 2))

        # ── Phase 4 (45-60): Flash out ──
        else:
            phase_t = (t - 45) / 15
            # White flash that fades
            flash_alpha = int(255 * (1.0 - phase_t))
            if flash_alpha > 0:
                flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                flash.fill((255, 255, 255, flash_alpha))
                screen.blit(flash, (0, 0))
