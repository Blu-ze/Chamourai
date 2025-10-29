import pygame

class Screen():
    def __init__(self, screen_size):
        self.size = screen_size
        self.window = pygame.display.set_mode(self.size)
        pygame.display.set_caption("Chamouraï")
