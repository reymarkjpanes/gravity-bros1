import pygame
from config import WIDTH, HEIGHT, STORE_ITEMS, GOLD, WHITE, GREEN, RED

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

    # Let list be narrow on all tabs if we want a uniform UI, or just on character tabs.
    # We will make the list narrow globally to leave room for the right detail pane.
    list_w = 320
    list_rect = pygame.Rect(30, 150, list_w, 400)
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
            pygame.draw.rect(screen, bg_color, (40, y, list_w - 20, 65), 0, 8)
            pygame.draw.rect(screen, border_color, (40, y, list_w - 20, 65), 2, 8)
        except TypeError:
            pygame.draw.rect(screen, bg_color, (40, y, list_w - 20, 65), 0)
            pygame.draw.rect(screen, border_color, (40, y, list_w - 20, 65), 2)
        
        # Determine name text scale
        nfont = pygame.font.SysFont("monospace", 15, bold=True)
        name_text = nfont.render(item['name'], True, WHITE)
        screen.blit(name_text, (50, y + 10))
        
        if is_selected and store_tab < 4:
            status_text = nfont.render("[EQUIPPED]", True, GREEN)
        elif is_unlocked and store_tab >= 4:
            status_text = nfont.render(f"[{'AWAKENED' if store_tab == 5 else 'UNLOCKED'}]", True, GREEN)
        elif is_unlocked:
            status_text = nfont.render("ENTER: Equip", True, (200, 200, 200))
        else:
            status_text = nfont.render(f"COST: {item['cost']}", True, GOLD)
        
        screen.blit(status_text, (50, y + 35))

    screen.set_clip(None)

    # ── DETAIL PANE ──
    dt_w = WIDTH - 420
    dt_rect = pygame.Rect(360, 150, dt_w, 400)
    try:
        pygame.draw.rect(screen, (10, 12, 18), dt_rect, 0, 15)
        pygame.draw.rect(screen, GOLD, dt_rect, 2, 15)
    except TypeError:
        pygame.draw.rect(screen, (10, 12, 18), dt_rect, 0)
        pygame.draw.rect(screen, GOLD, dt_rect, 2)

    cur_item = items[store_selection] if items else None
    if cur_item:
        if store_tab == 0 or store_tab == 5:
            # Character / Awaken Detail
            from ui.skill_info import _load_portrait, SKILL_CODEX, _wrap_text
            char_id = cur_item['id']
            portrait = _load_portrait(char_id)
            if portrait:
                # Scale portrait to fit left side of detail pane
                tw, th = portrait.get_size()
                scale = min(270 / tw, 360 / th)
                scaled_h = int(th * scale)
                port_scaled = pygame.transform.smoothscale(portrait, (int(tw * scale), scaled_h))
                screen.blit(port_scaled, (380, 170 + (360 - scaled_h)))

            info = SKILL_CODEX.get(char_id, {})
            detail_font = pygame.font.SysFont("monospace", 14, bold=True)
            
            # Character Name
            cname = font.render(char_id.upper(), True, GOLD)
            screen.blit(cname, (660, 170))
            
            # Stats (pseudo-randomly seeded by name so it's consistent)
            import random
            s_rand = random.Random(char_id)
            stats = {
                'HP': s_rand.randint(4, 10),
                'SPD': s_rand.randint(4, 10),
                'PWR': s_rand.randint(4, 10)
            }
            sy = 210
            for k, v in stats.items():
                lbl = detail_font.render(f"{k}:", True, (200, 200, 200))
                screen.blit(lbl, (660, sy))
                # Draw bar
                pygame.draw.rect(screen, (50, 50, 50), (700, sy + 3, 200, 10))
                bar_c = GREEN if v > 7 else (GOLD if v > 4 else RED)
                pygame.draw.rect(screen, bar_c, (700, sy + 3, int(200 * (v/10.0)), 10))
                sy += 25
                
            # Lore
            ly = sy + 20
            lore_lbl = font.render("LORE:", True, info.get('color', GOLD))
            screen.blit(lore_lbl, (660, ly))
            ly += 25
            desc = info.get('lore', 'A legendary hero of the Philippines.')
            for ln in _wrap_text(desc, detail_font, 240)[:6]:  # max 6 lines
                t = detail_font.render(ln, True, (180, 180, 200))
                screen.blit(t, (660, ly))
                ly += 18
        else:
            # Generic Detail
            bname = font.render(cur_item['name'].upper(), True, GOLD)
            screen.blit(bname, (430, 180))
            cst = font.render(f"PRICE: {cur_item['cost']} PISO", True, WHITE)
            screen.blit(cst, (430, 230))

    inst = font.render("UP/DOWN: Navigate | ENTER: Buy/Equip", True, (150, 150, 150))
    screen.blit(inst, (WIDTH // 2 - inst.get_width() // 2, HEIGHT - 35))
