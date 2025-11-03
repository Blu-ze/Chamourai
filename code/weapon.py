import pygame
import animation

class Weapon(animation.AnimateSprite):
    def __init__(self, weapon_name, x, y):
        super().__init__(weapon_name)
        self.damage = 0
        self.position = (x, y)


    def update(self, position):
        self.position = position
