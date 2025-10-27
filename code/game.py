import pygame
from player import Player
from map import MapManager

class Game:
    def __init__(self,screen_size):
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Chamouraï")
        self.clock = pygame.time.Clock()
        self.player = Player(0, 0)
        self.map_manager = MapManager(screen_size)

        self.running = True

    def handling_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_z]:
                self.player.velocity[1] = -1
            elif keys[pygame.K_s]:
                self.player.velocity[1] = 1
            else:
                self.player.velocity[1] = 0

            if keys[pygame.K_d]:
                self.player.velocity[0] = 1
                self.player.image = pygame.image.load('../characters/main/main_orange.png')
            elif keys[pygame.K_q]:
                self.player.velocity[0] = -1
                self.player.image = pygame.image.load('../characters/main/reverse_main_orange.png')
            else:
                self.player.velocity[0] = 0


    def update(self):
        self.player.move()
        self.screen.fill((0, 0, 0))

    def display(self):
        self.player.draw(self.screen)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handling_events()
            self.update()
            self.map_manager.render(self.screen, (0, 0))
            self.display()
            self.clock.tick(60)

        pygame.quit()
