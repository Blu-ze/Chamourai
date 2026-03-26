import pygame
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def asset_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)


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

        try:
            self.background = pygame.image.load(asset_path('assets/Chamourai.png')).convert()
            self.background = pygame.transform.scale(self.background, screen_size)
        except:
            self.background = None

        bw, bh  = 300, 60
        spacing = 20
        start_y = H // 2 - 60
        cx      = (W - bw) // 2

        self.main_buttons = [
            Button("Solo",        cx, start_y,                  bw, bh, (70,130,240), (90,150,255)),
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

    def _draw_bg(self):
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((30, 30, 50))

    def _draw_text(self, text, font, color, center):
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=center))

    def run_main_menu(self):
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
            self._draw_text("Chamouraï", self.font_title, (255,255,255), (W//2, H//2 - 220))

            for btn in self.main_buttons:
                btn.check_hover(mouse)
                btn.draw(self.screen)
                if btn.is_clicked(mouse, clicked):
                    if btn.text == "Solo":
                        return "solo"
                    elif btn.text == "Multijoueur":
                        return "multi"
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
        clock   = pygame.time.Clock()
        W, H    = self.screen_size
        box     = InputBox(W//2 - 100, H//2, 200, 70)
        confirm = Button("Rejoindre", W//2 - 150, H//2 + 100, 300, 55, (70,130,240), (90,150,255))
        error   = ""

        while True:
            clicked = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    clicked = True
                box.handle_event(event)

            mouse = pygame.mouse.get_pos()
            self._draw_bg()
            self._draw_text("Entrez le code du salon", self.font_normal, (255,255,255), (W//2, H//2 - 80))
            box.draw(self.screen)
            confirm.check_hover(mouse)
            confirm.draw(self.screen)

            if error:
                self._draw_text(error, self.font_small, (255, 80, 80), (W//2, H//2 + 180))

            if confirm.is_clicked(mouse, clicked):
                if len(box.text) == 4:
                    result = network.join_salon(box.text)
                    if result.get("status") == "ok":
                        return result
                    else:
                        error = result.get("msg", "Code invalide")
                        box.text = ""
                else:
                    error = "Le code doit contenir 4 chiffres"

            pygame.display.flip()
            clock.tick(60)