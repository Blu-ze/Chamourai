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
        self.map.group.add(self.player, layer=10)
        self.map.group.add(self.weapon, layer=9)

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

        mouse_position = pygame.mouse.get_pos()
        player_screen_position = self.map.world_to_screen(self.player.position)
        if mouse_position[0] < player_screen_position[0]:
            self.weapon.change_direction('left')
            self.player.change_direction('left')
        else:
            self.weapon.change_direction('right')
            self.player.change_direction('right')

    def update(self):
        # appelle la méthode update de chacun des membres du groupe (player, weapon)
        self.map.group.update()

        # récupère la position du joueur à l'écran
        player_screen_position = self.map.world_to_screen(self.player.position)
        # Fait tourner l'arme vers le curseur
        self.weapon.rotate(player_screen_position)

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
