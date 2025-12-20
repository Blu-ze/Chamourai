from time import sleep

import pygame
import animation
import math

class Weapon(animation.AnimateSprite):
    def __init__(self, weapon_name, x, y, animation_speed):
        super().__init__(weapon_name, animation_speed, True)
        self.damage = 0
        self.position = (x, y)


        self.last_mouse_pos = (0, 0)

        self.original_image_right = self.images[0] #image originale direction droite
        self.original_image_left = self.images[10] #image originale direction gauche

        self.handle_offset = pygame.math.Vector2(-20, 50) #distance par rapport au centre du joueur

    def move(self, x, y):
        self.position = (x, y)

    def hit(self):
        self.start_animation()

    def update(self):
        self.rect.center = self.position
        self.animate_hit()

    def rotate(self, player_world_pos, map_layer):
        if not self.animation:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            player_screen_x, player_screen_y = map_layer.translate_point(player_world_pos)

            dx = mouse_x - player_screen_x
            dy = mouse_y - player_screen_y

            self.angle = math.degrees(math.atan2(-dy, dx))

            if self.direction == 'right':
                self.image = pygame.transform.rotate(
                    self.original_image_right, self.angle - 90
                )
            else:
                self.image = pygame.transform.rotate(
                    self.original_image_left, self.angle - 90
                )

        self.rect = self.image.get_rect(center=self.position)








