import pygame
import animation

class Player(animation.AnimateSprite):
    def __init__(self, x, y):
        super().__init__('player')
        self.position = pygame.math.Vector2(x, y)
        self.speed = 5

    def move_up(self):
        self.position.y -= self.speed
        self.animation = True
    def move_down(self):
        self.position.y += self.speed
        self.animation = True

    def move_left(self):
        self.position.x -= self.speed
        self.direction = 'left'
        self.animation = True

    def move_right(self):
        self.position.x += self.speed
        self.direction = 'right'
        self.animation = True

    def update(self):
        self.animate()
        self.rect.center = self.position


    """def get_image(self, x, y):
        image = pygame.Surface([128, 128])
        image.blit(self.sprite_sheet, (0, 0), (x, y, 128, 128))
        return image"""