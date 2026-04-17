LEVEL_THEMES = [
    {"name": "Banaue Rice Terraces", "sky": (135, 250, 255), "bg1": (0, 200, 100), "bg2": (0, 255, 127), "ground": (160, 82, 45), "top": (50, 255, 50), "water": (0, 191, 255)},
    {"name": "Chocolate Hills", "sky": (150, 230, 255), "bg1": (180, 100, 40), "bg2": (210, 120, 50), "ground": (130, 70, 25), "top": (200, 110, 30), "water": (0, 200, 255)},
    {"name": "Boracay Beach", "sky": (0, 255, 255), "bg1": (150, 230, 255), "bg2": (255, 250, 200), "ground": (240, 230, 140), "top": (255, 255, 150), "water": (0, 255, 200)},
    {"name": "Palawan Underground River", "sky": (20, 40, 60), "bg1": (0, 255, 127), "bg2": (0, 150, 150), "ground": (50, 50, 50), "top": (80, 255, 200), "water": (0, 255, 255)},
    {"name": "Mayon Volcano", "sky": (255, 100, 50), "bg1": (255, 0, 0), "bg2": (200, 50, 50), "ground": (80, 40, 40), "top": (255, 165, 0), "water": (255, 50, 0)},
    {"name": "Mount Pulag", "sky": (200, 240, 255), "bg1": (150, 200, 255), "bg2": (230, 255, 255), "ground": (180, 200, 220), "top": (255, 255, 255), "water": (100, 200, 255)},
    {"name": "Tubbataha Reefs", "sky": (0, 50, 200), "bg1": (0, 255, 255), "bg2": (0, 200, 150), "ground": (0, 150, 100), "top": (0, 255, 200), "water": (0, 100, 255)},
    {"name": "Kawasan Falls", "sky": (200, 255, 255), "bg1": (0, 200, 100), "bg2": (50, 255, 150), "ground": (0, 150, 50), "top": (0, 255, 100), "water": (0, 255, 255)},
    {"name": "Vigan Calle Crisologo", "sky": (255, 200, 0), "bg1": (255, 140, 0), "bg2": (200, 100, 50), "ground": (150, 80, 20), "top": (255, 165, 0), "water": (200, 100, 20)},
    {"name": "Manila Skyline", "sky": (10, 10, 100), "bg1": (150, 0, 255), "bg2": (255, 0, 255), "ground": (50, 50, 60), "top": (0, 255, 255), "water": (50, 50, 255)},
]

BOSS_LIST = [
    'igorot', 'carabao', 'bakunawa', 'sirena', 'mayon',
    'tikbalang', 'dambuhala', 'diwata', 'kutsero', 'haring_ibon'
]

def get_theme(level):
    return LEVEL_THEMES[(level - 1) % len(LEVEL_THEMES)]

def get_boss_type(level):
    if level <= len(BOSS_LIST):
        return BOSS_LIST[level - 1]
    return 'mayon'
