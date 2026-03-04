import pygame
import os
import sys
import json
import random
from PIL import Image
import numpy as np
import tkinter as tk
from tkinter import filedialog

# Initialisation de Tkinter (caché) pour les boîtes de dialogue
root = tk.Tk()
root.withdraw()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Base Constants
BASE_WIDTH = 1200
BASE_HEIGHT = 900
TILE_ROWS = 5
TILE_COLS = 9
IMAGE_PATH = resource_path('799px-Mahjong_eg_Shanghai.webp')

# Grille Master
GRID_W = 40 
GRID_H = 22 

# UI Constants
PANEL_WIDTH = 280
BUTTON_HEIGHT = 40

class Button:
    def __init__(self, x, y, w, h, text, color, hover_color, action):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.is_hovered = False

    def draw(self, screen, font):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2, border_radius=8)
        txt = font.render(self.text, True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

class MahjongEditor:
    def __init__(self):
        pygame.init()
        self.width, self.height = BASE_WIDTH, BASE_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        pygame.display.set_caption("Mahjong Level Editor Pro")
        self.clock = pygame.time.Clock()
        
        self.tile_images_hd = []
        self.tile_variants = []
        self.load_tiles_hd()
        
        self.tiles = [] 
        self.undo_stack = []
        self.current_layer = 0
        self.level_name = "new_level"
        self.show_help = False
        
        self.layout_w_tiles, self.layout_h_tiles = GRID_W / 2.0, GRID_H / 2.0
        self.recompute_scaling()
        
        self.font_ui = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 24, bold=True)
        
        self.save_msg_time = 0
        self.save_msg = ""
        self.upper_layers_mode = "hidden"
        self.last_dir = resource_path("Levels")
        self.load_config()
        self.init_ui()

    def load_config(self):
        config_path = "editor_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    if "last_dir" in data and os.path.exists(data["last_dir"]):
                        self.last_dir = data["last_dir"]
            except: pass

    def save_config(self):
        config_path = "editor_config.json"
        try:
            data = {"last_dir": self.last_dir}
            with open(config_path, "w") as f:
                json.dump(data, f, indent=4)
        except: pass

    def load_tiles_hd(self):
        img = Image.open(IMAGE_PATH).convert('RGBA')
        w, h = img.size
        tw, th = w / TILE_COLS, h / TILE_ROWS
        self.all_tiles = []
        for r in range(TILE_ROWS):
            for c in range(TILE_COLS):
                tile_img = img.crop((int(c*tw), int(r*th), int((c+1)*tw), int((r+1)*th)))
                py_t = pygame.image.fromstring(tile_img.tobytes(), tile_img.size, tile_img.mode)
                self.all_tiles.append(py_t.convert_alpha())
        self.placeholder_tile = self.all_tiles[0]

    def save_state(self):
        # On sauvegarde une copie profonde de la liste des tuiles pour l'undo
        self.undo_stack.append([t.copy() for t in self.tiles])
        if len(self.undo_stack) > 50: # Limite à 50 étapes
            self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            self.tiles = self.undo_stack.pop()
            self.save_msg = "Undo"
            self.save_msg_time = pygame.time.get_ticks() + 1000

    def init_ui(self):
        self.buttons = []
        x, y = 20, 220
        bw = PANEL_WIDTH - 40
        
        self.buttons.append(Button(x, y, bw, BUTTON_HEIGHT, "New Level (N)", (200, 50, 50), (250, 70, 70), lambda: self.new_level()))
        y += 50
        self.buttons.append(Button(x, y, bw, BUTTON_HEIGHT, "Undo (Ctrl+Z)", (100, 100, 150), (120, 120, 200), lambda: self.undo()))
        y += 50
        self.buttons.append(Button(x, y, bw, BUTTON_HEIGHT, "Open Level...", (50, 100, 200), (70, 120, 250), lambda: self.load_level()))
        y += 50
        self.buttons.append(Button(x, y, bw, BUTTON_HEIGHT, "Save Level...", (50, 150, 50), (70, 200, 70), lambda: self.save_level()))
        y += 50
        
        # Croix directionnelle
        self.screen.blit(self.font_ui.render("Move Level:", True, (150, 150, 150)), (20, y + 5))
        y += 30
        cx = x + bw // 2
        sw = 40 # Size of small arrow buttons
        self.buttons.append(Button(cx - sw//2, y, sw, sw, "▲", (80, 80, 80), (120, 120, 120), lambda: self.move_all_tiles(0, -1)))
        y += 45
        self.buttons.append(Button(cx - sw - 5, y, sw, sw, "◄", (80, 80, 80), (120, 120, 120), lambda: self.move_all_tiles(-1, 0)))
        self.buttons.append(Button(cx + 5, y, sw, sw, "►", (80, 80, 80), (120, 120, 120), lambda: self.move_all_tiles(1, 0)))
        y += 45
        self.buttons.append(Button(cx - sw//2, y, sw, sw, "▼", (80, 80, 80), (120, 120, 120), lambda: self.move_all_tiles(0, 1)))
        
        y += 60
        self.buttons.append(Button(x, y, bw, BUTTON_HEIGHT, "Center (C)", (150, 100, 50), (180, 130, 70), lambda: self.center_tiles()))
        y += 50
        self.buttons.append(Button(x, y, bw, BUTTON_HEIGHT, "Help (H)", (100, 50, 150), (130, 70, 180), lambda: self.toggle_help()))
        y += 50
        self.buttons.append(Button(x, y, bw, BUTTON_HEIGHT, "Upper: Hidden", (80, 80, 80), (100, 100, 100), lambda: self.toggle_upper_visibility()))
        
        self.refresh_levels()

    def toggle_upper_visibility(self):
        if self.upper_layers_mode == "hidden":
            self.upper_layers_mode = "transparent"
        else:
            self.upper_layers_mode = "hidden"
        
        # Update button text
        for btn in self.buttons:
            if btn.text.startswith("Upper:"):
                btn.text = f"Upper: {self.upper_layers_mode.capitalize()}"

    def refresh_levels(self):
        self.level_files = []
        levels_dir = resource_path("Levels")
        if os.path.exists(levels_dir):
            for f in sorted(os.listdir(levels_dir)):
                if f.lower().endswith(".json"):
                    self.level_files.append(f[:-5])
        self.level_scroll = 0

    def toggle_help(self):
        self.show_help = not self.show_help

    def new_level(self):
        self.save_state()
        self.tiles = []
        self.current_layer = 0
        self.save_msg = "Board Cleared (Layer 0)"
        self.save_msg_time = pygame.time.get_ticks() + 2000

    def load_level_by_name(self, name):
        levels_dir = resource_path("Levels")
        path = os.path.join(levels_dir, f"{name}.json")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.tiles = json.load(f)
            self.level_name = name
            self.save_msg = f"Loaded: {name}"
            self.save_msg_time = pygame.time.get_ticks() + 2000
            self.undo_stack = []
        except Exception as e:
            self.save_msg = f"Error: {e}"
            self.save_msg_time = pygame.time.get_ticks() + 3000

    def recompute_scaling(self):
        self.layout_w_tiles = GRID_W / 2.0
        self.layout_h_tiles = GRID_H / 2.0
        available_w, available_h = self.width - PANEL_WIDTH - 40, self.height - 40
        unit_w = available_w / self.layout_w_tiles
        unit_h = available_h / self.layout_h_tiles
        self.tw = int(min(unit_w - 2, (unit_h - 2) * 0.75))
        self.th = int(self.tw * 1.33)
        self.depth_off = max(2, int((self.tw // 10 + 1) * 1.2))
        
        # Scale toutes les tuiles pour le rendu aléatoire
        ivory_color = (242, 228, 185)
        self.scaled_tiles = []
        for img_hd in self.all_tiles:
            scaled = pygame.transform.smoothscale(img_hd, (self.tw, self.th))
            it_surf = pygame.Surface((self.tw, self.th)); it_surf.fill(ivory_color)
            # Add a subtle darkening on edges for aging
            pygame.draw.rect(it_surf, (220, 205, 170), (0, 0, self.tw, self.th), 3)
            scaled.blit(it_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            pygame.draw.rect(scaled, (198, 180, 145), (0, 0, self.tw, self.th), 2, border_radius=int(self.tw/12))
            self.scaled_tiles.append(scaled)
        self.scaled_tile = self.scaled_tiles[0]
        self.transparent_tile = self.scaled_tile.copy()
        self.transparent_tile.set_alpha(100)

    def draw(self):
        self.screen.fill((40, 40, 40))
        
        mx, my = self.get_board_origin()
        
        # Alignement de la grille sur le calque actuel (effet 3D)
        gx_off = mx - self.current_layer * self.depth_off
        gy_off = my - self.current_layer * self.depth_off
        
        # Draw the 40x20 grid cells
        cell_w = (self.tw + 2) / 2.0
        cell_h = (self.th + 2) / 2.0
        for gx in range(GRID_W + 1):
            color = (60, 60, 60) if gx % 2 != 0 else (80, 80, 80)
            width = 3 if gx == GRID_W // 2 else 1
            pygame.draw.line(self.screen, color, (gx_off + gx * cell_w, gy_off), (gx_off + gx * cell_w, gy_off + GRID_H * cell_h), width)
        for gy in range(GRID_H + 1):
            color = (60, 60, 60) if gy % 2 != 0 else (80, 80, 80)
            width = 3 if gy == GRID_H // 2 else 1
            pygame.draw.line(self.screen, color, (gx_off, gy_off + gy * cell_h), (gx_off + GRID_W * cell_w, gy_off + gy * cell_h), width)

        # Sort tiles for correct 3D rendering
        if self.upper_layers_mode == "hidden":
            visible_tiles = [t for t in self.tiles if t['layer'] <= self.current_layer]
        else:
            visible_tiles = self.tiles
            
        sorted_tiles = sorted(visible_tiles, key=lambda t: (t['layer'], t['x'] + t['y']))
        
        for t in sorted_tiles:
            x = mx + (t['x'] / 2.0) * (self.tw + 2) - t['layer'] * self.depth_off
            y = my + (t['y'] / 2.0) * (self.th + 2) - t['layer'] * self.depth_off
            rect = pygame.Rect(x, y, self.tw, self.th)
            
            is_upper = t['layer'] > self.current_layer
            
            if not is_upper:
                for j in range(self.depth_off, 0, -1):
                    fac = (self.depth_off - j) / (self.depth_off - 1) if self.depth_off > 1 else 1.0
                    v = int(100 + (160 - 100) * (fac**3))
                    color = (75, 50, 25) if j >= self.depth_off - 1 else (v, int(v*0.96), int(v*0.85))
                    pygame.draw.rect(self.screen, color, rect.move(j, j), border_radius=5)
            
            if is_upper:
                self.screen.blit(self.transparent_tile, (x, y))
            else:
                # Utiliser uniquement la première tuile pour un rendu simple
                self.screen.blit(self.scaled_tiles[0], (x, y))
            
            if t['layer'] == self.current_layer:
                pygame.draw.rect(self.screen, (255, 255, 0), rect, 2, border_radius=5)
            elif t['layer'] < self.current_layer:
                # Dim layers below
                s = pygame.Surface((self.tw, self.th), pygame.SRCALPHA)
                s.fill((0, 0, 0, 80)) 
                self.screen.blit(s, (x, y))

        # Draw UI Sidebar
        ui_panel = pygame.Rect(0, 0, PANEL_WIDTH, self.height)
        pygame.draw.rect(self.screen, (30, 30, 30), ui_panel)
        pygame.draw.line(self.screen, (100, 100, 100), (PANEL_WIDTH, 0), (PANEL_WIDTH, self.height), 2)
        
        # Info
        self.screen.blit(self.font_large.render(f"Layer: {self.current_layer}", True, (255, 255, 255)), (20, 20))
        
        tile_count = len(self.tiles)
        count_color = (200, 200, 200) if tile_count % 2 == 0 else (255, 100, 100)
        self.screen.blit(self.font_ui.render(f"Tiles: {tile_count}", True, count_color), (20, 50))
        if tile_count % 2 != 0:
            self.screen.blit(self.font_ui.render("(Must be even!)", True, (255, 100, 100)), (110, 50))
        
        self.screen.blit(self.font_ui.render(f"Name: {self.level_name}", True, (200, 200, 200)), (20, 80))
        
        mpos = pygame.mouse.get_pos()
        hx, hy = self.screen_to_half_tile(mpos)
        self.screen.blit(self.font_ui.render(f"Cell: {hx}, {hy}", True, (100, 255, 100)), (20, 110))

        # Layer Buttons
        self.screen.blit(self.font_ui.render("Layer Selection:", True, (150, 150, 150)), (20, 145))
        self.layer_rects = []
        for l in range(6):
            lx = 20 + l * 42
            l_rect = pygame.Rect(lx, 170, 35, 30)
            self.layer_rects.append((l_rect, l))
            l_color = (100, 255, 100) if self.current_layer == l else (60, 60, 60)
            pygame.draw.rect(self.screen, l_color, l_rect, border_radius=5)
            pygame.draw.rect(self.screen, (200, 200, 200), l_rect, 1, border_radius=5)
            l_txt = self.font_ui.render(str(l), True, (0, 0, 0) if self.current_layer == l else (255, 255, 255))
            self.screen.blit(l_txt, l_txt.get_rect(center=l_rect.center))

        # Draw Buttons
        for btn in self.buttons:
            btn.check_hover(mpos)
            btn.draw(self.screen, self.font_ui)

        if self.show_help:
            ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA); ov.fill((0, 0, 0, 230)); self.screen.blit(ov, (0, 0))
            help_lines = ["MAHJONG EDITOR HELP", "", "LEFT CLICK: Place tile", "RIGHT CLICK: Remove tile", 
                          "SCROLL / 0-5 / UP-DOWN: Change layer", "S: Save level", "O: Load level", "N: Clear board", 
                          "T: Set Name", "C: Center tiles", "V: Toggle Upper Vis.", "H: Toggle Help", "", "Note: Tiles MUST be an even number."]
            for i, line in enumerate(help_lines):
                self.screen.blit(self.font_large.render(line, True, (255, 255, 255)), (self.width//2 - 200, 150 + i*35))
            pygame.display.flip(); return

        if pygame.time.get_ticks() < self.save_msg_time:
            msg_surf = self.font_ui.render(self.save_msg, True, (0, 255, 0))
            self.screen.blit(msg_surf, (PANEL_WIDTH + 20, 20))

        # Mouse placeholder
        if mpos[0] > PANEL_WIDTH:
            hx, hy = self.screen_to_half_tile(mpos)
            mx, my = self.get_board_origin()
            px = mx + (hx / 2.0) * (self.tw + 2) - self.current_layer * self.depth_off
            py = my + (hy / 2.0) * (self.th + 2) - self.current_layer * self.depth_off
            s = pygame.Surface((self.tw, self.th), pygame.SRCALPHA); s.fill((0, 255, 0, 100)); self.screen.blit(s, (px, py))

        pygame.display.flip()

    def get_board_origin(self):
        board_area_w = self.width - PANEL_WIDTH
        mx = PANEL_WIDTH + (board_area_w - self.layout_w_tiles * (self.tw + 2)) // 2
        my = (self.height - self.layout_h_tiles * (self.th + 2)) // 2
        return mx, my

    def screen_to_half_tile(self, pos):
        mx, my = self.get_board_origin()
        hx = round((pos[0] - mx + self.current_layer * self.depth_off) / ((self.tw + 2) / 2.0))
        hy = round((pos[1] - my + self.current_layer * self.depth_off) / ((self.th + 2) / 2.0))
        return max(0, min(GRID_W - 2, hx)), max(0, min(GRID_H - 2, hy))

    def add_tile(self, pos):
        hx, hy = self.screen_to_half_tile(pos)
        # Check if already exists at this exact spot
        for t in self.tiles:
            if t['x'] == hx and t['y'] == hy and t['layer'] == self.current_layer:
                return
        self.save_state()
        self.tiles.append({'x': hx, 'y': hy, 'layer': self.current_layer})

    def remove_tile(self, pos):
        # Find tile at pos in current layer first, then others
        hx, hy = self.screen_to_half_tile(pos)
        for t in self.tiles:
            if t['x'] == hx and t['y'] == hy and t['layer'] == self.current_layer:
                self.save_state()
                self.tiles.remove(t)
                return

    def move_all_tiles(self, dx, dy):
        if not self.tiles: return
        self.save_state()
        for t in self.tiles:
            t['x'] = max(0, min(GRID_W - 2, t['x'] + dx))
            t['y'] = max(0, min(GRID_H - 2, t['y'] + dy))
        self.save_msg = f"Moved {'X' if dx else 'Y'} by {dx if dx else dy}"
        self.save_msg_time = pygame.time.get_ticks() + 1000

    def save_level(self):
        if not self.tiles: return
        initial_dir = self.last_dir
        file_path = filedialog.asksaveasfilename(
            initialdir=initial_dir,
            initialfile=f"{self.level_name}.json",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if not file_path: return
        
        self.last_dir = os.path.dirname(file_path)
        self.save_config()
        self.level_name = os.path.basename(file_path).replace(".json", "")
        self.tiles.sort(key=lambda t: (t['layer'], t['y'], t['x']))
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.tiles, f, indent=2)
            self.save_msg = f"Saved: {self.level_name}"
            self.save_msg_time = pygame.time.get_ticks() + 2000
            self.refresh_levels()
        except Exception as e:
            self.save_msg = f"Error: {e}"
            self.save_msg_time = pygame.time.get_ticks() + 3000

    def load_level(self):
        initial_dir = self.last_dir
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            filetypes=[("JSON files", "*.json")]
        )
        if not file_path: return
        
        self.last_dir = os.path.dirname(file_path)
        self.save_config()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.tiles = json.load(f)
            self.level_name = os.path.basename(file_path).replace(".json", "")
            self.save_msg = f"Loaded: {self.level_name}"
            self.save_msg_time = pygame.time.get_ticks() + 2000
            self.undo_stack = [] # Reset undo on load
        except Exception as e:
            self.save_msg = f"Error: {e}"
            self.save_msg_time = pygame.time.get_ticks() + 3000

    def input_name(self):
        # Very basic input for name
        done = False
        new_name = self.level_name
        while not done:
            self.screen.fill((50, 50, 50))
            txt = self.font_large.render(f"Enter Level Name: {new_name}_", True, (255, 255, 255))
            self.screen.blit(txt, (self.width // 2 - txt.get_width() // 2, self.height // 2))
            pygame.display.flip()
            
            for e in pygame.event.get():
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_RETURN:
                        done = True
                    elif e.key == pygame.K_BACKSPACE:
                        new_name = new_name[:-1]
                    else:
                        if e.unicode.isalnum() or e.unicode in " _-":
                            new_name += e.unicode
                elif e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
        self.level_name = new_name

    def center_tiles(self):
        if not self.tiles: return
        self.save_state()
        min_x = min(t['x'] for t in self.tiles)
        max_x = max(t['x'] for t in self.tiles)
        min_y = min(t['y'] for t in self.tiles)
        max_y = max(t['y'] for t in self.tiles)
        
        # Grid center is (20, 10) in half-tile units. 
        # Bounding box center should move to grid center.
        target_cx, target_cy = GRID_W // 2 - 1, GRID_H // 2 - 1
        current_cx = (min_x + max_x) // 2
        current_cy = (min_y + max_y) // 2
        
        dx = target_cx - current_cx
        dy = target_cy - current_cy
        
        for t in self.tiles:
            t['x'] = max(0, min(GRID_W - 2, t['x'] + dx))
            t['y'] = max(0, min(GRID_H - 2, t['y'] + dy))
        
        self.save_msg = "Centered on 40x20 grid"
        self.save_msg_time = pygame.time.get_ticks() + 1000

    def get_board_origin(self):
        board_area_w = self.width - PANEL_WIDTH
        mx = PANEL_WIDTH + (board_area_w - self.layout_w_tiles * (self.tw + 2)) // 2
        my = (self.height - self.layout_h_tiles * (self.th + 2)) // 2
        return mx, my

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.VIDEORESIZE: 
                    self.width, self.height = e.w, e.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.recompute_scaling(); self.init_ui()
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if e.button == 1:
                        # Check buttons
                        btn_clicked = False
                        for btn in self.buttons:
                            if btn.rect.collidepoint(e.pos): btn.action(); btn_clicked = True; break
                        if not btn_clicked:
                            # Check layer select
                            for r, l in getattr(self, "layer_rects", []):
                                if r.collidepoint(e.pos): self.current_layer = l; btn_clicked = True; break
                        
                        if not btn_clicked and e.pos[0] > PANEL_WIDTH:
                            self.add_tile(e.pos)
                    elif e.button == 3:
                        if e.pos[0] > PANEL_WIDTH: self.remove_tile(e.pos)
                    elif e.button == 4: # Scroll Up
                        self.current_layer = min(5, self.current_layer + 1)
                    elif e.button == 5: # Scroll Down
                        self.current_layer = max(0, self.current_layer - 1)
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_z and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        self.undo()
                    elif e.key == pygame.K_s: self.save_level()
                    elif e.key == pygame.K_o: self.load_level()
                    elif e.key == pygame.K_n: self.new_level()
                    elif e.key == pygame.K_t: self.input_name()
                    elif e.key == pygame.K_c: self.center_tiles()
                    elif e.key == pygame.K_v: self.toggle_upper_visibility()
                    elif e.key == pygame.K_h: self.toggle_help()
                    elif e.key == pygame.K_UP: self.move_all_tiles(0, -1)
                    elif e.key == pygame.K_DOWN: self.move_all_tiles(0, 1)
                    elif e.key == pygame.K_LEFT: self.move_all_tiles(-1, 0)
                    elif e.key == pygame.K_RIGHT: self.move_all_tiles(1, 0)
                    elif e.key == pygame.K_PAGEUP: self.current_layer = min(5, self.current_layer + 1)
                    elif e.key == pygame.K_PAGEDOWN: self.current_layer = max(0, self.current_layer - 1)
                    elif e.key in [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                        self.current_layer = int(e.unicode)
            self.draw(); self.clock.tick(60)

if __name__ == "__main__":
    MahjongEditor().run()
