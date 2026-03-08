import json
import os
import math
import random

OUTPUT_DIR = "test"
TARGET_TILES = 144

def add_tile(tiles, occupied, x, y, l):
    # Mahjong tiles usually take 2x2 grid units.
    # To avoid overlap, any new tile at (x,y) must not have 
    # neighbors at x+/-1, y+/-1 on the same layer.
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if (x+dx, y+dy, l) in occupied:
                return False
    tiles.append({'x': x, 'y': y, 'layer': l})
    occupied.add((x, y, l))
    return True

def generate_heart(tiles, occupied):
    # Basic heart shape: Triangle at bottom, 2 circles top
    cx, cy = 15, 8
    # Layer 0: Full heart (Base)
    for y in range(0, 8): # Top lobes
        for x in range(cx-8, cx+9, 2):
            dist = math.sqrt((x-(cx-4))**2 + (y-4)**2)
            dist2 = math.sqrt((x-(cx+4))**2 + (y-4)**2)
            if dist < 4 or dist2 < 4: add_tile(tiles, occupied, x, y, 0)
    for y in range(8, 16, 2): # Bottom triangle
        w = 16 - (y-8)*2
        for x in range(cx - w//2, cx + w//2 + 1, 2):
            add_tile(tiles, occupied, x, y, 0)
    # Layers 1+: Smaller versions
    for l in range(1, 6):
        for y in range(l, 16-l, 2):
            w = 12 - l*2 - (y-l)*0.5
            if w <= 0: break
            for x in range(int(cx - w), int(cx + w + 1), 2):
                add_tile(tiles, occupied, x, y, l)

def generate_pyramid(tiles, occupied):
    # Perfect 6-layer pyramid
    cx, cy = 15, 10
    for l in range(6):
        size = 14 - l*2
        for x in range(cx - size, cx + size + 1, 2):
            for y in range(cy - size, cy + size + 1, 2):
                add_tile(tiles, occupied, x, y, l)

def generate_star(tiles, occupied):
    # 4-branch star (Cross-like)
    cx, cy = 15, 10
    for l in range(6):
        w, h = 18 - l*3, 2 + l
        for x in range(int(cx-w), int(cx+w+1), 2):
            for y in range(cy-2, cy+3, 2):
                add_tile(tiles, occupied, x, y, l)
        for y in range(int(cy-w), int(cy+w+1), 2):
            for x in range(cx-2, cx+3, 2):
                add_tile(tiles, occupied, x, y, l)

def generate_diamond(tiles, occupied):
    # Rhombus shape
    cx, cy = 15, 10
    for l in range(5):
        size = 12 - l*2
        for y in range(cy - size, cy + size + 1, 2):
            w = size - abs(y-cy)
            for x in range(int(cx - w), int(cx + w + 1), 2):
                add_tile(tiles, occupied, x, y, l)

def generate_arena(tiles, occupied):
    # Circular amphitheater
    cx, cy = 15, 10
    for l in range(5):
        outer_r, inner_r = 10 - l*0.5, 6 - l
        if inner_r < 0: inner_r = 0
        for x in range(0, 30, 2):
            for y in range(0, 20, 2):
                d = math.sqrt((x-cx)**2 + (y-cy)**2)
                if inner_r <= d <= outer_r:
                    add_tile(tiles, occupied, x, y, l)

def generate_tower_babel(tiles, occupied):
    # Spiral tower
    cx, cy = 15, 10
    for l in range(6):
        r = 8 - l
        for x in range(0, 30, 2):
            for y in range(0, 20, 2):
                d = math.sqrt((x-cx)**2 + (y-cy)**2)
                angle = math.atan2(y-cy, x-cx)
                if d <= r + (angle / (2*math.pi)):
                    add_tile(tiles, occupied, x, y, l)

def generate_butterfly(tiles, occupied):
    # Symmetrical wings
    cx, cy = 15, 10
    for l in range(4):
        for y in range(cy-8, cy+9, 2):
            w = 8 - abs(y-cy)*0.5 - l
            if w <= 0: continue
            for dx in range(2, int(w*2), 2):
                add_tile(tiles, occupied, cx + dx, y, l)
                add_tile(tiles, occupied, cx - dx, y, l)
        # Body
        for y in range(cy-10, cy+11, 2):
            add_tile(tiles, occupied, cx, y, l)

def generate_cross(tiles, occupied):
    # Classic Maltese cross style
    cx, cy = 15, 10
    for l in range(5):
        for x in range(cx-10+l, cx+11-l, 2):
            if abs(x-cx) < 3:
                for y in range(cy-10+l, cy+11-l, 2): add_tile(tiles, occupied, x, y, l)
            else:
                for y in range(cy-3, cy+4, 2): add_tile(tiles, occupied, x, y, l)

def generate_smiley(tiles, occupied):
    # Round face with eyes and mouth
    cx, cy = 15, 10
    # Face (Base)
    for x in range(cx-10, cx+11, 2):
        for y in range(cy-10, cy+11, 2):
            d = math.sqrt((x-cx)**2 + (y-cy)**2)
            if d <= 10:
                # Eyes hollow?
                is_eye = (abs(x-(cx-4)) < 2 or abs(x-(cx+4)) < 2) and abs(y-(cy-4)) < 2
                is_mouth = abs(y-(cy+4)) < 2 and abs(x-cx) < 6
                if not (is_eye or is_mouth): add_tile(tiles, occupied, x, y, 0)
                if d <= 8: add_tile(tiles, occupied, x, y, 1)
                if d <= 6: add_tile(tiles, occupied, x, y, 2)

def generate_hourglass(tiles, occupied):
    # Two triangles touching at tip
    cx, cy = 15, 10
    for l in range(5):
        size = 10 - l
        for y in range(cy-size, cy+size+1, 2):
            if y == cy: w = 2
            else: w = abs(y-cy)
            for x in range(cx-w, cx+w+1, 2):
                add_tile(tiles, occupied, x, y, l)

def adjust_to_144(tiles, occupied):
    # Remove if too many (start from top layer, furthest from center)
    if len(tiles) > TARGET_TILES:
        tiles.sort(key=lambda t: (-t['layer'], math.sqrt((t['x']-15)**2 + (t['y']-10)**2)), reverse=True)
        # Keep only the first 144
        final = tiles[:TARGET_TILES]
        return final
    
    # Add if too few (on layer 0, adjacent to existing)
    while len(tiles) < TARGET_TILES:
        added = False
        # Try finding neighbors on layer 0
        random.shuffle(tiles)
        for t in tiles:
            if t['layer'] == 0:
                for dx, dy in [(2,0), (-2,0), (0,2), (0,-2)]:
                    nx, ny = t['x']+dx, t['y']+dy
                    if 0 <= nx <= 30 and 0 <= ny <= 20:
                        if add_tile(tiles, occupied, nx, ny, 0):
                            added = True; break
                if added: break
        if not added:
            # Fallback random
            add_tile(tiles, occupied, random.randint(0,15)*2, random.randint(0,10)*2, 0)
    return tiles

def main():
    generators = [
        ("Pyramide", generate_pyramid),
        ("Cœur", generate_heart),
        ("Étoile", generate_star),
        ("Diamant", generate_diamond),
        ("Arène", generate_arena),
        ("Tour de Babel", generate_tower_babel),
        ("Papillon", generate_butterfly),
        ("Croix", generate_cross),
        ("Smiley", generate_smiley),
        ("Sablier", generate_hourglass)
    ]
    
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    for name, gen_func in generators:
        tiles = []
        occupied = set()
        gen_func(tiles, occupied)
        final_tiles = adjust_to_144(tiles, occupied)
        
        # Security check: exactly 144
        while len(final_tiles) > 144: final_tiles.pop()
        
        filepath = os.path.join(OUTPUT_DIR, f"{name}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_tiles, f, indent=2)
            
    print(f"Généré {len(generators)} niveaux dans {OUTPUT_DIR}")

if __name__ == "__main__": main()
