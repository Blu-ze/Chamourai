import pygame
import animation

class Player(animation.AnimateSprite):
    def __init__(self, x, y):
        super().__init__('player')
        self.position = pygame.math.Vector2(x, y)
        self.speed = 5

    def move_up(self):
        self.position.y -= self.speed
        self.start_animation()
    def move_down(self):
        self.position.y += self.speed
        self.start_animation()

    def move_left(self):
        self.position.x -= self.speed
        self.direction = 'left'
        self.start_animation()

    def move_right(self):
        self.position.x += self.speed
        self.direction = 'right'
        self.start_animation()

    def update(self):
        self.animate()
        self.rect.center = self.position
