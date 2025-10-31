import pygame


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.sprite_sheet = pygame.image.load('../characters/main/walk spritesheet/main_spritesheet_walk.png')
        self.image = self.get_image(0, 0)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        self.position = pygame.math.Vector2(x, y)
        self.speed = 5

    def move_up(self): self.position.y -= self.speed

    def move_down(self): self.position.y += self.speed

    def move_left(self): self.position.x -= self.speed

    def move_right(self): self.position.x += self.speed

    def update(self):
        self.rect.center = self.position


    def get_image(self, x, y):
        image = pygame.Surface([128, 128])
        image.blit(self.sprite_sheet, (0, 0), (x, y, 128, 128))
        return image