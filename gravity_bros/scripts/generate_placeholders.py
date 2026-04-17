import pygame
import os
import math

# Configuration for placeholders
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images')
os.makedirs(OUTPUT_DIR, exist_ok=True)

pygame.init()
# We don't need a screen, but pygame requires display initialization to draw on surfaces
screen = pygame.display.set_mode((100, 100), pygame.HIDDEN)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (229, 37, 33)
BLUE = (0, 67, 166)
SKIN = (255, 204, 153)
DIRT_BROWN = (200, 76, 12)
GOLD = (248, 216, 32)

def save_surface(surf, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    pygame.image.save(surf, path)
    print(f"Generated {path}")

def generate_player():
    for char_name, char_colors in {
        'Juan': (RED, BLUE),
        'Aswang': ((75, 0, 130), BLACK),
        'Manananggal': ((128, 0, 128), BLACK)
    }.items():
        primary, secondary = char_colors
        
        # Idle frame
        surf = pygame.Surface((24, 32), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(surf, secondary, (4, 18, 16, 10))
        pygame.draw.rect(surf, primary, (2, 18, 4, 8))
        pygame.draw.rect(surf, primary, (18, 18, 4, 8))
        # Head
        if char_name == 'Juan':
            pygame.draw.rect(surf, primary, (0, 0, 20, 6))
            pygame.draw.rect(surf, primary, (0, 6, 24, 2))
            pygame.draw.rect(surf, SKIN, (2, 8, 18, 10))
        else:
            pygame.draw.rect(surf, primary, (4, 4, 16, 14))
            pygame.draw.rect(surf, SKIN, (6, 6, 12, 10))
        # Eye
        pygame.draw.rect(surf, BLACK, (16, 10, 2, 4))
        # Legs Idle
        pygame.draw.rect(surf, secondary, (4, 28, 6, 4))
        pygame.draw.rect(surf, secondary, (14, 28, 6, 4))
        
        save_surface(surf, f"player_{char_name.lower()}_idle_right.png")
        save_surface(pygame.transform.flip(surf, True, False), f"player_{char_name.lower()}_idle_left.png")
        
        # Fall frame (for jump and gravity fall)
        surf_jump = pygame.Surface((24, 32), pygame.SRCALPHA)
        pygame.draw.rect(surf_jump, secondary, (4, 18, 16, 10))
        pygame.draw.rect(surf_jump, primary, (2, 18, 4, 8))
        pygame.draw.rect(surf_jump, primary, (18, 10, 4, 8)) # Arm up
        if char_name == 'Juan':
            pygame.draw.rect(surf_jump, primary, (0, 0, 20, 6))
            pygame.draw.rect(surf_jump, primary, (0, 6, 24, 2))
            pygame.draw.rect(surf_jump, SKIN, (2, 8, 18, 10))
        else:
            pygame.draw.rect(surf_jump, primary, (4, 4, 16, 14))
            pygame.draw.rect(surf_jump, SKIN, (6, 6, 12, 10))
        pygame.draw.rect(surf_jump, BLACK, (16, 10, 2, 4))
        pygame.draw.rect(surf_jump, secondary, (2, 28, 8, 4)) # Leg up
        pygame.draw.rect(surf_jump, secondary, (14, 26, 8, 4))
        save_surface(surf_jump, f"player_{char_name.lower()}_jump_right.png")
        save_surface(pygame.transform.flip(surf_jump, True, False), f"player_{char_name.lower()}_jump_left.png")

def generate_enemies():
    # Walker
    surf = pygame.Surface((24, 24), pygame.SRCALPHA)
    pygame.draw.rect(surf, DIRT_BROWN, (0, 4, 24, 16))
    pygame.draw.rect(surf, WHITE, (6, 8, 4, 6))
    pygame.draw.rect(surf, WHITE, (14, 8, 4, 6))
    pygame.draw.rect(surf, BLACK, (8, 10, 2, 4))
    pygame.draw.rect(surf, BLACK, (14, 10, 2, 4))
    pygame.draw.rect(surf, BLACK, (2, 20, 8, 4))
    pygame.draw.rect(surf, BLACK, (14, 20, 8, 4))
    save_surface(surf, "enemy_walker_right.png")
    save_surface(pygame.transform.flip(surf, True, False), "enemy_walker_left.png")
    
    # Hopper
    surf_hop = pygame.Surface((24, 24), pygame.SRCALPHA)
    pygame.draw.rect(surf_hop, (34, 139, 34), (0, 4, 24, 16))
    pygame.draw.rect(surf_hop, WHITE, (4, 6, 4, 4))
    pygame.draw.rect(surf_hop, WHITE, (16, 6, 4, 4))
    pygame.draw.rect(surf_hop, BLACK, (4, 8, 2, 2))
    pygame.draw.rect(surf_hop, BLACK, (16, 8, 2, 2))
    pygame.draw.rect(surf_hop, (0, 100, 0), (2, 20, 6, 4))
    pygame.draw.rect(surf_hop, (0, 100, 0), (16, 20, 6, 4))
    save_surface(surf_hop, "enemy_hopper_right.png")
    save_surface(pygame.transform.flip(surf_hop, True, False), "enemy_hopper_left.png")

def generate_items():
    # Coin
    surf_coin = pygame.Surface((16, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(surf_coin, GOLD, (0, 0, 16, 24))
    pygame.draw.ellipse(surf_coin, BLACK, (0, 0, 16, 24), 2)
    save_surface(surf_coin, "item_coin.png")
    
    # Gem
    surf_gem = pygame.Surface((20, 20), pygame.SRCALPHA)
    points = [(10, 0), (20, 10), (10, 20), (0, 10)]
    pygame.draw.polygon(surf_gem, (0, 255, 255), points)
    pygame.draw.polygon(surf_gem, BLACK, points, 2)
    save_surface(surf_gem, "item_gem.png")
    
    # Powerups
    surf_star = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(surf_star, (255, 0, 255), (15, 15), 15)
    pygame.draw.circle(surf_star, WHITE, (15, 15), 15, 2)
    save_surface(surf_star, "powerup_star.png")
    
    surf_shroom = pygame.Surface((30, 30), pygame.SRCALPHA)
    pygame.draw.circle(surf_shroom, (255, 255, 0), (15, 15), 15)
    pygame.draw.circle(surf_shroom, WHITE, (15, 15), 15, 2)
    save_surface(surf_shroom, "powerup_mushroom.png")

def generate_blocks():
    # Platform tile
    surf_plat = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(surf_plat, (139, 69, 19), (0, 0, 32, 32))
    pygame.draw.rect(surf_plat, (50, 205, 50), (0, 0, 32, 8))
    pygame.draw.rect(surf_plat, BLACK, (0, 0, 32, 32), 2)
    save_surface(surf_plat, "tile_platform.png")
    
    # Mystery block
    surf_block = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(surf_block, (248, 152, 0), (0, 0, 32, 32))
    pygame.draw.rect(surf_block, BLACK, (0, 0, 32, 32), 2)
    pygame.draw.rect(surf_block, BLACK, (12, 8, 8, 16)) # Mock question mark
    save_surface(surf_block, "tile_mystery_block.png")
    
    # Hit block
    surf_hit = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(surf_hit, DIRT_BROWN, (0, 0, 32, 32))
    pygame.draw.rect(surf_hit, BLACK, (0, 0, 32, 32), 2)
    save_surface(surf_hit, "tile_hit_block.png")

print("Generating placeholders...")
generate_player()
generate_enemies()
generate_items()
generate_blocks()
print("Done.")

pygame.quit()
