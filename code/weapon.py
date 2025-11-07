import pygame
import animation
import math

class Weapon(animation.AnimateSprite):
    def __init__(self, weapon_name, x, y):
        super().__init__(weapon_name)
        self.damage = 0
        self.position = (x, y)

        self.angle = 0
        self.last_mouse_pos = (0, 0)
        self.original_image = self.image.copy()  # garde l’image d’origine

    def move(self, x, y):
        self.position = (x, y)

    def update(self):
        self.rect.center = self.position

    def rotate(self, player_screen_position):
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # ne recalculer que si la souris bouge
        if (mouse_x, mouse_y) == self.last_mouse_pos:
            return
        self.last_mouse_pos = (mouse_x, mouse_y)

        dx = mouse_x - player_screen_position[0]
        dy = mouse_y - player_screen_position[1]
        self.angle = math.degrees(math.atan2(-dy, dx))

        # on repart toujours de l'image d'origine
        self.image = pygame.transform.rotate(self.original_image, self.angle)

        self.rect = self.image.get_rect()
        self.rect.center = (
            self.position[0],
            self.position[1]
        )



