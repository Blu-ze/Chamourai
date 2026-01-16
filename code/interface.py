# menu.py
import pygame
import sys

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
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Chamouraï - Interface")
        
        # Créer les boutons
        button_width, button_height = 300, 60
        spacing = 20
        start_y = 300

        self.background = pygame.image.load("../assets/Chamourai.png").convert()
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
            for button in self.buttons:
                button.draw(self.screen)

            pygame.display.flip()
            clock.tick(60)

        return "quit"