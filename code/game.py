import pygame
from player import Player
from map import MapManager
from weapon import Weapon
from mob import Mob

class Game:
    def __init__(self,screen_size):
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Chamouraï")

        self.clock = pygame.time.Clock()

        self.map = MapManager(screen_size)
        self.player = Player(self.map.spawn.x, self.map.spawn.y, 130)
        self.skeleton = Mob('skeleton', self.map.mob_spawn.x, self.map.mob_spawn.y, 100)
        self.weapon = Weapon('katana', self.map.spawn.x, self.map.spawn.y, 30)

        self.map.group.add(self.skeleton, layer=18)
        self.map.group.add(self.weapon, layer=17)
        self.map.group.add(self.player, layer=18)


        self.running = True

    def handling_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.weapon.hit()


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

        mouse_position = pygame.mouse.get_pos()
        player_screen_position = self.map.world_to_screen(self.player.position)
        if mouse_position[0] < player_screen_position[0]:
            self.player.change_direction('left')
            if not self.weapon.animation:
                self.weapon.change_direction('left')
        else:
            self.player.change_direction('right')
            if not self.weapon.animation:
                self.weapon.change_direction('right')

    def update(self):
        self.map.group.update()
        self.weapon.rotate(self.player.position, self.map.map_layer)

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
