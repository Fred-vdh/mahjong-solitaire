import pygame
import random
import os
import sys
import json
import numpy as np
import unicodedata
from PIL import Image
import ctypes
from ctypes import wintypes

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
GRID_W = 20
GRID_H = 12

class MahjongGame:
    def __init__(self):
        pygame.init()
        self.load_stats()
        self.width, self.height = self.window_size
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        hwnd = pygame.display.get_wm_info()["window"]

        if getattr(self, "is_maximized", False):
            ctypes.windll.user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE
        elif hasattr(self, "window_pos"):
            x, y = self.window_pos
            test_rect = wintypes.RECT(x, y, x + self.width, y + self.height)
            hMonitor = ctypes.windll.user32.MonitorFromRect(ctypes.pointer(test_rect), 0)
            if hMonitor != 0:
                ctypes.windll.user32.SetWindowPos(hwnd, 0, x, y, 0, 0, 0x0001)
        
        pygame.display.set_caption("Mahjong-solitaire 1.0")
        self.clock = pygame.time.Clock()
        
        self.tile_images_hd = []
        self.tile_variants = []
        self.load_tiles_hd()
        self.load_backgrounds()
        
        self.animating_tiles, self.matched_tiles, self.undo_animating_tiles = [], [], []
        self.show_history, self.history_anim_state, self.history_anim_progress = False, 'idle', 0.0
        self.shuffle_needed, self.shuffle_anim_state, self.shuffle_tiles_data = False, 'idle', []
        self.shuffle_count = 0
        self.total_shuffles = 0
        self.wins_without_shuffle = 0
        self.wins_with_one_shuffle = 0
        self.level_anim_state, self.level_anim_progress = 'in', 0.0
        self.next_layout_id = None
        self.prev_bg, self.bg_transition_progress = None, 1.0
        self.win_pressed_btn = None
        self.next_level_to_load = None
        self.open_stats_after_win = False
        self.layout, self.sorted_layout = [], []
        self.flying_scores = []
        
        self.victory_anim_state = 'idle'
        self.victory_tiles = []
        self.victory_anim_start_time = 0
        self.victory_anim_idx = 11 # Forced to Fontaine for now
        self.queued_debug_anim = None
        
        self.win_ui_progress = 0.0
        self.win_ui_state = 'closed'
        self.shuffle_ui_progress = 0.0
        self.shuffle_ui_state = 'closed'
        self.shuffle_confirmed = False
        self.shuffle_start_time = 0
        self.shuffle_duration = 800
        
        self.stats_ui_progress = 0.0
        self.stats_ui_state = 'closed'
        self.stats_scroll_y = 0
        self.pending_level_idx = None
        self.level_stats = {}
        self.level_previews = {}
        self.stats_sort_col = None
        self.stats_sort_reverse = False
        self.stats_display_indices = []
        self.stats_dragging_scrollbar = False
        
        self.options_ui_progress = 0.0
        self.options_ui_state = 'closed'
        self.show_gray_tiles = True
        self.show_win_count = True
        self.show_best_shuffles = True
        self.auto_hint = True
        self.music_volume = 0.5
        self.sfx_volume = 0.5
        self.music_files = []
        self.current_music_idx = -1
        self.music_dragging_slider = False
        self.sfx_dragging_slider = False
        self.pressed_button = None
        self.is_manual_paused = False
        self.click_sound = None
        self.MUSIC_END = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.MUSIC_END)
        
        self.load_stats()
        self.load_levels()
        self.load_music()
        self.load_sfx()
        self.generate_level_previews()
        
        self.layout_w_tiles, self.layout_h_tiles = GRID_W, GRID_H
        self.recompute_scaling()
        self.current_bg = None
        self.start_ticks = pygame.time.get_ticks()
        self.pause_start_ticks = 0
        self.level_pool = []
        self.init_game(None)

    def load_stats(self):
        self.global_games_played = 0
        self.total_shuffles = 0
        self.wins_without_shuffle = 0
        self.wins_with_one_shuffle = 0
        self.level_stats = {}
        self.recent_levels = []
        self.window_size = (BASE_WIDTH, BASE_HEIGHT)
        self.is_maximized = False
        stats_path = "mahjong_stats.json"
        if os.path.exists(stats_path):
            try:
                with open(stats_path, "r") as f:
                    data = json.load(f)
                    self.global_games_played = data.get("games_played", 0)
                    self.total_shuffles = data.get("total_shuffles", 0)
                    self.wins_without_shuffle = data.get("wins_without_shuffle", 0)
                    self.wins_with_one_shuffle = data.get("wins_with_one_shuffle", 0)
                    self.level_stats = data.get("level_stats", {})
                    self.recent_levels = data.get("recent_levels", [])
                    if "window_width" in data and "window_height" in data:
                        self.window_size = (data["window_width"], data["window_height"])
                    if "window_x" in data and "window_y" in data:
                        self.window_pos = (data["window_x"], data["window_y"])
                    self.is_maximized = data.get("maximized", False)
                    self.music_volume = data.get("music_volume", 0.5)
                    self.sfx_volume = data.get("sfx_volume", 0.5)
                    self.show_gray_tiles = data.get("show_gray_tiles", True)
                    self.show_win_count = data.get("show_win_count", True)
                    self.show_best_shuffles = data.get("show_best_shuffles", True)
                    self.auto_hint = data.get("auto_hint", True)
            except: pass

    def save_stats(self):
        stats_path = "mahjong_stats.json"
        try:
            hwnd = pygame.display.get_wm_info()["window"]
            is_maximized = ctypes.windll.user32.IsZoomed(hwnd)
            rect = wintypes.RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.pointer(rect))
            data = {
                "games_played": self.global_games_played,
                "total_shuffles": self.total_shuffles,
                "wins_without_shuffle": self.wins_without_shuffle,
                "wins_with_one_shuffle": self.wins_with_one_shuffle,
                "level_stats": self.level_stats,
                "recent_levels": self.recent_levels,
                "window_width": self.width,
                "window_height": self.height,
                "window_x": rect.left,
                "window_y": rect.top,
                "maximized": bool(is_maximized),
                "music_volume": self.music_volume,
                "sfx_volume": self.sfx_volume,
                "show_gray_tiles": self.show_gray_tiles,
                "show_win_count": self.show_win_count,
                "show_best_shuffles": self.show_best_shuffles,
                "auto_hint": self.auto_hint
            }
            with open(stats_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception: pass

    def load_music(self):
        music_dir = resource_path("Musiques")
        if os.path.exists(music_dir):
            self.music_files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.lower().endswith(('.mp3', '.ogg', '.wav'))]
            random.shuffle(self.music_files)
            if self.music_files and self.music_volume > 0:
                self.play_next_music()

    def play_next_music(self):
        if not self.music_files or self.music_volume <= 0: return
        self.current_music_idx = (self.current_music_idx + 1) % len(self.music_files)
        try:
            pygame.mixer.music.load(self.music_files[self.current_music_idx])
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(fade_ms=2000)
        except: pass

    def load_sfx(self):
        sfx_dir = resource_path("effets")
        if os.path.exists(sfx_dir):
            sfx_files = [f for f in os.listdir(sfx_dir) if f.lower().endswith(('.mp3', '.ogg', '.wav'))]
            if sfx_files:
                try:
                    self.click_sound = pygame.mixer.Sound(os.path.join(sfx_dir, sfx_files[0]))
                    self.click_sound.set_volume(self.sfx_volume)
                except: pass

    def play_click_sfx(self):
        if self.click_sound:
            self.click_sound.set_volume(self.sfx_volume)
            self.click_sound.play()

    def normalize_string(self, s):
        if not s: return ""
        nfkd_form = unicodedata.normalize('NFKD', s)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower()

    def load_levels(self):
        self.layout_names = []
        self.level_files = []
        levels_dir = resource_path("Levels")
        if os.path.exists(levels_dir):
            for f in sorted(os.listdir(levels_dir), key=lambda x: self.normalize_string(x)):
                if f.lower().endswith(".json"):
                    self.layout_names.append(f[:-5])
                    self.level_files.append(os.path.join(levels_dir, f))
        if not self.layout_names:
            self.layout_names = ["Default"]
            self.level_files = [None]
        self.stats_display_indices = list(range(len(self.layout_names)))

    def generate_level_previews(self):
        for i, name in enumerate(self.layout_names):
            path = self.level_files[i]
            if not path: continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not data: continue
                min_x = min(d['x'] for d in data); max_x = max(d['x'] for d in data)
                min_y = min(d['y'] for d in data); max_y = max(d['y'] for d in data)
                w_units = max_x - min_x + 2; h_units = max_y - min_y + 2
                grid_w, grid_h = 40, 20
                target_h = 80
                target_w = int(target_h * (grid_w / (grid_h * 1.33)))
                surf = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
                pygame.draw.rect(surf, (40, 40, 45), (0, 0, target_w, target_h), border_radius=10)
                ref_w, ref_h = max(grid_w, w_units), max(grid_h, h_units)
                scale = (target_h - 10) / (ref_h * 1.33)
                if ref_w * scale > target_w - 10: scale = (target_w - 10) / ref_w
                ox = (target_w - w_units * scale) / 2; oy = (target_h - h_units * 1.33 * scale) / 2
                data.sort(key=lambda d: d['layer'])
                tw = max(1, int(2 * scale)); th = max(1, int(2 * 1.33 * scale))
                ivory_color = (242, 228, 185)
                scaled_pool = []
                for img in self.tile_images_hd:
                    s = pygame.transform.smoothscale(img, (tw, th))
                    it_surf = pygame.Surface((tw, th)); it_surf.fill(ivory_color)
                    # Add a subtle darkening on edges for aging (even for previews)
                    if tw > 4: pygame.draw.rect(it_surf, (220, 205, 170), (0, 0, tw, th), 1)
                    s.blit(it_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                    scaled_pool.append(s)
                for d in data:
                    tx = ox + (d['x'] - min_x) * scale; ty = oy + (d['y'] - min_y) * 1.33 * scale
                    pygame.draw.rect(surf, (0, 0, 0, 150), (tx + 1, ty + 1, tw, th), border_radius=2)
                    surf.blit(random.choice(scaled_pool), (tx, ty))
                self.level_previews[name] = surf
            except: pass

    def load_backgrounds(self):
        self.bg_images = []
        bg_dir = resource_path("Images")
        if os.path.exists(bg_dir):
            for f in os.listdir(bg_dir):
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    try:
                        img = pygame.image.load(os.path.join(bg_dir, f)).convert()
                        self.bg_images.append(img)
                    except: pass
        self.current_bg = None

    def load_tiles_hd(self):
        img = Image.open(IMAGE_PATH).convert('RGBA')
        w, h = img.size; tw, th = w / TILE_COLS, h / TILE_ROWS
        for r in range(TILE_ROWS):
            for c in range(TILE_COLS):
                tile_img = img.crop((int(c*tw), int(r*th), int((c+1)*tw), int((r+1)*th)))
                stat = np.array(tile_img); avg = stat.mean(axis=(0, 1))
                if avg[0] > 150 and avg[1] < 100 and avg[2] < 100: continue
                py_t = pygame.image.fromstring(tile_img.tobytes(), tile_img.size, tile_img.mode)
                self.tile_images_hd.append(py_t.convert_alpha())

    def scale_background(self, img):
        if not img: return None
        iw, ih = img.get_size(); screen_ar = self.width / self.height; img_ar = iw / ih
        if screen_ar > img_ar:
            new_w = self.width; new_h = int(self.width / img_ar)
        else:
            new_h = self.height; new_w = int(self.height * img_ar)
        scaled = pygame.transform.smoothscale(img, (new_w, new_h))
        surf = pygame.Surface((self.width, self.height))
        ox = (self.width - new_w) // 2; oy = (self.height - new_h) // 2
        surf.blit(scaled, (ox, oy)); return surf

    def recompute_scaling(self):
        f_ui = pygame.font.SysFont("Arial", 24, bold=True)
        text_h = f_ui.get_height()
        margin_x = self.width * 0.05
        top_margin = 60 + text_h
        bottom_margin = 110
        available_w = self.width - 2 * margin_x
        available_h = self.height - top_margin - bottom_margin
        std_unit_w = (available_w / GRID_W) * 1.5; std_unit_h = (available_h / GRID_H) * 1.5
        self.std_tw = int(min(std_unit_w - 2, (std_unit_h - 2) * 0.75))
        self.std_th = int(self.std_tw * 1.33)
        unit_w = available_w / max(1, self.layout_w_tiles); unit_h = available_h / max(1, self.layout_h_tiles)
        self.tw = int(min(unit_w - 2, (unit_h - 2) * 0.75)); self.th = int(self.tw * 1.33)
        self.board_offset_x = margin_x + (available_w - self.layout_w_tiles * (self.tw + 2)) // 2
        self.board_offset_y = top_margin + (available_h - self.layout_h_tiles * (self.th + 2)) // 2
        self.depth_off = max(2, int((self.tw // 10 + 1) * 1.2))
        self.tile_variants = []
        self.std_tile_variants = []
        
        # Create a truly blank tile face for pause mode
        self.blank_tile = pygame.Surface((self.tw, self.th), pygame.SRCALPHA)
        # Main face color (Aged Ivory)
        face_color = (242, 228, 185)
        rad = int(self.tw/12)
        pygame.draw.rect(self.blank_tile, face_color, (0, 0, self.tw, self.th), border_radius=rad)
        # Subtle aged inner border for a weathered look
        pygame.draw.rect(self.blank_tile, (198, 180, 145), (0, 0, self.tw, self.th), 2, border_radius=rad)
        
        ivory_color = (242, 228, 185)
        for i, img_hd in enumerate(self.tile_images_hd):
            scaled = pygame.transform.smoothscale(img_hd, (self.tw, self.th))
            # Apply ivory tint to normal tiles
            it_surf = pygame.Surface((self.tw, self.th)); it_surf.fill(ivory_color)
            # Add a subtle darkening on edges for aging
            pygame.draw.rect(it_surf, (220, 205, 170), (0, 0, self.tw, self.th), 3)
            scaled.blit(it_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            
            mask = pygame.Surface((self.tw, self.th), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255), (0,0,self.tw,self.th), border_radius=int(self.tw/12))
            base = pygame.Surface((self.tw, self.th), pygame.SRCALPHA); base.blit(scaled, (0, 0)); base.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            filtered = base.copy(); nt = len(self.tile_images_hd)
            if nt - 8 <= i < nt - 4:
                sf = pygame.Surface((self.tw, self.th), pygame.SRCALPHA); sf.fill((255, 165, 0, 45)); filtered.blit(sf, (0, 0))
            elif i >= nt - 4:
                ff = pygame.Surface((self.tw, self.th), pygame.SRCALPHA); ff.fill((0, 255, 0, 35)); filtered.blit(ff, (0, 0))
            self.tile_variants.append({'normal': base, 'filtered': filtered})
            
            std_scaled = pygame.transform.smoothscale(img_hd, (self.std_tw, self.std_th))
            # Apply ivory tint to standard (victory) tiles
            it_std = pygame.Surface((self.std_tw, self.std_th)); it_std.fill(ivory_color)
            # Add a subtle darkening on edges for aging
            pygame.draw.rect(it_std, (220, 205, 170), (0, 0, self.std_tw, self.std_th), 3)
            std_scaled.blit(it_std, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            
            std_mask = pygame.Surface((self.std_tw, self.std_th), pygame.SRCALPHA)
            pygame.draw.rect(std_mask, (255, 255, 255), (0,0,self.std_tw,self.std_th), border_radius=int(self.std_tw/12))
            std_base = pygame.Surface((self.std_tw, self.std_th), pygame.SRCALPHA); std_base.blit(std_scaled, (0, 0)); std_base.blit(std_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            std_filtered = std_base.copy()
            if nt - 8 <= i < nt - 4:
                sf = pygame.Surface((self.std_tw, self.std_th), pygame.SRCALPHA); sf.fill((255, 165, 0, 45)); std_filtered.blit(sf, (0, 0))
            elif i >= nt - 4:
                ff = pygame.Surface((self.std_tw, self.std_th), pygame.SRCALPHA); ff.fill((0, 255, 0, 35)); std_filtered.blit(ff, (0, 0))
            self.std_tile_variants.append(std_filtered)
        if self.current_bg: self.scaled_bg = self.scale_background(self.current_bg)
        if self.prev_bg: self.scaled_prev_bg = self.scale_background(self.prev_bg)
        self.shadow_surf = pygame.Surface((self.tw, self.th), pygame.SRCALPHA); pygame.draw.rect(self.shadow_surf, (0, 0, 0, 50), (0,0,self.tw,self.th), border_radius=5)
        self.gray_overlay = pygame.Surface((self.tw, self.th)); self.gray_overlay.fill((0, 0, 0))

    def adjust_times_after_pause(self, paused_duration):
        self.start_ticks += paused_duration
        self.last_move_time += paused_duration
        self.last_match_time += paused_duration
        if getattr(self, 'shuffle_start_time', 0) > 0: self.shuffle_start_time += paused_duration
        if getattr(self, 'victory_anim_start_time', 0) > 0: self.victory_anim_start_time += paused_duration

    def init_game(self, l_id=None):
        if l_id is None:
            counts = []
            for i, name in enumerate(self.layout_names):
                count = self.level_stats.get(name, {}).get("times_completed", 0)
                counts.append((i, count))
            counts.sort(key=lambda x: x[1]); min_count = counts[0][1]
            candidates = [idx for idx, c in counts if c <= min_count + 1 and self.layout_names[idx] not in self.recent_levels]
            if not candidates: candidates = [idx for idx, c in counts if self.layout_names[idx] not in self.recent_levels]
            if not candidates: l_id = random.randint(0, len(self.layout_names) - 1)
            else: l_id = random.choice(candidates)
        self.current_l_id = l_id; lname = self.layout_names[l_id]
        if lname in self.recent_levels: self.recent_levels.remove(lname)
        self.recent_levels.append(lname)
        if len(self.recent_levels) > 20: self.recent_levels.pop(0)
        self.save_stats()
        self.animating_tiles, self.matched_tiles, self.undo_animating_tiles = [], [], []
        self.show_history, self.history_anim_state = False, 'idle'; self.is_manual_paused, self.is_paused_by_focus, self.pause_start_ticks = False, False, 0
        self.current_layout_name = self.layout_names[l_id]
        if self.bg_images:
            if self.current_bg:
                self.prev_bg, self.scaled_prev_bg, self.bg_transition_progress = self.current_bg, self.scaled_bg, 0.0
                if len(self.bg_images) > 1:
                    new_bg = self.current_bg
                    while new_bg == self.current_bg: new_bg = random.choice(self.bg_images)
                    self.current_bg = new_bg
                else: self.current_bg = random.choice(self.bg_images)
            else: self.current_bg = random.choice(self.bg_images); self.bg_transition_progress = 1.0
            self.scaled_bg = self.scale_background(self.current_bg)
        pos, self.layout_w_tiles, self.layout_h_tiles = self.get_layout_positions(l_id)
        self.recompute_scaling(); self.layout = [{'type': 0, 'pos': p, 'rect': None, 'anim_factor': (i/len(pos))*0.4 + random.random()*0.1} for i, p in enumerate(pos)]
        self.initial_tile_count = len(self.layout) if self.layout else 144
        self.score_scaling = 144.0 / self.initial_tile_count
        self.make_solvable(); self.update_sorted_layout(); self.selected, self.won, self.hint_pair = None, False, None
        self.victory_anim_state, self.victory_tiles = 'idle', []
        self.shuffle_count = 0; now = self.pause_start_ticks if self.is_paused else pygame.time.get_ticks()
        self.last_move_time, self.start_ticks, self.final_time, self.current_score, self.displayed_score, self.flying_scores = now, now, None, 0, 0, []
        self.last_match_time, self.match_multiplier = self.start_ticks, 1.0

    @property
    def is_paused(self):
        return (getattr(self, 'is_manual_paused', False) or getattr(self, 'is_paused_by_focus', False) or self.stats_ui_state != 'closed' or self.options_ui_state != 'closed')

    def finalize_victory(self):
        if self.final_time is not None: return
        self.final_time = max(0, pygame.time.get_ticks() - self.start_ticks)
        self.victory_anim_idx = 11; self.global_games_played += 1
        if self.shuffle_count == 0: self.wins_without_shuffle += 1
        elif self.shuffle_count == 1: self.wins_with_one_shuffle += 1
        lname = self.current_layout_name
        if lname not in self.level_stats: self.level_stats[lname] = {"best_time": self.final_time, "best_shuffles": self.shuffle_count, "times_completed": 1, "total_time": self.final_time, "best_score": self.current_score}
        else:
            current_best = self.level_stats[lname].get("best_time")
            if current_best is None or current_best == 0: current_best = 999999999
            self.level_stats[lname]["best_time"] = min(current_best, self.final_time)
            self.level_stats[lname]["best_shuffles"] = min(self.level_stats[lname].get("best_shuffles", 999), self.shuffle_count)
            self.level_stats[lname]["times_completed"] = self.level_stats[lname].get("times_completed", 0) + 1
            current_total = self.level_stats[lname].get("total_time")
            if current_total is None: current_total = 0
            self.level_stats[lname]["total_time"] = current_total + self.final_time
            self.level_stats[lname]["best_score"] = max(self.level_stats[lname].get("best_score", 0), self.current_score)
        self.save_stats()

    def update_sorted_layout(self):
        for t in self.layout:
            t['free'] = self.is_free(t)
            if getattr(self, 'show_gray_tiles', True): t['target_gray_alpha'] = 0.0 if t['free'] else 120.0
            else: t['target_gray_alpha'] = 0.0
            if 'gray_alpha' not in t: t['gray_alpha'] = t['target_gray_alpha']
        self.sorted_layout = sorted(self.layout, key=lambda t: (t['pos'][2], t['pos'][1], t['pos'][0]))

    def are_compatible(self, t1, t2):
        if t1 == t2: return True
        nt = len(self.tile_variants)
        if nt - 8 <= t1 < nt - 4 and nt - 8 <= t2 < nt - 4: return True
        if t1 >= nt - 4 and t2 >= nt - 4: return True
        return False

    def make_solvable(self, types_pool=None):
        if not self.layout: return
        nt, nv = len(self.layout), len(self.tile_variants)
        if not types_pool:
            types_pool = []
            for i in range(nt // 2): types_pool.extend([i % nv, i % nv])
        full_tp = list(types_pool)
        for _ in range(200):
            if self.construct_solvable_board(list(full_tp)): return

    def is_free_in_list(self, t, current_list):
        tx, ty, tz = t['pos']
        for o in current_list:
            if o == t: continue
            ox, oy, oz = o['pos']
            if oz > tz and abs(ox - tx) < 1.0 and abs(oy - ty) < 1.0: return False
        lb, rb = False, False
        for o in current_list:
            if o == t: continue
            ox, oy, oz = o['pos']
            if oz == tz and abs(oy - ty) < 1.0:
                if tx - 1.0 <= ox <= tx - 0.5: lb = True
                if tx + 0.5 <= ox <= tx + 1.0: rb = True
        return not (lb and rb)

    def construct_solvable_board(self, full_tp):
        nt = len(self.tile_variants); seasons = [t for t in full_tp if nt - 8 <= t < nt - 4]
        flowers = [t for t in full_tp if t >= nt - 4]; others = [t for t in full_tp if t < nt - 8]
        others.sort(); all_pairs = []
        for i in range(0, len(others), 2):
            if i+1 < len(others): all_pairs.append((others[i], others[i+1]))
        random.shuffle(seasons)
        for i in range(0, len(seasons), 2):
            if i+1 < len(seasons): all_pairs.append((seasons[i], seasons[i+1]))
        random.shuffle(flowers)
        for i in range(0, len(flowers), 2):
            if i+1 < len(flowers): all_pairs.append((flowers[i], flowers[i+1]))
        random.shuffle(all_pairs); slots = self.layout[:]
        for t in slots: t['type'] = -1
        success = True
        while slots and all_pairs:
            free_slots = [t for t in slots if self.is_free_in_list(t, slots)]
            if len(free_slots) < 2: success = False; break
            s1 = random.choice(free_slots); free_slots.remove(s1); s2 = random.choice(free_slots)
            p = all_pairs.pop(); s1['type'], s2['type'] = p; slots.remove(s1); slots.remove(s2)
        if slots:
            remaining = []; [remaining.extend(p) for p in all_pairs]; random.shuffle(remaining)
            for t in slots:
                if remaining: t['type'] = remaining.pop()
        return success

    def is_free(self, t):
        tx, ty, tz = t['pos']
        for o in self.layout:
            if o == t: continue
            ox, oy, oz = o['pos']
            if oz > tz and abs(ox - tx) < 1.0 and abs(oy - ty) < 1.0: return False
        lb, rb = False, False
        for o in self.layout:
            if o == t: continue
            ox, oy, oz = o['pos']
            if oz == tz and abs(oy - ty) < 1.0:
                if tx - 1.0 <= ox <= tx - 0.5: lb = True
                if tx + 0.5 <= ox <= tx + 1.0: rb = True
        return not (lb and rb)

    def get_hint(self):
        f = [t for t in self.layout if t.get('free', self.is_free(t))]
        for i in range(len(f)):
            for j in range(i + 1, len(f)):
                if self.are_compatible(f[i]['type'], f[j]['type']): return (f[i], f[j])
        return None

    def has_moves(self):
        f = [t for t in self.layout if t.get('free', self.is_free(t))]
        for i in range(len(f)):
            for j in range(i + 1, len(f)):
                if self.are_compatible(f[i]['type'], f[j]['type']): return True
        return False

    def count_moves(self):
        f = [t for t in self.layout if t.get('free', self.is_free(t))]
        count = 0
        for i in range(len(f)):
            for j in range(i + 1, len(f)):
                if self.are_compatible(f[i]['type'], f[j]['type']): count += 1
        return count

    def get_layout_positions(self, l_id):
        if l_id >= len(self.level_files) or self.level_files[l_id] is None: return [], 0, 0
        try:
            with open(self.level_files[l_id], 'r', encoding='utf-8') as f: data = json.load(f)
        except Exception: return [], 0, 0
        if not data: return [], 0, 0
        min_x = min(d['x'] for d in data); max_x = max(d['x'] for d in data)
        min_y = min(d['y'] for d in data); max_y = max(d['y'] for d in data)
        self.layout_w_tiles = (max_x - min_x + 2) / 2.0; self.layout_h_tiles = (max_y - min_y + 2) / 2.0
        final_tiles = []
        for d in data:
            gx = (d['x'] - min_x) / 2.0; gy = (d['y'] - min_y) / 2.0; gz = float(d['layer']); final_tiles.append((gx, gy, gz))
        if len(final_tiles) % 2 != 0: final_tiles.sort(key=lambda t: t[2], reverse=True); final_tiles.pop(0)
        final_tiles.sort(key=lambda t: (t[2], t[1], t[0])); return final_tiles, self.layout_w_tiles, self.layout_h_tiles

    def start_match_animation(self, t1, t2):
        ty = self.height - self.th - 20; tx1, tx2 = self.width-self.tw-20, self.width-self.tw*2-30
        for i, t in enumerate([t1, t2]):
            self.animating_tiles.append({'image_index': t['type'], 'pos': list(t['rect'].topleft if t['rect'] else (0,0)), 
                                        'target': (tx2 if i==0 else tx1, ty), 'original_tile': {'type':t['type'], 'pos':t['pos'], 'rect':None}})
            if t in self.layout: self.layout.remove(t)
        self.update_sorted_layout()

    def start_undo_animation(self, rd):
        mx, my = getattr(self, 'board_offset_x', (self.width - self.layout_w_tiles * (self.tw + 2)) // 2), getattr(self, 'board_offset_y', (self.height - self.layout_h_tiles * (self.th + 2)) // 2)
        for d in rd:
            t, sp, o = d['tile'], d['start_pos'], d['tile']['original_tile']
            tgt = (mx + o['pos'][0]*(self.tw+2) - o['pos'][2]*self.depth_off, my + o['pos'][1]*(self.th+2) - o['pos'][2]*self.depth_off)
            self.undo_animating_tiles.append({'image_index': t['image_index'], 'pos': list(sp), 'target': tgt, 'original_tile': o})

    def start_shuffle_animation(self, start_pos=None):
        if not self.layout: return
        self.shuffle_anim_state, self.shuffle_needed, self.hint_pair = 'fading_out', False, None
        for t in self.layout: t['target_gray_alpha'] = 0.0
        
        # Add negative flying score for shuffle
        penalty = 5000
        f_t = pygame.font.SysFont("Arial", 24, bold=True)
        target_x = 20 + f_t.size("Score : ")[0] + f_t.size(str(self.displayed_score))[0] // 2
        target_y = 25 + f_t.get_height() + f_t.get_height() // 2
        
        # Default to screen center if no start_pos provided
        sp = start_pos if start_pos else (self.width // 2, self.height // 2)
        
        self.flying_scores.append({
            'pos': [sp[0], sp[1]],
            'target': (target_x, target_y),
            'text': f"-{penalty}",
            'score_value': -penalty,
            'progress': 0.0
        })

    def _execute_shuffle_logic(self):
        self.matched_tiles = []; self.shuffle_count += 1; self.total_shuffles += 1; self.shuffle_anim_state = 'moving'
        old_data = [{'type': t['type'], 'pos': t['pos']} for t in self.layout]
        current_types = [t['type'] for t in self.layout]; self.make_solvable(types_pool=current_types); self.update_sorted_layout()
        self.shuffle_tiles_data = []
        mx, my = getattr(self, 'board_offset_x', (self.width - self.layout_w_tiles * (self.tw + 2)) // 2), getattr(self, 'board_offset_y', (self.height - self.layout_h_tiles * (self.th + 2)) // 2)
        used_old = [False] * len(old_data); self.shuffle_duration = 1200; self.shuffle_start_time = pygame.time.get_ticks()
        for t in self.layout:
            target_type = t['type']; found_idx = -1
            for j, old in enumerate(old_data):
                if not used_old[j] and old['type'] == target_type: found_idx = j; used_old[j] = True; break
            if found_idx != -1:
                old = old_data[found_idx]; sx = mx + old['pos'][0]*(self.tw+2) - old['pos'][2]*self.depth_off; sy = my + old['pos'][1]*(self.th+2) - old['pos'][2]*self.depth_off
                ex = mx + t['pos'][0]*(self.tw+2) - t['pos'][2]*self.depth_off; ey = my + t['pos'][1]*(self.th+2) - t['pos'][2]*self.depth_off
                # Organic parameters: individual delay, speed variation, and tilt
                self.shuffle_tiles_data.append({
                    'type': target_type, 'start_pos': (sx, sy), 'current_pos': [sx, sy], 'end_pos': (ex, ey), 
                    'tile': t, 
                    'delay': random.uniform(0, 0.5), # Slightly less staggered
                    'speed_mod': random.uniform(0.6, 1.4), 
                    'arc_strength': random.uniform(50, 200), # Reduced strength to stay on screen
                    'arc_dir': random.uniform(-1.0, 1.0),
                    'max_tilt': random.uniform(-45, 45), 
                    'scale_mod': random.uniform(0.2, 0.5),
                    'rot': 0.0, 'scale': 1.0
                })
        self.shuffle_tiles_data.sort(key=lambda d: (d['tile']['pos'][2], d['tile']['pos'][1], d['tile']['pos'][0]))

    def update_shuffle_animation(self):
        if self.shuffle_anim_state == 'fading_out':
            if all(t.get('gray_alpha', 0) == 0 for t in self.layout): self._execute_shuffle_logic()
        elif self.shuffle_anim_state == 'moving':
            total_prog = (pygame.time.get_ticks() - self.shuffle_start_time) / self.shuffle_duration
            all_finished = True
            for d in self.shuffle_tiles_data:
                # Individual progress based on delay and speed modifier
                tile_prog = max(0.0, min(1.0, (total_prog - d['delay']) * d['speed_mod']))
                if tile_prog < 1.0: all_finished = False
                
                ease = 1.0 - pow(1.0 - tile_prog, 3)
                base_x = d['start_pos'][0] + (d['end_pos'][0] - d['start_pos'][0]) * ease
                base_y = d['start_pos'][1] + (d['end_pos'][1] - d['start_pos'][1]) * ease
                
                arc_sin = np.sin(np.pi * tile_prog)
                dx, dy = d['end_pos'][0] - d['start_pos'][0], d['end_pos'][1] - d['start_pos'][1]
                px, py = -dy, dx
                length = (px**2 + py**2)**0.5 or 1
                
                d['current_pos'][0] = base_x + (px / length) * d['arc_strength'] * d['arc_dir'] * arc_sin
                d['current_pos'][1] = base_y + (py / length) * d['arc_strength'] * d['arc_dir'] * arc_sin
                
                # Keep within screen bounds
                d['current_pos'][0] = max(0, min(self.width - self.tw, d['current_pos'][0]))
                d['current_pos'][1] = max(0, min(self.height - self.th, d['current_pos'][1]))
                
                # Organic tilt and scale
                d['rot'] = arc_sin * d['max_tilt']
                d['scale'] = 1.0 + arc_sin * d.get('scale_mod', 0.4)
                
            if all_finished and total_prog >= 1.0:
                self.shuffle_anim_state = 'settling'
                self.shuffle_settling_start = pygame.time.get_ticks()
        elif self.shuffle_anim_state == 'settling':
            if pygame.time.get_ticks() - self.shuffle_settling_start > 500:
                self.shuffle_anim_state, self.shuffle_tiles_data = 'idle', []
                self.last_match_time = pygame.time.get_ticks()
                self.last_move_time = self.last_match_time

    def update_level_animations(self):
        if self.level_anim_state == 'in':
            self.level_anim_progress = min(1.0, self.level_anim_progress + 0.01)
            if self.level_anim_progress == 1.0:
                self.level_anim_state = 'idle'; now = self.pause_start_ticks if self.is_paused else pygame.time.get_ticks()
                self.start_ticks, self.last_match_time, self.last_move_time = now, now, now
        elif self.level_anim_state == 'out':
            self.level_anim_progress = max(0.0, self.level_anim_progress - 0.01)
            if self.level_anim_progress <= 0.0 and not self.victory_tiles: self.init_game(self.next_layout_id); self.next_layout_id, self.level_anim_state = None, 'in'

    def update_ui_animations(self):
        if self.won and self.win_ui_state == 'closed':
            if self.victory_anim_state == 'idle':
                self.victory_anim_state = 'active'; self.victory_anim_start_time = pygame.time.get_ticks(); self.init_victory_animation()
            elif self.victory_anim_state == 'active':
                if self.win_ui_state == 'closed' and pygame.time.get_ticks() - self.victory_anim_start_time > 3000:
                    self.finalize_victory(); self.win_ui_state, self.win_ui_progress = 'opening', 0.0
                if pygame.time.get_ticks() - self.victory_anim_start_time > 20000: self.victory_anim_state = 'draining'
        if self.win_ui_state == 'opening':
            self.win_ui_progress = min(1.0, self.win_ui_progress + 0.08)
            if self.win_ui_progress >= 1.0: self.win_ui_state = 'open'
        elif self.win_ui_state == 'closing':
            self.win_ui_progress = max(0.0, self.win_ui_progress - 0.08)
            if self.win_ui_progress <= 0.0:
                self.win_ui_state = 'closed'
                if getattr(self, 'open_stats_after_win', False):
                    self.open_stats_after_win = False; self.stats_ui_state, self.stats_scroll_y = 'opening', 0; self.stats_sort_col = None; self.stats_sort_reverse = False
                    self.stats_display_indices = list(range(len(self.layout_names))); self.pause_start_ticks = pygame.time.get_ticks()
                else: self.reset_game(getattr(self, 'next_level_to_load', None)); self.next_level_to_load = None
        if self.shuffle_needed and self.shuffle_ui_state == 'closed' and self.shuffle_anim_state == 'idle': 
            if not self.is_paused: self.pause_start_ticks = pygame.time.get_ticks()
            self.shuffle_ui_state, self.shuffle_ui_progress = 'opening', 0.0
        if self.shuffle_ui_state == 'opening':
            self.shuffle_ui_progress = min(1.0, self.shuffle_ui_progress + 0.08)
            if self.shuffle_ui_progress >= 1.0: self.shuffle_ui_state = 'open'
        elif self.shuffle_ui_state == 'closing':
            self.shuffle_ui_progress = max(0.0, self.shuffle_ui_progress - 0.08)
            if self.shuffle_ui_progress <= 0.0:
                self.shuffle_ui_state = 'closed'
                if not self.is_paused:
                    paused_duration = pygame.time.get_ticks() - self.pause_start_ticks; self.adjust_times_after_pause(paused_duration)
                if self.shuffle_confirmed:
                    # Use the dialog button position if available
                    sp = getattr(self, 'shuffle_confirm_btn', None)
                    self.start_shuffle_animation(sp.center if sp else None)
                    self.shuffle_confirmed = False
                else: self.shuffle_needed = False
        if self.stats_ui_state == 'opening':
            self.stats_ui_progress = min(1.0, self.stats_ui_progress + 0.08)
            if self.stats_ui_progress >= 1.0: self.stats_ui_state = 'open'
        elif self.stats_ui_state == 'closing':
            self.stats_ui_progress = max(0.0, self.stats_ui_progress - 0.08)
            if self.stats_ui_progress <= 0.0:
                self.stats_ui_state = 'closed'
                if not self.is_paused:
                    paused_duration = pygame.time.get_ticks() - self.pause_start_ticks; self.adjust_times_after_pause(paused_duration)
                if self.pending_level_idx is not None: self.reset_game(self.pending_level_idx); self.pending_level_idx = None
                elif self.won: self.win_ui_state, self.win_ui_progress = 'opening', 0.0
        if self.options_ui_state == 'opening':
            self.options_ui_progress = min(1.0, self.options_ui_progress + 0.08)
            if self.options_ui_progress >= 1.0: self.options_ui_state = 'open'
        elif self.options_ui_state == 'closing':
            self.options_ui_progress = max(0.0, self.options_ui_progress - 0.08)
            if self.options_ui_progress <= 0.0:
                self.options_ui_state = 'closed'
                if not self.is_paused:
                    paused_duration = pygame.time.get_ticks() - self.pause_start_ticks; self.adjust_times_after_pause(paused_duration)

    def update_animations(self):
        self.update_level_animations(); self.update_ui_animations()
        if self.bg_transition_progress < 1.0: self.bg_transition_progress = min(1.0, self.bg_transition_progress + 0.02)
        if self.is_paused: return
        self.update_shuffle_animation(); self.update_history_animations(); self.update_victory_animation()
        remaining_scores = []
        for s in self.flying_scores:
            s['progress'] += 0.01
            if s['progress'] < 1.0: remaining_scores.append(s)
            else: self.current_score = max(0, self.current_score + s.get('score_value', 0))
        self.flying_scores = remaining_scores
        if self.displayed_score < self.current_score:
            step = max(1, int((self.current_score - self.displayed_score) * 0.1)); self.displayed_score += step
        elif self.displayed_score > self.current_score:
            step = max(1, int((self.displayed_score - self.current_score) * 0.1)); self.displayed_score -= step
        if getattr(self, 'auto_hint', True) and not self.won and not self.hint_pair and self.stats_ui_state == 'closed' and self.options_ui_state == 'closed':
            if pygame.time.get_ticks() - self.last_move_time > 60000:
                hint = self.get_hint()
                if hint:
                    self.hint_pair = hint
                    # Add negative flying score (same as manual hint)
                    if hasattr(self, 'hint_btn_rect'):
                        penalty = 500
                        f_t = pygame.font.SysFont("Arial", 24, bold=True)
                        target_x = 20 + f_t.size("Score : ")[0] + f_t.size(str(self.displayed_score))[0] // 2
                        target_y = 25 + f_t.get_height() + f_t.get_height() // 2
                        start_x, start_y = self.hint_btn_rect.center
                        self.flying_scores.append({
                            'pos': [start_x, start_y],
                            'target': (target_x, target_y),
                            'text': f"-{penalty}",
                            'score_value': -penalty,
                            'progress': 0.0
                        })
        if self.shuffle_anim_state in ('idle', 'fading_out'):
            for t in self.layout:
                ta = t.get('target_gray_alpha', 0.0); ca = t.get('gray_alpha', ta)
                if ca < ta: t['gray_alpha'] = min(ta, ca + 4.0)
                elif ca > ta: t['gray_alpha'] = max(ta, ca - 4.0)
        fin = []
        for a in self.animating_tiles:
            dx, dy = a['target'][0]-a['pos'][0], a['target'][1]-a['pos'][1]; dist = (dx**2+dy**2)**0.5
            if dist < 25: a['pos'] = list(a['target']); fin.append(a)
            else: a['pos'][0] += (dx/dist)*25; a['pos'][1] += (dy/dist)*25
        for a in fin: self.animating_tiles.remove(a); self.matched_tiles.append(a)
        if not self.won and not self.layout and not self.animating_tiles and self.level_anim_state == 'idle':
            self.won = True
            self.matched_tiles = []
            self.show_history = False
            
    def update_history_animations(self):
        if self.history_anim_state == 'opening':
            self.history_anim_progress = min(1.0, self.history_anim_progress + 0.05)
            if self.history_anim_progress >= 1.0: self.history_anim_state = 'idle'
        elif self.history_anim_state == 'closing':
            self.history_anim_progress = max(0.0, self.history_anim_progress - 0.05)
            if self.history_anim_progress <= 0.0: self.history_anim_state, self.show_history = 'idle', False
        fin_u = []
        for a in self.undo_animating_tiles:
            dx, dy = a['target'][0]-a['pos'][0], a['target'][1]-a['pos'][1]; dist = (dx**2+dy**2)**0.5
            if dist < 35: a['pos'] = list(a['target']); a['finished'] = True; fin_u.append(a)
            else: a['pos'][0] += (dx/dist)*35; a['pos'][1] += (dy/dist)*35
        
        if self.undo_animating_tiles and all(a.get('finished') for a in self.undo_animating_tiles):
            if not hasattr(self, 'undo_settling_start') or self.undo_settling_start == 0:
                self.undo_settling_start = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - self.undo_settling_start > 500:
                for a in self.undo_animating_tiles:
                    self.layout.append(a['original_tile'])
                self.undo_animating_tiles = []
                self.update_sorted_layout()
                self.undo_settling_start = 0
        else:
            self.undo_settling_start = 0

    def init_victory_animation(self):
        self.victory_tiles = []
        nv = len(self.std_tile_variants); cx, cy = self.width // 2, self.height // 2
        anim_type = self.victory_anim_idx % 15
        for i in range(160):
            t = {'image_index': random.randint(0, nv - 1), 'rot': random.uniform(0, 360), 'rot_speed': random.uniform(-3, 3), 'anim_type': anim_type, 'pos': [0.0, 0.0], 'vel': [0.0, 0.0], 'dist': 0.0, 'angle': 0.0}
            if anim_type == 0: t['pos'] = [random.randint(-self.std_tw, self.width), random.randint(-self.height * 2, -self.std_th)]; t['vel'] = [0, random.uniform(10, 16)]
            elif anim_type == 1: t['angle'] = random.uniform(0, 2*np.pi); t['dist'] = random.uniform(self.width, self.width * 1.5)
            elif anim_type == 2: t['pos'] = [random.randint(0, self.width), random.randint(self.height, self.height + 2000)]; t['vel'] = [random.uniform(-1, 1), random.uniform(-10, -16)]; t['wobble'] = random.uniform(0, 2*np.pi)
            elif anim_type == 3: t['angle'] = random.uniform(0, 2*np.pi); t['dist'] = random.uniform(self.width, self.width * 1.5); t['speed'] = random.uniform(8, 14); t['radial_dir'] = -1
            elif anim_type == 4: t['pos'] = [random.randint(-1500, -self.std_tw), random.randint(100, self.height - 100)]; t['vel'] = [random.uniform(11, 15), 0]; t['base_y'], t['phase'] = t['pos'][1], random.uniform(0, 2 * np.pi)
            elif anim_type == 5: t['pos'] = [random.randint(-1500, -self.std_tw), random.randint(0, self.height)]; t['vel'] = [random.uniform(12, 18), random.uniform(-1, 1)]
            elif anim_type == 6: t['target_dist'], t['dist'] = random.uniform(100, self.width // 2), random.uniform(self.width, self.width * 1.5); t['angle'], t['orbit_speed'] = random.uniform(0, 2*np.pi), random.uniform(0.015, 0.03)
            elif anim_type == 7: t['pos'] = [random.randint(0, self.width), -random.randint(50, 500)]; t['vel'] = [random.uniform(-3, 3), random.uniform(10, 15)]; t['bounces'] = 0
            elif anim_type == 8: t['pos'] = [random.randint(-3000, -100), random.randint(-3000, -100)]; t['vel'] = [random.uniform(8, 12), random.uniform(8, 12)]
            elif anim_type == 9: t['pos'] = [cx - self.std_tw//2, cy - self.std_th//2]; t['vel'] = [random.uniform(-3, 3), random.uniform(-3, 3)]
            elif anim_type == 10: t['angle'] = (i / 80.0) * 2 * np.pi; t['dist'] = random.uniform(self.width * 0.5, self.width); t['side'] = 1 if i % 2 == 0 else -1
            elif anim_type == 11: t['pos'] = [cx + random.uniform(-50, 50), self.height + 100 + random.randint(0, 10000)]; angle = random.uniform(np.pi + 0.6, 2 * np.pi - 0.6); speed = random.uniform(24, 32); t['vel'] = [np.cos(angle) * speed, np.sin(angle) * speed]
            elif anim_type == 12: t['pos'] = [-self.std_tw - random.randint(0, 1000), (i % 20) * (self.height // 20)]; t['vel'] = [random.uniform(11, 15), 0]
            elif anim_type == 13: t['pos'] = [-100 - (i * 60), 0]; t['side'] = 1 if i % 2 == 0 else -1; t['phase'] = i * 0.2; t['vel'] = [13, 0]
            elif anim_type == 14: t['pos'] = [random.randint(0, self.width), -self.std_th - random.randint(0, 2000)]; t['vel'] = [0, random.uniform(8, 13)]; t['zig_phase'] = random.uniform(0, 2 * np.pi)
            self.victory_tiles.append(t)

    def update_victory_animation(self):
        if self.victory_anim_state not in ('active', 'finished', 'draining'): return
        now = pygame.time.get_ticks(); elapsed = now - self.victory_anim_start_time
        if self.victory_anim_state != 'draining' and elapsed > 20000: self.victory_anim_state = 'draining'
        is_draining = (self.victory_anim_state == 'draining')
        cx, cy, new_tiles = self.width // 2, self.height // 2, []
        
        for t in self.victory_tiles:
            t['rot'] += t['rot_speed']; v_anim = t['anim_type']
            
            if is_draining:
                # UNIVERSAL EXIT PHYSICS
                if v_anim in (1, 3, 6, 10): t['dist'] += 12
                elif v_anim == 9: 
                    dx, dy = t['pos'][0] - cx, t['pos'][1] - cy; d = (dx**2 + dy**2)**0.5 or 1; t['pos'][0] += (dx/d) * 15; t['pos'][1] += (dy/d) * 15
                elif v_anim == 7: # Force fall down through floor
                    t['pos'][1] += 15; t['pos'][0] += t['vel'][0]
                elif v_anim == 11: # Fountain: keep gravity but no recycling
                    t['pos'][0] += t['vel'][0]; t['vel'][1] += 0.4; t['pos'][1] += t['vel'][1]
                else: t['pos'][0] += t['vel'][0] * 1.2; t['pos'][1] += t['vel'][1] * 1.2
            else:
                # NORMAL ACTIVE LOGIC
                        if v_anim == 0:
                            t['pos'][1] += t['vel'][1]
                            if t['pos'][1] > self.height + self.std_th: t['pos'][1] = random.randint(-self.height, -self.std_th); t['pos'][0] = random.randint(-self.std_tw, self.width)
                        elif v_anim == 1:
                            t['angle'] += 0.02; t['dist'] = max(0, t['dist'] - 4)
                            if t['dist'] < 10: t['dist'] = random.uniform(self.width, self.width * 1.5)
                        elif v_anim == 2:
                            t['wobble'] += 0.1; t['pos'][0] += t['vel'][0] + np.sin(t['wobble']) * 2; t['pos'][1] += t['vel'][1]
                            if t['pos'][1] < -self.std_th: t['pos'][1] = self.height + random.randint(0, 1000)
                        elif v_anim == 3:
                            rot_speed = 0.01 + (0.05 * (1.0 - min(1.0, t['dist'] / self.width)))
                            t['angle'] += rot_speed
                            if not is_draining:
                                if t['dist'] < 30: t['radial_dir'] = 1
                                elif t['dist'] > self.width * 0.8: t['radial_dir'] = -1
                                t['dist'] += t['speed'] * 0.5 * t.get('radial_dir', -1)
                        elif v_anim == 4:
                            t['pos'][0] += t['vel'][0]; t['phase'] += 0.1; t['pos'][1] = t['base_y'] + np.sin(t['phase']) * 50
                            if t['pos'][0] > self.width + self.std_tw: t['pos'][0] = -random.randint(100, 500)
                        elif v_anim == 5:
                            t['pos'][0] += t['vel'][0]; t['pos'][1] += t['vel'][1]
                            if t['pos'][0] > self.width + self.std_tw: t['pos'][0] = -random.randint(100, 500)
                        elif v_anim == 6:
                            t['angle'] += t['orbit_speed']
                            if abs(t['dist'] - t['target_dist']) > 5: t['dist'] += (t['target_dist'] - t['dist']) * 0.02
                        elif v_anim == 7:
                            t['pos'][0] += t['vel'][0]; t['vel'][1] += 0.5; t['pos'][1] += t['vel'][1]
                            if t['pos'][1] > self.height - self.std_th:
                                t['pos'][1] = self.height - self.std_th; t['vel'][1] *= -0.7; t['bounces'] += 1
                                if t['bounces'] > 5: t['pos'][1] = -random.randint(50, 500); t['vel'][1] = random.uniform(10, 15); t['bounces'] = 0
                        elif v_anim == 8:
                            t['pos'][0] += t['vel'][0]; t['pos'][1] += t['vel'][1]
                            if t['pos'][0] > self.width + 100: t['pos'][0] = random.randint(-1500, -100); t['pos'][1] = random.randint(-1500, -100)
                        elif v_anim == 9: t['pos'][0] += t['vel'][0]; t['pos'][1] += t['vel'][1]
                        elif v_anim == 10:
                            t['angle'] += 0.025 * t['side']
                            wave = np.sin(t['angle'] * 2 + elapsed * 0.002) * 120
                            spread = (t['image_index'] % 8) * 30
                            target_dist = 250 + spread + wave
                            t['dist'] += (target_dist - t['dist']) * 0.05
                        elif v_anim == 11:
                            t['pos'][0] += t['vel'][0]; t['vel'][1] += 0.4; t['pos'][1] += t['vel'][1]
                            if t['pos'][1] > self.height + 100 and not is_draining:
                                t['pos'][0] = cx + random.uniform(-50, 50); t['pos'][1] = self.height + 100 + random.randint(0, 500)
                                angle = random.uniform(np.pi + 0.6, 2 * np.pi - 0.6); speed = random.uniform(24, 32); t['vel'] = [np.cos(angle) * speed, np.sin(angle) * speed]
                        elif v_anim == 12:
                            t['pos'][0] += t['vel'][0]
                            if t['pos'][0] > self.width + 100 and not is_draining: t['pos'][0] = -random.randint(100, 500)
                        elif v_anim == 13:
                            t['pos'][0] += 13; t['phase'] += 0.1; t['pos'][1] = cy + t['side'] * 150 * np.sin(t['phase'])
                            if t['pos'][0] > self.width + 100 and not is_draining: t['pos'][0] -= (160 * 60)
                        elif v_anim == 14:
                            t['zig_phase'] += 0.1; t['pos'][0] += np.sin(t['zig_phase']) * 10; t['pos'][1] += t['vel'][1]
                            if t['pos'][1] > self.height + 100 and not is_draining: t['pos'][1] = -random.randint(100, 1000)
            if v_anim in (1, 3, 6, 10): t['pos'][0] = cx + np.cos(t['angle']) * t['dist']; t['pos'][1] = cy + np.sin(t['angle']) * t['dist']
            off = (t['pos'][1] > self.height + 200 or t['pos'][1] < -200 or t['pos'][0] > self.width + 200 or t['pos'][0] < -200)
            if not (is_draining and off): new_tiles.append(t)
        self.victory_tiles = new_tiles
        if is_draining and len(self.victory_tiles) < 3:
            self.victory_tiles, self.victory_anim_state = [], 'idle'
            if self.queued_debug_anim is not None:
                self.victory_anim_idx = self.queued_debug_anim; self.queued_debug_anim = None
                self.victory_anim_state, self.victory_anim_start_time = 'active', pygame.time.get_ticks(); self.init_victory_animation()

    def reset_game(self, l_id=None):
        self.won = False
        if not self.layout and not self.animating_tiles and not self.matched_tiles and not self.victory_tiles: self.init_game(l_id); self.next_layout_id, self.level_anim_state, self.level_anim_progress = None, 'in', 0.0
        else: self.next_layout_id, self.level_anim_state, self.level_anim_progress = l_id, 'out', 1.0

    def draw(self):
        self.update_animations()
        if self.bg_transition_progress < 1.0 and self.scaled_prev_bg:
            self.screen.blit(self.scaled_prev_bg, (0, 0))
            if self.scaled_bg: self.scaled_bg.set_alpha(int(255 * self.bg_transition_progress)); self.screen.blit(self.scaled_bg, (0, 0))
        elif self.scaled_bg: self.screen.blit(self.scaled_bg, (0, 0))
        else: self.screen.fill((34, 139, 34))
        ov_bg = pygame.Surface((self.width, self.height), pygame.SRCALPHA); ov_bg.fill((0, 0, 0, 60)); self.screen.blit(ov_bg, (0, 0))
        def get_off_y(t, idx, tot):
            if self.level_anim_state == 'idle' and self.level_anim_progress == 1.0: return 0
            f = t.get('anim_factor', (idx/tot)*0.5)
            if self.level_anim_state == 'in': return -self.height * (1.0 - max(0, min(1, (self.level_anim_progress - f) / 0.5)))**2
            if self.level_anim_state == 'out': return self.height * (max(0, min(1, (1.0 - self.level_anim_progress - f) / 0.5)))**2
            return 0
        f_ui = pygame.font.SysFont("Arial", 24, bold=True)
        if self.won or self.win_ui_state != 'closed' or self.level_anim_state != 'idle': el = 0
        elif self.is_paused: el = max(0, (self.pause_start_ticks - self.start_ticks) // 1000)
        else: el = max(0, (pygame.time.get_ticks() - self.start_ticks) // 1000)
        timer_text = f"Temps : {el//60:02}:{el%60:02}"
        if self.is_paused: timer_text += " (PAUSE)"
        self.screen.blit(f_ui.render(timer_text, True, (255,255,255)), (20,20))
        score_surf = f_ui.render(f"Score : {self.displayed_score}", True, (255, 255, 255)); self.screen.blit(score_surf, (20, 20 + f_ui.get_height() + 5))
        rem = len(self.layout)+len(self.animating_tiles); tr_t = f_ui.render(f"Tuiles : {rem}", True, (255,255,255)); self.screen.blit(tr_t, (self.width - tr_t.get_width() - 20, 20))
        poss = self.count_moves(); f_sub = pygame.font.SysFont("Arial", 18, bold=True)
        # Combination color: Red only if tiles remain but no moves. Green if no tiles or moves available.
        poss_color = (200, 255, 200) if (poss > 0 or not self.layout) else (255, 100, 100)
        poss_t = f_sub.render(f"Combinaisons : {poss}", True, poss_color)
        self.screen.blit(poss_t, (self.width - poss_t.get_width() - 20, 20 + tr_t.get_height() + 2))
        level_display_name = self.current_layout_name; stats = self.level_stats.get(self.current_layout_name, {})
        if getattr(self, 'show_win_count', True): level_display_name += f" ({stats.get('times_completed', 0)})"
        if getattr(self, 'show_best_shuffles', True):
            best_sh = stats.get("best_shuffles")
            if best_sh is not None: level_display_name += f" ({best_sh})"
        ln_t = f_ui.render(level_display_name, True, (255, 255, 255)); self.screen.blit(ln_t, (self.width//2-ln_t.get_width()//2, 20))
        mt_tot = len(self.matched_tiles); rad = max(3, int(self.tw/12))
        if not self.won and self.level_anim_state == 'idle' and self.victory_anim_state == 'idle':
            for i, t in enumerate(self.matched_tiles):
                oy = get_off_y(t, i, mt_tot); x, y = t['pos']; self.screen.blit(self.shadow_surf, (x + 2, y + oy + 2))
                for j in range(self.depth_off, 0, -1):
                    fac = (self.depth_off - j) / (self.depth_off - 1) if self.depth_off > 1 else 1.0; v = int(100 + (160 - 100) * (fac**3)); side_c = (75, 50, 25) if j >= self.depth_off - 1 else (v, int(v*0.96), int(v*0.85)); pygame.draw.rect(self.screen, side_c, pygame.Rect(x, y + oy, self.tw, self.th).move(j, j), border_radius=rad)
                self.screen.blit(self.tile_variants[t['image_index']]['filtered'], (x, y + oy))
        if self.shuffle_count > 0:
            sh_text = f_ui.render(f"Mélanges : {self.shuffle_count}", True, (255, 255, 255))
            tx2 = self.width - self.tw * 2 - 30; ty = self.height - self.th - 20; self.screen.blit(sh_text, (tx2 - sh_text.get_width() - 20, ty + (self.th - sh_text.get_height()) // 2))
        if self.victory_tiles:
            for t in self.victory_tiles:
                img = self.std_tile_variants[t['image_index']]; scale = t.get('scale', 1.0)
                if scale != 1.0:
                    tw, th = int(self.std_tw * scale), int(self.std_th * scale)
                    if tw > 0 and th > 0: img = pygame.transform.smoothscale(img, (tw, th))
                if abs(t['rot']) > 0.1: img = pygame.transform.rotate(img, t['rot'])
                rect = img.get_rect(center=(int(t['pos'][0] + (self.std_tw*scale)//2), int(t['pos'][1] + (self.std_th*scale)//2))); self.screen.blit(img, rect)
        if self.win_ui_progress > 0:
            ov = pygame.Surface((self.width,self.height), pygame.SRCALPHA); ov.fill((0,0,0,int(200 * self.win_ui_progress))); self.screen.blit(ov,(0,0))
            pw, ph = 650, 520; win_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            # Background & Border
            pygame.draw.rect(win_surf, (30, 30, 35, 255), (0, 0, pw, ph), border_radius=25)
            pygame.draw.rect(win_surf, (218, 165, 32, 255), (0, 0, pw, ph), 4, border_radius=25)
            
            # Header
            f_title = pygame.font.SysFont("Arial", 70, True)
            t_shadow = f_title.render("VICTOIRE", True, (0, 0, 0))
            t_main = f_title.render("VICTOIRE", True, (255, 215, 0))
            win_surf.blit(t_shadow, t_shadow.get_rect(center=(pw//2 + 3, 73)))
            win_surf.blit(t_main, t_main.get_rect(center=(pw//2, 70)))
            
            st = pygame.font.SysFont("Arial", 24, italic=True).render(self.current_layout_name, True, (200, 200, 200))
            win_surf.blit(st, st.get_rect(center=(pw//2, 130)))
            
            pygame.draw.line(win_surf, (100, 100, 100), (100, 160), (pw-100, 160), 1)
            f_stats = pygame.font.SysFont("Arial", 22)
            
            # Highlighted Time and Score
            f_highlight = pygame.font.SysFont("Arial", 42, True)
            el_final = self.final_time // 1000
            time_str = f"{el_final//60:02}:{el_final%60:02}"
            
            # Time block
            pygame.draw.rect(win_surf, (40, 45, 40), (100, 190, 210, 90), border_radius=15)
            pygame.draw.rect(win_surf, (46, 139, 87), (100, 190, 210, 90), 2, border_radius=15)
            win_surf.blit(f_stats.render("TEMPS", True, (46, 139, 87)), (115, 200))
            t_val = f_highlight.render(time_str, True, (255, 255, 255))
            win_surf.blit(t_val, t_val.get_rect(center=(205, 245)))
            
            # Score block
            pygame.draw.rect(win_surf, (45, 45, 40), (pw-310, 190, 210, 90), border_radius=15)
            pygame.draw.rect(win_surf, (218, 165, 32), (pw-310, 190, 210, 90), 2, border_radius=15)
            win_surf.blit(f_stats.render("SCORE", True, (218, 165, 32)), (pw-295, 200))
            s_val = f_highlight.render(str(self.current_score), True, (255, 255, 255))
            win_surf.blit(s_val, s_val.get_rect(center=(pw-205, 245)))
            
            # Shuffles for this level
            sh_color = (220, 220, 220) if self.shuffle_count == 0 else (255, 140, 0)
            sh_surf = f_stats.render(f"Mélanges effectués : {self.shuffle_count}", True, sh_color)
            win_surf.blit(sh_surf, sh_surf.get_rect(center=(pw//2, 325)))            
            # Total games played
            gp_surf = f_stats.render(f"Total des parties gagnées : {self.global_games_played}", True, (200, 200, 200))
            win_surf.blit(gp_surf, gp_surf.get_rect(center=(pw//2, 360)))
            
            # Buttons
            bw, bh, gap = 200, 50, 40; total_bw = bw * 2 + gap; start_bx = (pw - total_bw) // 2
            m_p = pygame.mouse.get_pos(); scale = 0.8 + 0.2 * self.win_ui_progress; sw, sh = int(pw * scale), int(ph * scale); sx, sy = (self.width-sw)//2, (self.height-sh)//2; adj_m_p = ((m_p[0] - sx) / scale, (m_p[1] - sy) / scale)
            btn_configs = [("Niveau Suivant", "random"), ("Choisir un niveau", "choose")]; self.win_btn_rects = []; f_btn = pygame.font.SysFont("Arial", 20, bold=True)
            for i, (label, b_id) in enumerate(btn_configs):
                bx = start_bx + i * (bw + gap); rect = pygame.Rect(bx, 430, bw, bh); is_h = rect.collidepoint(adj_m_p) if self.win_ui_state == 'open' else False; is_p = getattr(self, 'win_pressed_btn', None) == b_id and is_h; self.draw_button(win_surf, rect, label, (60, 179, 113) if b_id=="random" else (70, 130, 180), f_btn, is_h, is_p, border_radius=15); self.win_btn_rects.append({'rect': pygame.Rect(sx + rect.x * scale, sy + rect.y * scale, rect.w * scale, rect.h * scale), 'id': b_id})
            
            scaled_win = pygame.transform.smoothscale(win_surf, (sw, sh))
            if self.win_ui_progress < 1.0: scaled_win.set_alpha(int(255 * self.win_ui_progress))
            self.screen.blit(scaled_win, (sx, sy))
            if self.win_ui_state in ('open', 'opening', 'closing'): pygame.display.flip(); return
            
            scaled_win = pygame.transform.smoothscale(win_surf, (sw, sh))
            if self.win_ui_progress < 1.0: scaled_win.set_alpha(int(255 * self.win_ui_progress))
            self.screen.blit(scaled_win, (sx, sy))
            if self.win_ui_state in ('open', 'opening', 'closing'): pygame.display.flip(); return
        mx, my = self.board_offset_x, self.board_offset_y
        if self.shuffle_anim_state == 'moving':
            for d in self.shuffle_tiles_data:
                tile_type, x, y = d['type'], d['current_pos'][0], d['current_pos'][1]
                img = self.tile_variants[tile_type]['filtered']
                # Apply scaling
                scale = d.get('scale', 1.0)
                if scale != 1.0:
                    sw, sh = int(self.tw * scale), int(self.th * scale)
                    if sw > 0 and sh > 0: img = pygame.transform.smoothscale(img, (sw, sh))
                # Apply rotation
                rot = d.get('rot', 0.0)
                if abs(rot) > 0.1: img = pygame.transform.rotate(img, rot)
                # Shadow
                rect = img.get_rect(center=(int(x + self.tw//2), int(y + self.th//2)))
                self.screen.blit(self.shadow_surf, rect.move(2, 2))
                self.screen.blit(img, rect)
        else:
            self.sorted_layout.sort(key=lambda t: (t['pos'][2], t['pos'][0] + t['pos'][1])); tot = len(self.sorted_layout); rad = max(3, int(self.tw/12))
            for i,t in enumerate(self.sorted_layout):
                x, y = mx+t['pos'][0]*(self.tw+2)-t['pos'][2]*self.depth_off, my+t['pos'][1]*(self.th+2)-t['pos'][2]*self.depth_off+get_off_y(t,i,tot); t['rect'] = pygame.Rect(x,y,self.tw,self.th)
                for j in range(self.depth_off, 0, -1): fac = (self.depth_off - j) / (self.depth_off - 1) if self.depth_off > 1 else 1.0; v = int(100 + (160 - 100) * (fac**3)); side_c = (75, 50, 25) if j >= self.depth_off - 1 else (v, int(v*0.96), int(v*0.85)); pygame.draw.rect(self.screen, side_c, t['rect'].move(j,j), border_radius=rad)
                
                # Show blank tiles if paused
                if self.is_paused:
                    self.screen.blit(self.blank_tile, (x, y))
                else:
                    self.screen.blit(self.tile_variants[t['type']]['filtered'], (x, y))
                
                ga = t.get('gray_alpha', 0.0)
                if ga > 0: self.gray_overlay.set_alpha(int(ga)); self.screen.blit(self.gray_overlay, (x, y))
                if self.selected==t: pygame.draw.rect(self.screen,(255,255,0),t['rect'],6,5)
                elif self.hint_pair and t in self.hint_pair: alp = int(128+127*np.sin(pygame.time.get_ticks()*0.01)); s=pygame.Surface((self.tw,self.th),pygame.SRCALPHA); pygame.draw.rect(s,(0,191,255,alp),s.get_rect(),8,5); self.screen.blit(s,(x,y))
        at_tot = len(self.animating_tiles + self.undo_animating_tiles)
        for i, a in enumerate(self.animating_tiles + self.undo_animating_tiles): oy = get_off_y(a, i, at_tot); x,y = a['pos']; self.screen.blit(self.tile_variants[a['image_index']]['filtered'],(x,y+oy))
        if not self.won and (self.show_history or self.history_anim_state != 'idle' or self.history_anim_progress > 0):
            csy, ih, start_y = self.height - self.th - 15, self.th + 15, 110; available_h = csy - start_y; max_pairs = max(1, available_h // ih); vh = self.matched_tiles[-(max_pairs * 2):]; hp = [(vh[i], vh[i+1]) for i in range(0, len(vh), 2) if i+1 < len(vh)]; hp.reverse(); self.history_rects = []; e = 1 - (1 - self.history_anim_progress)**3; tx1, tx2 = self.width - self.tw - 25, self.width - self.tw * 2 - 40
            for idx, p in enumerate(hp):
                ty = start_y + idx * ih; cy = csy + (ty - csy) * e if ty + ih <= csy else ty; pr = pygame.Rect(tx2 - 8, cy - 8, (tx1 - tx2) + self.tw + 16, self.th + 16)
                for j in range(self.depth_off, 0, -1): fac = (self.depth_off - j) / (self.depth_off - 1) if self.depth_off > 1 else 1.0; v = int(100 + (160 - 100) * (fac**3)); side_c = (75, 50, 25) if j >= self.depth_off - 1 else (v, int(v*0.96), int(v*0.85)); pygame.draw.rect(self.screen, side_c, pygame.Rect(tx2, cy, self.tw, self.th).move(j, j), border_radius=5); pygame.draw.rect(self.screen, side_c, pygame.Rect(tx1, cy, self.tw, self.th).move(j, j), border_radius=5)
                
                if self.is_paused:
                    self.screen.blit(self.blank_tile, (tx2, cy))
                    self.screen.blit(self.blank_tile, (tx1, cy))
                else:
                    self.screen.blit(self.tile_variants[p[0]['image_index']]['filtered'], (tx2, cy)); self.screen.blit(self.tile_variants[p[1]['image_index']]['filtered'], (tx1, cy))
                
                if self.show_history and self.history_anim_state == 'idle': pygame.draw.rect(self.screen, (200, 200, 255), pr, 2, 10); self.history_rects.append({'rect': pr, 'index': len(self.matched_tiles) - 2 - idx * 2, 'p1': (tx2, cy), 'p2': (tx1, cy)})
        if self.flying_scores:
            f_score = pygame.font.SysFont("Arial", 40, bold=True)
            for s in self.flying_scores:
                p = s['progress']; ease_p = 1.0 - (1.0 - p)**2; curr_x = s['pos'][0] + (s['target'][0] - s['pos'][0]) * ease_p; curr_y = s['pos'][1] + (s['target'][1] - s['pos'][1]) * ease_p
                # Color: Red for negative, Gold for positive
                val = s.get('score_value', 0)
                color = (255, 100, 100) if val < 0 else (255, 215, 0)
                txt_surf = f_score.render(s['text'], True, color); shadow_surf = f_score.render(s['text'], True, (0, 0, 0)); txt_rect = txt_surf.get_rect(center=(int(curr_x), int(curr_y))); self.screen.blit(shadow_surf, txt_rect.move(3, 3)); self.screen.blit(txt_surf, txt_rect)
        if not self.won and self.history_anim_state == 'idle' and self.shuffle_ui_state == 'closed':
            bw, bh, gap = 140, 35, 10; bx, by = 10, self.height - bh - 15
            f_btn = pygame.font.SysFont("Arial", 18, True); m_pos = pygame.mouse.get_pos()
            self.stats_btn_rect = pygame.Rect(bx, by, bw, bh); self.draw_button(self.screen, self.stats_btn_rect, "Statistiques", (0, 128, 128), f_btn, self.stats_btn_rect.collidepoint(m_pos), self.pressed_button == "stats")
            self.change_layout_btn_rect = pygame.Rect(bx + bw + gap, by, bw, bh); self.draw_button(self.screen, self.change_layout_btn_rect, "Niveau Suivant", (65, 105, 225), f_btn, self.change_layout_btn_rect.collidepoint(m_pos), self.pressed_button == "next_level")
            self.options_btn_rect = pygame.Rect(bx + (bw + gap) * 2, by, bw, bh); self.draw_button(self.screen, self.options_btn_rect, "Options", (199, 21, 133), f_btn, self.options_btn_rect.collidepoint(m_pos), self.pressed_button == "options")
            self.hint_btn_rect = pygame.Rect(bx, by - (bh + gap + 5), bw, bh); self.draw_button(self.screen, self.hint_btn_rect, "Indice", (138, 43, 226), f_btn, self.hint_btn_rect.collidepoint(m_pos), self.pressed_button == "hint")
            self.manual_shuffle_btn_rect = pygame.Rect(bx + bw + gap, by - (bh + gap + 5), bw, bh); self.draw_button(self.screen, self.manual_shuffle_btn_rect, "Mélanger", (255, 140, 0), f_btn, self.manual_shuffle_btn_rect.collidepoint(m_pos), self.pressed_button == "manual_shuffle")
            self.pause_btn_rect = pygame.Rect(bx + (bw + gap) * 2, by - (bh + gap + 5), bw, bh); pause_text = "Reprendre" if self.is_manual_paused else "Pause"; self.draw_button(self.screen, self.pause_btn_rect, pause_text, (218, 165, 32), f_btn, self.pause_btn_rect.collidepoint(m_pos), self.pressed_button == "pause")
        if self.shuffle_ui_progress > 0:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA); overlay.fill((0, 0, 0, int(180 * self.shuffle_ui_progress))); self.screen.blit(overlay, (0, 0))
            dw, dh = 400, 220; dialog_surf = pygame.Surface((dw, dh), pygame.SRCALPHA); pygame.draw.rect(dialog_surf, (40, 40, 45, 255), (0, 0, dw, dh), border_radius=20)
            # Gold border
            pygame.draw.rect(dialog_surf, (218, 165, 32, 255), (0, 0, dw, dh), 4, border_radius=20); f_title = pygame.font.SysFont("Arial", 26, True); f_msg = pygame.font.SysFont("Arial", 20); t1 = f_title.render("Plus de paires possibles !", True, (255, 255, 255)); t2 = f_msg.render("Voulez-vous mélanger les tuiles ?", True, (220, 220, 220)); dialog_surf.blit(t1, t1.get_rect(centerx=dw//2, centery=60)); dialog_surf.blit(t2, t2.get_rect(centerx=dw//2, centery=100)); bw, bh = 150, 45; btn1_rect = pygame.Rect(dw//2 - bw - 10, dh - bh - 35, bw, bh); btn2_rect = pygame.Rect(dw//2 + 10, dh - bh - 35, bw, bh); m_p = pygame.mouse.get_pos(); scale = 0.8 + 0.2 * self.shuffle_ui_progress; sw, sh = int(dw * scale), int(dh * scale); sx, sy = (self.width-sw)//2, (self.height-sh)//2; adj_m_p = ((m_p[0] - sx) / scale, (m_p[1] - sy) / scale); h1 = btn1_rect.collidepoint(adj_m_p) if self.shuffle_ui_state == 'open' else False; h2 = btn2_rect.collidepoint(adj_m_p) if self.shuffle_ui_state == 'open' else False; self.draw_button(dialog_surf, btn1_rect, "Mélanger", (36, 119, 77), f_msg, h1, self.pressed_button == "shuffle_confirm"); self.draw_button(dialog_surf, btn2_rect, "Annuler", (148, 24, 24), f_msg, h2, self.pressed_button == "shuffle_cancel"); self.shuffle_confirm_btn = pygame.Rect(sx + btn1_rect.x * scale, sy + btn1_rect.y * scale, btn1_rect.w * scale, btn1_rect.h * scale); self.shuffle_cancel_btn = pygame.Rect(sx + btn2_rect.x * scale, sy + btn2_rect.y * scale, btn2_rect.w * scale, btn2_rect.h * scale); scaled_dialog = pygame.transform.smoothscale(dialog_surf, (sw, sh))
            if self.shuffle_ui_progress < 1.0: scaled_dialog.set_alpha(int(255 * self.shuffle_ui_progress))
            self.screen.blit(scaled_dialog, (sx, sy))
        if self.stats_ui_progress > 0: self.draw_stats_ui()
        if self.options_ui_progress > 0: self.draw_options_ui()
        pygame.display.flip()

    def sort_stats(self, column):
        if self.stats_sort_col == column: self.stats_sort_reverse = not self.stats_sort_reverse
        else: self.stats_sort_col, self.stats_sort_reverse = column, False
        def sort_key(idx):
            name, stats = self.layout_names[idx], self.level_stats.get(self.layout_names[idx], {})
            if column == "Niveau": return self.normalize_string(name)
            elif column == "T. Min": val = stats.get("best_time", 999999999); return val if val is not None else 999999999
            elif column == "T. Moy.":
                tt = stats.get("total_time", stats.get("best_time"))
                if tt is not None: tc = max(1, stats.get("times_completed", 1)); return tt / tc
                return 999999999
            elif column == "Mél. Min": val = stats.get("best_shuffles", 999); return val if val is not None else 999
            elif column == "Victoires": return stats.get("times_completed", 0)
            elif column == "Score": return stats.get("best_score", 0)
            return 0
        self.stats_display_indices.sort(key=sort_key, reverse=self.stats_sort_reverse)

    def draw_button(self, surface, rect, text, base_color, font, is_hover, is_pressed, border_radius=10):
        off = 4; shadow_color = [max(0, int(c * 0.7)) for c in base_color]
        if not is_pressed: pygame.draw.rect(surface, shadow_color, (rect.x + off, rect.y + off, rect.w, rect.h), border_radius=border_radius)
        btn_rect = rect.copy()
        if is_pressed: btn_rect.x += off; btn_rect.y += off
        draw_color = [min(255, c + 30) for c in base_color] if is_hover else base_color
        pygame.draw.rect(surface, draw_color, btn_rect, border_radius=border_radius)
        if not is_pressed: light_color = [min(255, c + 50) for c in draw_color]; pygame.draw.rect(surface, light_color, btn_rect, width=1, border_radius=border_radius)
        txt_surf = font.render(text, True, (255, 255, 255)); txt_rect = txt_surf.get_rect(center=btn_rect.center); surface.blit(txt_surf, txt_rect)

    def draw_stats_ui(self):
        ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA); ov.fill((0, 0, 0, int(200 * self.stats_ui_progress))); self.screen.blit(ov, (0, 0))
        sw, sh = 800, 600; scale = 0.8 + 0.2 * self.stats_ui_progress; dsw, dsh = int(sw * scale), int(sh * scale); sx, sy = (self.width - dsw) // 2, (self.height - dsh) // 2; m_pos = pygame.mouse.get_pos(); adj_m_pos = ((m_pos[0] - sx) / scale, (m_pos[1] - sy) / scale); stats_surf = pygame.Surface((sw, sh), pygame.SRCALPHA); pygame.draw.rect(stats_surf, (30, 30, 35, 255), (0, 0, sw, sh), border_radius=20)
        # Gold border
        pygame.draw.rect(stats_surf, (218, 165, 32, 255), (0, 0, sw, sh), 4, border_radius=20)
        f_title, f_header, f_row, f_arrow_icon = pygame.font.SysFont("Arial", 32, True), pygame.font.SysFont("Arial", 18, True), pygame.font.SysFont("Arial", 15), pygame.font.SysFont("Arial", 12, True); t_title = f_title.render("Statistiques par Niveau", True, (255, 255, 255)); stats_surf.blit(t_title, t_title.get_rect(centerx=sw//2, y=30)); hy = 90
        header_configs = [("Aperçu", 40, 100, None), ("Niveau", 180, 180, "Niveau"), ("T. Min", 380, 80, "T. Min"), ("Mél.", 480, 70, "Mél. Min"), ("Victoires", 570, 90, "Victoires"), ("Score", 680, 100, "Score")]; self.stats_header_rects = []
        for text, h_x, h_w, col_id in header_configs:
            color = (200, 200, 255) if self.stats_sort_col == col_id else (150, 150, 150); t_surf = f_header.render(text, True, color); stats_surf.blit(t_surf, (h_x, hy))
            if col_id and self.stats_sort_col == col_id: arrow_char = "▲" if not self.stats_sort_reverse else "▼"; a_surf = f_arrow_icon.render(arrow_char, True, color); stats_surf.blit(a_surf, (h_x + t_surf.get_width() + 4, hy + 4))
            if col_id: h_rect = pygame.Rect(sx + h_x * scale, sy + hy * scale, h_w * scale, 35 * scale); self.stats_header_rects.append({'rect': h_rect, 'column': col_id})
        pygame.draw.line(stats_surf, (100, 100, 100), (40, hy+30), (sw-40, hy+30), 1); row_h, clip_rect = 80, pygame.Rect(40, hy + 40, sw - 80, sh - hy - 100); content_h = len(self.layout_names) * row_h; self.stats_rows_rects = []; rows_view = pygame.Surface((clip_rect.width, clip_rect.height), pygame.SRCALPHA); start_idx, end_idx = max(0, self.stats_scroll_y // row_h), min(len(self.layout_names), (self.stats_scroll_y + clip_rect.height) // row_h + 1)
        for display_idx in range(start_idx, end_idx):
            i = self.stats_display_indices[display_idx]; name, ry = self.layout_names[i], display_idx * row_h - self.stats_scroll_y; preview, pw_icon = self.level_previews.get(name), 100
            final_y, final_h = 0, 0
            if preview:
                rows_view.blit(preview, (0, ry)); pw_icon = preview.get_width()
                ix, iy, iw, ih = sx + (clip_rect.x + 0) * scale, sy + (clip_rect.y + ry) * scale, pw_icon * scale, 80 * scale; g_clip_top, g_clip_bottom = sy + clip_rect.y * scale, sy + (clip_rect.y + clip_rect.height) * scale; final_y, final_h = max(iy, g_clip_top), min(iy + ih, g_clip_bottom) - final_y
            if final_h > 0: self.stats_rows_rects.append({'rect': pygame.Rect(ix, final_y, iw, final_h), 'level_index': i})
            rows_view.blit(f_row.render(name, True, (220, 220, 220)), (140, ry + 30))
            s = self.level_stats.get(name)
            if s:
                bt = s.get("best_time")
                time_str = f"{(bt//1000)//60:02}:{(bt//1000)%60:02}" if bt and 0 < bt < 999999999 else "--:--"
                t_surf = f_row.render(time_str, True, (0, 255, 127)); rows_view.blit(t_surf, (340 + (80 - t_surf.get_width()) // 2, ry + 30))
                bs_surf = f_row.render(str(s.get("best_shuffles", 0)), True, (255, 165, 0)); rows_view.blit(bs_surf, (440 + (70 - bs_surf.get_width()) // 2, ry + 30))
                tc_surf = f_row.render(str(s.get("times_completed", 0)), True, (100, 200, 255)); rows_view.blit(tc_surf, (530 + (90 - tc_surf.get_width()) // 2, ry + 30))
                sc_surf = f_row.render(str(s.get("best_score") or 0), True, (255, 215, 0)); rows_view.blit(sc_surf, (630 + (100 - sc_surf.get_width()) // 2, ry + 30))
            else:
                t_surf = f_row.render("--:--", True, (100, 100, 100)); rows_view.blit(t_surf, (340 + (80 - t_surf.get_width()) // 2, ry + 30))
                bs_surf = f_row.render("-", True, (100, 100, 100)); rows_view.blit(bs_surf, (440 + (70 - bs_surf.get_width()) // 2, ry + 30))
                tc_surf = f_row.render("0", True, (100, 100, 100)); rows_view.blit(tc_surf, (530 + (90 - tc_surf.get_width()) // 2, ry + 30))
                sc_surf = f_row.render("0", True, (100, 100, 100)); rows_view.blit(sc_surf, (630 + (100 - sc_surf.get_width()) // 2, ry + 30))
        stats_surf.blit(rows_view, clip_rect.topleft)
        if content_h > clip_rect.height:
            pygame.draw.rect(stats_surf, (50, 50, 60), (sw - 37, clip_rect.y, 12, clip_rect.height), border_radius=6); sb_h = max(30, int(clip_rect.height * (clip_rect.height / content_h))); sb_y = clip_rect.y + int((self.stats_scroll_y / (content_h - clip_rect.height)) * (clip_rect.height - sb_h)); pygame.draw.rect(stats_surf, (120, 120, 140), (sw - 37, sb_y, 12, sb_h), border_radius=6); self.stats_scrollbar_rect_global = pygame.Rect(sx + (sw - 45) * scale, sy + clip_rect.y * scale, 30 * scale, clip_rect.height * scale)
        else: self.stats_scrollbar_rect_global = None
        self.stats_close_btn = pygame.Rect(sw//2 - 60, sh - 50, 120, 35); is_hover = self.stats_close_btn.collidepoint(adj_m_pos); self.draw_button(stats_surf, self.stats_close_btn, "Fermer", (150, 50, 50), f_row, is_hover, self.pressed_button == "stats_close"); self.stats_close_btn_global = pygame.Rect(sx + self.stats_close_btn.x * scale, sy + self.stats_close_btn.y * scale, self.stats_close_btn.w * scale, self.stats_close_btn.h * scale); scaled_surf = pygame.transform.smoothscale(stats_surf, (dsw, dsh))
        if self.stats_ui_progress < 1.0: scaled_surf.set_alpha(int(255 * self.stats_ui_progress))
        self.screen.blit(scaled_surf, (sx, sy))

    def draw_options_ui(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA); overlay.fill((0, 0, 0, int(180 * self.options_ui_progress))); self.screen.blit(overlay, (0, 0)); sw, sh, scale = 700, 700, 0.8 + 0.2 * self.options_ui_progress; w, h = int(sw * scale), int(sh * scale); x, y = (self.width - w) // 2, (self.height - h) // 2; panel = pygame.Surface((sw, sh), pygame.SRCALPHA); pygame.draw.rect(panel, (30, 30, 35, 255), (0, 0, sw, sh), border_radius=20)
        # Gold border
        pygame.draw.rect(panel, (218, 165, 32, 255), (0, 0, sw, sh), 4, border_radius=20)
        f_title, f_msg = pygame.font.SysFont("Arial", 32, True), pygame.font.SysFont("Arial", 22); title_surf = f_title.render("Options", True, (255, 255, 255)); panel.blit(title_surf, title_surf.get_rect(centerx=sw//2, y=30)); m_pos = pygame.mouse.get_pos(); adj_m_pos = ((m_pos[0] - x) / scale, (m_pos[1] - y) / scale); start_y, spacing = 110, 80
        opt_configs = [("Ombrage des tuiles bloquées :", 'show_gray_tiles', 'toggle_gray_rect'), ("Afficher le nombre de victoires :", 'show_win_count', 'toggle_wins_rect'), ("Afficher le nombre de mélanges min :", 'show_best_shuffles', 'toggle_best_sh_rect'), ("Indice automatique :", 'auto_hint', 'toggle_hint_rect')]
        for i, (txt, attr, rect_name) in enumerate(opt_configs):
            oy = start_y + i * spacing; label = f_msg.render(txt, True, (220, 220, 220)); panel.blit(label, (50, oy)); rect = pygame.Rect(sw - 130, oy - 5, 80, 34); setattr(self, rect_name, rect); val = getattr(self, attr); t_color = (46, 139, 87) if val else (100, 100, 110)
            if rect.collidepoint(adj_m_pos): t_color = tuple(min(255, c + 20) for c in t_color)
            pygame.draw.rect(panel, t_color, rect, border_radius=17); circle_x = rect.x + (60 if val else 20); pygame.draw.circle(panel, (255, 255, 255), (circle_x, rect.centery), 13); setattr(self, rect_name + '_global', pygame.Rect(x + rect.x * scale, y + rect.y * scale, rect.w * scale, rect.h * scale))
        opt_y = start_y + len(opt_configs) * spacing; slider_w, slider_h = 250, 10
        vol_configs = [("Volume de la musique :", 'music_volume', 'music_slider_rect', 'music_knob_rect'), ("Volume des effets :", 'sfx_volume', 'sfx_slider_rect', 'sfx_knob_rect')]
        for txt, attr, s_rect_name, k_rect_name in vol_configs:
            label = f_msg.render(txt, True, (220, 220, 220)); panel.blit(label, (50, opt_y)); s_rect = pygame.Rect(sw - 300, opt_y + 10, slider_w, slider_h); setattr(self, s_rect_name, s_rect); pygame.draw.rect(panel, (60, 60, 70), s_rect, border_radius=5); val = getattr(self, attr); active_w = int(slider_w * val); pygame.draw.rect(panel, (46, 139, 87), (s_rect.x, s_rect.y, active_w, slider_h), border_radius=5); knob_x = s_rect.x + active_w; k_rect = pygame.Rect(knob_x - 10, s_rect.y - 10, 20, 30); setattr(self, k_rect_name, k_rect); k_color = (200, 200, 200) if k_rect.collidepoint(adj_m_pos) else (160, 160, 160); pygame.draw.rect(panel, k_color, k_rect, border_radius=5); setattr(self, s_rect_name + '_global', pygame.Rect(x + s_rect.x * scale, y + s_rect.y * scale, s_rect.w * scale, s_rect.h * scale)); opt_y += spacing
        self.options_close_btn = pygame.Rect((sw - 140) // 2, sh - 75, 140, 45); is_h = self.options_close_btn.collidepoint(adj_m_pos); self.draw_button(panel, self.options_close_btn, "Fermer", (150, 50, 50), f_msg, is_h, self.pressed_button == "options_close"); self.options_close_btn_global = pygame.Rect(x + self.options_close_btn.x * scale, y + self.options_close_btn.y * scale, self.options_close_btn.w * scale, self.options_close_btn.h * scale); scaled_panel = pygame.transform.smoothscale(panel, (w, h))
        if self.options_ui_progress < 1.0: scaled_panel.set_alpha(int(255 * self.options_ui_progress))
        self.screen.blit(scaled_panel, (x, y))

    def handle_click(self, pos, button=1):
        if button in (4, 5): return
        if self.win_ui_state == 'open' and hasattr(self, 'win_btn_rects'):
            for b in self.win_btn_rects:
                if b['rect'].collidepoint(pos): self.play_click_sfx(); self.win_pressed_btn = b['id']; return
            return
        if self.options_ui_state == 'open':
            for r in ['toggle_gray_rect_global', 'toggle_wins_rect_global', 'toggle_best_sh_rect_global', 'toggle_hint_rect_global']:
                if hasattr(self, r) and getattr(self, r).collidepoint(pos):
                    self.play_click_sfx()
                    if 'gray' in r: self.show_gray_tiles = not self.show_gray_tiles; self.update_sorted_layout()
                    elif 'wins' in r: self.show_win_count = not self.show_win_count
                    elif 'best_sh' in r: self.show_best_shuffles = not self.show_best_shuffles
                    elif 'hint' in r: self.auto_hint = not self.auto_hint
                    return
            if hasattr(self, 'music_slider_rect_global') and self.music_slider_rect_global.inflate(20, 40).collidepoint(pos): self.play_click_sfx(); self.music_dragging_slider = True; return
            if hasattr(self, 'sfx_slider_rect_global') and self.sfx_slider_rect_global.inflate(20, 40).collidepoint(pos): self.play_click_sfx(); self.sfx_dragging_slider = True; return
            if hasattr(self, 'options_close_btn_global') and self.options_close_btn_global.collidepoint(pos): self.play_click_sfx(); self.pressed_button = "options_close"; return
            return
        if self.stats_ui_state == 'open':
            if hasattr(self, 'stats_scrollbar_rect_global') and self.stats_scrollbar_rect_global and self.stats_scrollbar_rect_global.collidepoint(pos): self.play_click_sfx(); self.stats_dragging_scrollbar = True; return
            if hasattr(self, 'stats_header_rects'):
                for h in self.stats_header_rects:
                    if h['rect'].collidepoint(pos): self.play_click_sfx(); self.sort_stats(h['column']); return
            if hasattr(self, 'stats_rows_rects'):
                for row in self.stats_rows_rects:
                    if row['rect'].collidepoint(pos): self.play_click_sfx(); self.pending_level_idx, self.stats_ui_state = row['level_index'], 'closing'; return
            if hasattr(self, 'stats_close_btn_global') and self.stats_close_btn_global.collidepoint(pos): self.play_click_sfx(); self.pressed_button = "stats_close"; return
            return
        if self.show_history and self.history_anim_state == 'idle':
            if hasattr(self,'history_rects'):
                for it in self.history_rects:
                    if it['rect'].collidepoint(pos):
                        self.play_click_sfx(); tr = self.matched_tiles[it['index']:]; rd = [{'tile':tr[0],'start_pos':it['p1']},{'tile':tr[1],'start_pos':it['p2']}]
                        for i in range(2,len(tr)): rd.append({'tile':tr[i],'start_pos':(self.width-100,self.height-100)})
                        self.matched_tiles = self.matched_tiles[:it['index']]; self.start_undo_animation(rd); self.show_history, self.history_anim_state, self.history_anim_progress = False, 'idle', 0.0; return
            self.play_click_sfx(); self.history_anim_state = 'closing'; return
        pw, ph = self.tw * 2 + 15, self.th + 10; pile_area = pygame.Rect(self.width - pw - 25, self.height - ph - 15, pw, ph)
        if pile_area.collidepoint(pos) and self.matched_tiles and not self.animating_tiles: self.play_click_sfx(); self.show_history, self.history_anim_state = True, 'opening'; return
        if self.shuffle_ui_state == 'open':
            if hasattr(self, 'shuffle_confirm_btn') and self.shuffle_confirm_btn.collidepoint(pos): self.play_click_sfx(); self.pressed_button = "shuffle_confirm"
            elif hasattr(self, 'shuffle_cancel_btn') and self.shuffle_cancel_btn.collidepoint(pos): self.play_click_sfx(); self.pressed_button = "shuffle_cancel"; return
        if getattr(self, 'is_manual_paused', False):
            if hasattr(self,'pause_btn_rect') and self.pause_btn_rect.collidepoint(pos): self.play_click_sfx(); self.pressed_button = "pause"
            return
        if not self.won and self.history_anim_state == 'idle':
            for r, b in [('stats_btn_rect', "stats"), ('options_btn_rect', "options"), ('change_layout_btn_rect', "next_level"), ('manual_shuffle_btn_rect', "manual_shuffle"), ('pause_btn_rect', "pause"), ('hint_btn_rect', "hint")]:
                if hasattr(self, r) and getattr(self, r).collidepoint(pos): self.play_click_sfx(); self.pressed_button = b; return
        for t in reversed(self.sorted_layout):
            if t['rect'] and t['rect'].collidepoint(pos) and t.get('free', False):
                self.play_click_sfx()
                if self.hint_pair and t in self.hint_pair:
                    t1, t2 = self.hint_pair; self.start_match_animation(t1, t2); self.selected, self.hint_pair, self.last_move_time = None, None, pygame.time.get_ticks(); self.last_match_time = pygame.time.get_ticks(); self.match_multiplier = 1.0
                    if not self.layout: self.won = True
                    elif not self.has_moves(): self.shuffle_needed = True
                    return
                self.last_move_time, self.hint_pair = pygame.time.get_ticks(), None
                if self.selected:
                    if self.selected == t: self.selected = None
                    elif self.are_compatible(self.selected['type'], t['type']):
                        now = pygame.time.get_ticks(); diff = (now - self.last_match_time) / 1000.0; base_points = 1000 if diff <= 4.0 else int(1000 - (diff - 4.0) * 90) if diff <= 14.0 else 100
                        move_score = int(base_points * self.score_scaling)
                        self.last_match_time = now
                        if t['rect']:
                            start_x, start_y = t['rect'].center; f_t = pygame.font.SysFont("Arial", 24, bold=True); tx = 20 + f_t.size("Score : ")[0] + f_t.size(str(self.displayed_score))[0] // 2; ty = 25 + f_t.get_height() + f_t.get_height() // 2
                            self.flying_scores.append({'pos': [start_x, start_y], 'target': (tx, ty), 'text': f"+{move_score}", 'score_value': move_score, 'progress': 0.0})
                        self.start_match_animation(self.selected, t); self.selected = None
                        if not self.layout: self.won = True
                        elif not self.has_moves(): self.shuffle_needed = True
                    else: self.selected = t
                else: self.selected = t
                return

    def handle_release(self, pos):
        self.stats_dragging_scrollbar = False; self.music_dragging_slider = False; self.sfx_dragging_slider = False
        if not self.pressed_button:
            if self.win_pressed_btn:
                btn_id = self.win_pressed_btn; self.win_pressed_btn = None
                if hasattr(self, 'win_btn_rects'):
                    for b in self.win_btn_rects:
                        if b['id'] == btn_id and b['rect'].collidepoint(pos):
                            if btn_id == 'random': self.next_level_to_load = None
                            elif btn_id == 'choose': self.open_stats_after_win = True
                            self.win_ui_state, self.victory_anim_state, self.drain_start_time = 'closing', 'draining', pygame.time.get_ticks(); return
            return
        pb = self.pressed_button; self.pressed_button = None
        if pb == "options_close" and hasattr(self, 'options_close_btn_global') and self.options_close_btn_global.collidepoint(pos): self.options_ui_state = 'closing'
        elif pb == "stats_close" and hasattr(self, 'stats_close_btn_global') and self.stats_close_btn_global.collidepoint(pos): self.pending_level_idx, self.stats_ui_state = None, 'closing'
        elif pb == "shuffle_confirm" and hasattr(self, 'shuffle_confirm_btn') and self.shuffle_confirm_btn.collidepoint(pos): self.shuffle_confirmed, self.shuffle_ui_state = True, 'closing'
        elif pb == "shuffle_cancel" and hasattr(self, 'shuffle_cancel_btn') and self.shuffle_cancel_btn.collidepoint(pos): self.shuffle_confirmed, self.shuffle_ui_state = False, 'closing'
        elif pb == "stats" and hasattr(self, 'stats_btn_rect') and self.stats_btn_rect.collidepoint(pos):
            if not self.is_paused: self.pause_start_ticks = pygame.time.get_ticks()
            self.stats_ui_state, self.stats_scroll_y, self.stats_sort_col, self.stats_sort_reverse, self.stats_display_indices = 'opening', 0, None, False, list(range(len(self.layout_names)))
        elif pb == "options" and hasattr(self, 'options_btn_rect') and self.options_btn_rect.collidepoint(pos):
            if not self.is_paused: self.pause_start_ticks = pygame.time.get_ticks()
            self.options_ui_state = 'opening'
        elif pb == "next_level" and hasattr(self, 'change_layout_btn_rect') and self.change_layout_btn_rect.collidepoint(pos): self.reset_game(None)
        elif pb == "manual_shuffle" and hasattr(self, 'manual_shuffle_btn_rect') and self.manual_shuffle_btn_rect.collidepoint(pos):
            self.start_shuffle_animation(self.manual_shuffle_btn_rect.center)
        elif pb == "pause" and hasattr(self, 'pause_btn_rect') and self.pause_btn_rect.collidepoint(pos):
            if not self.is_manual_paused:
                if not self.is_paused: self.pause_start_ticks = pygame.time.get_ticks()
                self.is_manual_paused, self.last_move_time = True, pygame.time.get_ticks()
            else:
                self.is_manual_paused = False
                if not self.is_paused: paused_duration = pygame.time.get_ticks() - self.pause_start_ticks; self.adjust_times_after_pause(paused_duration)
        elif pb == "hint" and hasattr(self, 'hint_btn_rect') and self.hint_btn_rect.collidepoint(pos):
            hint = self.get_hint()
            if hint:
                penalty = 500
                # Add negative flying score
                f_t = pygame.font.SysFont("Arial", 24, bold=True)
                target_x = 20 + f_t.size("Score : ")[0] + f_t.size(str(self.displayed_score))[0] // 2
                target_y = 25 + f_t.get_height() + f_t.get_height() // 2
                start_x, start_y = self.hint_btn_rect.center
                self.flying_scores.append({
                    'pos': [start_x, start_y],
                    'target': (target_x, target_y),
                    'text': f"-{penalty}",
                    'score_value': -penalty,
                    'progress': 0.0
                })
                self.hint_pair, self.last_move_time = hint, pygame.time.get_ticks()

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: self.save_stats(); pygame.quit(); sys.exit()
                if e.type == pygame.VIDEORESIZE: self.width, self.height = e.w, e.h; self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE); self.recompute_scaling()
                if e.type == pygame.WINDOWFOCUSLOST:
                    if not self.won and not self.is_paused: self.pause_start_ticks = pygame.time.get_ticks()
                    if not self.won: self.is_paused_by_focus = True
                if e.type == pygame.WINDOWFOCUSGAINED and self.is_paused_by_focus:
                    self.is_paused_by_focus = False
                    if not self.is_paused: paused_duration = pygame.time.get_ticks() - self.pause_start_ticks; self.adjust_times_after_pause(paused_duration)
                if self.is_paused_by_focus: continue
                if e.type == pygame.MOUSEBUTTONDOWN: self.handle_click(e.pos, e.button)
                if e.type == pygame.MOUSEBUTTONUP: self.handle_release(e.pos)
                if e.type == pygame.MOUSEWHEEL and self.stats_ui_state == 'open': self.stats_scroll_y = max(0, min(self.stats_scroll_y - e.y * 80, max(0, len(self.layout_names) * 80 - 410)))
                if e.type == self.MUSIC_END: self.play_next_music()
            if self.stats_ui_state == 'open' and getattr(self, 'stats_dragging_scrollbar', False):
                m_pos, sw, sh, scale = pygame.mouse.get_pos(), 800, 600, 0.8 + 0.2 * self.stats_ui_progress
                sx, sy = (self.width - int(sw * scale)) // 2, (self.height - int(sh * scale)) // 2; clip_y, clip_h, content_h = sy + 130 * scale, 410 * scale, len(self.layout_names) * 80
                if content_h > 410: self.stats_scroll_y = max(0, min(int(((m_pos[1] - clip_y) / clip_h) * content_h), content_h - 410))
            if self.options_ui_state == 'open':
                m_pos = pygame.mouse.get_pos()
                if getattr(self, 'music_dragging_slider', False) and hasattr(self, 'music_slider_rect_global'):
                    s = self.music_slider_rect_global; self.music_volume = max(0.0, min(1.0, (m_pos[0] - s.x) / float(s.w))); pygame.mixer.music.set_volume(self.music_volume)
                    if self.music_volume <= 0: pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                        if not pygame.mixer.music.get_busy(): self.play_next_music()
                if getattr(self, 'sfx_dragging_slider', False) and hasattr(self, 'sfx_slider_rect_global'):
                    s = self.sfx_slider_rect_global; self.sfx_volume = max(0.0, min(1.0, (m_pos[0] - s.x) / float(s.w)))
                    if self.click_sound: self.click_sound.set_volume(self.sfx_volume)
            self.draw(); self.clock.tick(60)

if __name__ == "__main__": MahjongGame().run()
