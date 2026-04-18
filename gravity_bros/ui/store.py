import pygame
from config import WIDTH, HEIGHT, STORE_ITEMS, GOLD, WHITE, GREEN

def draw_store(screen, font, total_coins, unlocked_characters, unlocked_skins, unlocked_powerups, unlocked_pets, unlocked_upgrades, unlocked_evolutions, selected_character, selected_skin, selected_powerup, selected_pet, store_tab, store_selection):
    screen.fill((20, 20, 25))
    
    pygame.draw.rect(screen, (30, 30, 50), (0, 0, WIDTH, 70))
    pygame.draw.line(screen, GOLD, (0, 70), (WIDTH, 70), 3)
    
    title = font.render("SARI-SARI STORE", True, GOLD)
    screen.blit(title, (20, 20))
    
    try:
        pygame.draw.rect(screen, (50, 40, 20), (WIDTH - 220, 15, 200, 40), 0, 20)
        pygame.draw.rect(screen, GOLD, (WIDTH - 220, 15, 200, 40), 2, 20)
    except TypeError:
        pygame.draw.rect(screen, (50, 40, 20), (WIDTH - 220, 15, 200, 40), 0)
        pygame.draw.rect(screen, GOLD, (WIDTH - 220, 15, 200, 40), 2)
        
    coins_text = font.render(f"Piso: {total_coins}", True, GOLD)
    screen.blit(coins_text, (WIDTH - 200, 23))

    esc_hint = font.render("[ESC] Back", True, (150, 150, 150))
    screen.blit(esc_hint, (WIDTH//2 - 50, 25))

    tabs = [("CHARACTERS", 0), ("SKINS", 1), ("POWER", 2), ("PETS", 3), ("UPGRADE", 4), ("AWAKEN", 5)]
    for text, index in tabs:
        is_active = (store_tab == index)
        tab_bg = (50, 100, 200) if is_active else (40, 40, 50)
        border = WHITE if is_active else (100, 100, 100)
        rx = 20 + index * 125
        try:
            pygame.draw.rect(screen, tab_bg, (rx, 90, 115, 40), 0, 10)
            pygame.draw.rect(screen, border, (rx, 90, 115, 40), 2, 10)
        except TypeError:
            pygame.draw.rect(screen, tab_bg, (rx, 90, 115, 40), 0)
            pygame.draw.rect(screen, border, (rx, 90, 115, 40), 2)
            
        sfont = pygame.font.SysFont("monospace", 14, bold=True)
        t_surf = sfont.render(text, True, WHITE if is_active else (150, 150, 150))
        screen.blit(t_surf, (rx + 57 - t_surf.get_width()//2, 102))

    if store_tab == 0:
        items = STORE_ITEMS['characters']
        unlocked_list = unlocked_characters
        selected_item = selected_character
    elif store_tab == 1:
        items = STORE_ITEMS['skins']
        unlocked_list = unlocked_skins
        selected_item = selected_skin
    elif store_tab == 2:
        items = STORE_ITEMS['powerups']
        unlocked_list = unlocked_powerups
        selected_item = selected_powerup
    elif store_tab == 3:
        items = STORE_ITEMS['pets']
        unlocked_list = unlocked_pets
        selected_item = selected_pet
    elif store_tab == 4:
        items = STORE_ITEMS['upgrades']
        unlocked_list = unlocked_upgrades
        selected_item = None
    else:
        # Awaken uses the user's ALREADY UNLOCKED characters, applying an evolution to them
        items = [{'id': c, 'name': f"AWAKEN: {c}", 'cost': 100000} for c in unlocked_characters]
        unlocked_list = unlocked_evolutions
        selected_item = None

    scroll_y = max(0, store_selection - 2) * 75

    list_rect = pygame.Rect(40, 150, 720, 400)
    try:
        pygame.draw.rect(screen, (15, 15, 20), list_rect, 0, 10)
    except TypeError:
        pygame.draw.rect(screen, (15, 15, 20), list_rect, 0)
    screen.set_clip(list_rect)

    for idx, item in enumerate(items):
        y = 160 + idx * 75 - scroll_y
        if y < 80 or y > 580: continue
        
        is_unlocked = item['id'] in unlocked_list
        is_selected = item['id'] == selected_item
        is_highlighted = idx == store_selection
        
        bg_color = (40, 80, 40) if is_selected else ((50, 60, 90) if is_highlighted else (30, 30, 40))
        border_color = GREEN if is_selected else (GOLD if is_highlighted else (80, 80, 80))
        
        try:
            pygame.draw.rect(screen, bg_color, (50, y, 700, 65), 0, 8)
            pygame.draw.rect(screen, border_color, (50, y, 700, 65), 2, 8)
        except TypeError:
            pygame.draw.rect(screen, bg_color, (50, y, 700, 65), 0)
            pygame.draw.rect(screen, border_color, (50, y, 700, 65), 2)
        
        name_text = font.render(item['name'], True, WHITE)
        screen.blit(name_text, (70, y + 20))
        
        if is_selected and store_tab < 4:
            status_text = font.render("[EQUIPPED]", True, GREEN)
        elif is_unlocked and store_tab >= 4:
            status_text = font.render(f"[{'AWAKENED' if store_tab == 5 else 'UNLOCKED'}]", True, GREEN)
        elif is_unlocked:
            status_text = font.render("Press ENTER to Equip", True, (200, 200, 200))
        else:
            status_text = font.render(f"COST: {item['cost']}", True, GOLD)
        
        screen.blit(status_text, (730 - status_text.get_width(), y + 20))

    screen.set_clip(None)

    inst = font.render("UP/DOWN: Navigate | ENTER: Buy/Equip", True, (150, 150, 150))
    screen.blit(inst, (WIDTH // 2 - inst.get_width() // 2, HEIGHT - 35))
