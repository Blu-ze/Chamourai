import pygame
import animation

class Player(animation.AnimateSprite):
    def __init__(self, x, y, animation_speed):
        super().__init__('player', animation_speed)
        self.position = None
        self.speed = 5