import pygame

class Player:
    def __init__(self, x, y):
        self.image = pygame.image.load('../characters/main/main_orange.png')
        self.rect = self.image.get_rect(x=x, y=y)
        self.speed = 5
        self.velocity = [0, 0]

    def move(self):
        self.rect.move_ip(self.velocity[0] * self.speed, self.velocity[1] * self.speed)

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Player2(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.sprite_sheet = pygame.image.load('../characters/main/walk_spritesheet/main_spritesheet_walk.png')
        self.image = self.get_image(0, 0)
        self.rect = self.image.get_rect()


    def get_image(self, x, y):
        image = pygame.Surface([1024, 1024])
        image.blit(self.sprite_sheet, (0, 0), (x, y, 1024, 1024))
        return image