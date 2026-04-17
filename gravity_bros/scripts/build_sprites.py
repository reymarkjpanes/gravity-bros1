import os
from PIL import Image, ImageDraw

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Character visual properties mapping (Head Color, Body Color, Accessory Color)
CHAR_PALETTES = {
    'Juan':          [(210, 180, 140), (139, 69, 19),  (0, 100, 0)],      # Tan, Brown, Green Hat
    'Maria':         [(255, 228, 196), (255, 105, 180), (255, 192, 203)], # Fair, Pink dress, Pink details
    'LapuLapu':      [(160, 82, 45),   (205, 133, 63),  (255, 0, 0)],      # Red bandana, dark skin
    'Jose':          [(222, 184, 135), (105, 105, 105), (0, 0, 0)],        # Coat
    'Andres':        [(160, 82, 45),   (255, 255, 255), (178, 34, 34)],    # White shirt, red pants
    'Aswang':        [(75, 0, 130),    (47, 79, 79),    (128, 0, 128)],    # Purple/Dark
    'Tikbalang':     [(105, 80, 50),   (139, 69, 19),   (210, 105, 30)],   # Horse colors
    'Kapre':         [(47, 79, 79),    (47, 79, 79),    (105, 105, 105)],  # Dark grey/green, cigar
    'Manananggal':   [(216, 191, 216), (139, 0, 0),     (0, 0, 0)],        # Pale, red guts, bat wings
    'Datu':          [(139, 69, 19),   (218, 165, 32),  (255, 215, 0)],    # Gold/Yellow regal
    'Sorbetero':     [(222, 184, 135), (255, 255, 255), (0, 0, 255)],      # White uniform, blue hat
    'Taho':          [(205, 133, 63),  (245, 245, 220), (139, 69, 19)],    # Tan, buckets
    'Malunggay':     [(144, 238, 144), (34, 139, 34),   (0, 128, 0)],      # Greens
    'Batak':         [(139, 69, 19),   (139, 69, 19),   (255, 0, 0)],      # Bare skin, tattoos (red markings)
    'Jeepney':       [(192, 192, 192), (255, 215, 0),   (255, 0, 0)],      # Metal, yellow, red trims
}

def build_character(char_id):
    # 24x32 is our player rect size
    img = Image.new('RGBA', (24, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    
    colors = CHAR_PALETTES.get(char_id, [(200, 200, 200), (100, 100, 100), (50, 50, 50)])
    skin, body, acc = colors
    
    # Base Silhouette offsets for animation
    # Idle
    y_off = 0
    
    # 1. Body
    if char_id == 'Jeepney':
        # Jeepney is basically a small vehicle block
        d.rectangle([2, 10+y_off, 22, 30+y_off], fill=body)
        d.rectangle([5, 15+y_off, 12, 22+y_off], fill=(135, 206, 235)) # Window
        d.rectangle([18, 25+y_off, 22, 30+y_off], fill=acc) # Bumper
        d.ellipse([4, 28+y_off, 10, 32+y_off], fill=(40, 40, 40)) # Wheel
        d.ellipse([14, 28+y_off, 20, 32+y_off], fill=(40, 40, 40)) # Wheel
    else:
        # Legs
        d.rectangle([6, 26+y_off, 10, 32+y_off], fill=(40, 40, 40))
        d.rectangle([14, 26+y_off, 18, 32+y_off], fill=(40, 40, 40))
        
        # Torso
        d.rectangle([5, 12+y_off, 19, 26+y_off], fill=body)
        
        # Arms
        d.rectangle([1, 14+y_off, 5, 22+y_off], fill=skin)
        d.rectangle([19, 14+y_off, 23, 22+y_off], fill=skin)
        
        # Head
        d.rectangle([6, 2+y_off, 18, 12+y_off], fill=skin)
        
        # Eyes facing right
        d.rectangle([12, 5+y_off, 14, 7+y_off], fill=(0, 0, 0))
        d.rectangle([16, 5+y_off, 18, 7+y_off], fill=(0, 0, 0))
        
        # Specific details
        if char_id == 'Juan': d.rectangle([4, 0+y_off, 20, 4+y_off], fill=acc) # Hat
        if char_id == 'Maria': d.polygon([(5, 26+y_off), (19, 26+y_off), (24, 32+y_off), (0, 32+y_off)], fill=body) # Skirt
        if char_id == 'LapuLapu': d.rectangle([6, 2+y_off, 18, 4+y_off], fill=acc) # Bandana
        if char_id == 'Kapre': d.rectangle([18, 10+y_off, 24, 12+y_off], fill=acc) # Cigar
        if char_id == 'Manananggal': d.polygon([(0, 10+y_off), (5, 15+y_off), (0, 20+y_off)], fill=(20, 20, 20)) # Wing
        if char_id == 'Andres': d.rectangle([6, 26+y_off, 18, 30+y_off], fill=acc) # Red pants
        if char_id == 'Taho': 
            d.rectangle([20, 15+y_off, 23, 22+y_off], fill=(192, 192, 192)) # Bucket
            d.rectangle([1, 15+y_off, 4, 22+y_off], fill=(192, 192, 192))
    
    # Save Right Idle
    img.save(os.path.join(OUTPUT_DIR, f"player_{char_id.lower()}_idle_right.png"))
    
    # Save Right Jump (Lift legs up slightly using offset)
    y_off = -2
    jump_img = Image.new('RGBA', (24, 32), (0, 0, 0, 0))
    jump_img.paste(img.crop((0, 0, 24, 26)), (0, 0))
    dj = ImageDraw.Draw(jump_img)
    dj.rectangle([6, 24, 10, 28], fill=(40, 40, 40)) # Retracted legs
    dj.rectangle([14, 24, 18, 28], fill=(40, 40, 40))
    jump_img.save(os.path.join(OUTPUT_DIR, f"player_{char_id.lower()}_jump_right.png"))
    
    # Flip for Left
    img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(os.path.join(OUTPUT_DIR, f"player_{char_id.lower()}_idle_left.png"))
    jump_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(os.path.join(OUTPUT_DIR, f"player_{char_id.lower()}_jump_left.png"))

def main():
    print("Synthesizing diverse 16-bit characters...")
    for char_id in CHAR_PALETTES.keys():
        build_character(char_id)
        print(f"[OK] Generated transparent assets for {char_id}!")

if __name__ == "__main__":
    main()
