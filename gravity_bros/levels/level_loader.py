import random
from entities.items import Platform, Block, Coin, Gem, Star, PowerUp, Portal, Scenery, Spike, FallingPlatform, Checkpoint, HiddenPortal
from entities.enemy import Enemy
from entities.boss import Boss
from .themes import get_boss_type

def build_level(level, difficulty):
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
    
    platforms.append(Platform(0, 450, 400, 600))
    current_x = 400

    while current_x < level_length:
        width = 200
        y = 450
        gap = 50

        if level == 1:
            width = 150 + random.random() * 100
            gap = 0
            y = 450 - (random.randint(0, 3) * 40)
            if random.random() > 0.7: gap = 80
        elif level == 2:
            width = 100 + random.random() * 150
            gap = 40 + random.random() * 60
            y = 450 - (random.random() * 150)
        else:
            width = 150 + random.random() * 150
            gap = 90
            y = 450 - (random.random() * 300)

        current_x += gap
        if random.random() > 0.8:
            platforms.append(FallingPlatform(current_x, y, width, 800 - y))
        else:
            platforms.append(Platform(current_x, y, width, 800 - y))
            if random.random() > 0.8:
                hazards.append(Spike(current_x + width/2 - 16, y - 16))

        if random.random() > 0.6:
            if level == 1: scenery.append(Scenery(current_x + random.random() * width, y, 'rice_stalk'))
            elif level == 3: scenery.append(Scenery(current_x + random.random() * width, y, 'palm_tree'))
            elif level == 6: scenery.append(Scenery(current_x + random.random() * width, y, 'pine_tree'))
            elif level == 9: scenery.append(Scenery(current_x + width/2, y, 'lamp'))
        
        if random.random() > (1 - enemy_spawn_chance) and width > 100 and current_x < level_length - 800:
            rnd = random.random()
            if rnd > 0.8: e_type = 'archer'
            elif rnd > 0.6: e_type = 'shielded'
            elif rnd > 0.3: e_type = 'hopper'
            else: e_type = 'walker'
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
