    def draw_stats_ui(self):
        # Dark overlay
        ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ov.fill((0, 0, 0, int(200 * self.stats_ui_progress)))
        self.screen.blit(ov, (0, 0))

        sw, sh = 800, 600
        scale = 0.8 + 0.2 * self.stats_ui_progress
        dsw, dsh = int(sw * scale), int(sh * scale)
        sx, sy = (self.width - dsw) // 2, (self.height - dsh) // 2

        stats_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(stats_surf, (30, 30, 35, 255), (0, 0, sw, sh), border_radius=20)
        pygame.draw.rect(stats_surf, (200, 200, 220, 255), (0, 0, sw, sh), 3, border_radius=20)

        f_title = pygame.font.SysFont("Arial", 32, True)
        f_header = pygame.font.SysFont("Arial", 22, True)
        f_row = pygame.font.SysFont("Arial", 18)

        t_title = f_title.render("Statistiques par Niveau", True, (255, 255, 255))
        stats_surf.blit(t_title, t_title.get_rect(centerx=sw//2, y=30))

        # Headers
        hy = 90
        stats_surf.blit(f_header.render("Aper\u00e7u", True, (150, 150, 150)), (50, hy))
        stats_surf.blit(f_header.render("Niveau", True, (150, 150, 150)), (200, hy))
        stats_surf.blit(f_header.render("T. Min", True, (150, 150, 150)), (360, hy))
        stats_surf.blit(f_header.render("T. Moy.", True, (150, 150, 150)), (460, hy))
        stats_surf.blit(f_header.render("M\u00e9l. Min", True, (150, 150, 150)), (560, hy))
        stats_surf.blit(f_header.render("Victoires", True, (150, 150, 150)), (680, hy))

        pygame.draw.line(stats_surf, (100, 100, 100), (40, hy+30), (sw-40, hy+30), 1)

        # Scrollable area
        row_h = 140
        clip_rect = pygame.Rect(40, hy + 40, sw - 80, sh - hy - 100)
        content_h = len(self.layout_names) * row_h
        
        self.stats_rows_rects = []
        
        # Create a surface for the scrollable view
        rows_view = pygame.Surface((clip_rect.width, clip_rect.height), pygame.SRCALPHA)
        
        start_idx = max(0, self.stats_scroll_y // row_h)
        end_idx = min(len(self.layout_names), (self.stats_scroll_y + clip_rect.height) // row_h + 1)

        for i in range(start_idx, end_idx):
            name = self.layout_names[i]
            ry = i * row_h - self.stats_scroll_y
            
            # Background for alternate rows
            if i % 2 == 0:
                pygame.draw.rect(rows_view, (255, 255, 255, 10), (0, ry, clip_rect.width, row_h))
            
            # Draw preview
            preview = self.level_previews.get(name)
            pw_icon = 192
            if preview:
                rows_view.blit(preview, (5, ry + 6))
                pw_icon = preview.get_width()
            
            # Collision detection (Global coords)
            ix = sx + (clip_rect.x + 5) * scale
            iy = sy + (clip_rect.y + ry + 6) * scale
            iw = pw_icon * scale
            ih = 128 * scale
            g_clip_top = sy + clip_rect.y * scale
            g_clip_bottom = sy + (clip_rect.y + clip_rect.height) * scale
            final_y = max(iy, g_clip_top)
            final_h = min(iy + ih, g_clip_bottom) - final_y
            if final_h > 0:
                self.stats_rows_rects.append({'rect': pygame.Rect(ix, final_y, iw, final_h), 'level_index': i})
            
            rows_view.blit(f_row.render(name, True, (220, 220, 220)), (max(160, pw_icon + 15), ry + 60))
            
            s = self.level_stats.get(name)
            if s:
                bt = s.get("best_time", 0) // 1000
                time_str = f"{bt//60:02}:{bt%60:02}"
                t_surf = f_row.render(time_str, True, (0, 255, 127))
                rows_view.blit(t_surf, (320 + (60 - t_surf.get_width()) // 2, ry + 60))
                
                tc = max(1, s.get("times_completed", 1))
                tt = s.get("total_time", s.get("best_time", 0))
                avg_t = (tt // tc) // 1000
                avg_str = f"{avg_t//60:02}:{avg_t%60:02}"
                avg_surf = f_row.render(avg_str, True, (200, 255, 200))
                rows_view.blit(avg_surf, (420 + (70 - avg_surf.get_width()) // 2, ry + 60))

                rows_view.blit(f_row.render(str(s.get("best_shuffles", 0)), True, (255, 165, 0)), (520 + 30, ry + 60))
                rows_view.blit(f_row.render(str(s.get("times_completed", 0)), True, (100, 200, 255)), (640 + 20, ry + 60))
            else:
                t_surf = f_row.render("--:--", True, (100, 100, 100))
                rows_view.blit(t_surf, (320 + (60 - t_surf.get_width()) // 2, ry + 60))
                avg_surf = f_row.render("--:--", True, (100, 100, 100))
                rows_view.blit(avg_surf, (420 + (70 - avg_surf.get_width()) // 2, ry + 60))
                rows_view.blit(f_row.render("-", True, (100, 100, 100)), (520 + 30, ry + 60))
                rows_view.blit(f_row.render("0", True, (100, 100, 100)), (640 + 20, ry + 60))

        stats_surf.blit(rows_view, clip_rect.topleft)

        # Scrollbar (simple)
        if content_h > clip_rect.height:
            sb_h = int(clip_rect.height * (clip_rect.height / content_h))
            sb_y = clip_rect.y + int((self.stats_scroll_y / (content_h - clip_rect.height)) * (clip_rect.height - sb_h))
            pygame.draw.rect(stats_surf, (80, 80, 90), (sw - 35, sb_y, 8, sb_h), border_radius=4)

        # Close button
        self.stats_close_btn = pygame.Rect(sw//2 - 60, sh - 50, 120, 35)
        pygame.draw.rect(stats_surf, (150, 50, 50), self.stats_close_btn, border_radius=10)
        ct = f_row.render("Fermer", True, (255, 255, 255))
        stats_surf.blit(ct, ct.get_rect(center=self.stats_close_btn.center))
        
        self.stats_close_btn_global = pygame.Rect(sx + self.stats_close_btn.x * scale, sy + self.stats_close_btn.y * scale, self.stats_close_btn.w * scale, self.stats_close_btn.h * scale)

        scaled_surf = pygame.transform.smoothscale(stats_surf, (dsw, dsh))
        if self.stats_ui_progress < 1.0: scaled_surf.set_alpha(int(255 * self.stats_ui_progress))
        self.screen.blit(scaled_surf, (sx, sy))
