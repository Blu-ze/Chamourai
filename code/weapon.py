import pygame
import animation
import math

class Weapon(animation.AnimateSprite):
    def __init__(self, weapon_name, x, y, animation_speed):
        super().__init__(weapon_name, animation_speed)
        self.damage = 0
        self.position = (x, y)


        self.last_mouse_pos = (0, 0)

        self.original_image_right = self.images[0] #image originale direction droite
        self.original_image_left = self.images[10] #image originale direction gauche

        self.handle_offset = pygame.math.Vector2(-20, 50) #distance par rapport au centre du joueur

    def move(self, x, y):
        self.position = (x, y)

    def update(self):
        self.animate_hit()

    def rotate(self, player_screen_position):
        if not self.animation:
            mouse_x, mouse_y = pygame.mouse.get_pos()

            dx = mouse_x - player_screen_position[0]
            dy = mouse_y - player_screen_position[1]
            self.angle = math.degrees(math.atan2(-dy, dx))

            # on repart toujours de l'image d'origine
            if self.direction == 'right':
                self.image = pygame.transform.rotate(self.original_image_right, self.angle-90)
            else:
                self.image = pygame.transform.rotate(self.original_image_left, self.angle-90)

        self.rect = self.image.get_rect()


    def hit(self):
        self.start_animation()





