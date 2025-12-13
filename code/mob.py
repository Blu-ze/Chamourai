import pygame
import animation

class Mob(animation.AnimateSprite):
    def __init__(self, name, x, y, animation_speed):
        super().__init__(name, animation_speed)
        self.position = (x, y)
        self.rect.center = self.position
        self.speed = 5

    def update(self):
        self.rect.center = self.position