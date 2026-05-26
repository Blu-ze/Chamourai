import pygame
import sys
import os

import random
import math


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_AUDIO_VOLUME_MULTIPLIER = 0.64
LEVEL_MUSIC_VOLUME_MULTIPLIER = 0.75
SFX_VOLUME_MULTIPLIERS = {
    'slash': 2 / 7,
    'walk_grass': 4 / 7,
    'walk2': 1.0,
    'dash': 10 / 7,
    'kill': 2 / 7,
}

def asset_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)


class Particle:
    """Particule étoile style pixel art"""

    def __init__(self, screen_size):
        W, H = screen_size
        self.x = random.randint(0, W)
        self.y = random.randint(0, H)
        self.size = random.choice([2, 3, 4])

        # Mouvement plus fluide et constant
        self.vx = random.uniform(-0.3, 0.3)
        self.vy = random.uniform(-0.3, -0.1)  # Tendance à monter

        self.alpha = random.randint(100, 255)
        self.twinkle_speed = random.uniform(1, 3)
        self.twinkle_offset = random.uniform(0, 6.28)

        self.color = random.choice([
            (255, 255, 255),  # blanc
            (255, 255, 200),  # jaune pâle
            (200, 230, 255),  # bleu clair
            (255, 240, 180),  # doré
            (255, 220, 220),  # rose pâle
        ])

        self.age = 0
        self.lifetime = random.randint(600, 1500)
        self.screen_size = screen_size

        # Type de particule : 0=cercle, 1=étoile, 2=diamant
        self.shape = random.choice(['circle', 'star', 'diamond'])

    def update(self):
        # Mouvement constant et fluide
        self.x += self.vx
        self.y += self.vy

        # Effet de scintillement sinusoïdal
        self.twinkle_offset += self.twinkle_speed * 0.05
        self.alpha = 150 + 105 * math.sin(self.twinkle_offset)
        self.alpha = max(50, min(255, self.alpha))

        # Vieillissement
        self.age += 1

        # Respawn si hors écran ou trop vieille
        if (self.age >= self.lifetime or
                self.x < -10 or self.x > self.screen_size[0] + 10 or
                self.y < -10 or self.y > self.screen_size[1] + 10):
            self.__init__(self.screen_size)

    def draw(self, surface):
        # Création d'une surface temporaire avec transparence
        size = self.size * 2
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        color_with_alpha = (*self.color, int(self.alpha))

        if self.shape == 'circle':
            # Cercle doux
            pygame.draw.circle(s, color_with_alpha, (size // 2, size // 2), self.size)

        elif self.shape == 'star':
            # Petite croix/étoile pixel art
            center = size // 2
            pygame.draw.rect(s, color_with_alpha, (center - 1, center - self.size, 2, self.size * 2))
            pygame.draw.rect(s, color_with_alpha, (center - self.size, center - 1, self.size * 2, 2))

        else:  # diamond
            # Losange
            center = size // 2
            points = [
                (center, 0),
                (size, center),
                (center, size),
                (0, center)
            ]
            pygame.draw.polygon(s, color_with_alpha, points)

        # Blit la particule
        surface.blit(s, (int(self.x) - size // 2, int(self.y) - size // 2))


class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, font_size=32):
        self.text        = text
        self.rect        = pygame.Rect(x, y, width, height)
        self.color       = color
        self.hover_color = hover_color
        self.font        = pygame.font.Font(None, font_size)
        self.is_hovered  = False

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(surf, surf.get_rect(center=self.rect.center))

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, clicked):
        return self.rect.collidepoint(mouse_pos) and clicked


class InputBox:
    def __init__(self, x, y, width, height, font_size=48, max_chars=4):
        self.rect      = pygame.Rect(x, y, width, height)
        self.font      = pygame.font.Font(None, font_size)
        self.text      = ""
        self.max_chars = max_chars
        self.active    = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif len(self.text) < self.max_chars and event.unicode.isdigit():
                self.text += event.unicode

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), self.rect, border_radius=8)
        pygame.draw.rect(screen, (90, 150, 255),  self.rect, 3, border_radius=8)
        surf = self.font.render(self.text, True, (20, 20, 20))
        screen.blit(surf, surf.get_rect(center=self.rect.center))


class Interface:
    def __init__(self, screen_size, screen):
        self.screen_size = screen_size
        self.screen      = screen
        W, H             = screen_size

        self.particles = []
        for _ in range(80):
            p = Particle(screen_size)
            self.particles.append(p)

        try:
            self.background = pygame.image.load(asset_path('assets/Chamourai.png')).convert()
            self.background = pygame.transform.scale(self.background, screen_size)
        except:
            self.background = None

        try:
            self.logo = pygame.image.load(asset_path("assets/titre.png")).convert_alpha()
            original_width, original_height = self.logo.get_size()

            scale_factor = 0.35  # 1.5 = +50% plus grand

            new_size = (
                int(original_width * scale_factor),
                int(original_height * scale_factor)
            )

            self.logo = pygame.transform.smoothscale(self.logo, new_size)
        except:
            self.logo = None

        bw, bh  = 300, 60
        spacing = 20
        start_y = H // 2 - 60
        cx      = (W - bw) // 2

        self.main_buttons = [
            Button("1 Joueur",    cx, start_y,                  bw, bh, (70,130,240), (90,150,255)),
            Button("Multijoueur", cx, start_y + bh + spacing,   bw, bh, (70,130,240), (90,150,255)),
            Button("Options",     cx, start_y + 2*(bh+spacing), bw, bh, (70,130,240), (90,150,255)),
            Button("Quitter",     cx, start_y + 3*(bh+spacing), bw, bh, (200,50,50),  (220,70,70)),
        ]

        self.multi_buttons = [
            Button("Créer un salon", cx, start_y,                  bw, bh, (70,130,240), (90,150,255)),
            Button("Rejoindre",      cx, start_y + bh + spacing,   bw, bh, (70,130,240), (90,150,255)),
            Button("Retour",         cx, start_y + 2*(bh+spacing), bw, bh, (120,120,120),(160,160,160)),
        ]

        self.font_title  = pygame.font.Font(None, 72)
        self.font_normal = pygame.font.Font(None, 36)
        self.font_code   = pygame.font.Font(None, 100)
        self.font_small  = pygame.font.Font(None, 28)
        self.volume = 0.5
        self.sfx_volume = 0.7
        self.current_music_track = 'ambiance'

        # Sons d'effets
        self.sounds = {}
        try:
            self.sounds['slash'] = pygame.mixer.Sound(asset_path('assets/sounds/slash.ogg'))
            self.sounds['walk_grass'] = pygame.mixer.Sound(asset_path('assets/sounds/walk.wav'))
            self.sounds['walk2'] = pygame.mixer.Sound(asset_path('assets/sounds/walk2.wav'))
            self.sounds['walk'] = self.sounds['walk_grass']  # son actif par défaut
            self.sounds['dash'] = pygame.mixer.Sound(asset_path('assets/sounds/dash.wav'))
            self.sounds['kill'] = pygame.mixer.Sound(asset_path('assets/sounds/kill.wav'))

            self._apply_sfx_volume()
        except Exception as e:
            print(f"[SFX] Erreur chargement sons: {e}")

        try:
            pygame.mixer.music.load(asset_path('assets/sounds/ambiance.wav'))
            self._apply_music_volume()
            pygame.mixer.music.play(-1)  # -1 = boucle infinie
        except Exception as e:
            print(f"[Musique] Impossible de charger assets/sounds/ambiance.wav : {e}")

        bw2, bh2 = 200, 55
        cx2 = (W - bw2) // 2
        self.options_buttons = [
            Button("- Volume", cx2 - 110, H // 2 - 10, bw2, bh2, (70, 130, 240), (90, 150, 255)),
            Button("+ Volume", cx2 + 110, H // 2 - 10, bw2, bh2, (70, 130, 240), (90, 150, 255)),
            Button("Retour", cx2, H // 2 + 200, bw2, bh2, (120, 120, 120), (160, 160, 160)),
        ]
    def _apply_music_volume(self):
        level_track = self.current_music_track in ('cave', 'boss')
        multiplier = LEVEL_MUSIC_VOLUME_MULTIPLIER if level_track else 1.0
        pygame.mixer.music.set_volume(
            min(1.0, self.volume * multiplier * MASTER_AUDIO_VOLUME_MULTIPLIER)
        )

    def _apply_sfx_volume(self):
        for name, multiplier in SFX_VOLUME_MULTIPLIERS.items():
            if name in self.sounds:
                self.sounds[name].set_volume(
                    min(1.0, self.sfx_volume * multiplier * MASTER_AUDIO_VOLUME_MULTIPLIER)
                )

    def play_music(self, track_name, fadeout_ms=800, fadein_ms=0):
        """Change la musique en cours. track_name = nom sans extension (ex: 'cave', 'boss')."""
        try:
            pygame.mixer.music.fadeout(fadeout_ms)
            path = asset_path(f'assets/sounds/{track_name}.ogg')
            # Fallback .wav si .ogg absent
            if not os.path.exists(path):
                path = asset_path(f'assets/sounds/{track_name}.wav')
            pygame.mixer.music.load(path)
            self.current_music_track = track_name
            self._apply_music_volume()
            if fadein_ms:
                pygame.mixer.music.play(-1, fade_ms=fadein_ms)
            else:
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[Musique] Impossible de jouer '{track_name}' : {e}")

    def set_walk_surface(self, surface_name):
        """Change le son de pas actif. surface_name = 'grass' ou 'cave'."""
        if surface_name == 'cave' and 'walk2' in self.sounds:
            self.sounds['walk'] = self.sounds['walk2']
        elif surface_name == 'grass' and 'walk_grass' in self.sounds:
            self.sounds['walk'] = self.sounds['walk_grass']

    def _draw_bg(self):
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((30, 30, 50))


        # Dessin des particules étoiles
        for p in self.particles:
            p.update()
            p.draw(self.screen)


    def _draw_text(self, text, font, color, center):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def run_main_menu(self):
        clock = pygame.time.Clock()
        W, H  = self.screen_size
        self.play_music('ambiance', fadeout_ms=600, fadein_ms=800)
        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            if self.logo:
                rect = self.logo.get_rect(center=(W // 2, H // 2 - 190))
                self.screen.blit(self.logo, rect)
            else:
                self._draw_text("Chamouraï", self.font_title, (255, 255, 255), (W // 2, H // 2 - 220))

            for btn in self.main_buttons:
                btn.check_hover(mouse)
                btn.draw(self.screen)
                if btn.is_clicked(mouse, clicked):
                    if btn.text == "1 Joueur":
                        return "solo"
                    elif btn.text == "Multijoueur":
                        return "multi"
                    if btn.text == "Options":
                        return "options"
                    elif btn.text == "Quitter":
                        pygame.quit(); sys.exit()
            pygame.display.flip()
            clock.tick(60)
    def run_multi_menu(self):
        clock = pygame.time.Clock()
        W, H  = self.screen_size
        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            self._draw_text("Multijoueur", self.font_title, (255,255,255), (W//2, H//2 - 220))

            for btn in self.multi_buttons:
                btn.check_hover(mouse)
                btn.draw(self.screen)
                if btn.is_clicked(mouse, clicked):
                    if btn.text == "Créer un salon":
                        return "create"
                    elif btn.text == "Rejoindre":
                        return "join"
                    elif btn.text == "Retour":
                        return "back"

            pygame.display.flip()
            clock.tick(60)

    def run_create_salon(self, network):
        import threading

        clock = pygame.time.Clock()
        W, H = self.screen_size
        import socket
        local_ip = socket.gethostbyname(socket.gethostname())
        result = network.create_salon()

        if result.get("status") != "ok":
            return None

        code = result["code"]
        start_btn = Button("Lancer la partie", W // 2 - 150, H // 2 + 120, 300, 55, (70, 200, 70), (90, 220, 90))
        guest_ready = [False]  # liste pour pouvoir modifier depuis le thread

        def check_guest():
            while not guest_ready[0]:
                try:
                    ping = network.ping()
                    if ping.get("guest_connected", False):
                        guest_ready[0] = True
                        return
                except:
                    return
                pygame.time.wait(500)  # vérifie toutes les 500ms

        # Lancer le ping dans un thread séparé
        threading.Thread(target=check_guest, daemon=True).start()

        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            self._draw_text("Votre code de salon", self.font_normal, (200, 200, 200), (W // 2, H // 2 - 100))
            self._draw_text(code, self.font_code, (255, 220, 50), (W // 2, H // 2))
            self._draw_text(f"Votre IP : {local_ip}", self.font_small, (180, 255, 180), (W // 2, H // 2 + 35))

            if guest_ready[0]:
                self._draw_text("Joueur 2 connecté !", self.font_normal, (100, 255, 100), (W // 2, H // 2 + 70))
                start_btn.check_hover(mouse)
                start_btn.draw(self.screen)
                if start_btn.is_clicked(mouse, clicked):
                    spawn = network.start_game()
                    return spawn
            else:
                self._draw_text("En attente du joueur 2...", self.font_normal, (180, 180, 180), (W // 2, H // 2 + 70))

            pygame.display.flip()
            clock.tick(60)

    def run_join_salon(self, network):
        import threading
        clock = pygame.time.Clock()
        W, H = self.screen_size
        box = InputBox(W // 2 - 100, H // 2, 200, 70)
        confirm = Button("Rejoindre", W // 2 - 150, H // 2 + 100, 300, 55, (70, 130, 240), (90, 150, 255))
        back = Button("Retour", W // 2 - 150, H // 2 + 170, 300, 55, (95, 95, 105), (125, 125, 140))
        error = ""
        success = ""

        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True
                box.handle_event(event)

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            self._draw_text("Entrez le code du salon", self.font_normal, (255, 255, 255), (W // 2, H // 2 - 80))
            box.draw(self.screen)
            confirm.check_hover(mouse)
            confirm.draw(self.screen)
            back.check_hover(mouse)
            back.draw(self.screen)

            if error:
                self._draw_text(error, self.font_small, (255, 80, 80), (W // 2, H // 2 + 250))
            if success:
                self._draw_text(success, self.font_normal, (100, 255, 100), (W // 2, H // 2 + 250))
                return {"status": "ok"}

            if back.is_clicked(mouse, clicked):
                return {"status": "back"}
            if confirm.is_clicked(mouse, clicked):
                if len(box.text) == 4:
                    result = network.join_salon(box.text)
                    if result.get("status") == "ok":
                        success = f"Salon {box.text} rejoint ! En attente de l'hôte..."
                    else:
                        error = result.get("msg", "Code invalide")
                        box.text = ""
                else:
                    error = "Le code doit contenir 4 chiffres"

            pygame.display.flip()
            clock.tick(60)

    def run_waiting_for_host(self, network):
        """Affiche un écran d'attente pendant que le guest attend le START de l'hôte."""
        import threading
        clock = pygame.time.Clock()
        W, H = self.screen_size
        result = [None]
        received = [False]

        def wait_for_start():
            try:
                result[0] = network.recv_raw()
                received[0] = True
            except:
                received[0] = True

        threading.Thread(target=wait_for_start, daemon=True).start()

        dots = 0
        timer = 0
        while not received[0]:
            clock.tick(60)
            timer += 1
            if timer % 30 == 0:
                dots = (dots + 1) % 4

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()

            self._draw_bg()
            self._draw_text(
                "En attente du lancement par l'hôte" + "." * dots,
                self.font_normal, (200, 200, 200), (W // 2, H // 2)
            )
            pygame.display.flip()

        return result[0]

    def run_enter_ip(self):
        clock = pygame.time.Clock()
        W, H = self.screen_size
        ip_text = ""
        confirm = Button("Confirmer", W // 2 - 150, H // 2 + 100, 300, 55, (70, 130, 240), (90, 150, 255))
        back = Button("Retour", W // 2 - 150, H // 2 + 170, 300, 55, (95, 95, 105), (125, 125, 140))
        error = ""

        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        ip_text = ip_text[:-1]
                    elif len(ip_text) < 15 and (event.unicode.isdigit() or event.unicode == '.'):
                        ip_text += event.unicode

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            self._draw_text("IP du serveur (hôte)", self.font_normal, (255, 255, 255), (W // 2, H // 2 - 80))
            ip_surf = self.font_code.render(ip_text or "_", True, (255, 220, 50))
            self.screen.blit(ip_surf, ip_surf.get_rect(center=(W // 2, H // 2)))
            confirm.check_hover(mouse)
            confirm.draw(self.screen)
            back.check_hover(mouse)
            back.draw(self.screen)
            if error:
                self._draw_text(error, self.font_small, (255, 80, 80), (W // 2, H // 2 + 250))
            if back.is_clicked(mouse, clicked):
                return None
            if confirm.is_clicked(mouse, clicked):
                parts = ip_text.split('.')
                if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                    return ip_text
                else:
                    error = "IP invalide (ex: 192.168.1.10)"

            pygame.display.flip()
            clock.tick(60)

    def run_options(self):
        clock = pygame.time.Clock()
        W, H = self.screen_size

        # Boutons pour SFX — placés sous la barre SFX
        bw2, bh2 = 200, 55
        cx2 = (W - bw2) // 2
        sfx_buttons = [
            Button("- Effets", cx2 - 110, H // 2 + 110, bw2, bh2, (70, 130, 240), (90, 150, 255)),
            Button("+ Effets", cx2 + 110, H // 2 + 110, bw2, bh2, (70, 130, 240), (90, 150, 255)),
        ]

        bar_w = 400
        bar_h = 20
        bar_x = W // 2 - bar_w // 2

        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            self._draw_text("Options", self.font_title, (255, 255, 255), (W // 2, H // 2 - 230))

            # --- Volume Musique ---
            self._draw_text(f"Volume Musique : {int(self.volume * 100)}%", self.font_normal, (255, 220, 50),
                            (W // 2, H // 2 - 155))
            bar_y_music = H // 2 - 120
            pygame.draw.rect(self.screen, (80, 80, 80), (bar_x, bar_y_music, bar_w, bar_h), border_radius=8)
            pygame.draw.rect(self.screen, (70, 180, 255), (bar_x, bar_y_music, int(bar_w * self.volume), bar_h),
                             border_radius=8)

            # Boutons + / - Volume (sous la barre musique)
            for btn in self.options_buttons:
                if btn.text in ("- Volume", "+ Volume"):
                    btn.rect.y = H // 2 - 55
                btn.check_hover(mouse)
                btn.draw(self.screen)
                if btn.is_clicked(mouse, clicked):
                    if btn.text == "+ Volume":
                        self.volume = min(1.0, self.volume + 0.1)
                        self._apply_music_volume()
                    elif btn.text == "- Volume":
                        self.volume = max(0.0, self.volume - 0.1)
                        self._apply_music_volume()
                    elif btn.text == "Retour":
                        return

            # --- Volume Effets Sonores ---
            self._draw_text(f"Volume Effets Sonores : {int(self.sfx_volume * 100)}%", self.font_normal, (255, 220, 50),
                            (W // 2, H // 2 + 20))
            sfx_bar_y = H // 2 + 55
            pygame.draw.rect(self.screen, (80, 80, 80), (bar_x, sfx_bar_y, bar_w, bar_h), border_radius=8)
            pygame.draw.rect(self.screen, (255, 180, 70), (bar_x, sfx_bar_y, int(bar_w * self.sfx_volume), bar_h),
                             border_radius=8)

            for btn in sfx_buttons:
                btn.check_hover(mouse)
                btn.draw(self.screen)
                if btn.is_clicked(mouse, clicked):
                    if btn.text == "+ Effets":
                        self.sfx_volume = min(1.0, self.sfx_volume + 0.1)
                        self._apply_sfx_volume()
                    elif btn.text == "- Effets":
                        self.sfx_volume = max(0.0, self.sfx_volume - 0.1)
                        self._apply_sfx_volume()

            pygame.display.flip()
            clock.tick(60)

    def run_create_salon(self, network):
        import threading

        clock = pygame.time.Clock()
        W, H = self.screen_size
        import socket
        local_ip = socket.gethostbyname(socket.gethostname())
        result = network.create_salon()

        if result.get("status") != "ok":
            return None

        code = result["code"]
        start_btn = Button("Lancer la partie", W // 2 - 150, H // 2 + 120, 300, 55, (70, 200, 70), (90, 220, 90))
        guest_ready = [False]  # liste pour pouvoir modifier depuis le thread

        def check_guest():
            while not guest_ready[0]:
                try:
                    ping = network.ping()
                    if ping.get("guest_connected", False):
                        guest_ready[0] = True
                        return
                except:
                    return
                pygame.time.wait(500)  # vérifie toutes les 500ms

        # Lancer le ping dans un thread séparé
        threading.Thread(target=check_guest, daemon=True).start()

        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            self._draw_text("Votre code de salon", self.font_normal, (200, 200, 200), (W // 2, H // 2 - 100))
            self._draw_text(code, self.font_code, (255, 220, 50), (W // 2, H // 2))
            self._draw_text(f"Votre IP : {local_ip}", self.font_small, (180, 255, 180), (W // 2, H // 2 + 35))

            if guest_ready[0]:
                self._draw_text("Joueur 2 connecté !", self.font_normal, (100, 255, 100), (W // 2, H // 2 + 70))
                start_btn.check_hover(mouse)
                start_btn.draw(self.screen)
                if start_btn.is_clicked(mouse, clicked):
                    spawn = network.start_game()
                    return spawn
            else:
                self._draw_text("En attente du joueur 2...", self.font_normal, (180, 180, 180), (W // 2, H // 2 + 70))

            pygame.display.flip()
            clock.tick(60)

    def run_join_salon(self, network):
        import threading
        clock = pygame.time.Clock()
        W, H = self.screen_size
        box = InputBox(W // 2 - 100, H // 2, 200, 70)
        confirm = Button("Rejoindre", W // 2 - 150, H // 2 + 100, 300, 55, (70, 130, 240), (90, 150, 255))
        error = ""
        success = ""

        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True
                box.handle_event(event)

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            self._draw_text("Entrez le code du salon", self.font_normal, (255, 255, 255), (W // 2, H // 2 - 80))
            box.draw(self.screen)
            confirm.check_hover(mouse)
            confirm.draw(self.screen)

            if error:
                self._draw_text(error, self.font_small, (255, 80, 80), (W // 2, H // 2 + 180))
            if success:
                self._draw_text(success, self.font_normal, (100, 255, 100), (W // 2, H // 2 + 180))
                return {"status": "ok"}

            if confirm.is_clicked(mouse, clicked):
                if len(box.text) == 4:
                    result = network.join_salon(box.text)
                    if result.get("status") == "ok":
                        success = f"Salon {box.text} rejoint ! En attente de l'hôte..."
                    else:
                        error = result.get("msg", "Code invalide")
                        box.text = ""
                else:
                    error = "Le code doit contenir 4 chiffres"

            pygame.display.flip()
            clock.tick(60)

    def run_waiting_for_host(self, network):
        """Affiche un écran d'attente pendant que le guest attend le START de l'hôte."""
        import threading
        clock = pygame.time.Clock()
        W, H = self.screen_size
        result = [None]
        received = [False]

        def wait_for_start():
            try:
                result[0] = network.recv_raw()
                received[0] = True
            except:
                received[0] = True

        threading.Thread(target=wait_for_start, daemon=True).start()

        dots = 0
        timer = 0
        while not received[0]:
            clock.tick(60)
            timer += 1
            if timer % 30 == 0:
                dots = (dots + 1) % 4

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()

            self._draw_bg()
            self._draw_text(
                "En attente du lancement par l'hôte" + "." * dots,
                self.font_normal, (200, 200, 200), (W // 2, H // 2)
            )
            pygame.display.flip()

        return result[0]

    def run_pause_menu(self, surface):
        W, H = self.screen_size
        clock = pygame.time.Clock()

        bw, bh = 280, 55
        cx = (W - bw) // 2
        btn_resume = Button("Reprendre", cx, H // 2 + 120, bw, bh, (60, 160, 60), (80, 200, 80))
        btn_menu = Button("Menu principal", cx, H // 2 + 190, bw, bh, (180, 60, 60), (220, 80, 80))

        music_vol = self.volume
        sfx_vol = self.sfx_volume

        # Sliders
        slider_x = cx
        music_slider_y = H // 2 - 60
        sfx_slider_y = H // 2 + 10
        slider_w = bw
        slider_h = 8
        knob_r = 11

        dragging_music = False
        dragging_sfx = False

        font_title = pygame.font.Font(None, 72)
        font_label = pygame.font.Font(None, 30)

        while True:
            clicked = False
            mouse = pygame.mouse.get_pos()
            mx, my = mouse

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "resume"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True
                    # Check Music Knob
                    knob_cx = slider_x + int(music_vol * slider_w)
                    if math.hypot(mx - knob_cx, my - (music_slider_y + slider_h // 2)) <= knob_r + 4:
                        dragging_music = True
                    # Check SFX Knob
                    knob_sfx_x = slider_x + int(sfx_vol * slider_w)
                    if math.hypot(mx - knob_sfx_x, my - (sfx_slider_y + slider_h // 2)) <= knob_r + 4:
                        dragging_sfx = True

                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    dragging_music = False
                    dragging_sfx = False

                if event.type == pygame.MOUSEMOTION:
                    if dragging_music:
                        music_vol = max(0.0, min(1.0, (mx - slider_x) / slider_w))
                        try:
                            self.volume = music_vol
                            self._apply_music_volume()
                        except:
                            pass
                    if dragging_sfx:
                        sfx_vol = max(0.0, min(1.0, (mx - slider_x) / slider_w))
                        self.sfx_volume = sfx_vol
                        self._apply_sfx_volume()

            # Fond semi-transparent
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((10, 10, 20, 175))
            surface.blit(overlay, (0, 0))

            # Panneau central (assez grand pour sliders + 2 boutons)
            panel_w, panel_h = 380, 460
            panel_x = (W - panel_w) // 2
            panel_y = H // 2 - 190
            panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            panel.fill((20, 22, 40, 220))
            pygame.draw.rect(panel, (90, 130, 255, 120), (0, 0, panel_w, panel_h), 2, border_radius=14)
            surface.blit(panel, (panel_x, panel_y))

            # Titre
            txt = font_title.render("PAUSE ", True, (220, 220, 255))
            surface.blit(txt, txt.get_rect(center=(W // 2, panel_y + 50)))

            # Label Volume Musique
            label_music = font_label.render(f"Musique {int(music_vol * 100):3d}% ", True, (190, 190, 230))
            surface.blit(label_music, label_music.get_rect(center=(W // 2, music_slider_y - 18)))

            # Track Musique
            pygame.draw.rect(surface, (50, 50, 80), pygame.Rect(slider_x, music_slider_y, slider_w, slider_h),
                             border_radius=4)
            fill_w = int(music_vol * slider_w)
            pygame.draw.rect(surface, (70, 180, 255), pygame.Rect(slider_x, music_slider_y, fill_w, slider_h),
                             border_radius=4)
            knob_cx = slider_x + fill_w
            pygame.draw.circle(surface, (200, 210, 255), (knob_cx, music_slider_y + slider_h // 2), knob_r)

            # Label Volume Effets
            label_sfx = font_label.render(f"Effets {int(sfx_vol * 100):3d}% ", True, (190, 190, 230))
            surface.blit(label_sfx, label_sfx.get_rect(center=(W // 2, sfx_slider_y - 18)))

            # Track SFX
            pygame.draw.rect(surface, (50, 50, 80), pygame.Rect(slider_x, sfx_slider_y, slider_w, slider_h),
                             border_radius=4)
            fill_w_sfx = int(sfx_vol * slider_w)
            pygame.draw.rect(surface, (255, 180, 70), pygame.Rect(slider_x, sfx_slider_y, fill_w_sfx, slider_h),
                             border_radius=4)
            knob_sfx_x = slider_x + fill_w_sfx
            pygame.draw.circle(surface, (200, 210, 255), (knob_sfx_x, sfx_slider_y + slider_h // 2), knob_r)

            # Boutons
            for btn in (btn_resume, btn_menu):
                btn.check_hover(mouse)
                btn.draw(surface)
                if btn.is_clicked(mouse, clicked):
                    if btn.text == "Reprendre":
                        return "resume"
                    elif btn.text == "Menu principal":
                        return "menu"

            pygame.display.flip()
            clock.tick(60)

    def run_enter_ip(self):
        clock = pygame.time.Clock()
        W, H = self.screen_size
        ip_text = ""
        confirm = Button("Confirmer", W // 2 - 150, H // 2 + 100, 300, 55, (70, 130, 240), (90, 150, 255))
        back = Button("Retour", W // 2 - 150, H // 2 + 170, 300, 55, (95, 95, 105), (125, 125, 140))
        error = ""

        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_BACKSPACE:
                        ip_text = ip_text[:-1]
                    elif len(ip_text) < 15 and (event.unicode.isdigit() or event.unicode == '.'):
                        ip_text += event.unicode

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            self._draw_text("IP du serveur (hôte)", self.font_normal, (255, 255, 255), (W // 2, H // 2 - 80))
            ip_surf = self.font_code.render(ip_text or "_", True, (255, 220, 50))
            self.screen.blit(ip_surf, ip_surf.get_rect(center=(W // 2, H // 2)))
            confirm.check_hover(mouse)
            confirm.draw(self.screen)
            back.check_hover(mouse)
            back.draw(self.screen)
            if error:
                self._draw_text(error, self.font_small, (255, 80, 80), (W // 2, H // 2 + 250))
            if back.is_clicked(mouse, clicked):
                return None
            if confirm.is_clicked(mouse, clicked):
                parts = ip_text.split('.')
                if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                    return ip_text
                else:
                    error = "IP invalide (ex: 192.168.1.10)"

            pygame.display.flip()
            clock.tick(60)
