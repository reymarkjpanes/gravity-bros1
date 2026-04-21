"""
Procedural background renderer for Gravity Bros: Philippine Adventure.
Each of the 10 levels has a unique, multi-layered parallax background
based on real Philippine landmarks and ecosystems.
"""
import pygame
import math
import random

from config import WIDTH, HEIGHT

# ─────────────────────────────────────────────────────────────────────
# Pre-cached surfaces (built once per level, reused every frame)
# ─────────────────────────────────────────────────────────────────────
_bg_cache = {}


def _clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def _lerp_color(c1, c2, t):
    return tuple(_clamp(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _gradient_fill(surf, top_color, bot_color):
    """Vertical gradient fill on a surface."""
    w, h = surf.get_size()
    for y in range(h):
        t = y / max(1, h - 1)
        c = _lerp_color(top_color, bot_color, t)
        pygame.draw.line(surf, c, (0, y), (w, y))


def _draw_cloud(surf, x, y, w, h, color=(255, 255, 255), alpha=120):
    """Soft puffy cloud using overlapping ellipses."""
    cs = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
    c = (*color, alpha)
    cx, cy = w // 2 + 10, h // 2 + 10
    pygame.draw.ellipse(cs, c, (cx - w // 3, cy - h // 3, w // 2, h // 2))
    pygame.draw.ellipse(cs, c, (cx - w // 4 - 10, cy - h // 5, w // 2, h // 2))
    pygame.draw.ellipse(cs, c, (cx + 5, cy - h // 4, w // 2, h * 2 // 5))
    pygame.draw.ellipse(cs, c, (cx - w // 6, cy, w // 3, h // 3))
    surf.blit(cs, (x - 10, y - 10))


def _draw_mountain_range(surf, base_y, peaks, color, shadow_color=None):
    """Draw a mountain range with multiple peaks."""
    w = surf.get_width()
    points = [(0, base_y)]
    for px, py in peaks:
        points.append((px, py))
    points.append((w, base_y))
    points.append((w, base_y + 100))
    points.append((0, base_y + 100))
    pygame.draw.polygon(surf, color, points)
    if shadow_color:
        for px, py in peaks:
            shadow_pts = [(px, py), (px + 30, py + 40), (px - 10, base_y)]
            pygame.draw.polygon(surf, shadow_color, shadow_pts)


def _draw_palm_tree(surf, x, y, trunk_h=50, leaf_color=(34, 139, 34)):
    """Draw a simple palm tree."""
    pygame.draw.rect(surf, (100, 60, 20), (x - 3, y - trunk_h, 6, trunk_h))
    # Leaves
    for angle_deg in [-60, -30, 0, 30, 60]:
        rad = math.radians(angle_deg)
        ex = x + int(math.sin(rad) * 25)
        ey = y - trunk_h + int(-abs(math.cos(rad)) * 10)
        pygame.draw.line(surf, leaf_color, (x, y - trunk_h), (ex, ey - 15), 3)
        pygame.draw.ellipse(surf, leaf_color, (ex - 8, ey - 20, 16, 12))


def _draw_pine_tree(surf, x, y, h=40, color=(27, 94, 32)):
    """Draw a pine/conifer tree."""
    pygame.draw.rect(surf, (80, 50, 30), (x - 2, y - 8, 4, 8))
    for i in range(3):
        iy = y - 8 - i * (h // 4)
        iw = 14 - i * 3
        pygame.draw.polygon(surf, color, [(x, iy - h // 4), (x - iw, iy), (x + iw, iy)])


def _draw_building(surf, x, y, w, h, wall_color, roof_color, has_windows=True):
    """Draw a building with optional windows."""
    pygame.draw.rect(surf, wall_color, (x, y - h, w, h))
    # Roof
    pygame.draw.polygon(surf, roof_color, [(x - 5, y - h), (x + w // 2, y - h - 15), (x + w + 5, y - h)])
    if has_windows:
        for wy in range(y - h + 10, y - 5, 14):
            for wx in range(x + 4, x + w - 6, 10):
                wc = (255, 255, 150) if random.random() > 0.4 else (40, 40, 60)
                pygame.draw.rect(surf, wc, (wx, wy, 6, 8))


def _draw_stalactite(surf, x, y, h, color):
    """Hanging stalactite for cave themes."""
    w = max(3, abs(h) // 4)
    pygame.draw.polygon(surf, color, [(x - w, y), (x, y + h), (x + w, y)])


def _draw_coral(surf, x, y, color):
    """Simple branching coral."""
    pygame.draw.line(surf, color, (x, y), (x, y - 20), 3)
    pygame.draw.line(surf, color, (x, y - 10), (x - 8, y - 18), 2)
    pygame.draw.line(surf, color, (x, y - 10), (x + 8, y - 18), 2)
    pygame.draw.circle(surf, color, (x, y - 20), 4)
    pygame.draw.circle(surf, color, (x - 8, y - 18), 3)
    pygame.draw.circle(surf, color, (x + 8, y - 18), 3)


# ─────────────────────────────────────────────────────────────────────
# Per-level background builders (called once, cached)
# ─────────────────────────────────────────────────────────────────────

def _build_banaue(w, h):
    """Level 1 — Banaue Rice Terraces: layered green terraces under blue sky."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (135, 200, 255), (200, 240, 255))
    # Distant misty mountains
    _draw_mountain_range(mid, h * 0.45, [
        (w * 0.1, h * 0.25), (w * 0.25, h * 0.18), (w * 0.5, h * 0.22),
        (w * 0.7, h * 0.15), (w * 0.9, h * 0.28)
    ], (120, 180, 140), (90, 150, 110))
    # Rice terraces (horizontal stepped layers)
    terrace_colors = [(100, 180, 80), (80, 160, 60), (60, 140, 40), (40, 120, 30), (30, 100, 20)]
    for i, tc in enumerate(terrace_colors):
        ty = int(h * 0.50 + i * 28)
        pygame.draw.rect(fg, tc, (0, ty, w, 28))
        # Terrace edge highlight
        pygame.draw.line(fg, (tc[0] + 30, tc[1] + 30, tc[2] + 10), (0, ty), (w, ty), 2)
        # Water reflection in paddy
        water_c = (100, 200, 220, 80)
        ws = pygame.Surface((w, 8), pygame.SRCALPHA)
        ws.fill(water_c)
        fg.blit(ws, (0, ty + 10))
    # Scattered huts
    for hx in [w * 0.2, w * 0.65]:
        pygame.draw.rect(fg, (120, 70, 30), (hx, h * 0.44, 20, 15))
        pygame.draw.polygon(fg, (80, 50, 20), [(hx - 3, h * 0.44), (hx + 10, h * 0.44 - 12), (hx + 23, h * 0.44)])
    return {'sky': sky, 'mid': mid, 'fg': fg}


def _build_chocolate_hills(w, h):
    """Level 2 — Chocolate Hills, Bohol: rounded brown hills under clear sky."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (150, 220, 255), (220, 240, 255))
    # Layered hills
    random.seed(42)
    for layer in range(3):
        shade = 140 + layer * 25
        base_y = h * (0.55 + layer * 0.08)
        for i in range(8):
            cx = i * (w // 7) + random.randint(-20, 20)
            cr = random.randint(35, 65) - layer * 5
            c = (shade, shade - 40, shade - 80)
            pygame.draw.circle(fg, c, (int(cx), int(base_y)), cr)
            # Highlight
            pygame.draw.arc(fg, (shade + 20, shade - 20, shade - 60),
                            (int(cx) - cr, int(base_y) - cr, cr * 2, cr * 2),
                            0.3, 2.8, 2)
    # Green grass base
    pygame.draw.rect(fg, (80, 140, 50), (0, int(h * 0.78), w, int(h * 0.22)))
    _gradient_fill(pygame.Surface((1, 1)), (80, 140, 50), (60, 100, 30))  # just to avoid error
    # Scattered palm trees
    for tx in range(50, w, 180):
        _draw_palm_tree(fg, tx + random.randint(-15, 15), int(h * 0.78), 40)
    random.seed()
    return {'sky': sky, 'mid': mid, 'fg': fg}


def _build_boracay(w, h):
    """Level 3 — Boracay Beach: white sand, turquoise ocean, sunset sky."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (255, 150, 80), (100, 200, 255))
    # Sun
    pygame.draw.circle(sky, (255, 220, 100), (int(w * 0.75), int(h * 0.2)), 40)
    pygame.draw.circle(sky, (255, 240, 180), (int(w * 0.75), int(h * 0.2)), 50, 3)
    # Ocean layers
    ocean_colors = [(0, 150, 200), (0, 170, 220), (20, 190, 230), (60, 210, 240)]
    for i, oc in enumerate(ocean_colors):
        oy = int(h * 0.50 + i * 25)
        pygame.draw.rect(fg, oc, (0, oy, w, 25))
    # White sand beach
    pygame.draw.rect(fg, (245, 235, 200), (0, int(h * 0.75), w, int(h * 0.25)))
    pygame.draw.rect(fg, (235, 225, 190), (0, int(h * 0.80), w, int(h * 0.20)))
    # Foam line
    for fx in range(0, w, 12):
        fy = int(h * 0.75) + random.randint(-2, 2)
        pygame.draw.circle(fg, (255, 255, 255), (fx, fy), random.randint(3, 6))
    # Palm trees on beach
    for tx in [w * 0.1, w * 0.35, w * 0.7, w * 0.9]:
        _draw_palm_tree(fg, int(tx), int(h * 0.75), 55, (20, 120, 20))
    # Sailboat
    bx, by = int(w * 0.5), int(h * 0.55)
    pygame.draw.polygon(fg, (200, 180, 150), [(bx - 15, by), (bx + 15, by), (bx + 5, by + 10), (bx - 5, by + 10)])
    pygame.draw.line(fg, (120, 80, 40), (bx, by), (bx, by - 25), 2)
    pygame.draw.polygon(fg, (255, 255, 255), [(bx, by - 25), (bx + 15, by - 10), (bx, by - 5)])
    return {'sky': sky, 'mid': mid, 'fg': fg}


def _build_palawan_cave(w, h):
    """Level 4 — Palawan Underground River: dark cave with glowing formations."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (10, 15, 30), (20, 40, 60))
    # Stalactites from ceiling
    random.seed(44)
    for i in range(20):
        sx = random.randint(0, w)
        sh = random.randint(20, 80)
        sc = (random.randint(60, 100), random.randint(70, 110), random.randint(80, 120))
        _draw_stalactite(fg, sx, 0, sh, sc)
    # Stalagmites from floor
    for i in range(15):
        sx = random.randint(0, w)
        sh = random.randint(15, 50)
        sc = (random.randint(50, 90), random.randint(60, 100), random.randint(70, 110))
        _draw_stalactite(fg, sx, h, -sh, sc)
    # Bioluminescent glow spots
    for _ in range(30):
        gx = random.randint(0, w)
        gy = random.randint(0, h)
        gr = random.randint(3, 12)
        gc = random.choice([(0, 255, 200), (0, 200, 255), (100, 255, 150), (80, 200, 255)])
        gs = pygame.Surface((gr * 4, gr * 4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*gc, 60), (gr * 2, gr * 2), gr * 2)
        pygame.draw.circle(gs, (*gc, 150), (gr * 2, gr * 2), gr)
        fg.blit(gs, (gx - gr * 2, gy - gr * 2))
    # Underground river water at bottom
    water = pygame.Surface((w, 50), pygame.SRCALPHA)
    _gradient_fill(water, (0, 80, 120), (0, 40, 80))
    water.set_alpha(180)
    fg.blit(water, (0, h - 50))
    random.seed()
    return {'sky': sky, 'mid': mid, 'fg': fg}


def _build_mayon(w, h):
    """Level 5 — Mayon Volcano: erupting volcano with lava glow."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (60, 10, 10), (180, 60, 20))
    # Volcanic ash clouds
    for _ in range(6):
        _draw_cloud(sky, random.randint(0, w), random.randint(10, int(h * 0.3)),
                    random.randint(80, 140), random.randint(30, 50), (80, 40, 30), 100)
    # The volcano (center)
    vx = w // 2
    pygame.draw.polygon(fg, (60, 40, 30), [(vx - 200, h * 0.85), (vx, h * 0.15), (vx + 200, h * 0.85)])
    pygame.draw.polygon(fg, (80, 50, 35), [(vx - 180, h * 0.85), (vx, h * 0.18), (vx + 100, h * 0.85)])
    # Crater glow
    pygame.draw.ellipse(fg, (255, 100, 0), (vx - 15, h * 0.14, 30, 12))
    pygame.draw.ellipse(fg, (255, 200, 50), (vx - 8, h * 0.145, 16, 6))
    # Lava streams
    random.seed(45)
    for i in range(4):
        lx = vx + random.randint(-80, 80)
        points = [(lx, int(h * 0.2))]
        cy = h * 0.2
        for _ in range(6):
            cy += random.randint(20, 40)
            lx += random.randint(-15, 15)
            points.append((int(lx), int(cy)))
        for j in range(len(points) - 1):
            pygame.draw.line(fg, (255, random.randint(80, 180), 0), points[j], points[j + 1], 3)
    # Ground lava glow
    lava = pygame.Surface((w, 40), pygame.SRCALPHA)
    _gradient_fill(lava, (255, 80, 0), (200, 30, 0))
    lava.set_alpha(150)
    fg.blit(lava, (0, h - 40))
    random.seed()
    return {'sky': sky, 'mid': mid, 'fg': fg}


def _build_pulag(w, h):
    """Level 6 — Mount Pulag: sea of clouds, misty peaks, purple sunrise."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (180, 120, 200), (220, 240, 255))
    # Distant mountain silhouettes (dark blue)
    _draw_mountain_range(mid, h * 0.55, [
        (w * 0.05, h * 0.30), (w * 0.2, h * 0.22), (w * 0.35, h * 0.28),
        (w * 0.55, h * 0.18), (w * 0.75, h * 0.25), (w * 0.95, h * 0.32)
    ], (80, 100, 140), (60, 80, 120))
    # Closer mountains (blue-green)
    _draw_mountain_range(mid, h * 0.65, [
        (w * 0.1, h * 0.42), (w * 0.3, h * 0.38), (w * 0.6, h * 0.35),
        (w * 0.8, h * 0.45), (w * 0.95, h * 0.50)
    ], (100, 130, 100), (80, 110, 80))
    # Sea of clouds
    for i in range(12):
        cx = random.randint(-20, w)
        cy = int(h * 0.58 + random.randint(-10, 20))
        _draw_cloud(sky, cx, cy, random.randint(100, 200), random.randint(25, 45), (255, 255, 255), 160)
    # Pine trees in foreground
    for tx in range(30, w, 80):
        _draw_pine_tree(fg, tx + random.randint(-10, 10), int(h * 0.82), random.randint(30, 50))
    # Grass base
    pygame.draw.rect(fg, (50, 100, 40), (0, int(h * 0.82), w, int(h * 0.18)))
    return {'sky': sky, 'mid': mid, 'fg': fg}


def _build_tubbataha(w, h):
    """Level 7 — Tubbataha Reefs: deep ocean with coral and fish."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (0, 30, 100), (0, 80, 140))
    # Light rays from above
    random.seed(47)
    for _ in range(8):
        rx = random.randint(0, w)
        rw = random.randint(15, 40)
        ray = pygame.Surface((rw, h), pygame.SRCALPHA)
        for ry in range(h):
            a = int(40 * (1.0 - ry / h))
            pygame.draw.line(ray, (100, 200, 255, a), (0, ry), (rw, ry))
        fg.blit(ray, (rx, 0))
    # Coral reef floor
    reef_y = int(h * 0.75)
    pygame.draw.rect(fg, (40, 80, 60), (0, reef_y, w, h - reef_y))
    coral_colors = [(255, 80, 80), (255, 150, 50), (200, 100, 200), (0, 200, 150), (255, 200, 100)]
    for i in range(25):
        cx = random.randint(0, w)
        _draw_coral(fg, cx, reef_y, random.choice(coral_colors))
    # Bubbles
    for _ in range(20):
        bx = random.randint(0, w)
        by = random.randint(int(h * 0.2), int(h * 0.7))
        br = random.randint(2, 6)
        pygame.draw.circle(fg, (150, 220, 255), (bx, by), br, 1)
    # Small fish silhouettes
    for _ in range(8):
        fx = random.randint(0, w)
        fy = random.randint(int(h * 0.15), int(h * 0.65))
        fc = random.choice([(255, 200, 0), (0, 200, 255), (255, 100, 100)])
        pygame.draw.ellipse(fg, fc, (fx, fy, 12, 6))
        pygame.draw.polygon(fg, fc, [(fx + 12, fy + 3), (fx + 18, fy - 1), (fx + 18, fy + 7)])
    random.seed()
    return {'sky': sky, 'mid': mid, 'fg': fg}


def _build_kawasan(w, h):
    """Level 8 — Kawasan Falls: lush jungle waterfall canyon."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (150, 220, 200), (80, 180, 140))
    # Cliff walls on sides
    pygame.draw.rect(fg, (60, 90, 50), (0, 0, 80, h))
    pygame.draw.rect(fg, (60, 90, 50), (w - 80, 0, 80, h))
    pygame.draw.rect(fg, (50, 80, 40), (0, 0, 70, h))
    pygame.draw.rect(fg, (50, 80, 40), (w - 70, 0, 70, h))
    # Waterfall (center)
    wf_x = w // 2 - 20
    wf_w = 40
    wf_surf = pygame.Surface((wf_w, h), pygame.SRCALPHA)
    for y in range(h):
        a = 120 + int(30 * math.sin(y * 0.1))
        pygame.draw.line(wf_surf, (200, 240, 255, a), (0, y), (wf_w, y))
    fg.blit(wf_surf, (wf_x, 0))
    # Pool at bottom
    pool = pygame.Surface((w, 60), pygame.SRCALPHA)
    _gradient_fill(pool, (0, 180, 200), (0, 140, 160))
    pool.set_alpha(200)
    fg.blit(pool, (0, h - 60))
    # Lush vegetation
    random.seed(48)
    for side in [0, w]:
        for i in range(8):
            ty = random.randint(0, h - 40)
            tx = side + random.randint(-10, 60) if side == 0 else side + random.randint(-60, 10)
            leaf_c = (random.randint(20, 60), random.randint(120, 200), random.randint(20, 80))
            pygame.draw.ellipse(fg, leaf_c, (tx, ty, random.randint(20, 45), random.randint(15, 30)))
    # Mist
    for _ in range(6):
        mx = random.randint(0, w)
        my = random.randint(int(h * 0.4), int(h * 0.7))
        ms = pygame.Surface((120, 30), pygame.SRCALPHA)
        ms.fill((255, 255, 255, 40))
        fg.blit(ms, (mx, my))
    random.seed()
    return {'sky': sky, 'mid': mid, 'fg': fg}


def _build_vigan(w, h):
    """Level 9 — Vigan Calle Crisologo: colonial Spanish-era cobblestone street."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (255, 180, 80), (255, 220, 130))
    # Warm sunset clouds
    for _ in range(5):
        _draw_cloud(sky, random.randint(0, w), random.randint(20, int(h * 0.25)),
                    random.randint(80, 140), random.randint(20, 35), (255, 200, 150), 100)
    # Row of colonial buildings
    random.seed(49)
    bx = 0
    while bx < w:
        bw = random.randint(40, 70)
        bh = random.randint(80, 130)
        wall = random.choice([(200, 170, 120), (180, 150, 100), (220, 190, 140), (190, 160, 110)])
        roof = random.choice([(140, 60, 30), (120, 50, 20), (160, 70, 35)])
        _draw_building(fg, bx, int(h * 0.78), bw, bh, wall, roof, True)
        bx += bw + random.randint(3, 10)
    # Cobblestone road
    road_y = int(h * 0.78)
    pygame.draw.rect(fg, (120, 100, 70), (0, road_y, w, h - road_y))
    for sy in range(road_y + 4, h, 12):
        for sx in range(0, w, 14):
            sc = random.randint(90, 130)
            pygame.draw.rect(fg, (sc, sc - 10, sc - 25), (sx + (sy % 2) * 7, sy, 10, 8), border_radius=2)
    # Calesa (horse carriage) silhouette
    cx = int(w * 0.6)
    cy = int(h * 0.78) - 5
    pygame.draw.circle(fg, (60, 40, 20), (cx, cy), 12, 2)
    pygame.draw.circle(fg, (60, 40, 20), (cx + 30, cy), 12, 2)
    pygame.draw.rect(fg, (100, 60, 30), (cx - 5, cy - 25, 40, 20))
    random.seed()
    return {'sky': sky, 'mid': mid, 'fg': fg}


def _build_manila(w, h):
    """Level 10 — Manila Skyline: neon-lit city at night with skyscrapers."""
    sky = pygame.Surface((w, h), pygame.SRCALPHA)
    mid = pygame.Surface((w, h), pygame.SRCALPHA)
    fg = pygame.Surface((w, h), pygame.SRCALPHA)
    _gradient_fill(sky, (5, 5, 30), (20, 15, 60))
    # Stars
    random.seed(50)
    for _ in range(60):
        sx = random.randint(0, w)
        sy = random.randint(0, int(h * 0.4))
        pygame.draw.circle(sky, (255, 255, 255), (sx, sy), 1)
    # Moon
    pygame.draw.circle(sky, (220, 220, 240), (int(w * 0.8), int(h * 0.12)), 25)
    pygame.draw.circle(sky, (200, 200, 220), (int(w * 0.8) + 5, int(h * 0.12) - 3), 22)
    # Skyscrapers
    building_base = int(h * 0.85)
    bx = 0
    while bx < w:
        bw = random.randint(25, 55)
        bh = random.randint(80, 220)
        # Dark building body
        bc = random.choice([(30, 30, 50), (25, 25, 45), (35, 35, 55), (20, 20, 40)])
        pygame.draw.rect(fg, bc, (bx, building_base - bh, bw, bh))
        # Lit windows
        for wy in range(building_base - bh + 5, building_base - 3, 10):
            for wx in range(bx + 3, bx + bw - 3, 8):
                if random.random() > 0.3:
                    wc = random.choice([(255, 255, 150), (255, 200, 100), (200, 200, 255), (100, 200, 255)])
                    pygame.draw.rect(fg, wc, (wx, wy, 4, 6))
        # Antenna/spire on tall buildings
        if bh > 150:
            pygame.draw.line(fg, (100, 100, 100), (bx + bw // 2, building_base - bh), (bx + bw // 2, building_base - bh - 20), 2)
            pygame.draw.circle(fg, (255, 0, 0), (bx + bw // 2, building_base - bh - 20), 2)
        bx += bw + random.randint(2, 8)
    # Neon glow strip at building base
    neon = pygame.Surface((w, 6), pygame.SRCALPHA)
    for nx in range(0, w, 4):
        nc = random.choice([(255, 0, 200), (0, 255, 255), (255, 100, 0), (0, 255, 100)])
        pygame.draw.rect(neon, (*nc, 180), (nx, 0, 4, 6))
    fg.blit(neon, (0, building_base - 3))
    # Water reflection at bottom
    refl = pygame.Surface((w, int(h * 0.15)), pygame.SRCALPHA)
    _gradient_fill(refl, (10, 10, 50), (5, 5, 30))
    refl.set_alpha(200)
    fg.blit(refl, (0, building_base))
    random.seed()
    return {'sky': sky, 'mid': mid, 'fg': fg}


# ─────────────────────────────────────────────────────────────────────
# Builder dispatch
# ─────────────────────────────────────────────────────────────────────

_BUILDERS = [
    _build_banaue,          # 1
    _build_chocolate_hills, # 2
    _build_boracay,         # 3
    _build_palawan_cave,    # 4
    _build_mayon,           # 5
    _build_pulag,           # 6
    _build_tubbataha,       # 7
    _build_kawasan,         # 8
    _build_vigan,           # 9
    _build_manila,          # 10
]


def get_background(level, w=None, h=None):
    """Return (or build+cache) the static background surface for a level."""
    if w is None: w = WIDTH
    if h is None: h = HEIGHT
    key = (level, w, h)
    if key not in _bg_cache:
        idx = (level - 1) % len(_BUILDERS)
        _bg_cache[key] = _BUILDERS[idx](w, h)
    return _bg_cache[key]


def draw_background(screen, level, camera_x, time):
    """Render the full multi-layer background with parallax for a level."""
    bg_layers = get_background(level)
    
    # Parallax speeds
    speeds = {
        'sky': 0.02,
        'mid': 0.08,
        'fg': 0.15
    }
    
    for layer in ['sky', 'mid', 'fg']:
        surf = bg_layers[layer]
        parallax_x = int(camera_x * speeds[layer]) % surf.get_width()
        screen.blit(surf, (-parallax_x, 0))
        if parallax_x > 0:
            screen.blit(surf, (surf.get_width() - parallax_x, 0))
