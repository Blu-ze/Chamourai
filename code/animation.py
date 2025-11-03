import pygame

class AnimateSprite(pygame.sprite.Sprite):

    def __init__(self, name):
        super().__init__()
        self.images = animations.get(name)
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.current_image = 0
        self.animation = False
        self.animation_speed = 100
        self.last_update = pygame.time.get_ticks()
        self.direction = 'right'
        self.last_direction = 'right'

    def start_animation(self):
        self.animation = True

    def animate(self):
        now = pygame.time.get_ticks()

        if self.direction != self.last_direction:
            self.last_direction = self.direction
            self.last_update = now
            if self.direction == 'right':
                self.current_image = 0
            else:
                self.current_image = 5
            self.image = self.images[self.current_image]
            return

        if self.animation and now - self.last_update > self.animation_speed:
            self.last_update = now
            self.current_image += 1

            if self.direction == 'right':
                if self.current_image >= len(self.images) // 2:
                    self.current_image = 0
                    self.animation = False
            elif self.direction == 'left':
                if self.current_image >= len(self.images):
                    self.current_image = 5
                    self.animation = False

            self.image = self.images[self.current_image]


def get_sprite(spritesheet, x, y):
    sprite = pygame.Surface([128, 128])
    sprite.blit(spritesheet, (0, 0), (x, y, 128, 128))
    sprite.set_colorkey((0, 0, 0))
    return sprite

def load_animation_images(name):
    images = []
    spritesheet = pygame.image.load(f'../assets/{name}.png')
    for y in range(0, 256, 128):
        for x in range(0, 640, 128):
            images.append(get_sprite(spritesheet, x, y))
    return images


animations = {
    'player': load_animation_images('player/spritesheet')
}
