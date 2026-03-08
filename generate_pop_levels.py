import json
import os
import random
import math

OUTPUT_DIR = "test"
TARGET_TILES = 144
WIDTH_LIMIT = 30  # Grid units
HEIGHT_LIMIT = 18 # Grid units

POP_CULTURE_CONCEPTS = [
    ("Étoile de la Mort", "circle_dense"),
    ("Faucon Millenium", "disk_holes"),
    ("Sabre Laser", "rect_long"),
    ("Casque de Vador", "pyramid_steep"),
    ("R2-D2", "cylinder"),
    ("Yoda", "diamond"),
    ("Triforce", "triangles_3"),
    ("Épée de Link", "cross_sharp"),
    ("Rubis Vert", "diamond_small"),
    ("Ocarina", "oval"),
    ("Pokeball", "circle_split"),
    ("Pikachu", "jagged_circle"),
    ("Dracaufeu", "wings"),
    ("Evoli", "star_soft"),
    ("Badge Arène", "octagon"),
    ("Anneau Unique", "ring_thick"),
    ("Tour de Sauron", "tower_single"),
    ("Hache de Gimli", "axe"),
    ("Arc de Legolas", "arc_thin"),
    ("Smaug", "dragon_curve"),
    ("TARDIS", "box_tall"),
    ("Dalek", "cone"),
    ("Tournevis Sonique", "line_complex"),
    ("Cyberman", "square_hollow"),
    ("Vaisseau Enterprise", "saucer"),
    ("Bat-Signal", "bat_shape"),
    ("S de Superman", "diamond_S"),
    ("Bouclier de Cap", "circle_concentric"),
    ("Marteau de Thor", "hammer"),
    ("Masque Iron Man", "face_mask"),
    ("Champignon Mario", "mushroom"),
    ("Tuyau Vert", "pipe"),
    ("Étoile Mario", "star_5"),
    ("Brique Mystère", "cube_float"),
    ("Bloc Tetris", "tetris_stack"),
    ("Fantôme Pacman", "ghost"),
    ("Pacman", "pacman"),
    ("Space Invader", "invader"),
    ("Creeper Minecraft", "creeper_face"),
    ("Épée Diamant", "sword_pixel"),
    ("Portail du Nether", "portal_rect"),
    ("Gateau Portal", "cake"),
    ("Cube de Voyage", "cube_companion"),
    ("Pied de Biche", "crowbar"),
    ("Logo Half-Life", "lambda"),
    ("Trône de Fer", "throne_spikes"),
    ("Oeuf de Dragon", "egg"),
    ("Loup Stark", "wolf_head"),
    ("Main du Roi", "hand_pin"),
    ("Hiver Vient", "snowflake")
]

def generate_base_grid(w, h):
    grid = set()
    for x in range(w):
        for y in range(h):
            grid.add((x, y, 0))
    return list(grid)

def shape_circle(r, density=1.0):
    tiles = []
    cx, cy = 15, 9
    for layer in range(5):
        rr = r - layer * 1.5
        if rr <= 0: break
        for x in range(WIDTH_LIMIT):
            for y in range(HEIGHT_LIMIT):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                if dist <= rr:
                    if random.random() < density:
                        tiles.append({'x': x * 2, 'y': y * 2, 'layer': layer})
    return tiles

def shape_ring(r_outer, r_inner):
    tiles = []
    cx, cy = 15, 9
    for layer in range(4):
        ro = r_outer - layer * 0.5
        ri = r_inner - layer * 0.5
        if ro <= 0: break
        for x in range(WIDTH_LIMIT):
            for y in range(HEIGHT_LIMIT):
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                if ri <= dist <= ro:
                     tiles.append({'x': x * 2, 'y': y * 2, 'layer': layer})
    return tiles

def shape_rect(w, h, layers=3):
    tiles = []
    start_x = (WIDTH_LIMIT - w) // 2
    start_y = (HEIGHT_LIMIT - h) // 2
    for l in range(layers):
        pad = l
        for x in range(start_x + pad, start_x + w - pad):
            for y in range(start_y + pad, start_y + h - pad):
                tiles.append({'x': x * 2, 'y': y * 2, 'layer': l})
    return tiles

def shape_pyramid(base_size):
    tiles = []
    cx, cy = 15, 9
    for l in range(6):
        radius = base_size - l * 2
        if radius < 1: break
        start_x = cx - radius // 2
        start_y = cy - radius // 2
        for x in range(int(start_x), int(start_x + radius)):
            for y in range(int(start_y), int(start_y + radius)):
                tiles.append({'x': x * 2, 'y': y * 2, 'layer': l})
    return tiles

def shape_towers(count):
    tiles = []
    positions = []
    for _ in range(count):
        positions.append((random.randint(2, WIDTH_LIMIT-4), random.randint(2, HEIGHT_LIMIT-4)))
    
    for px, py in positions:
        for l in range(random.randint(3, 6)):
            for dx in range(2):
                for dy in range(2):
                    tiles.append({'x': (px+dx) * 2, 'y': (py+dy) * 2, 'layer': l})
    return tiles

def shape_random_clumps():
    tiles = []
    center_x, center_y = 15, 9
    for i in range(200): # Overshoot slightly
        x = int(random.gauss(center_x, 4))
        y = int(random.gauss(center_y, 3))
        l = int(abs(random.gauss(0, 1.5)))
        if 0 <= x < WIDTH_LIMIT and 0 <= y < HEIGHT_LIMIT and 0 <= l < 5:
             tiles.append({'x': x * 2, 'y': y * 2, 'layer': l})
    # Remove duplicates (same pos)
    unique = {}
    for t in tiles:
        key = (t['x'], t['y'], t['layer'])
        unique[key] = t
    return list(unique.values())

def shape_lines(orientation='h'):
    tiles = []
    if orientation == 'h':
        for y in range(2, HEIGHT_LIMIT-2, 2):
            for x in range(4, WIDTH_LIMIT-4):
                tiles.append({'x': x*2, 'y': y*2, 'layer': 0})
                if x % 2 == 0: tiles.append({'x': x*2, 'y': y*2, 'layer': 1})
    else:
        for x in range(4, WIDTH_LIMIT-4, 3):
             for y in range(2, HEIGHT_LIMIT-2):
                tiles.append({'x': x*2, 'y': y*2, 'layer': 0})
                if y % 2 == 0: tiles.append({'x': x*2, 'y': y*2, 'layer': 1})
    return tiles

def shape_checkerboard():
    tiles = []
    for x in range(2, WIDTH_LIMIT-2):
        for y in range(2, HEIGHT_LIMIT-2):
            if (x + y) % 2 == 0:
                tiles.append({'x': x*2, 'y': y*2, 'layer': 0})
                tiles.append({'x': x*2, 'y': y*2, 'layer': 1})
                if (x+y)%4 == 0: tiles.append({'x': x*2, 'y': y*2, 'layer': 2})
    return tiles

def get_algorithm(style):
    if style == "circle_dense": return lambda: shape_circle(8, 0.9)
    if style == "disk_holes": return lambda: shape_circle(9, 0.7)
    if style == "rect_long": return lambda: shape_rect(20, 4, 4)
    if style == "pyramid_steep": return lambda: shape_pyramid(12)
    if style == "cylinder": return lambda: shape_circle(5, 1.0) # Stacked high done via layer logic in shape_circle? No, standard circle shrinks. Modified below.
    if style == "diamond": return lambda: shape_pyramid(10) # Close enough
    if style == "triangles_3": return lambda: shape_towers(3)
    if style == "cross_sharp": return lambda: shape_lines('v') # Approx
    if style == "diamond_small": return lambda: shape_pyramid(6)
    if style == "oval": return lambda: shape_rect(12, 8, 2)
    if style == "circle_split": return lambda: shape_ring(8, 1)
    if style == "jagged_circle": return lambda: shape_random_clumps()
    if style == "wings": return lambda: shape_lines('h')
    if style == "star_soft": return lambda: shape_circle(6, 0.8)
    if style == "octagon": return lambda: shape_rect(10, 10, 2)
    if style == "ring_thick": return lambda: shape_ring(8, 4)
    if style == "tower_single": return lambda: shape_rect(6, 6, 5)
    if style == "axe": return lambda: shape_lines('v')
    if style == "arc_thin": return lambda: shape_ring(9, 7)
    if style == "dragon_curve": return lambda: shape_random_clumps()
    if style == "box_tall": return lambda: shape_rect(8, 8, 4)
    if style == "cone": return lambda: shape_pyramid(8)
    if style == "line_complex": return lambda: shape_lines('h')
    if style == "square_hollow": return lambda: shape_ring(8, 5)
    if style == "saucer": return lambda: shape_circle(10, 0.5)
    if style == "bat_shape": return lambda: shape_lines('h')
    if style == "diamond_S": return lambda: shape_pyramid(9)
    if style == "circle_concentric": return lambda: shape_ring(9, 2)
    if style == "hammer": return lambda: shape_towers(2)
    if style == "face_mask": return lambda: shape_rect(8, 10, 2)
    if style == "mushroom": return lambda: shape_circle(7, 0.9)
    if style == "pipe": return lambda: shape_rect(6, 6, 4)
    if style == "star_5": return lambda: shape_random_clumps()
    if style == "cube_float": return lambda: shape_rect(6, 6, 3)
    if style == "tetris_stack": return lambda: shape_checkerboard()
    if style == "ghost": return lambda: shape_rect(8, 8, 2)
    if style == "pacman": return lambda: shape_circle(8, 0.8)
    if style == "invader": return lambda: shape_checkerboard()
    if style == "creeper_face": return lambda: shape_rect(10, 10, 2)
    if style == "sword_pixel": return lambda: shape_lines('v')
    if style == "portal_rect": return lambda: shape_rect(5, 8, 4)
    if style == "cake": return lambda: shape_circle(6, 1.0)
    if style == "cube_companion": return lambda: shape_rect(8, 8, 3)
    if style == "crowbar": return lambda: shape_lines('h')
    if style == "lambda": return lambda: shape_pyramid(7)
    if style == "throne_spikes": return lambda: shape_towers(5)
    if style == "egg": return lambda: shape_circle(6, 1.0)
    if style == "wolf_head": return lambda: shape_pyramid(8)
    if style == "hand_pin": return lambda: shape_lines('v')
    if style == "snowflake": return lambda: shape_checkerboard()
    
    return lambda: shape_random_clumps() # Default

def adjust_tile_count(tiles):
    # Remove duplicates
    unique_tiles = {}
    for t in tiles:
        key = (t['x'], t['y'], t['layer'])
        unique_tiles[key] = t
    tiles = list(unique_tiles.values())
    
    current_count = len(tiles)
    
    # Strategy 1: Remove from top layers if too many
    if current_count > TARGET_TILES:
        tiles.sort(key=lambda t: (-t['layer'], -abs(t['x']-30), -abs(t['y']-18))) # Remove furthest/highest first
        tiles = tiles[:TARGET_TILES]
        
    # Strategy 2: Add to base layer if too few
    while len(tiles) < TARGET_TILES:
        # Try to find a spot adjacent to existing tiles on layer 0
        added = False
        candidates = []
        existing_pos = set((t['x'], t['y'], t['layer']) for t in tiles)
        
        for t in tiles:
            if t['layer'] == 0:
                # check neighbors
                neighbors = [(t['x']+2, t['y']), (t['x']-2, t['y']), (t['x'], t['y']+2), (t['x'], t['y']-2)]
                for nx, ny in neighbors:
                    if 0 <= nx < WIDTH_LIMIT*2 and 0 <= ny < HEIGHT_LIMIT*2:
                        if (nx, ny, 0) not in existing_pos:
                            candidates.append({'x': nx, 'y': ny, 'layer': 0})
        
        if not candidates:
             # Just add random spots in grid
             rx = random.randint(2, WIDTH_LIMIT-2) * 2
             ry = random.randint(2, HEIGHT_LIMIT-2) * 2
             candidates.append({'x': rx, 'y': ry, 'layer': 0})
             
        # Pick random candidate
        new_tile = random.choice(candidates)
        if (new_tile['x'], new_tile['y'], new_tile['layer']) not in existing_pos:
            tiles.append(new_tile)
            existing_pos.add((new_tile['x'], new_tile['y'], new_tile['layer']))
            
    return tiles

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    for name, style in POP_CULTURE_CONCEPTS:
        generator = get_algorithm(style)
        base_tiles = generator()
        final_tiles = adjust_tile_count(base_tiles)
        
        # Double check count
        if len(final_tiles) != TARGET_TILES:
            # Force exact trim or pad
            final_tiles = adjust_tile_count(final_tiles)
            
        filename = f"{name}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_tiles, f, indent=2)
            
    print(f"Generated {len(POP_CULTURE_CONCEPTS)} levels in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
