# gravity_bros/config.py
# All constants for Gravity Bros: Philippine Adventure

WIDTH, HEIGHT = 800, 600
FPS = 60

# --- Colors ---
SKY_BLUE    = (92,  148, 252)
GRASS_GREEN = (0,   168, 0)
DIRT_BROWN  = (200, 76,  12)
BLUE_GRASS  = (0,   88,  248)
NIGHT_BLUE  = (11,  11,  42)
WHITE  = (255, 255, 255)
BLACK  = (0,   0,   0)
RED    = (229, 37,  33)
SKIN   = (255, 204, 153)
BLUE   = (0,   67,  166)
GREEN  = (0,   255, 0)
GOLD   = (248, 216, 32)
ORANGE = (248, 152, 0)

# --- Store Items & Pricing ---
STORE_ITEMS = {
    'characters': [
        {'id': 'Juan',        'name': 'Juan Tamad (Guava Rest)',           'cost': 0},
        {'id': 'Maria',       'name': 'Maria Clara (Fan Shield)',          'cost': 500},
        {'id': 'LapuLapu',    'name': 'Lapu-Lapu (Mactan Strike)',         'cost': 1500},
        {'id': 'Jose',        'name': 'Jose Rizal (Noli Projectile)',      'cost': 2000},
        {'id': 'Andres',      'name': 'Andres Bonifacio (Rage Mode)',      'cost': 2500},
        {'id': 'Aswang',      'name': 'Aswang (Life Steal)',               'cost': 3000},
        {'id': 'Tikbalang',   'name': 'Tikbalang (High Jump)',             'cost': 3500},
        {'id': 'Kapre',       'name': 'Kapre (Smoke Screen)',              'cost': 4000},
        {'id': 'Manananggal', 'name': 'Manananggal (Flight)',              'cost': 4500},
        {'id': 'Datu',        'name': 'Datu (Twin Fire)',                  'cost': 5000},
        {'id': 'Sorbetero',   'name': 'Sorbetero (Brain Freeze)',          'cost': 5500},
        {'id': 'Taho',        'name': 'Magtataho (Arnibal Splash)',        'cost': 6000},
        {'id': 'Malunggay',   'name': 'Malunggay (Chlorophyll Boost)',     'cost': 6500},
        {'id': 'Batak',       'name': 'Batak (Endurance Run)',             'cost': 7000},
        {'id': 'Jeepney',     'name': 'Jeepney Driver (Full Speed)',       'cost': 7500},
    ],
    'skins': [
        {'id': 'Default', 'name': 'Default Skin',  'cost': 0},
        {'id': 'Gold',    'name': 'Gold Skin',     'cost': 1000},
        {'id': 'Neon',    'name': 'Neon Skin',     'cost': 2000},
        {'id': 'Shadow',  'name': 'Shadow Skin',   'cost': 5000},
    ],
    'powerups': [
        {'id': 'None',     'name': 'No Starter Powerup', 'cost': 0},
        {'id': 'star',     'name': 'Invincibility Star', 'cost': 500},
        {'id': 'mushroom', 'name': 'Speed Mushroom',     'cost': 500},
    ],
    'pets': [
        {'id': 'None',     'name': 'No Pet', 'cost': 0},
        {'id': 'Tarsier',  'name': 'Tarsier (Auto-Magnet)', 'cost': 5000},
        {'id': 'Agila',    'name': 'Agila (Auto-Attack)', 'cost': 8000},
    ],
    'upgrades': [
        {'id': 'speed',    'name': '+Speed Multiplier', 'cost': 2000},
        {'id': 'jump',     'name': '+Jump Power',       'cost': 2000},
        {'id': 'magnet',   'name': '+Loot Magnet',      'cost': 3000},
    ],
}
