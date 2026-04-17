import os
import sys
import requests
import base64
from PIL import Image
from io import BytesIO

# The user provided API Key
API_KEY = "YOUR_API_KEY_HERE"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'images')
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHARACTERS = [
    'Juan', 'Maria', 'LapuLapu', 'Jose', 'Andres', 
    'Aswang', 'Tikbalang', 'Kapre', 'Manananggal', 
    'Datu', 'Sorbetero', 'Taho', 'Malunggay', 'Batak', 'Jeepney'
]

def remove_white_bg(img):
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    bg_color = data[0]
    tolerance = 25
    for item in data:
        if (abs(item[0] - bg_color[0]) < tolerance and 
            abs(item[1] - bg_color[1]) < tolerance and 
            abs(item[2] - bg_color[2]) < tolerance):
            new_data.append((255, 255, 255, 0)) # transparent
        else:
            new_data.append(item)
    img.putdata(new_data)
    return img

def generate_sprites():
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    for char in CHARACTERS:
        d_left = os.path.join(OUTPUT_DIR, f"player_{char.lower()}_idle_left.png")
        d_right = os.path.join(OUTPUT_DIR, f"player_{char.lower()}_idle_right.png")
        jump_left = os.path.join(OUTPUT_DIR, f"player_{char.lower()}_jump_left.png")
        jump_right = os.path.join(OUTPUT_DIR, f"player_{char.lower()}_jump_right.png")

        if os.path.exists(d_right):
            print(f"Skipping {char}, already exists.")
            continue
            
        prompt = (f"Pixel art Filipino hero '{char}', Mario-style side-scroller game character, "
                  f"16-bit cute sprite, facing right, pure white solid background. "
                  f"Simple and clear character design without any background scenery.")
        
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1}
        }
        
        print(f"Generating image for {char}...")
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            res_json = response.json()
            
            # The Imagen API returns base64 in res_json['predictions'][0]['bytesBase64Encoded']
            img_b64 = res_json['predictions'][0]['bytesBase64Encoded']
            img_data = base64.b64decode(img_b64)
            img = Image.open(BytesIO(img_data))
            
            img.thumbnail((128, 128))
            
            transparent_img = remove_white_bg(img)
            bbox = transparent_img.getbbox()
            if bbox:
                transparent_img = transparent_img.crop(bbox)
                
            final_img = transparent_img.resize((24, 32), Image.Resampling.NEAREST)
            
            final_img.save(d_right)
            final_img.save(jump_right)
            
            flipped = final_img.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            flipped.save(d_left)
            flipped.save(jump_left)
            
            print(f"Successfully saved transparent sprites for {char}.")
            
        except Exception as e:
            print(f"Error generating {char}: {e}")

if __name__ == "__main__":
    generate_sprites()
