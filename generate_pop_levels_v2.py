import json
import os
import random
import math

OUTPUT_DIR = "test"
TARGET_TILES = 144
WIDTH_LIMIT = 24  # Grid units (max 30)
HEIGHT_LIMIT = 14 # Grid units (max 18)

# Liste de 50 concepts de monuments mondiaux (formes géométriques iconiques)
WORLD_MONUMENTS = [
    ("Tour Eiffel", "tower_taper"),
    ("Pyramide de Gizeh", "pyramid_solid"),
    ("Le Colisée", "ring_oval"),
    ("Arc de Triomphe", "arch_thick"),
    ("Mont Saint-Michel", "island_peak"),
    ("Tour de Pise", "tower_leaning"),
    ("Taj Mahal", "dome_complex"),
    ("Statue de la Liberté", "monolith_pedestal"),
    ("Mont Rushmore", "wall_carved"),
    ("Grand Canyon", "ravine_layered"),
    ("Big Ben", "tower_clock"),
    ("Opéra de Sydney", "shells_overlapping"),
    ("Grande Muraille", "winding_wall"),
    ("Machu Picchu", "terraces"),
    ("Château de Versailles", "u_shape_palace"),
    ("Cathédrale Notre-Dame", "h_cathedral"),
    ("Le Louvre", "pyramid_glass"),
    ("Acropole d'Athènes", "pillared_hill"),
    ("Sagrada Família", "multi_spire"),
    ("Empire State Building", "stepped_skyscraper"),
    ("Burj Khalifa", "needle_tall"),
    ("Château de Chambord", "castle_turrets"),
    ("Alhambra", "courtyard_complex"),
    ("Pétra", "facade_in_wall"),
    ("Le Parthénon", "pillared_box"),
    ("Mont Fuji", "perfect_cone"),
    ("Everest", "high_peak"),
    ("Kilimandjaro", "plateau_volcano"),
    ("Uluru", "solid_block"),
    ("Table Mountain", "flat_plateau"),
    ("Baie d'Ha Long", "scattered_peaks"),
    ("Chutes du Niagara", "horseshoe_curve"),
    ("Vésuve", "caldera_ring"),
    ("Aurore Boréale", "wave_layers"),
    ("Barrière de Corail", "organic_reef"),
    ("Amazonie", "forest_clump"),
    ("Sahara", "dune_waves"),
    ("Antarctique", "central_dome"),
    ("Forêt Noire", "dense_grid"),
    ("Galápagos", "archipelago"),
    ("Île de Pâques", "vertical_monoliths"),
    ("Stonehenge", "stone_circle"),
    ("Angkor Wat", "five_tower_lotus"),
    ("Cité Interdite", "rect_courtyard"),
    ("Kremlin", "spired_fortress"),
    ("Neuschwanstein", "fairy_castle"),
    ("Alcatraz", "prison_island"),
    ("Canaux de Venise", "split_islands"),
    ("Santorin", "stepped_white_houses"),
    ("Dubrovnik", "walled_city")
]

def add_tile(tiles, x, y, l):
    tiles.append({'x': int(x) * 2, 'y': int(y) * 2, 'layer': int(l)})

# --- Primitives de formes ---

def build_tower(tiles, cx, cy, base_w, layers, taper=True):
    for l in range(layers):
        w = max(1, base_w - (l if taper else 0))
        for dx in range(-w//2, w//2 + (w%2)):
            for dy in range(-w//2, w//2 + (w%2)):
                add_tile(tiles, cx + dx, cy + dy, l)

def build_arch(tiles, cx, cy, w, h, layers):
    for l in range(layers):
        for dx in range(-w//2, w//2 + (w%2)):
            for dy in range(-h//2, h//2 + (h%2)):
                if abs(dx) > w//4 or dy < -h//4: # Make it an arch/hollow
                    add_tile(tiles, cx + dx, cy + dy, l)

def build_ring(tiles, cx, cy, r_outer, r_inner, layers):
    for l in range(layers):
        ro = r_outer - l*0.5
        ri = r_inner - l*0.5
        if ro <= ri: break
        for x in range(int(cx - ro), int(cx + ro + 1)):
            for y in range(int(cy - ro), int(cy + ro + 1)):
                d = math.sqrt((x-cx)**2 + (y-cy)**2)
                if ri <= d <= ro:
                    add_tile(tiles, x, y, l)

def build_pyramid(tiles, cx, cy, size, max_layers):
    for l in range(max_layers):
        s = size - l*2
        if s < 1: break
        for dx in range(-s//2, s//2 + (s%2)):
            for dy in range(-s//2, s//2 + (s%2)):
                add_tile(tiles, cx + dx, cy + dy, l)

def build_wall(tiles, x1, y1, x2, y2, layers, winding=False):
    length = int(math.sqrt((x2-x1)**2 + (y2-y1)**2))
    for i in range(length + 1):
        t = i / length
        px = x1 + (x2-x1)*t
        py = y1 + (y2-y1)*t
        if winding: py += math.sin(t * 10) * 2
        for l in range(layers):
            add_tile(tiles, px, py, l)

def build_dome(tiles, cx, cy, r, layers):
    for l in range(layers):
        curr_r = r * math.cos((l/layers) * (math.pi/2))
        for x in range(int(cx - curr_r), int(cx + curr_r + 1)):
            for y in range(int(cy - curr_r), int(cy + curr_r + 1)):
                if math.sqrt((x-cx)**2 + (y-cy)**2) <= curr_r:
                    add_tile(tiles, x, y, l)

# --- Dispatcher d'algorithmes ---

def generate_level_tiles(style):
    tiles = []
    cx, cy = 12, 7
    if style == "tower_taper": build_tower(tiles, cx, cy, 6, 6, True)
    elif style == "pyramid_solid": build_pyramid(tiles, cx, cy, 12, 6)
    elif style == "ring_oval": build_ring(tiles, cx, cy, 8, 5, 3)
    elif style == "arch_thick": build_arch(tiles, cx, cy, 10, 8, 3)
    elif style == "island_peak":
        build_ring(tiles, cx, cy, 9, 0, 1) # Base
        build_pyramid(tiles, cx, cy, 6, 5) # Peak
    elif style == "tower_leaning":
        for l in range(6):
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    add_tile(tiles, cx + dx + l, cy + dy, l) # Offset X for leaning
    elif style == "dome_complex":
        build_dome(tiles, cx, cy, 6, 4)
        for dx, dy in [(-7, -7), (7, -7), (-7, 7), (7, 7)]: build_tower(tiles, cx+dx, cy+dy, 2, 5, False)
    elif style == "monolith_pedestal":
        build_rect(tiles, cx, cy, 10, 10, 2)
        build_tower(tiles, cx, cy, 4, 6, False)
    elif style == "wall_carved":
        build_rect(tiles, cx, cy, 18, 10, 2)
        build_rect(tiles, cx, cy, 12, 6, 5)
    elif style == "ravine_layered":
        build_rect(tiles, cx, cy, 22, 12, 1)
        build_ring(tiles, cx, cy, 10, 4, 4)
    elif style == "tower_clock": build_tower(tiles, cx, cy, 4, 7, False)
    elif style == "shells_overlapping":
        for i in range(3): build_dome(tiles, cx - 4 + i*4, cy, 5, 4)
    elif style == "winding_wall": build_wall(tiles, 2, 7, 22, 7, 3, True)
    elif style == "terraces":
        for l in range(5): build_rect(tiles, cx + l, cy + l, 15 - l, 10 - l, 1)
    elif style == "u_shape_palace":
        build_rect(tiles, cx-6, cy, 4, 10, 3)
        build_rect(tiles, cx+6, cy, 4, 10, 3)
        build_rect(tiles, cx, cy-4, 12, 3, 2)
    elif style == "h_cathedral":
        build_tower(tiles, cx-5, cy, 4, 5, False)
        build_tower(tiles, cx+5, cy, 4, 5, False)
        build_rect(tiles, cx, cy, 6, 4, 2)
    elif style == "pyramid_glass": build_pyramid(tiles, cx, cy, 10, 5)
    elif style == "pillared_hill":
        build_rect(tiles, cx, cy, 16, 10, 1) # Hill
        for x in range(cx-6, cx+7, 3):
            for y in [cy-3, cy+3]: build_tower(tiles, x, y, 1, 4, False)
    elif style == "multi_spire":
        for _ in range(5): build_tower(tiles, cx + random.randint(-5, 5), cy + random.randint(-4, 4), 2, 6, True)
    elif style == "stepped_skyscraper":
        for l in range(6): build_rect(tiles, cx, cy, 12 - l*2, 12 - l*2, 1)
    elif style == "needle_tall": build_tower(tiles, cx, cy, 3, 7, True)
    elif style == "castle_turrets":
        build_rect(tiles, cx, cy, 10, 10, 2)
        for dx, dy in [(-5,-5), (5,-5), (-5,5), (5,5)]: build_tower(tiles, cx+dx, cy+dy, 2, 6, False)
    elif style == "courtyard_complex":
        build_rect(tiles, cx, cy, 18, 12, 1)
        build_ring(tiles, cx, cy, 6, 4, 3)
    elif style == "facade_in_wall":
        build_rect(tiles, cx, cy, 20, 10, 1)
        build_arch(tiles, cx, cy, 6, 8, 4)
    elif style == "pillared_box": build_arch(tiles, cx, cy, 14, 8, 3)
    elif style == "perfect_cone": build_dome(tiles, cx, cy, 8, 6)
    elif style == "high_peak": build_pyramid(tiles, cx, cy, 14, 7)
    elif style == "plateau_volcano":
        build_dome(tiles, cx, cy, 9, 3)
        build_ring(tiles, cx, cy, 4, 2, 5)
    elif style == "solid_block": build_rect(tiles, cx, cy, 16, 8, 4)
    elif style == "flat_plateau": build_rect(tiles, cx, cy, 20, 10, 2)
    elif style == "scattered_peaks":
        for _ in range(6): build_pyramid(tiles, random.randint(4, 20), random.randint(3, 11), 5, 4)
    elif style == "horseshoe_curve": build_ring(tiles, cx, cy+4, 10, 8, 3) # Bottom half
    elif style == "caldera_ring": build_ring(tiles, cx, cy, 9, 6, 4)
    elif style == "wave_layers":
        for l in range(5):
            for x in range(4, 21):
                y = cy + math.sin(x*0.5 + l)*3
                add_tile(tiles, x, y, l)
    elif style == "organic_reef":
        for _ in range(12): build_dome(tiles, random.randint(5, 19), random.randint(3, 11), random.randint(2, 4), 3)
    elif style == "forest_clump": build_dome(tiles, cx, cy, 10, 2)
    elif style == "dune_waves":
        for i in range(3): build_wall(tiles, 4, 3+i*4, 20, 5+i*4, 2, True)
    elif style == "central_dome": build_dome(tiles, cx, cy, 10, 5)
    elif style == "dense_grid": build_rect(tiles, cx, cy, 12, 12, 1)
    elif style == "archipelago":
        for _ in range(8): build_dome(tiles, random.randint(4, 20), random.randint(3, 11), 3, 2)
    elif style == "vertical_monoliths":
        for x in range(5, 20, 4): build_tower(tiles, x, cy, 2, 6, False)
    elif style == "stone_circle": build_ring(tiles, cx, cy, 9, 7, 3)
    elif style == "five_tower_lotus":
        build_tower(tiles, cx, cy, 4, 6, True)
        for dx, dy in [(-6,-6), (6,-6), (-6,6), (6,6)]: build_tower(tiles, cx+dx, cy+dy, 2, 4, True)
    elif style == "rect_courtyard": build_ring(tiles, cx, cy, 10, 7, 2)
    elif style == "spired_fortress":
        build_rect(tiles, cx, cy, 12, 12, 2)
        for i in range(4): build_tower(tiles, cx + random.randint(-5,5), cy + random.randint(-5,5), 2, 6, True)
    elif style == "fairy_castle":
        build_rect(tiles, cx, cy, 8, 8, 3)
        build_tower(tiles, cx-3, cy-3, 2, 7, True)
        build_tower(tiles, cx+3, cy+3, 2, 7, True)
    elif style == "prison_island": build_rect(tiles, cx, cy, 14, 8, 3)
    elif style == "split_islands":
        build_rect(tiles, cx-6, cy, 6, 10, 2)
        build_rect(tiles, cx+6, cy, 6, 10, 2)
    elif style == "stepped_white_houses":
        for l in range(5): build_rect(tiles, cx - 6 + l*2, cy - 4 + l, 6, 4, 1)
    elif style == "walled_city":
        build_ring(tiles, cx, cy, 10, 9, 4)
        build_rect(tiles, cx, cy, 8, 8, 1)
    else: build_pyramid(tiles, cx, cy, 10, 4)
    return tiles

def build_rect(tiles, cx, cy, w, h, layers):
    for l in range(layers):
        for dx in range(-w//2, w//2 + (w%2)):
            for dy in range(-h//2, h//2 + (h%2)):
                add_tile(tiles, cx + dx, cy + dy, l)

def adjust_tiles(tiles):
    # Remove duplicates
    seen = {}
    for t in tiles:
        key = (t['x'], t['y'], t['layer'])
        seen[key] = t
    tiles = list(seen.values())
    
    # Adjust to exactly 144
    if len(tiles) > TARGET_TILES:
        # Sort by layer descending, then distance from center (to keep center/base)
        tiles.sort(key=lambda t: (-t['layer'], math.sqrt((t['x']/2-12)**2 + (t['y']/2-7)**2)), reverse=True)
        tiles = tiles[:TARGET_TILES]
    
    while len(tiles) < TARGET_TILES:
        # Add to layer 0
        cand = []
        exist = set((t['x'], t['y'], t['layer']) for t in tiles)
        for t in tiles:
            if t['layer'] == 0:
                for dx, dy in [(2,0), (-2,0), (0,2), (0,-2)]:
                    nx, ny = t['x']+dx, t['y']+dy
                    if 0 <= nx < 60 and 0 <= ny < 36 and (nx, ny, 0) not in exist:
                        cand.append({'x': nx, 'y': ny, 'layer': 0})
        if not cand:
            rx, ry = random.randint(2, 28)*2, random.randint(2, 16)*2
            if (rx, ry, 0) not in exist: cand.append({'x': rx, 'y': ry, 'layer': 0})
        
        if cand:
            nt = random.choice(cand)
            if (nt['x'], nt['y'], nt['layer']) not in exist:
                tiles.append(nt); exist.add((nt['x'], nt['y'], nt['layer']))
    
    # Sort for consistency
    tiles.sort(key=lambda t: (t['layer'], t['y'], t['x']))
    return tiles

def main():
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    for name, style in WORLD_MONUMENTS:
        raw = generate_level_tiles(style)
        final = adjust_tiles(raw)
        with open(os.path.join(OUTPUT_DIR, f"{name}.json"), 'w', encoding='utf-8') as f:
            json.dump(final, f, indent=2)
    print(f"Généré {len(WORLD_MONUMENTS)} niveaux dans {OUTPUT_DIR}")

if __name__ == "__main__": main()
