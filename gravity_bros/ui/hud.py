import pygame
import math
from config import WIDTH, HEIGHT, WHITE, GOLD, RED, ORANGE, GREEN

def draw_hud(screen, font, big_font, player, theme, current_level, weapon, bosses=None):
    if bosses is None: bosses = []

    # Character Attack Info (bottom-left)
    ATTACK_NAMES = {
        'Juan': ('Guava Throw', (180, 220, 80)),
        'Maria': ('Fan Swipe', (255, 160, 190)),
        'LapuLapu': ('Kris Blade', (255, 200, 0)),
        'Jose': ('Quill Shot', (100, 150, 255)),
        'Andres': ('Bolo Slash', (200, 200, 200)),
        'Aswang': ('Tongue Lash', (220, 60, 80)),
        'Tikbalang': ('Hoof Kick', (130, 90, 40)),
        'Kapre': ('Ember Toss', (255, 80, 0)),
        'Manananggal': ('Claw Swipe', (160, 0, 80)),
        'Datu': ('Spear Throw', (255, 140, 0)),
        'Sorbetero': ('Ice Scoop', (200, 230, 255)),
        'Taho': ('Taho Splash', (160, 90, 20)),
        'Malunggay': ('Leaf Burst', (0, 200, 50)),
        'Batak': ('Poison Dart', (0, 180, 40)),
        'Jeepney': ('HONK!', (255, 220, 0)),
    }
    ch = getattr(player, 'selected_character', 'Juan')
    atk_name, atk_color = ATTACK_NAMES.get(ch, ('Attack', WHITE))
    wx, wy = 20, HEIGHT - 55
    # Attack label
    atk_bg = pygame.Surface((160, 28), pygame.SRCALPHA)
    atk_bg.fill((0, 0, 0, 160))
    screen.blit(atk_bg, (wx, wy))
    pygame.draw.rect(screen, atk_color, (wx, wy, 160, 28), 2)
    lbl = font.render(f"F: {atk_name}", True, atk_color)
    screen.blit(lbl, (wx + 6, wy + 4))
    # Attack cooldown micro-bar
    cd = getattr(player, 'attack_cooldown', 0)
    rate = getattr(player, 'attack_rate', 20)
    if cd > 0:
        filled = int(156 * (1.0 - cd / max(1, rate)))
        pygame.draw.rect(screen, (60, 60, 60), (wx + 2, wy + 24, 156, 4))
        pygame.draw.rect(screen, atk_color,   (wx + 2, wy + 24, filled, 4))

    hud_bg = pygame.Surface((WIDTH, 70), pygame.SRCALPHA)
    hud_bg.fill((0, 0, 0, 180))
    screen.blit(hud_bg, (0, 0))
    
    level_text = big_font.render(f"LEVEL {current_level}", True, WHITE)
    theme_text = font.render(f"{theme['name']}", True, (200, 200, 255))
    
    # Center Block
    screen.blit(level_text, (WIDTH // 2 - level_text.get_width() // 2, 5))
    screen.blit(theme_text, (WIDTH // 2 - theme_text.get_width() // 2, 40))

    score_text = font.render(f"SCORE: {player.level_score}", True, GOLD)
    coins_text = font.render(f"PISO:  {player.coins}", True, GOLD)

    # Left Block
    screen.blit(score_text, (20, 10))
    screen.blit(coins_text, (20, 35))
    
    # ── HP Hearts ──
    hp = getattr(player, 'hp', 3)
    max_hp = getattr(player, 'max_hp', 3)
    heart_x = 20
    heart_y = 58
    for i in range(max_hp):
        cx = heart_x + i * 22
        cy = heart_y + 8
        if i < hp:
            # Full heart — red with slight pulse
            pulse = 1.0 + 0.1 * math.sin(pygame.time.get_ticks() * 0.005 + i * 0.5)
            r = int(8 * pulse)
            # Heart shape using two circles and a triangle
            pygame.draw.circle(screen, (220, 20, 30), (cx - 3, cy - 2), r // 2 + 2)
            pygame.draw.circle(screen, (220, 20, 30), (cx + 3, cy - 2), r // 2 + 2)
            pygame.draw.polygon(screen, (220, 20, 30), [
                (cx - r // 2 - 2, cy), (cx + r // 2 + 2, cy), (cx, cy + r)
            ])
            # Highlight
            pygame.draw.circle(screen, (255, 100, 100), (cx - 2, cy - 3), 2)
        else:
            # Empty heart — dark outline
            pygame.draw.circle(screen, (80, 20, 20), (cx - 3, cy - 2), 5)
            pygame.draw.circle(screen, (80, 20, 20), (cx + 3, cy - 2), 5)
            pygame.draw.polygon(screen, (80, 20, 20), [
                (cx - 6, cy), (cx + 6, cy), (cx, cy + 7)
            ])
    
    combo = getattr(player, 'combo_kills', 0)
    if combo > 1:
        # Color escalation
        if combo >= 10: c_color = (255, 0, 0)
        elif combo >= 6: c_color = ORANGE
        elif combo >= 3: c_color = (255, 255, 0)
        else: c_color = WHITE
        # Multiplier text
        if combo >= 10: mult = "×3.0"
        elif combo >= 6: mult = "×2.0"
        elif combo >= 3: mult = "×1.5"
        else: mult = ""
        # Pulsing scale effect
        pulse = 1.0 + 0.1 * math.sin(pygame.time.get_ticks() * 0.01)
        combo_str = f"COMBO ×{combo}! {mult}"
        combo_surf = big_font.render(combo_str, True, c_color)
        pw = int(combo_surf.get_width() * pulse)
        ph = int(combo_surf.get_height() * pulse)
        combo_surf = pygame.transform.scale(combo_surf, (max(1, pw), max(1, ph)))
        screen.blit(combo_surf, (20, 80))
        
    # Right Block
    gravity_text = font.render(f"GRAVITY: {'UP' if getattr(player, 'gravity_dir', 1) == -1 else 'DOWN'}", True, WHITE)
    screen.blit(gravity_text, (WIDTH - gravity_text.get_width() - 20, 10))
    
    # Skill Bar (E)
    ab_rect = pygame.Rect(WIDTH - 150, 35, 130, 12)
    pygame.draw.rect(screen, (50, 50, 50), ab_rect)
    max_cd = getattr(player, 'max_cooldown', 100)
    if max_cd <= 0: max_cd = 100
    ab_pct = 1.0 - (player.ability_cooldown / max_cd)
    if ab_pct < 0: ab_pct = 0; 
    if ab_pct > 1: ab_pct = 1
    
    color = (0, 255, 0) if ab_pct >= 1.0 else (255, 165, 0)
    pygame.draw.rect(screen, color, (ab_rect.x, ab_rect.y, int(130 * ab_pct), 12))
    pygame.draw.rect(screen, WHITE, ab_rect, 1)
    ab_txt = font.render(f"SKILL", True, WHITE)
    screen.blit(ab_txt, (WIDTH - 150 - ab_txt.get_width() - 10, 30))

    # Awaken Bar (R) — only if character is evolved
    if getattr(player, 'is_evolved', False):
        aw_rect = pygame.Rect(WIDTH - 150, 52, 130, 12)
        pygame.draw.rect(screen, (50, 40, 0), aw_rect)
        aw_max = getattr(player, 'awaken_max_cooldown', 900)
        aw_cd = getattr(player, 'awaken_cooldown', 0)
        aw_pct = 1.0 - (aw_cd / max(1, aw_max))
        if aw_pct < 0: aw_pct = 0
        if aw_pct > 1: aw_pct = 1
        aw_color = (255, 215, 0) if aw_pct >= 1.0 else (180, 120, 0)
        pygame.draw.rect(screen, aw_color, (aw_rect.x, aw_rect.y, int(130 * aw_pct), 12))
        pygame.draw.rect(screen, (255, 215, 0), aw_rect, 1)
        aw_txt = font.render(f"AWAKEN", True, (255, 215, 0))
        screen.blit(aw_txt, (WIDTH - 150 - aw_txt.get_width() - 10, 48))

    # Boss Health Bar (Dark Souls Style)
    alive_bosses = [b for b in bosses if not b.dead]
    if alive_bosses:
        boss = alive_bosses[0] # Just track the first alive boss
        bw = 600
        bx = WIDTH // 2 - bw // 2
        by = HEIGHT - 40
        pygame.draw.rect(screen, (40, 0, 0), (bx, by, bw, 20))
        h_pct = max(0, boss.health / getattr(boss, 'max_health', 1))
        pygame.draw.rect(screen, (200, 0, 0), (bx, by, int(bw * h_pct), 20))
        pygame.draw.rect(screen, GOLD, (bx, by, bw, 20), 2)
        
        boss_name = font.render(boss.type.replace('_', ' ').upper(), True, WHITE)
        screen.blit(boss_name, (WIDTH // 2 - boss_name.get_width() // 2, HEIGHT - 70))
        
        hp_txt = font.render(f"HP: {max(0, boss.health)} / {boss.max_health}", True, (255, 100, 100))
        screen.blit(hp_txt, (bx + bw + 10, by))
        
        if getattr(boss, 'phase', 1) == 2:
            enrage_txt = font.render("! ENRAGED !", True, RED)
            screen.blit(enrage_txt, (WIDTH // 2 - enrage_txt.get_width() // 2, HEIGHT - 95))

def draw_survival_hud(screen, font, wave_number, enemies_remaining, countdown_timer):
    """Render survival mode HUD at top-center: wave number, enemy count, inter-wave countdown."""
    y = 80
    wave_surf = font.render(f"WAVE {wave_number}", True, GOLD)
    screen.blit(wave_surf, (WIDTH // 2 - wave_surf.get_width() // 2, y))

    enemies_surf = font.render(f"{enemies_remaining} enemies remaining", True, WHITE)
    screen.blit(enemies_surf, (WIDTH // 2 - enemies_surf.get_width() // 2, y + 28))

    if countdown_timer > 0:
        secs = countdown_timer // 60 + 1
        cd_surf = font.render(f"Next wave in {secs}s", True, (255, 255, 0))
        screen.blit(cd_surf, (WIDTH // 2 - cd_surf.get_width() // 2, y + 56))


def draw_challenge_hud(screen, font, objective, time_remaining, progress, target):
    """Render challenge mode HUD at top-center: objective, timer, progress."""
    y = 80
    obj_surf = font.render(objective, True, WHITE)
    screen.blit(obj_surf, (WIDTH // 2 - obj_surf.get_width() // 2, y))

    secs = time_remaining // 60
    timer_color = RED if time_remaining < 10 * 60 else GOLD
    timer_surf = font.render(f"TIME: {secs}s", True, timer_color)
    screen.blit(timer_surf, (WIDTH // 2 - timer_surf.get_width() // 2, y + 28))

    if target > 0:
        prog_surf = font.render(f"{progress}/{target}", True, WHITE)
        screen.blit(prog_surf, (WIDTH // 2 - prog_surf.get_width() // 2, y + 56))


def draw_survival_game_over(screen, font, big_font, wave_number, score):
    """Render survival game-over overlay with wave reached, score, and replay prompt."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    title_surf = big_font.render("SURVIVAL OVER", True, RED)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 100))

    wave_surf = font.render(f"Reached Wave {wave_number}", True, GOLD)
    screen.blit(wave_surf, (WIDTH // 2 - wave_surf.get_width() // 2, HEIGHT // 2 - 30))

    score_surf = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_surf, (WIDTH // 2 - score_surf.get_width() // 2, HEIGHT // 2 + 10))

    retry_surf = font.render("Press R to Play Again", True, WHITE)
    screen.blit(retry_surf, (WIDTH // 2 - retry_surf.get_width() // 2, HEIGHT // 2 + 60))


def draw_challenge_result(screen, font, big_font, stars, coins_earned, failed):
    """Render challenge result overlay: stars or failed, coins earned, retry prompt."""
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    if failed:
        title_surf = big_font.render("FAILED", True, RED)
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 100))
    else:
        star_str = "★" * max(0, min(3, stars)) + "☆" * (3 - max(0, min(3, stars)))
        star_surf = big_font.render(star_str, True, GOLD)
        screen.blit(star_surf, (WIDTH // 2 - star_surf.get_width() // 2, HEIGHT // 2 - 100))

        coins_surf = font.render(f"Coins earned: {coins_earned}", True, GOLD)
        screen.blit(coins_surf, (WIDTH // 2 - coins_surf.get_width() // 2, HEIGHT // 2 - 30))

    retry_surf = font.render("Press R to Retry", True, WHITE)
    screen.blit(retry_surf, (WIDTH // 2 - retry_surf.get_width() // 2, HEIGHT // 2 + 30))


def draw_minimap(screen, platforms, player, bosses, portal, current_level):
    map_w = 200
    map_h = 40
    map_x = WIDTH - map_w - 20
    map_y = HEIGHT - 100
    
    map_bg = pygame.Surface((map_w, map_h), pygame.SRCALPHA)
    map_bg.fill((0, 0, 0, 150))
    screen.blit(map_bg, (map_x, map_y))
    pygame.draw.rect(screen, WHITE, (map_x, map_y, map_w, map_h), 1)
    
    level_length = 2000 + current_level * 500 + 800
    scale = map_w / level_length
    
    for p in platforms:
        pygame.draw.rect(screen, (85, 85, 85), (map_x + p.rect.x * scale, map_y + map_h - 10, p.rect.w * scale, 5))
        
    pygame.draw.rect(screen, GREEN, (map_x + player.rect.x * scale, map_y + map_h - 15, 4, 4))
    
    alive_bosses = [b for b in bosses if not b.dead]
    if alive_bosses:
        pygame.draw.rect(screen, RED, (map_x + alive_bosses[0].rect.x * scale, map_y + map_h - 15, 4, 4))
    else:
        pygame.draw.rect(screen, (153, 50, 204), (map_x + portal.rect.x * scale, map_y + map_h - 15, 4, 4))

def draw_pause_menu(screen, font, big_font):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))
    p_text = big_font.render("GAME PAUSED", True, GOLD)
    screen.blit(p_text, (WIDTH//2 - p_text.get_width()//2, 100))
    
    c1 = font.render("--- CONTROLS ---", True, (0, 255, 255))
    c2 = font.render("Move: A/D or LEFT/RIGHT", True, WHITE)
    c3 = font.render("Jump: W or UP Arrow  (Wall Jump supported!)", True, WHITE)
    c4 = font.render("Basic Attack: F  |  Unique Skill: E", True, WHITE)
    c4b = font.render("Awaken Ultimate: R  (requires Awaken)", True, (255, 215, 0))
    c5 = font.render("Melee Attack: Q", True, (255, 200, 0))
    c6 = font.render("Gravity Dash: CTRL  |  Flip Gravity: G", True, (0, 200, 255))
    c7 = font.render("Wall Slide: Hold into wall while airborne", True, (200, 200, 255))
    c8 = font.render("Cheats: C  |  Quit to Menu: Q (while paused)", True, ORANGE)
    
    for i, t in enumerate([c1, c2, c3, c4, c4b, c5, c6, c7, c8]):
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 190 + i * 38))
    
    r_text = font.render("Press 'ESC' or 'P' to Resume", True, RED)
    screen.blit(r_text, (WIDTH//2 - r_text.get_width()//2, HEIGHT - 50))

def draw_game_over(screen, font, big_font):
    go_text = big_font.render("GAME OVER", True, RED)
    r_text = font.render("Press 'R' to Restart", True, WHITE)
    screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 20))
    screen.blit(r_text, (WIDTH//2 - r_text.get_width()//2, HEIGHT//2 + 30))

def _calc_star_rating(player):
    """Calculate 1-3 star rating based on performance."""
    stars = 1  # Base: you completed it
    # ★★: Collected 80%+ coins
    total = getattr(player, 'level_coins_total', 0)
    collected = getattr(player, 'level_coins', 0)
    if total > 0 and collected >= total * 0.8:
        stars = 2
    # ★★★: No deaths AND all stars collected
    deaths = getattr(player, 'death_count', 0)
    if deaths == 0 and stars >= 2:
        stars = 3
    return stars

def draw_level_cleared(screen, font, big_font, current_level, player=None):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((10, 15, 30, 220))
    screen.blit(overlay, (0, 0))
    
    # Header
    lc_text = big_font.render("MISSION ACCOMPLISHED!", True, GOLD)
    screen.blit(lc_text, (WIDTH//2 - lc_text.get_width()//2, HEIGHT//2 - 150))
    
    # Star Rating
    if player:
        star_count = _calc_star_rating(player)
        star_str = "★" * star_count + "☆" * (3 - star_count)
        star_colors = [(255, 215, 0), (200, 200, 200)]
        # Draw each star individually for color
        star_x = WIDTH // 2 - 60
        for i, ch_star in enumerate(star_str):
            color = (255, 215, 0) if ch_star == "★" else (80, 80, 80)
            s_surf = big_font.render(ch_star, True, color)
            screen.blit(s_surf, (star_x + i * 40, HEIGHT//2 - 110))
    
    # Stats Panel
    pygame.draw.rect(screen, (30, 40, 60), (WIDTH//2 - 200, HEIGHT//2 - 60, 400, 180), border_radius=15)
    pygame.draw.rect(screen, (100, 150, 255), (WIDTH//2 - 200, HEIGHT//2 - 60, 400, 180), 3, border_radius=15)
    
    # Draw stats if player is provided
    if player:
        deaths = getattr(player, 'death_count', 0)
        stats = [
            ("Score Earned:", str(getattr(player, 'level_score', 0)), WHITE),
            ("Total Coins:", str(player.coins), GOLD),
            ("Max Combo:", str(getattr(player, 'combo_kills', 0)), (255, 150, 50)),
            ("Deaths:", str(deaths), (255, 100, 100) if deaths > 0 else (100, 255, 100)),
        ]
        
        for i, (label, val, color) in enumerate(stats):
            y_pos = HEIGHT//2 - 40 + (i * 38)
            l_surf = font.render(label, True, (200, 200, 200))
            v_surf = font.render(val, True, color)
            screen.blit(l_surf, (WIDTH//2 - 170, y_pos))
            screen.blit(v_surf, (WIDTH//2 + 100, y_pos))

    next_lvl = current_level + 1 if current_level < 10 else 1
    prep_text = font.render(f"Proceeding to Level {next_lvl}...", True, (150, 255, 150))
    screen.blit(prep_text, (WIDTH//2 - prep_text.get_width()//2, HEIGHT//2 + 150))
