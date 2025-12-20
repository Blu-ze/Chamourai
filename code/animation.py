import pygame
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def asset_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)


class AnimateSprite(pygame.sprite.Sprite):

    def __init__(self, name, animation_speed, weapon):
        super().__init__()
        self.name = name
        if weapon:
            self.images = animations.get(f"{self.name}")
        else:
            self.images = animations.get(f"{self.name}_idle")
        self.image = self.images[0]
        self.angle = 0
        self.rect = self.image.get_rect()
        self.current_image = 0
        self.animation = False
        self.animation_speed = animation_speed
        self.last_update = pygame.time.get_ticks()
        self.direction = 'right'
        self.last_direction = 'right'

    def change_direction(self, direction):
        if self.direction != direction:
            self.direction = direction

    def start_animation(self):
        self.animation = True

    def animate_walk(self):
        now = pygame.time.get_ticks()

        if self.direction != self.last_direction:
            self.last_direction = self.direction
            self.last_update = now
            if self.direction == 'right':
                self.current_image = 0
            else:
                self.current_image = len(self.images) // 2
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
                    self.current_image = len(self.images) // 2
                    self.animation = False

            self.image = self.images[self.current_image]

    def animate_hit(self):
        now = pygame.time.get_ticks()

        if self.direction != self.last_direction:
            self.last_direction = self.direction
            self.last_update = now
            if self.direction == 'right':
                self.current_image = 0
            else:
                self.current_image = len(self.images) // 2
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
                    self.current_image = len(self.images) // 2
                    self.animation = False

            self.image = pygame.transform.rotate(self.images[self.current_image], self.angle-90)

    def animate_idle(self):
        now = pygame.time.get_ticks()
        if not self.animation and now - self.last_update > self.animation_speed:
            self.images = animations.get(f"{self.name}_idle")
            self.last_update = now
            self.current_image += 1

            if self.direction == 'right':
                if self.current_image >= len(self.images) // 2:
                    self.current_image = 0
                    self.animation = False
            elif self.direction == 'left':
                if self.current_image >= len(self.images):
                    self.current_image = len(self.images) // 2
                    self.animation = False

            self.image = self.images[self.current_image]


"""def get_sprite(spritesheet, x, y, l):
    sprite = pygame.Surface([l[0], l[1]])
    sprite.blit(spritesheet, (0, 0), (x, y, l[0], l[1]))
    sprite.set_colorkey((0, 0, 0))
    return sprite"""
def get_sprite(spritesheet, x, y, l):
    sprite = pygame.Surface(l, pygame.SRCALPHA)
    sprite.blit(spritesheet, (0, 0), (x, y, l[0], l[1]))
    return sprite

def load_animation_images(name, size, sprite_size, scale=1.0):
    images = []
    #spritesheet = pygame.image.load(asset_path(f'assets/{name}.png'))
    spritesheet = pygame.image.load(asset_path(f'assets/{name}.png'))

    for y in range(0, size[1], sprite_size[1]):
        for x in range(0, size[0], sprite_size[0]):
            sprite = get_sprite(spritesheet, x, y, sprite_size)
            if scale != 1.0:
                new_size = (
                    int(sprite.get_width() * scale),
                    int(sprite.get_height() * scale)
                )
                sprite = pygame.transform.scale(sprite, new_size)
            images.append(sprite)
    return images



animations = {
    'player_idle': load_animation_images(
        'player/spritesheet', [320, 128], [64, 64], scale=1
    ),
    'katana': load_animation_images(
        'katana/spritesheet', [1250, 160], [125, 80], scale=1
    ),
    'skeleton_idle': load_animation_images(
        'mobs/Skeleton/SkeletonIdle', [364, 32], [24, 32], scale=2
    )
}

