# menu.py
import pygame
import sys
import os
import random
import math


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def asset_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

<<<<<<< Updated upstream
=======

class Particle:
    """Particule étoile style pixel art améliorée"""

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

>>>>>>> Stashed changes
class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, font_size=32):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.Font(None, font_size)
        self.is_hovered = False

    def draw(self, screen):
        current_color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(screen, current_color, self.rect, border_radius=10)
        text_surf = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_click):
        if self.rect.collidepoint(mouse_pos) and mouse_click:
            return True
        return False


class Interface:
    def __init__(self, screen_size):
        self.screen_size = screen_size
<<<<<<< Updated upstream
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Chamouraï - Interface")
        
        # Créer les boutons
        button_width, button_height = 300, 60
=======
        self.screen      = screen
        W, H             = screen_size
        # Initialisation particules étoiles
        self.particles = []
        for _ in range(60):  # nombres de particules
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
>>>>>>> Stashed changes
        spacing = 20
        start_y = 300

        self.background = pygame.image.load(asset_path(f'assets/Chamourai.png')).convert()
        self.background = pygame.transform.scale(self.background, screen_size)
        
        self.buttons = [
            Button("Jouer", (screen_size[0] - button_width) // 2, start_y, button_width, button_height, (70, 130, 240), (90, 150, 255)),
            Button("Options", (screen_size[0] - button_width) // 2, start_y + button_height + spacing, button_width, button_height, (70, 130, 240), (90, 150, 255)),
            Button("Quitter", (screen_size[0] - button_width) // 2, start_y + 2*(button_height + spacing), button_width, button_height, (200, 50, 50), (220, 70, 70)),
        ]

        self.running = True

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_click = True
                    
            # Mettre à jour les boutons
            for button in self.buttons:
                button.check_hover(mouse_pos)
                if button.is_clicked(mouse_pos, mouse_click):
                    if button.text == "Jouer":
                        return "play"  # Retourne l'état pour lancer le jeu
                    elif button.text == "Options":
                        print("Options clicked")  # À implémenter plus tard
                    elif button.text == "Quitter":
                        pygame.quit()
                        sys.exit()

            # Dessiner
            self.screen.blit(self.background, (0, 0))
<<<<<<< Updated upstream
            for button in self.buttons:
                button.draw(self.screen)
=======
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
                    elif btn.text == "Quitter":
                        pygame.quit(); sys.exit()
>>>>>>> Stashed changes

            pygame.display.flip()
            clock.tick(60)

        return "quit"