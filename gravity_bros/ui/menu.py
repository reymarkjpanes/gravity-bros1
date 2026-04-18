import pygame
from config import WIDTH, HEIGHT, WHITE, GOLD, RED, GREEN

def draw_main_menu(screen, font, big_font, mm_selection):
    screen.fill((10, 15, 25))
    
    title1 = big_font.render("GRAVITY BROS:", True, WHITE)
    title2 = big_font.render("PHILIPPINE ADVENTURE", True, GOLD)
    
    screen.blit(title1, (WIDTH//2 - title1.get_width()//2, 120))
    screen.blit(title2, (WIDTH//2 - title2.get_width()//2, 170))
    
    options = ["PLAY", "MODES", "STORE", "DATA", "SETTINGS", "QUIT"]
    for i, opt in enumerate(options):
        is_selected = (mm_selection == i)
        bg_col = (50, 50, 80) if is_selected else (30, 30, 40)
        border_col = GOLD if is_selected else (100, 100, 100)
        
        rect = pygame.Rect(WIDTH//2 - 150, 240 + i * 55, 300, 45)
        pygame.draw.rect(screen, bg_col, rect, 0, 15)
        pygame.draw.rect(screen, border_col, rect, 2, 15)
        
        txt = font.render(opt, True, WHITE if is_selected else (200, 200, 200))
        screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2))

    inst = font.render("UP/DOWN: Select | ENTER: Confirm", True, (100, 100, 150))
    screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT - 50))


def draw_level_select(screen, font, unlocked_levels, selected_level, difficulty, global_level, global_xp, total_coins):
    screen.fill((10, 10, 30))
    
    pygame.draw.rect(screen, (30, 30, 50), (0, 0, WIDTH, 70))
    pygame.draw.line(screen, GOLD, (0, 70), (WIDTH, 70), 3)
    
    title = font.render("LEVEL SELECT", True, GOLD)
    screen.blit(title, (20, 20))
    
    pygame.draw.rect(screen, (40, 40, 70), (WIDTH - 450, 15, 430, 40), 0, 20)
    stats_txt = font.render(f"Lv {global_level} (XP {global_xp}) | Piso: {total_coins}", True, WHITE)
    screen.blit(stats_txt, (WIDTH - 430, 23))
    
    instr = font.render("[S] STORE | [ESC] MAIN MENU | [ENTER] PLAY", True, (0, 255, 255))
    screen.blit(instr, (WIDTH // 2 - instr.get_width() // 2, 100))

    grid_start_x = 110
    grid_start_y = 170
    for i in range(1, 11):
        row = (i - 1) // 5
        col = (i - 1) % 5
        x = grid_start_x + col * 120
        y = grid_start_y + row * 110
        
        is_unlocked = i in unlocked_levels
        is_selected = i == selected_level
        
        if is_selected:
            bg_color, border_color = (80, 70, 20), GOLD
        elif is_unlocked:
            bg_color, border_color = (30, 50, 80), (100, 150, 255)
        else:
            bg_color, border_color = (30, 30, 40), (60, 60, 60)
            
        pygame.draw.rect(screen, bg_color, (x, y, 90, 90), 0, 15)
        pygame.draw.rect(screen, border_color, (x, y, 90, 90), 3 if is_selected else 1, 15)
        
        txt = font.render(str(i), True, WHITE if is_unlocked else (100, 100, 100))
        screen.blit(txt, (x + 45 - txt.get_width() // 2, y + 45 - txt.get_height() // 2))
        
        if not is_unlocked:
            pygame.draw.line(screen, RED, (x+25, y+25), (x+65, y+65), 4)
            pygame.draw.line(screen, RED, (x+65, y+25), (x+25, y+65), 4)

    diff_bg = pygame.Rect(100, 420, 600, 100)
    pygame.draw.rect(screen, (20, 20, 40), diff_bg, 0, 15)
    pygame.draw.rect(screen, (100, 100, 120), diff_bg, 2, 15)
    
    diff_text = font.render("SELECT DIFFICULTY: (E/N/H)", True, WHITE)
    screen.blit(diff_text, (diff_bg.centerx - diff_text.get_width()//2, 435))
    
    diff_options = ['easy', 'normal', 'hard']
    colors = [GREEN, GOLD, RED]
    for idx, d in enumerate(diff_options):
        is_active = (d == difficulty)
        color = colors[idx] if is_active else (100, 100, 100)
        bg = (colors[idx][0]//3, colors[idx][1]//3, colors[idx][2]//3) if is_active else (40, 40, 40)
        
        rect = pygame.Rect(150 + idx * 170, 475, 130, 40)
        pygame.draw.rect(screen, bg, rect, 0, 10)
        pygame.draw.rect(screen, color, rect, 2, 10)
        
        text = font.render(d.upper(), True, WHITE if is_active else (150, 150, 150))
        screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))
    
    # Navigation hints
    nav_hint = font.render("[S] Store   [X] Skill Tree   [ENTER] Select Level   [ESC] Back", True, (120, 120, 140))
    screen.blit(nav_hint, (WIDTH//2 - nav_hint.get_width()//2, HEIGHT - 30))

def draw_mission_briefing(screen, font, big_font, level, difficulty, theme_name):
    screen.fill((20, 20, 30))
    title = big_font.render(f"MISSION {level}", True, GOLD)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 150))
    
    theme = font.render(f"Location: {theme_name}", True, (0, 255, 255))
    screen.blit(theme, (WIDTH//2 - theme.get_width()//2, 220))
    
    diff_color = GREEN if difficulty == 'easy' else (GOLD if difficulty == 'normal' else RED)
    diff_text = font.render(f"Difficulty: {difficulty.upper()}", True, diff_color)
    screen.blit(diff_text, (WIDTH//2 - diff_text.get_width()//2, 270))
    
    obj = font.render("Objective: Defeat bosses and reach the portal!", True, WHITE)
    screen.blit(obj, (WIDTH//2 - obj.get_width()//2, 330))
    
    inst = font.render("Press ENTER to Begin Mission", True, (150, 150, 150))
    screen.blit(inst, (WIDTH//2 - inst.get_width()//2, HEIGHT - 100))
