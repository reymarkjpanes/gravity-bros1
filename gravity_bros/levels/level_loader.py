import random
from entities.items import Platform, Block, Coin, Gem, Star, PowerUp, Portal, Scenery, Spike, FallingPlatform, Checkpoint, HiddenPortal, MovingPlatform
from entities.enemy import Enemy
from entities.boss import Boss
from .themes import get_boss_type

# Level-themed enemy types: each level prefers certain enemy archetypes
LEVEL_ENEMY_POOL = {
    1: ['walker'],                           # Tutorial: easy walkers only
    2: ['walker', 'hopper'],                 # Rice fields: basic mix
    3: ['walker', 'hopper', 'archer'],       # Beach: with archers
    4: ['hopper', 'archer'],                 # Forest: agile enemies
    5: ['walker', 'shielded', 'archer'],     # Volcano: tough enemies
    6: ['shielded', 'hopper'],               # Mountains: defensive
    7: ['archer', 'hopper', 'shielded'],     # River: mixed
    8: ['shielded', 'walker', 'archer'],     # Urban: all types
    9: ['archer', 'shielded'],               # City night: ranged
    10: ['walker', 'hopper', 'archer', 'shielded'],  # Final: everything
}

def build_tutorial_level(difficulty):
    """Hand-crafted tutorial level that teaches core mechanics."""
    platforms = []
    blocks = []
    enemies = []
    bosses = []
    coins = []
    gems = []
    stars = []
    power_ups = []
    scenery = []
    hazards = []
    checkpoints = []
    hidden_portals = []
    
    # Section 1: Movement — flat ground
    platforms.append(Platform(0, 450, 600, 600))
    # Place coins in a line to guide movement
    for i in range(8):
        coins.append(Coin(80 + i * 60, 410))
    scenery.append(Scenery(100, 450, 'rice_stalk'))
    scenery.append(Scenery(300, 450, 'rice_stalk'))
    
    # Section 2: Jumping — small gap
    platforms.append(Platform(700, 450, 300, 600))
    coins.append(Coin(750, 380))
    coins.append(Coin(850, 380))
    
    # Section 3: Higher platform to teach vertical jumps
    platforms.append(Platform(1100, 350, 200, 20))
    platforms.append(Platform(1100, 450, 200, 600))
    coins.append(Coin(1180, 310))
    gems.append(Gem(1180, 280))
    
    # Section 4: Blocks to hit
    platforms.append(Platform(1400, 450, 400, 600))
    blocks.append(Block(1500, 320))
    blocks.append(Block(1540, 320))
    blocks.append(Block(1580, 320))
    
    # Section 5: First enemy (just a walker)
    platforms.append(Platform(1900, 450, 300, 600))
    enemies.append(Enemy(2000, 426, 'walker', difficulty))
    checkpoints.append(Checkpoint(2050, 450))
    
    # Section 6: Gravity flip practice — coins above and below
    platforms.append(Platform(2300, 450, 400, 600))
    # Ceiling platform for gravity flip
    platforms.append(Platform(2300, 100, 400, 20))
    for i in range(5):
        coins.append(Coin(2350 + i * 60, 70))
    coins.append(Coin(2550, 410))
    
    # Section 7: Moving platform
    platforms.append(MovingPlatform(2800, 350, 120, 20, 'horizontal', 200, 2))
    platforms.append(Platform(3100, 450, 300, 600))
    
    # Section 8: Spike avoidance
    platforms.append(Platform(3500, 450, 600, 600))
    hazards.append(Spike(3650, 434))
    hazards.append(Spike(3700, 434))
    coins.append(Coin(3550, 410))
    coins.append(Coin(3800, 410))
    
    # Section 9: Power-up introduction
    platforms.append(Platform(4200, 450, 300, 600))
    power_ups.append(PowerUp(4300, 300, 'speedBoost'))
    
    # Boss Arena
    arena_x = 4700
    platforms.append(Platform(arena_x, 450, 200, 600))
    platforms.append(Platform(arena_x + 300, 450, 200, 600))
    platforms.append(Platform(arena_x + 600, 450, 800, 600))
    platforms.append(Platform(arena_x + 150, 320, 100, 20))
    platforms.append(Platform(arena_x + 450, 260, 100, 20))
    platforms.append(Platform(arena_x + 750, 320, 100, 20))
    
    boss_type = get_boss_type(1)
    bosses.append(Boss(arena_x + 800, 370, boss_type, difficulty))
    portal = Portal(arena_x + 1200, 370)
    
    # Bonus Room
    bx, by = 0, -2000
    platforms.append(Platform(bx, by + 400, 800, 600))
    for i in range(10):
        coins.append(Coin(bx + 100 + i * 50, by + 300))
        if i % 3 == 0: gems.append(Gem(bx + 100 + i * 50, by + 200))
    hidden_portals.append(HiddenPortal(bx + 700, by + 320))
    
    return platforms, blocks, enemies, bosses, coins, gems, stars, power_ups, portal, scenery, hazards, checkpoints, hidden_portals


def build_level(level, difficulty):
    # Level 1 is a hand-crafted tutorial
    if level == 1:
        return build_tutorial_level(difficulty)
    
    level_length = 2000 + level * 500
    platforms = []
    blocks = []
    enemies = []
    bosses = []
    coins = []
    gems = []
    stars = []
    power_ups = []
    scenery = []
    hazards = []
    checkpoints = []
    hidden_portals = []
    
    enemy_spawn_chance = 0.2 if difficulty == 'easy' else (0.6 if difficulty == 'hard' else 0.4)
    enemy_pool = LEVEL_ENEMY_POOL.get(level, ['walker', 'hopper', 'archer', 'shielded'])
    
    platforms.append(Platform(0, 450, 400, 600))
    current_x = 400
    last_y = 450

    while current_x < level_length:
        width = 200
        y = 450
        gap = 50

        if level == 2:
            width = 100 + random.random() * 150
            gap = 40 + random.random() * 60
            y = last_y + random.randint(-40, 40)
        else:
            width = 150 + random.random() * 150
            gap = 90
            y = last_y + random.randint(-80, 80)
            
        y = max(250, min(550, y))
        last_y = y

        current_x += gap
        
        # Platform type selection
        rnd = random.random()
        if rnd > 0.9 and level >= 4:
            # Moving platform (level 4+)
            move_type = random.choice(['horizontal', 'vertical'])
            dist = random.randint(100, 250)
            spd = random.choice([1, 2, 3])
            platforms.append(MovingPlatform(current_x, y, width, 20, move_type, dist, spd))
        elif rnd > 0.8:
            platforms.append(FallingPlatform(current_x, y, width, 800 - y))
        else:
            platforms.append(Platform(current_x, y, width, 800 - y))
            if random.random() > 0.8:
                hazards.append(Spike(current_x + width/2 - 16, y - 16))

        if random.random() > 0.6:
            if level == 2: scenery.append(Scenery(current_x + random.random() * width, y, 'rice_stalk'))
            elif level == 3: scenery.append(Scenery(current_x + random.random() * width, y, 'palm_tree'))
            elif level == 6: scenery.append(Scenery(current_x + random.random() * width, y, 'pine_tree'))
            elif level == 9: scenery.append(Scenery(current_x + width/2, y, 'lamp'))
        
        if random.random() > (1 - enemy_spawn_chance) and width > 100 and current_x < level_length - 800:
            e_type = random.choice(enemy_pool)
            enemies.append(Enemy(current_x + width / 2, y - 24, e_type, difficulty))
            
        if random.random() > 0.3:
            coins.append(Coin(current_x + width / 2, y - 60))
            
        if random.random() > 0.8:
            gems.append(Gem(current_x + width / 2 + 20, y - 80))
            
        if random.random() > 0.95:
            stars.append(Star(current_x + width / 2 - 20, y - 100))
            
        if random.random() > 0.9:
            p_type = random.choice(['invincibility', 'doubleJump', 'speedBoost'])
            power_ups.append(PowerUp(current_x + width / 2, y - 150, p_type))
            
        if random.random() > 0.6:
            blocks.append(Block(current_x + width / 2 - 16, y - 120))
            
        if random.random() > 0.95 and current_x > 1000:
            checkpoints.append(Checkpoint(current_x + width / 2, y))
            
        if random.random() > 0.97 and current_x > 800:
            hidden_portals.append(HiddenPortal(current_x + width / 2, y - 80))
            
        current_x += width
        
    # Arena
    arena_x = current_x
    platforms.append(Platform(arena_x, 450, 200, 600))
    platforms.append(Platform(arena_x + 300, 450, 200, 600))
    platforms.append(Platform(arena_x + 600, 450, 800, 600))
    
    platforms.append(Platform(arena_x + 150, 320, 100, 20))
    platforms.append(Platform(arena_x + 450, 260, 100, 20))
    platforms.append(Platform(arena_x + 750, 320, 100, 20))

    boss_type = get_boss_type(level)
    bosses.append(Boss(arena_x + 800, 370, boss_type, difficulty))
    portal = Portal(arena_x + 1200, 370)
    
    # Bonus Room Generation at Y = -2000
    bx = 0
    by = -2000
    platforms.append(Platform(bx, by + 400, 800, 600))
    for i in range(10):
        coins.append(Coin(bx + 100 + i * 50, by + 300))
        if i % 3 == 0: gems.append(Gem(bx + 100 + i * 50, by + 200))
    # Return portal back to normal spawn
    hidden_portals.append(HiddenPortal(bx + 700, by + 320))

    return platforms, blocks, enemies, bosses, coins, gems, stars, power_ups, portal, scenery, hazards, checkpoints, hidden_portals
