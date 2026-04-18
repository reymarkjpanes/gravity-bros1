import os
import glob
try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Please install it using: pip install Pillow")
    exit(1)

def extract_sprite(src_path, dest_dir, base_name, prefix="player_"):
    print(f"Processing {base_name} from {src_path}...")
    img = Image.open(src_path).convert("RGBA")
    data = img.getdata()
    
    new_data = []
    # Simple color keying for bright green
    for item in data:
        r, g, b, a = item
        # Look for dominating green
        if g > 150 and r < 100 and b < 100:
            new_data.append((255, 255, 255, 0))
        elif g > 200 and r < 150 and b < 150:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
        
    # Resize to game proportions. Standard hitboxes are 24x32.
    # We will resize image to width 48 (give it some bleed) and height proportional.
    target_height = 42
    target_width = int((float(img.size[0]) / float(img.size[1])) * target_height)
    
    img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    # Left and Right facing
    right_img = img
    left_img = img.transpose(Image.FLIP_LEFT_RIGHT)
    
    # Jump variations (tilted)
    jump_right = right_img.rotate(10, expand=True, resample=Image.Resampling.BICUBIC)
    jump_left = left_img.rotate(-10, expand=True, resample=Image.Resampling.BICUBIC)
    
    # Save files
    right_img.save(os.path.join(dest_dir, f"{prefix}{base_name}_idle_right.png"))
    left_img.save(os.path.join(dest_dir, f"{prefix}{base_name}_idle_left.png"))
    jump_right.save(os.path.join(dest_dir, f"{prefix}{base_name}_jump_right.png"))
    jump_left.save(os.path.join(dest_dir, f"{prefix}{base_name}_jump_left.png"))
    print(f"[{base_name}] Processed and saved to assets directory!")

if __name__ == "__main__":
    src_dir = os.path.join(os.path.dirname(__file__), "..", "concept_art")
    dest_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "images")
    
    os.makedirs(dest_dir, exist_ok=True)
    
    image_files = glob.glob(os.path.join(src_dir, "*_concept_*.png"))
    
    for file in image_files:
        basename = os.path.basename(file)
        # Parse the actual name (e.g. juan_concept_123.png -> juan)
        char_name = basename.split("_concept_")[0]
        
        prefix = "player_"
        if char_name in ['walker', 'hopper', 'archer', 'shielded', 'kapre', 'igorot', 'carabao']:
            prefix = "enemy_" # or just generic prefix if we want it to adapt. Let's use player_ for all so player class can read it, enemies use their own string.
            # actually enemy class uses pygame.image.load directly over strings or generic names?
            # Let's save enemies as enemy_NAME_idle_... or just player_NAME if player uses it.
            
            # The player loading logic does: f'player_{char}_{state}_{d}.png'
        
        extract_sprite(file, dest_dir, char_name, prefix)

    print("All available assets have been successfully extracted and ported to the engine!")
