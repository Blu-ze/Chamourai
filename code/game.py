import pygame
from player import Player
from map import MapManager
from screen import Screen

class Game:
    def __init__(self,screen_size):
        self.screen = Screen(screen_size)
        self.clock = pygame.time.Clock()

        self.map = MapManager(screen_size)
        self.player = Player(self.map.spawn.x, self.map.spawn.y)
        self.map.group.add(self.player)

        self.running = True

    def handling_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        self.player.update()
        self.map.group.center(self.player.rect)

    def display(self):
        self.map.render(self.screen.window, (0, 0))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handling_events()
            self.update()
            self.display()
            self.clock.tick(60)

        pygame.quit()
