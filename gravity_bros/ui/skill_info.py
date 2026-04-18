import pygame
import math
import os
import glob
from config import WIDTH, HEIGHT, GOLD, WHITE

# Complete Skill Codex — one entry per character
SKILL_CODEX = {
    'Juan': {
        'skill_name':  'BAYANIHAN SPIRIT',
        'lore':        'The iconic Filipino community value where neighbors unite to help each other — inspired by the tradition of literally carrying a neighbor\'s house together.',
        'effect':      'Radiates a communal gold aura, stunning ALL nearby enemies. Grants full 3-second invincibility.',
        'cooldown':    '9 sec',
        'type':        'Support / Aura',
        'color':       (255, 215, 0),
        'tip':         'Best used when surrounded by many enemies at once.',
    },
    'Maria': {
        'skill_name':  'FILIPINA GRACE — FAN',
        'lore':        'Maria Clara\'s legendary fan from Noli Me Tangere becomes a weapon of iridescent grace — both shield and projectile in the hands of a true Filipina.',
        'effect':      'Releases a 35-petal fan-arc of energy projectiles forward. Nearest enemy is charmed and retreats. Grants a deflection shield.',
        'cooldown':    '9 sec',
        'type':        'Attack / Shield',
        'color':       (255, 140, 180),
        'tip':         'Use facing a crowd — the fan arc covers a wide angle.',
    },
    'LapuLapu': {
        'skill_name':  'BATTLE OF MACTAN',
        'lore':        'On April 27, 1521, Chieftain Lapu-Lapu defeated Ferdinand Magellan at the shores of Mactan — the first Filipino to repel foreign invaders.',
        'effect':      'Invincible kris-slash dash dealing -5 HP direct boss damage. Melee hitbox activates during the full dash. Gold war sparks trail.',
        'cooldown':    '5.3 sec',
        'type':        'Dash / Strike',
        'color':       (255, 160, 30),
        'tip':         'Always face the boss before activating to maximize kris range.',
    },
    'Jose': {
        'skill_name':  'NOLI ME TANGERE',
        'lore':        'Rizal\'s three legendary works (Noli Me Tangere, El Filibusterismo, Mi Ultimo Adios) become enchanted book-blades — the pen truly is mightier.',
        'effect':      'Fires 3 enchanted books in an expanding spread. Blue enlightenment aura erupts. Each book deals boss damage.',
        'cooldown':    '3.3 sec',
        'type':        'Projectile',
        'color':       (100, 150, 255),
        'tip':         'Fast cooldown — spam books to whittle boss health down over time.',
    },
    'Andres': {
        'skill_name':  'SIGAW NG PUGAD LAWIN',
        'lore':        'Andres Bonifacio\'s legendary war cry at Pugad Lawin on August 23, 1896, that launched the Philippine Revolution against Spanish colonial rule.',
        'effect':      '360° fire explosion instantly kills all enemies within 130px. Boss hit for -3 HP with a bolo shockwave. Berserker speed buff for 6 sec.',
        'cooldown':    '15 sec',
        'type':        'AoE / Berserker',
        'color':       (255, 60, 0),
        'tip':         'Most powerful AoE — save it for enemy mob rushes or enraged boss phase.',
    },
    'Aswang': {
        'skill_name':  'HIGOP NG DUGO',
        'lore':        'The Aswang is a shapeshifting blood-drinking creature from Visayan mythology — the most feared monster in Philippine folklore.',
        'effect':      'Drains the 3 nearest enemies simultaneously. Blood particles fly toward you. Each kill restores 90 frames of invincibility (life-steal).',
        'cooldown':    '10.8 sec',
        'type':        'Drain / Heal',
        'color':       (180, 0, 40),
        'tip':         'Most effective when 3+ enemies are nearby. Can also deal boss drain damage.',
    },
    'Tikbalang': {
        'skill_name':  'WILD STAMPEDE',
        'lore':        'The Tikbalang is a half-man, half-horse spirit that lurks in forests, known for leading travelers astray with its uncontrollable stampede speed.',
        'effect':      'Mega leap (-28vy) + triple-speed invincible dash for 30 frames. Brown stampede dust trails behind. Excellent escape or gap-close tool.',
        'cooldown':    '3.3 sec',
        'type':        'Mobility',
        'color':       (140, 100, 50),
        'tip':         'Fastest cooldown — use repeatedly to stay airborne and mobile constantly.',
    },
    'Kapre': {
        'skill_name':  'TABAHOY NG KAPRE',
        'lore':        'The Kapre is a giant tree-dwelling spirit who smokes a huge magical tobacco pipe that produces cursed smoke — whoever breathes it is forever lost.',
        'effect':      'Exhales 50-particle toxic smoke globe. ALL enemies stunned for 5 seconds. Boss takes -3 HP and stunned for 2.5 sec.',
        'cooldown':    '11.7 sec',
        'type':        'Mass Stun',
        'color':       (90, 90, 60),
        'tip':         'Greatest crowd control in the game. Use right before a boss attack pattern.',
    },
    'Manananggal': {
        'skill_name':  'HATAW NG MANANANGGAL',
        'lore':        'The Manananggal splits herself at the torso and flies through the night, raining terror from above. She detaches her upper body to hunt.',
        'effect':      'Splits and floats upward. Rains 5 viscera fireballs downward in a fan. Full invincibility for 4 seconds with dark-red aura.',
        'cooldown':    '11.7 sec',
        'type':        'Aerial / Ranged',
        'color':       (160, 0, 90),
        'tip':         'Air-dominant skill — rise above the boss, then rain fireballs on its head.',
    },
    'Datu': {
        'skill_name':  'HUSGADO NG DATU',
        'lore':        'Pre-colonial Filipino Datus were warrior-chieftains who commanded formations of warriors (barangay) into battle using coded battle orders.',
        'effect':      'Commands 7 fireballs in a full 180° war formation arc simultaneously. Gold + red tribal war-paint particles spiral outward.',
        'cooldown':    '3 sec',
        'type':        'Multi-Shot',
        'color':       (255, 130, 0),
        'tip':         'Very fast cooldown — fire constantly. The arc covers multiple vertical angles.',
    },
    'Sorbetero': {
        'skill_name':  'DIRTY KITCHEN BLIZZARD',
        'lore':        'The legendary "dirty kitchen" sorbetes vendor — a staple of Philippine street life, his ice cream freezer is rumored to contain supernatural cold.',
        'effect':      'ENTIRE LEVEL blizzard — ALL enemies frozen solid for 4+ seconds. Boss takes -2 HP and frozen 3 sec. 60-particle ice storm erupts.',
        'cooldown':    '15 sec',
        'type':        'Global Freeze',
        'color':       (150, 230, 255),
        'tip':         'Only skill that affects the ENTIRE SCREEN. Save for when you\'re overwhelmed.',
    },
    'Taho': {
        'skill_name':  'ARNIBAL GROUND SLAM',
        'lore':        '"TAHO!" — the morning cry of the taho vendor who carries his steaming silken tofu and arnibal (brown sugar syrup) in aluminum canisters on his shoulders.',
        'effect':      '[AIRBORNE ONLY] — Slams down fast. Sticky arnibal stuns enemies 200f. Boss takes -3 HP on impact. Brown syrup particles drip on descent.',
        'cooldown':    '7.5 sec',
        'type':        'Ground Pound',
        'color':       (180, 110, 20),
        'tip':         'Must be airborne first! Jump high, then press E to slam down.',
    },
    'Malunggay': {
        'skill_name':  'SUPERFOOD SURGE',
        'lore':        'Moringa oleifera — the "Miracle Tree" of the Philippines, packed with Vitamins A, C, E, iron, and calcium. Used as a natural remedy for centuries.',
        'effect':      '350-frame speed boost (×1.8) + double jump unlock + 120-frame invincibility. 45 lime-green health particles burst radially.',
        'cooldown':    '10 sec',
        'type':        'Self-Buff',
        'color':       (0, 210, 60),
        'tip':         'Best pre-fight buff — activate just before entering a boss room.',
    },
    'Batak': {
        'skill_name':  'PANA AT TABAK',
        'lore':        'The Batak are indigenous hunter-gatherers of Palawan — masters of the sumpit (blowgun) and bow, using poison darts to hunt in the deep forest.',
        'effect':      'Fires 8 rapid-fire poison darts alternating high-low flight paths (arrow-rain). Green poison particle burst at launch point.',
        'cooldown':    '2.5 sec',
        'type':        'Rapid Fire',
        'color':       (0, 180, 30),
        'tip':         'Fastest attacking skill. Use constantly while moving for continuous damage output.',
    },
    'Jeepney': {
        'skill_name':  'KONTING TIYAGA — FULL THROTTLE',
        'lore':        'The jeepney — converted WWII jeep turned iconic Filipino transport — embodies the spirit of "konting tiyaga lang" (just a little patience, we\'ll get there).',
        'effect':      'KILLS ALL ENEMIES on screen instantly. Boss hit -4 HP. 45-frame invincible turbo dash. Chrome exhaust smoke + gold gleam particles.',
        'cooldown':    '11.7 sec',
        'type':        'Screen Wipe / Ram',
        'color':       (255, 200, 0),
        'tip':         'Absolute panic button — use when screen is full of enemies to wipe them instantly.',
    },
}

CHARACTER_ORDER = [
    'Juan', 'Maria', 'LapuLapu', 'Jose', 'Andres',
    'Aswang', 'Tikbalang', 'Kapre', 'Manananggal', 'Datu',
    'Sorbetero', 'Taho', 'Malunggay', 'Batak', 'Jeepney'
]

_portrait_cache = {}

def _load_portrait(char_name):
    key = char_name.lower()
    if key in _portrait_cache: return _portrait_cache[key]
    path = os.path.join(os.path.dirname(__file__), '..', 'concept_art', f"{key}_concept_*.png")
    matches = glob.glob(path)
    if matches:
        try:
            img = pygame.image.load(matches[0]).convert_alpha()
            w, h = img.get_size()
            target_h = 340
            img = pygame.transform.smoothscale(img, (int(w * (target_h / h)), target_h))
            _portrait_cache[key] = img
            return img
        except: pass
    _portrait_cache[key] = None
    return None


def draw_skill_info(screen, font, big_font, selected_idx):
    """Full-screen character skill codex viewer."""
    ch = CHARACTER_ORDER[selected_idx % len(CHARACTER_ORDER)]
    info = SKILL_CODEX.get(ch, {})
    col = info.get('color', (255, 215, 0))

    # Dark background with gradient tint
    screen.fill((8, 10, 20))
    grad = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for y in range(HEIGHT):
        alpha = int(60 * (y / HEIGHT))
        r = int(col[0] * 0.15)
        g = int(col[1] * 0.15)
        b = int(col[2] * 0.15)
        pygame.draw.line(grad, (r, g, b, alpha), (0, y), (WIDTH, y))
    screen.blit(grad, (0, 0))

    # Top header bar
    pygame.draw.rect(screen, (20, 20, 40), (0, 0, WIDTH, 80))
    pygame.draw.line(screen, col, (0, 80), (WIDTH, 80), 3)
    title_surf = big_font.render("CHARACTER SKILL CODEX", True, col)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 22))

    # Navigation hint
    nav = font.render(f"[◄] [{selected_idx + 1}/{len(CHARACTER_ORDER)}] [►]  |  [ESC] Back", True, (130, 130, 130))
    screen.blit(nav, (WIDTH // 2 - nav.get_width() // 2, HEIGHT - 32))

    # Left panel — portrait
    portrait_area = pygame.Rect(30, 100, 340, 400)
    pygame.draw.rect(screen, (18, 18, 35), portrait_area, border_radius=15)
    pygame.draw.rect(screen, col, portrait_area, 3, border_radius=15)

    portrait = _load_portrait(ch)
    if portrait:
        px = portrait_area.centerx - portrait.get_width() // 2
        py = portrait_area.centery - portrait.get_height() // 2
        screen.blit(portrait, (px, py))
    else:
        # Fallback placeholder
        pfont = pygame.font.SysFont("monospace", 48, bold=True)
        ph = pfont.render(ch[0].upper(), True, col)
        screen.blit(ph, (portrait_area.centerx - ph.get_width()//2,
                          portrait_area.centery - ph.get_height()//2))

    # Character name below portrait
    cname = big_font.render(ch.upper(), True, WHITE)
    screen.blit(cname, (portrait_area.centerx - cname.get_width()//2, portrait_area.bottom + 12))

    # Right panel — skill info
    rx = portrait_area.right + 30
    ry = 98
    rw = WIDTH - rx - 20
    rh = HEIGHT - 130

    # Skill name banner
    pygame.draw.rect(screen, col, (rx, ry, rw, 58), border_radius=10)
    sk_name = big_font.render(info.get('skill_name', '???'), True, (10, 10, 20))
    screen.blit(sk_name, (rx + rw//2 - sk_name.get_width()//2, ry + 14))

    # Type badge
    ty = ry + 70
    type_str = info.get('type', '')
    type_surf = font.render(f"Type: {type_str}", True, col)
    screen.blit(type_surf, (rx, ty))
    cd_surf = font.render(f"Cooldown: {info.get('cooldown', '?')}", True, (200, 200, 200))
    screen.blit(cd_surf, (rx + rw - cd_surf.get_width(), ty))

    # Divider
    pygame.draw.line(screen, col, (rx, ty + 28), (rx + rw, ty + 28), 1)

    # Lore section
    ly = ty + 42
    lore_label = font.render("LORE", True, col)
    screen.blit(lore_label, (rx, ly))
    ly += 28
    for line in _wrap_text(info.get('lore', ''), font, rw):
        lore_line = font.render(line, True, (190, 190, 220))
        screen.blit(lore_line, (rx, ly))
        ly += 26

    ly += 12
    pygame.draw.line(screen, (60, 60, 80), (rx, ly), (rx + rw, ly), 1)
    ly += 14

    # Effect section
    eff_label = font.render("SKILL EFFECT", True, col)
    screen.blit(eff_label, (rx, ly))
    ly += 28
    for line in _wrap_text(info.get('effect', ''), font, rw):
        eff_line = font.render(line, True, WHITE)
        screen.blit(eff_line, (rx, ly))
        ly += 26

    ly += 14
    pygame.draw.line(screen, (60, 60, 80), (rx, ly), (rx + rw, ly), 1)
    ly += 14

    # Tip section
    tip_label = font.render("💡 PRO TIP", True, (255, 230, 0))
    screen.blit(tip_label, (rx, ly))
    ly += 28
    for line in _wrap_text(info.get('tip', ''), font, rw):
        tip_line = font.render(line, True, (220, 220, 120))
        screen.blit(tip_line, (rx, ly))
        ly += 26

    # Mini character selector row at bottom
    _draw_char_row(screen, font, selected_idx, HEIGHT - 75)


def _wrap_text(text, font, max_w):
    words = text.split()
    lines, cur = [], []
    for w in words:
        cur.append(w)
        if font.size(' '.join(cur))[0] > max_w - 10:
            cur.pop()
            lines.append(' '.join(cur))
            cur = [w]
    lines.append(' '.join(cur))
    return lines


def _draw_char_row(screen, font, selected_idx, y):
    """Mini tab row showing all characters at the bottom."""
    n = len(CHARACTER_ORDER)
    slot_w = min(70, (WIDTH - 40) // n)
    total_w = slot_w * n
    start_x = WIDTH // 2 - total_w // 2
    for i, ch in enumerate(CHARACTER_ORDER):
        col = SKILL_CODEX[ch]['color']
        x = start_x + i * slot_w
        is_sel = (i == selected_idx)
        bg = col if is_sel else (30, 30, 45)
        brd = col if is_sel else (60, 60, 80)
        try:
            pygame.draw.rect(screen, bg,  (x+2, y, slot_w-4, 38), border_radius=6)
            pygame.draw.rect(screen, brd, (x+2, y, slot_w-4, 38), 2, border_radius=6)
        except TypeError:
            pygame.draw.rect(screen, bg,  (x+2, y, slot_w-4, 38))
            pygame.draw.rect(screen, brd, (x+2, y, slot_w-4, 38), 2)
        abbr = font.render(ch[:4], True, (10,10,10) if is_sel else (160,160,160))
        screen.blit(abbr, (x + slot_w//2 - abbr.get_width()//2, y + 10))


# ──────────────────────────────────────────
# In-game HUD skill flash (shown on E press)
# ──────────────────────────────────────────

def get_skill_flash_info(character_name):
    """Return (skill_name, color) for HUD flash display."""
    info = SKILL_CODEX.get(character_name)
    if not info: return None, None
    return info['skill_name'], info['color']
