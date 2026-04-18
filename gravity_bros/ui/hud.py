import pygame
from config import WIDTH, HEIGHT, WHITE, GOLD, RED, ORANGE, GREEN

def draw_hud(screen, font, big_font, player, theme, current_level, weapon, bosses=None):
    if bosses is None: bosses = []
    # Weapon Selection UI
    weapon_data = [
        {'id': 'fireball', 'label': '1:FIRE', 'color': (255, 69, 0)},
        {'id': 'gun', 'label': '2:GUN', 'color': (255, 255, 0)},
        {'id': 'grenade', 'label': '3:GREN', 'color': (0, 100, 0)}
    ]
    for i, w in enumerate(weapon_data):
        is_active = weapon == w['id']
        wx, wy = 20 + i * 90, HEIGHT - 60
        rect = pygame.Rect(wx, wy, 80, 30)
        bg_color = (100, 100, 100, 150) if is_active else (0, 0, 0, 150)
        s = pygame.Surface((80, 30), pygame.SRCALPHA)
        s.fill(bg_color)
        screen.blit(s, (wx, wy))
        border_color = w['color'] if is_active else (100, 100, 100)
        pygame.draw.rect(screen, border_color, rect, 2 if is_active else 1)
        w_text = font.render(w['label'], True, WHITE if is_active else (170, 170, 170))
        screen.blit(w_text, (wx + 5, wy + 5))

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
    
    if getattr(player, 'combo_kills', 0) > 1:
        combo_text = big_font.render(f"COMBO x{player.combo_kills}!", True, ORANGE)
        screen.blit(combo_text, (20, 65))
        
    # Right Block
    gravity_text = font.render(f"GRAVITY: {'UP' if getattr(player, 'gravity_dir', 1) == -1 else 'DOWN'}", True, WHITE)
    screen.blit(gravity_text, (WIDTH - gravity_text.get_width() - 20, 10))
    
    # Skill Bar
    ab_rect = pygame.Rect(WIDTH - 150, 40, 130, 15)
    pygame.draw.rect(screen, (50, 50, 50), ab_rect)
    ab_pct = 1.0 - (player.ability_cooldown / getattr(player, 'max_cooldown', 100) if hasattr(player, 'max_cooldown') else 1)
    if ab_pct < 0: ab_pct = 0; 
    if ab_pct > 1: ab_pct = 1
    
    color = (0, 255, 0) if ab_pct >= 1.0 else (255, 165, 0)
    pygame.draw.rect(screen, color, (ab_rect.x, ab_rect.y, int(130 * ab_pct), 15))
    pygame.draw.rect(screen, WHITE, ab_rect, 1)
    ab_txt = font.render(f"SKILL", True, WHITE)
    screen.blit(ab_txt, (WIDTH - 150 - ab_txt.get_width() - 10, 35))

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
    c2 = font.render("Move: W,A,S,D or Arrow Keys", True, WHITE)
    c3 = font.render("Jump: W or UP Arrow", True, WHITE)
    c4 = font.render("Shoot: F  |  Ability: E", True, WHITE)
    c5 = font.render("Gravity Flip: G", True, (255, 100, 100))
    c6 = font.render("Swap Weapons: 1, 2, 3", True, WHITE)
    c7 = font.render("Cheats Menu: C", True, WHITE)
    c8 = font.render("Quit to Menu: Q", True, ORANGE)
    
    for i, t in enumerate([c1, c2, c3, c4, c5, c6, c7, c8]):
        screen.blit(t, (WIDTH//2 - t.get_width()//2, 200 + i * 40))
    
    r_text = font.render("Press 'ESC' or 'P' to Resume", True, RED)
    screen.blit(r_text, (WIDTH//2 - r_text.get_width()//2, HEIGHT - 80))

def draw_game_over(screen, font, big_font):
    go_text = big_font.render("GAME OVER", True, RED)
    r_text = font.render("Press 'R' to Restart", True, WHITE)
    screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - 20))
    screen.blit(r_text, (WIDTH//2 - r_text.get_width()//2, HEIGHT//2 + 30))

def draw_level_cleared(screen, font, big_font, current_level):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    lc_text = big_font.render("LEVEL CLEARED!", True, GOLD)
    next_lvl = current_level + 1 if current_level < 10 else 1
    prep_text = font.render(f"PREPARING LEVEL {next_lvl}...", True, WHITE)
    screen.blit(lc_text, (WIDTH//2 - lc_text.get_width()//2, HEIGHT//2 - 40))
    screen.blit(prep_text, (WIDTH//2 - prep_text.get_width()//2, HEIGHT//2 + 20))
