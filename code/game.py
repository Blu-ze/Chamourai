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

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_z]:
            self.player.move_up()
        if pressed[pygame.K_s]:
            self.player.move_down()
        if pressed[pygame.K_q]:
            self.player.move_left()
        if pressed[pygame.K_d]:
            self.player.move_right()


    def update(self):
        self.player.update()
        self.map.group.update()
        self.map.group.center(self.player.rect)

    def display(self):
        self.map.render(self.screen.window, self.player.position)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handling_events()
            self.update()
            self.display()
            self.clock.tick(60)

        pygame.quit()
