import pygame
from player import Player
from map import MapManager
from weapon import Weapon


class Game:
    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption("Chamouraï")

        self.clock = pygame.time.Clock()

        self.map    = MapManager(screen_size)
        self.player = Player(self.map.spawn.x, self.map.spawn.y, 130)
        self.weapon = Weapon('katana', self.map.spawn.x, self.map.spawn.y, 30)

        self.map.group.add(self.weapon, layer=17)
        self.map.group.add(self.player, layer=18)

        self.running = True

    # ──────────────────────────────────────────────────────────────────────────

    def handling_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.weapon.hit()

        pressed = pygame.key.get_pressed()
        self.player.velocity.update(0, 0)
        if pressed[pygame.K_q]:
            self.player.velocity.x = -self.player.speed
        if pressed[pygame.K_d]:
            self.player.velocity.x = self.player.speed
        if pressed[pygame.K_z]:
            self.player.velocity.y = -self.player.speed
        if pressed[pygame.K_s]:
            self.player.velocity.y = self.player.speed

        mouse_position    = pygame.mouse.get_pos()
        player_screen_pos = self.map.world_to_screen(self.player.position)
        if mouse_position[0] < player_screen_pos[0]:
            self.player.change_direction('left')
            if not self.weapon.animation:
                self.weapon.change_direction('left')
        else:
            self.player.change_direction('right')
            if not self.weapon.animation:
                self.weapon.change_direction('right')

    # ──────────────────────────────────────────────────────────────────────────

    def update(self):
        now_ms = pygame.time.get_ticks()

        self.player.move(self.map.collisions)
        self.weapon.move(self.player.position.x, self.player.position.y)
        self.weapon.rotate(self.player.position, self.map.map_layer)

        for mob in self.map.mobs:
            try:
                mob.update_ai(self.player.position, self.map.collisions, now_ms)
            except Exception as e:
                print(f"[ERREUR mob IA] {e}")

        self.map.group.update()

    # ──────────────────────────────────────────────────────────────────────────

    def display(self):
        self.map.render(self.screen, self.player.position)
        pygame.display.flip()

    # ──────────────────────────────────────────────────────────────────────────

    def run(self):
        while self.running:
            self.player.save_location()
            self.handling_events()
            self.update()
            self.display()
            self.clock.tick(60)

        pygame.quit()
