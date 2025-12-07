import pygame

class AnimateSprite(pygame.sprite.Sprite):

    def __init__(self, name, animation_speed):
        super().__init__()
        self.images = animations.get(name)
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


def get_sprite(spritesheet, x, y, l):
    sprite = pygame.Surface([l, l])
    sprite.blit(spritesheet, (0, 0), (x, y, l, l))
    sprite.set_colorkey((0, 0, 0))
    return sprite

def load_animation_images(name, width, height, sprite_size):
    images = []
    spritesheet = pygame.image.load(f'../assets/{name}.png')
    for y in range(0, height, sprite_size):
        for x in range(0, width, sprite_size):
            images.append(get_sprite(spritesheet, x, y, sprite_size))
    return images


animations = {
    'player': load_animation_images('player/spritesheet', 640, 256, 128),
    'katana': load_animation_images('katana/spritesheet', 4000, 800, 400)
}
