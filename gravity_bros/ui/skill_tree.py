import pygame
from config import WIDTH, HEIGHT, GOLD, WHITE

# Skill tree definition  
# Each skill: id, name, description, branch (0=Gravity, 1=Combat, 2=Agility), row, cost
SKILLS = [
    # Branch 0: Gravity Mastery (purple)
    {'id': 'grav_flip_speed', 'name': 'Quick Flip',    'desc': 'Gravity flip recharge -30%',       'branch': 0, 'row': 0, 'cost': 2},
    {'id': 'grav_air_control','name': 'Air Ride',      'desc': 'Full movement control mid-air',    'branch': 0, 'row': 1, 'cost': 3, 'requires': 'grav_flip_speed'},
    {'id': 'grav_cooldown',   'name': 'Zero Gravity',  'desc': 'Unique skill cooldown -25%',       'branch': 0, 'row': 2, 'cost': 4, 'requires': 'grav_air_control'},
    
    # Branch 1: Combat Power (red)
    {'id': 'combat_proj',     'name': 'Power Shot',    'desc': 'Projectiles deal 2x boss damage',  'branch': 1, 'row': 0, 'cost': 2},
    {'id': 'combat_melee',    'name': 'Iron Fist',     'desc': 'Melee damage +50%, wider arc',     'branch': 1, 'row': 1, 'cost': 3, 'requires': 'combat_proj'},
    {'id': 'combat_dash',     'name': 'Blade Rush',    'desc': 'Dash knocks back bosses heavily',  'branch': 1, 'row': 2, 'cost': 4, 'requires': 'combat_melee'},

    # Branch 2: Agility (green)
    {'id': 'agil_speed',      'name': 'Fleet Foot',    'desc': 'Move speed +20%',                  'branch': 2, 'row': 0, 'cost': 2},
    {'id': 'agil_jump',       'name': 'Spring Step',   'desc': 'Jump height +25%',                 'branch': 2, 'row': 1, 'cost': 3, 'requires': 'agil_speed'},
    {'id': 'agil_double_jump','name': 'Sky Walker',    'desc': 'Gain permanent double jump',       'branch': 2, 'row': 2, 'cost': 4, 'requires': 'agil_jump'},
]

BRANCH_COLORS = [(130, 80, 210), (220, 60, 60), (60, 200, 80)]
BRANCH_NAMES  = ['GRAVITY MASTERY', 'COMBAT POWER', 'AGILITY']

def draw_skill_tree(screen, font, big_font, unlocked_skills, skill_points, selection):
    screen.fill((8, 10, 20))
    
    # Header
    pygame.draw.rect(screen, (25, 25, 45), (0, 0, WIDTH, 75))
    pygame.draw.line(screen, GOLD, (0, 75), (WIDTH, 75), 3)
    
    title = big_font.render("RPG SKILL TREE", True, GOLD)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 18))
    
    sp_surf = font.render(f"Skill Points: {skill_points}", True, (200, 230, 255))
    screen.blit(sp_surf, (WIDTH - 260, 25))
    
    hint = font.render("[1/2/3] Branch | [UP/DOWN] Node | [ENTER] Unlock | [ESC] Back", True, (120, 120, 120))
    screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 35))
    
    # Draw branch headers
    branch_x = [WIDTH // 4, WIDTH // 2, (WIDTH * 3) // 4]
    for i, (bx, bname) in enumerate(zip(branch_x, BRANCH_NAMES)):
        col = BRANCH_COLORS[i]
        hdr = font.render(bname, True, col)
        screen.blit(hdr, (bx - hdr.get_width()//2, 90))
        pygame.draw.line(screen, col, (bx, 120), (bx, HEIGHT - 60), 2)
    
    # Draw nodes
    for idx, sk in enumerate(SKILLS):
        bx = branch_x[sk['branch']]
        row_y = 155 + sk['row'] * 130
        is_unlocked = sk['id'] in unlocked_skills
        req = sk.get('requires')
        req_met = (req is None or req in unlocked_skills)
        is_selected = (idx == selection)
        
        col = BRANCH_COLORS[sk['branch']]
        bg   = (40, 40, 60) if not req_met else ((20, 60, 20) if is_unlocked else (50, 50, 80))
        border = col if (is_selected or is_unlocked) else (80, 80, 80)
        border_w = 3 if is_selected else (2 if is_unlocked else 1)
        
        node_rect = pygame.Rect(bx - 100, row_y - 40, 200, 80)
        try:
            pygame.draw.rect(screen, bg, node_rect, 0, 10)
            pygame.draw.rect(screen, border, node_rect, border_w, 10)
        except TypeError:
            pygame.draw.rect(screen, bg, node_rect)
            pygame.draw.rect(screen, border, node_rect, border_w)
        
        # Draw connector line to next node in same branch
        next_nodes = [s for s in SKILLS if s['branch'] == sk['branch'] and s['row'] == sk['row'] + 1]
        if next_nodes:
            ny = 155 + next_nodes[0]['row'] * 130 - 40
            pygame.draw.line(screen, col, (bx, row_y + 40), (bx, ny), 2)
        
        # Lock icon or checkmark
        status_icon = "✓" if is_unlocked else ("?" if not req_met else f"[{sk['cost']}SP]")
        status_col  = (80, 255, 80) if is_unlocked else ((80, 80, 80) if not req_met else GOLD)
        
        name_surf = font.render(sk['name'], True, WHITE if req_met else (80, 80, 80))
        desc_sf   = pygame.font.SysFont("monospace", 14).render(sk['desc'], True, (160, 160, 180) if req_met else (60, 60, 60))
        sp_sf     = font.render(status_icon, True, status_col)
        
        screen.blit(name_surf, (bx - name_surf.get_width()//2, row_y - 30))
        screen.blit(desc_sf,   (bx - desc_sf.get_width()//2,   row_y - 8))
        screen.blit(sp_sf,     (bx - sp_sf.get_width()//2,     row_y + 14))


def apply_skill_buffs(player, unlocked_skills):
    """Apply passive buffs from unlocked skills to player each frame."""
    if 'agil_speed' in unlocked_skills:
        player.speed = max(player.speed, 6)
    if 'agil_jump' in unlocked_skills:
        player.jump_power = max(player.jump_power, 17)
    if 'agil_double_jump' in unlocked_skills:
        player.double_jump_active = True
    if 'grav_cooldown' in unlocked_skills and player.ability_cooldown > 0:
        player.max_cooldown = int(player.max_cooldown * 0.75)
