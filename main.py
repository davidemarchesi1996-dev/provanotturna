import pygame
import random
import sys
import math
import asyncio # Necessario per il web (Pygbag)
import os
# --- 1. CONFIGURAZIONE & BRANDING ---
class Config:
    # Dimensioni
    TILE_SIZE = 30
    COLS = 19
    ROWS = 21
    UI_HEIGHT = 180
    WIDTH = COLS * TILE_SIZE
    HEIGHT = (ROWS * TILE_SIZE) + UI_HEIGHT
    FPS = 60
   
    # Gameplay
    SPEED_PLAYER = 4
    SPEED_GHOST = 2
   
    # Brand Timing
    POWERUP_DURATION = 5.0 # Durata invincibilità
    BRAND_TEXT_DURATION = 3.0 # Durata scritta "Made in Provincia"
   
    # Punteggi
    DOT_POINTS = 10
    LOGO_POINTS = 50
    GHOST_EAT_POINTS = 200
    # Palette Colori
    BLACK = (10, 10, 15)
    BLUE_WALL = (0, 50, 150) # Blu Istituzionale
    WHITE = (240, 240, 240)
    GOLD = (255, 215, 0) # Colore Logo
    YELLOW_BRAND = (255, 255, 0)# Giallo Powerup
    RED_ERROR = (255, 50, 50)
   
    # UI Touch
    UI_BG = (25, 25, 30)
    BTN_COLOR = (60, 60, 70)
    BTN_ACTIVE = (100, 100, 120)

# Layout: 1=Muro, 0=Vuoto, 2=Pallino, 9=LOGO BRAND
MAZE_LAYOUT = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,9,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,9,1], # Loghi in alto
    [1,2,1,1,2,1,1,1,2,1,2,1,1,1,2,1,1,2,1],
    [1,2,1,1,2,1,1,1,2,1,2,1,1,1,2,1,1,2,1],
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
    [1,2,1,1,1,1,2,1,1,0,1,1,2,1,1,1,1,2,1],
    [1,2,2,2,2,2,2,1,0,0,0,1,2,2,2,2,2,2,1],
    [1,1,1,1,1,1,2,1,0,0,0,1,2,1,1,1,1,1,1],
    [1,0,0,0,0,1,2,1,0,0,0,1,2,1,0,0,0,0,1],
    [1,1,1,1,1,1,2,1,1,0,1,1,2,1,1,1,1,1,1],
    [1,2,2,2,2,2,2,0,0,0,0,0,2,2,2,2,2,2,1],
    [1,2,1,1,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1],
    [1,2,2,2,1,1,2,2,2,1,2,2,2,1,1,2,2,2,1],
    [1,1,1,2,1,1,2,1,2,1,2,1,2,1,1,2,1,1,1],
    [1,2,2,2,2,2,2,1,2,2,2,1,2,2,2,2,2,2,1],
    [1,2,1,1,1,1,1,1,2,1,2,1,1,1,1,1,1,2,1],
    [1,2,1,1,1,1,1,1,2,1,2,1,1,1,1,1,1,2,1],
    [1,9,2,2,2,2,2,2,2,1,2,2,2,2,2,2,2,9,1], # Loghi in basso
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]
# --- 2. GESTIONE ASSET FAIL-SAFE ---
class AssetManager:
    def __init__(self):
        self.player_img = None
        self.logo_img = None
       
        # A) Caricamento MOCASSINO (con fallback disegno)
        try:
            if os.path.exists('mocassino.png'):
                img = pygame.image.load('mocassino.png').convert_alpha()
                self.player_img = pygame.transform.scale(img, (26, 26))
        except: pass
       
        if self.player_img is None:
            # Genera Mocassino Marrone via codice
            self.player_img = pygame.Surface((26, 26), pygame.SRCALPHA)
            pygame.draw.ellipse(self.player_img, (139, 69, 19), (0, 0, 26, 26)) # Scafo
            pygame.draw.ellipse(self.player_img, (80, 40, 10), (5, 5, 16, 16)) # Interno
        # B) Caricamento LOGO (con fallback disegno)
        try:
            if os.path.exists('logo_amr.png'):
                img = pygame.image.load('logo_amr.png').convert_alpha()
                self.logo_img = pygame.transform.scale(img, (28, 28))
        except: pass
        if self.logo_img is None:
            # Genera Logo Dorato via codice
            self.logo_img = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(self.logo_img, Config.GOLD, (15, 15), 14)
            pygame.draw.circle(self.logo_img, Config.WHITE, (15, 15), 12, 1)
    def get_player(self, angle=0):
        return pygame.transform.rotate(self.player_img, angle)
    def get_logo(self):
        return self.logo_img
# --- 3. INPUT TOUCH & KEYBOARD ---
class TouchController:
    def __init__(self):
        cx = Config.WIDTH // 2
        sy = Config.HEIGHT - Config.UI_HEIGHT + 25
        sz = 55
        gap = 15
       
        # Pulsanti virtuali (Hitbox allargate per facilitare il tocco)
        self.btns = [
            (pygame.Rect(cx - sz//2, sy, sz, sz), "UP", 0, -1),
            (pygame.Rect(cx - sz//2, sy + sz + gap*2, sz, sz), "DOWN", 0, 1),
            (pygame.Rect(cx - sz - gap - sz//2, sy + sz + gap, sz, sz), "LEFT", -1, 0),
            (pygame.Rect(cx + gap + sz//2, sy + sz + gap, sz, sz), "RIGHT", 1, 0)
        ]
    def get_movement(self):
        dx, dy = 0, 0
        keys = pygame.key.get_pressed()
       
        # Tastiera PC
        if keys[pygame.K_UP]: dy = -1
        if keys[pygame.K_DOWN]: dy = 1
        if keys[pygame.K_LEFT]: dx = -1
        if keys[pygame.K_RIGHT]: dx = 1
       
        # Touch Mobile
        if pygame.mouse.get_pressed()[0]:
            mp = pygame.mouse.get_pos()
            for r, _, ix, iy in self.btns:
                if r.inflate(20, 20).collidepoint(mp): # Hitbox tollerante
                    dx, dy = ix, iy
        return dx, dy
    def draw(self, screen):
        # Sfondo pannello controlli
        pygame.draw.rect(screen, Config.UI_BG, (0, Config.HEIGHT - Config.UI_HEIGHT, Config.WIDTH, Config.UI_HEIGHT))
       
        mp = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()[0]
       
        for r, d, _, _ in self.btns:
            active = click and r.inflate(20,20).collidepoint(mp)
            col = Config.BTN_ACTIVE if active else Config.BTN_COLOR
            pygame.draw.rect(screen, col, r, border_radius=12)
            pygame.draw.rect(screen, (80,80,90), r, 2, border_radius=12)
           
            # Frecce direzionali
            c = r.center
            off = 15
            poly = []
            if d=="UP": poly = [(c[0], r.top+off), (r.left+off, r.bottom-off), (r.right-off, r.bottom-off)]
            if d=="DOWN": poly = [(c[0], r.bottom-off), (r.left+off, r.top+off), (r.right-off, r.top+off)]
            if d=="LEFT": poly = [(r.left+off, c[1]), (r.right-off, r.top+off), (r.right-off, r.bottom-off)]
            if d=="RIGHT": poly = [(r.right-off, c[1]), (r.left+off, r.top+off), (r.left+off, r.bottom-off)]
            pygame.draw.polygon(screen, Config.WHITE, poly)
# --- 4. MOTORE DI GIOCO ---
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.WIDTH, Config.HEIGHT))
        pygame.display.set_caption("Crep a Coer - Made in Provincia")
        self.clock = pygame.time.Clock()
       
        self.font = pygame.font.Font(None, 36)
        self.brand_font = pygame.font.Font(None, 54) # Scritta grande
       
        self.assets = AssetManager()
        self.input = TouchController()
       
        self.reset()
    def reset(self):
        self.walls, self.dots, self.logos = [], [], []
       
        # Parsing Mappa
        for r, row in enumerate(MAZE_LAYOUT):
            for c, val in enumerate(row):
                x, y = c * Config.TILE_SIZE, r * Config.TILE_SIZE
                if val == 1: self.walls.append(pygame.Rect(x, y, Config.TILE_SIZE, Config.TILE_SIZE))
                elif val == 2: self.dots.append(pygame.Rect(x+12, y+12, 6, 6))
                elif val == 9: self.logos.append(pygame.Rect(x+2, y+2, 26, 26))
        # Setup Player – posizione sicura, lontana dai fantasmi
        self.player = pygame.Rect(11 * Config.TILE_SIZE, 10 * Config.TILE_SIZE, 20, 20)
        self.player_vel = [0, 0]
        self.player_angle = 0
        self.next_dir = None # Buffer per curve fluide
       
        # Setup Fantasmi (Colori diversi)
        colors = [(255,0,0), (255,180,255), (0,255,255), (255,180,80)]
        self.ghosts = []
        for i, pos in enumerate([(9,9), (9,10), (10,9), (8,9)]):
            self.ghosts.append({
                'rect': pygame.Rect(pos[0]*Config.TILE_SIZE, pos[1]*Config.TILE_SIZE, 22, 22),
                'color': colors[i], 'dir': [1,0]
            })
        self.score = 0
        self.state = 'playing'
        self.powerup_timer = 0
        self.brand_timer = 0
    # Verifica Collisioni Anticipata
    def can_move(self, r, dx, dy):
        test = r.copy()
        test.x += dx
        test.y += dy
        return test.collidelist(self.walls) == -1
    def update(self):
        if self.state != 'playing': return
        dt = self.clock.get_time() / 1000.0
       
        # -- 1. INPUT --
        idx, idy = self.input.get_movement()
       
        # Salva intenzione (Buffer)
        if idx != 0 or idy != 0:
            self.next_dir = (idx * Config.SPEED_PLAYER, idy * Config.SPEED_PLAYER)
            # Calcola angolo sprite
            if idx > 0: self.player_angle = 0
            elif idx < 0: self.player_angle = 180
            elif idy > 0: self.player_angle = 270
            elif idy < 0: self.player_angle = 90
        # -- 2. MOVIMENTO PLAYER (Con Buffer) --
        # Prova a eseguire la svolta bufferizzata
        moved = False
        if self.next_dir:
            if self.can_move(self.player, self.next_dir[0], self.next_dir[1]):
                self.player_vel = list(self.next_dir)
                self.next_dir = None
       
        # Applica velocità corrente
        if self.can_move(self.player, self.player_vel[0], self.player_vel[1]):
            self.player.x += self.player_vel[0]
            self.player.y += self.player_vel[1]
            moved = True
       
        # -- 3. LOGICA BRANDING --
        if self.powerup_timer > 0: self.powerup_timer -= dt
        if self.brand_timer > 0: self.brand_timer -= dt
        # Collisione LOGO
        for l in self.logos[:]:
            if self.player.colliderect(l):
                self.logos.remove(l)
                self.score += Config.LOGO_POINTS
                self.powerup_timer = Config.POWERUP_DURATION # Diventa giallo
                self.brand_timer = Config.BRAND_TEXT_DURATION # Scritta Made in Provincia
        # Collisione PALLINI
        for d in self.dots[:]:
            if self.player.colliderect(d):
                self.dots.remove(d)
                self.score += Config.DOT_POINTS
        # -- 4. GHOST AI (Smart Random) --
        for g in self.ghosts:
            spd = Config.SPEED_GHOST
            if self.powerup_timer > 0: spd = 1 # Rallenta se vulnerabile
           
            # Movimento
            nx = g['dir'][0] * spd
            ny = g['dir'][1] * spd
           
            # Controllo collisione imminente
            test = g['rect'].copy()
            test.x += nx; test.y += ny
            hit = test.collidelist(self.walls) != -1
           
            if hit or random.random() < 0.02:
                # Sceglie nuova direzione valida
                dirs = [[1,0], [-1,0], [0,1], [0,-1]]
                random.shuffle(dirs)
                for d in dirs:
                    t2 = g['rect'].copy()
                    t2.x += d[0]*5; t2.y += d[1]*5
                    if t2.collidelist(self.walls) == -1:
                        g['dir'] = d; break
           
            # Applica
            g['rect'].x += g['dir'][0] * spd
            g['rect'].y += g['dir'][1] * spd
            # Collisione Player-Ghost
            if self.player.colliderect(g['rect']):
                if self.powerup_timer > 0:
                    g['rect'].topleft = (9*Config.TILE_SIZE, 9*Config.TILE_SIZE) # Respawn
                    self.score += Config.GHOST_EAT_POINTS
                else:
                    self.state = 'lose'
        if not self.dots and not self.logos: self.state = 'win'
    def draw(self):
        self.screen.fill(Config.BLACK)
       
        # Muri
        for w in self.walls:
            pygame.draw.rect(self.screen, Config.BLUE_WALL, w)
            pygame.draw.line(self.screen, (30,60,180), w.topleft, w.topright)
        # Pallini
        for d in self.dots:
            pygame.draw.circle(self.screen, (200,200,200), d.center, 3)
        # Loghi Brand (Pulsanti)
        ls = self.assets.get_logo()
        scale = 1.0 + (0.1 * math.sin(pygame.time.get_ticks() * 0.005))
        for l in self.logos:
            r = ls.get_rect(center=l.center)
            sz = (int(r.width*scale), int(r.height*scale))
            self.screen.blit(pygame.transform.scale(ls, sz), ls.get_rect(center=l.center))
        # Player
        ps = self.assets.get_player(self.player_angle)
        # BRAND EFFECT: Diventa Giallo se powerup attivo
        if self.powerup_timer > 0:
            if (pygame.time.get_ticks() // 100) % 2 == 0: # Lampeggio sottile
                ps = ps.copy()
                ps.fill(Config.YELLOW_BRAND, special_flags=pygame.BLEND_MULT)
        self.screen.blit(ps, ps.get_rect(center=self.player.center))
        # Fantasmi
        for g in self.ghosts:
            col = (50,50,255) if self.powerup_timer > 0 else g['color']
            pygame.draw.rect(self.screen, col, g['rect'], border_radius=5)
            # Occhi
            pygame.draw.circle(self.screen, Config.WHITE, (g['rect'].centerx-4, g['rect'].y+8), 3)
            pygame.draw.circle(self.screen, Config.WHITE, (g['rect'].centerx+4, g['rect'].y+8), 3)
        # UI Overlay
        self.input.draw(self.screen)
       
        # Punteggio
        st = self.font.render(f"PUNTI: {self.score}", True, Config.WHITE)
        self.screen.blit(st, (15, 15))
        # --- BRAND OVERLAY: MADE IN PROVINCIA ---
        if self.brand_timer > 0:
            # Banner scuro per contrasto
            bg = pygame.Surface((Config.WIDTH, 70))
            bg.set_alpha(200)
            bg.fill((0,0,0))
            self.screen.blit(bg, (0, Config.HEIGHT//2 - 35))
           
            # Scritta Oro
            txt = self.brand_font.render("MADE IN PROVINCIA", True, Config.GOLD)
            r = txt.get_rect(center=(Config.WIDTH//2, Config.HEIGHT//2))
           
            # Bordo testo (Outline)
            out = self.brand_font.render("MADE IN PROVINCIA", True, Config.BLACK)
            for ox, oy in [(-2,0), (2,0), (0,-2), (0,2)]: self.screen.blit(out, (r.x+ox, r.y+oy))
           
            self.screen.blit(txt, r)
        # Win/Lose
        if self.state != 'playing':
            box = pygame.Surface((Config.WIDTH, Config.HEIGHT))
            box.set_alpha(180)
            box.fill((0,0,0))
            self.screen.blit(box, (0,0))
           
            msg = "VITTORIA!" if self.state == 'win' else "GAME OVER"
            col = Config.GOLD if self.state == 'win' else Config.RED_ERROR
            t = self.brand_font.render(msg, True, col)
            self.screen.blit(t, t.get_rect(center=(Config.WIDTH//2, Config.HEIGHT//2 - 20)))
           
            t2 = self.font.render("Tocca per continuare", True, Config.WHITE)
            self.screen.blit(t2, t2.get_rect(center=(Config.WIDTH//2, Config.HEIGHT//2 + 40)))
        pygame.display.flip()
    async def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT: return
                if self.state != 'playing':
                    if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                        self.reset()
           
            self.update()
            self.draw()
            self.clock.tick(Config.FPS)
            await asyncio.sleep(0)
if __name__ == "__main__":
    game = Game()
    asyncio.run(game.run())