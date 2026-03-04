        elif not self.won and not self.hint_pair and pygame.time.get_ticks()-self.last_move_time>30000: self.hint_pair = self.get_hint()
        pygame.display.flip()

    def handle_click(self, pos):
        if self.won:
            if hasattr(self,'play_again_btn_rect') and self.play_again_btn_rect.collidepoint(pos):
                self.play_again_pressed = True
            return
        if self.show_history:
            if hasattr(self,'history_rects'):
                for it in self.history_rects:
                    if it['rect'].collidepoint(pos):
                        tr = self.matched_tiles[it['index']:]; rd = [{'tile':tr[0],'start_pos':it['p1']},{'tile':tr[1],'start_pos':it['p2']}]
                        for i in range(2,len(tr)): rd.append({'tile':tr[i],'start_pos':(self.width-100,self.height-100)})
                        self.matched_tiles = self.matched_tiles[:it['index']]; self.start_undo_animation(rd); self.show_history, self.history_anim_state, self.history_anim_progress = False, 'idle', 0.0; return
            self.history_anim_state = 'closing'; return
        
        # Détection dynamique de la zone des piles (bas droite)
        pw = self.tw * 2 + 15
        ph = self.th + 10
        pile_area = pygame.Rect(self.width - pw - 25, self.height - ph - 15, pw, ph)
        if pile_area.collidepoint(pos) and self.matched_tiles and not self.animating_tiles: 
            self.show_history, self.history_anim_state = True, 'opening'
            return
            
        if self.shuffle_needed and self.shuffle_anim_state == 'idle' and hasattr(self,'shuffle_btn_rect') and self.shuffle_btn_rect.collidepoint(pos): self.start_shuffle_animation(); return
        if not self.won and self.history_anim_state == 'idle':
            if hasattr(self,'change_layout_btn_rect') and self.change_layout_btn_rect.collidepoint(pos): self.reset_game(); return
            if hasattr(self,'manual_shuffle_btn_rect') and self.manual_shuffle_btn_rect.collidepoint(pos): self.start_shuffle_animation(); return
            if hasattr(self,'hint_btn_rect') and self.hint_btn_rect.collidepoint(pos): self.hint_pair, self.last_move_time = self.get_hint(), pygame.time.get_ticks(); return
        
        sl = sorted(self.layout, key=lambda t: (t['pos'][2], t['pos'][1], t['pos'][0]), reverse=True)
        for t in sl:
            if t['rect'] and t['rect'].collidepoint(pos) and self.is_free(t):
                if self.hint_pair and t in self.hint_pair:
                    t1, t2 = self.hint_pair; self.start_match_animation(t1, t2); self.selected, self.hint_pair = None, None
                    self.last_move_time = pygame.time.get_ticks()
                    if not self.layout: self.won, self.final_time = True, pygame.time.get_ticks()-self.start_ticks
                    elif not self.has_moves(): self.shuffle_needed = True
                    return
                self.last_move_time, self.hint_pair = pygame.time.get_ticks(), None
                if self.selected:
                    if self.selected == t: self.selected = None
                    elif self.are_compatible(self.selected['type'], t['type']):
                        self.start_match_animation(self.selected, t); self.selected = None
                        if not self.layout: self.won, self.final_time = True, pygame.time.get_ticks()-self.start_ticks
                        elif not self.has_moves(): self.shuffle_needed = True
                    else: self.selected = t
                else: self.selected = t
                return

    def handle_release(self, pos):
        if self.play_again_pressed:
            self.play_again_pressed = False
            if hasattr(self, 'play_again_btn_rect') and self.play_again_btn_rect.collidepoint(pos):
                self._do_reset()
                self.level_anim_state = 'in'
                self.level_anim_progress = 0.0

    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.VIDEORESIZE:
                    self.width, self.height = e.w, e.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    self.recompute_scaling()
                if e.type == pygame.MOUSEBUTTONDOWN: self.handle_click(e.pos)
                if e.type == pygame.MOUSEBUTTONUP: self.handle_release(e.pos)
            self.draw(); self.clock.tick(60)

if __name__ == "__main__": MahjongGame().run()
