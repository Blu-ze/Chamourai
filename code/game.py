import pygame
from player import Player
from map import MapManager
from weapon import Weapon

class Game:
    def __init__(self,screen_size):
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Chamouraï")

        self.clock = pygame.time.Clock()

        self.map = MapManager(screen_size)
        self.player = Player(self.map.spawn.x, self.map.spawn.y)
        self.weapon = Weapon('katana', self.map.spawn.x, self.map.spawn.y)
        self.map.group.add(self.player, layer=2)
        self.map.group.add(self.weapon, layer=1)

        self.running = True

    def handling_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_z]:
            self.player.move_up()
            self.weapon.move(self.player.position.x, self.player.position.y)
        if pressed[pygame.K_s]:
            self.player.move_down()
            self.weapon.move(self.player.position.x, self.player.position.y)
        if pressed[pygame.K_q]:
            self.player.move_left()
            self.weapon.move(self.player.position.x, self.player.position.y)
        if pressed[pygame.K_d]:
            self.player.move_right()
            self.weapon.move(self.player.position.x, self.player.position.y)


    def update(self):
        self.map.group.update()
        self.map.group.center(self.player.rect)

    def display(self):
        self.map.render(self.screen, self.player.position)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handling_events()
            self.update()
            self.display()
            self.clock.tick(60)

        pygame.quit()
