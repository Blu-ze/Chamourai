import pygame
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def asset_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

class AnimateSprite(pygame.sprite.Sprite):

    def __init__(self, name, animation_speed, is_weapon=False):
        super().__init__()
        self.name = name
        self.is_weapon = is_weapon

        if is_weapon:
            self.animations = {
                "idle": animations.get(name)
            }
        else:
            self.animations = {
                "walk": animations.get(f"{name}_walk"),
                "idle": animations.get(f"{name}_idle")
            }

        self.state = "idle"
        self.images = self.animations["idle"]

        self.image = self.images[0]
        self.rect = self.image.get_rect()

        self.current_image = 0
        self.animation_speed = animation_speed
        self.last_update = pygame.time.get_ticks()

        self.direction = "right"

        # Attributs pour animate_hit
        self.animation = False
        self.angle = 0

    def start_animation(self):
        self.animation = True
        if self.direction == 'right':
            self.current_image = 0
        else:
            self.current_image = len(self.images) // 2

    def set_direction(self, direction):
        if direction != self.direction:
            self.direction = direction

    def update_animation(self):
        now = pygame.time.get_ticks()

        if self.state == "walk":
            self.images = self.animations["walk"]
        else:
            self.images = self.animations["idle"]

        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.current_image += 1

            if self.direction == "right":
                max_frame = len(self.images) // 2
                if self.current_image >= max_frame:
                    self.current_image = 0
            else:
                min_frame = len(self.images) // 2
                if self.current_image < min_frame:
                    self.current_image = min_frame
                if self.current_image >= len(self.images):
                    self.current_image = min_frame

            self.image = self.images[self.current_image]

    def animate_hit(self):
        now = pygame.time.get_ticks()

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

            self.image = pygame.transform.rotate(self.images[self.current_image], self.angle - 90)


def get_sprite(spritesheet, x, y, l):
    sprite = pygame.Surface(l, pygame.SRCALPHA)
    sprite.blit(spritesheet, (0, 0), (x, y, l[0], l[1]))
    return sprite

def load_animation_images(name, size, sprite_size, scale=1.0):
    images = []
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
    'player_walk': load_animation_images(
        'player/spritesheet', [320, 128], [64, 64], scale=1
    ),
    'player_idle': load_animation_images(
        'player/idle', [64, 128], [64, 64], scale=1
    ),
    'player_jump': load_animation_images(
        'player/jump', [320, 128], [64, 64], scale=1
    ),
    'player2_walk': load_animation_images(
        'player/spritesheet2', [320, 128], [64, 64], scale=1
    ),
    'player2_idle': load_animation_images(
        'player/idle2', [64, 128], [64, 64], scale=1
    ),
    'player2_jump': load_animation_images(
        'player/jump2', [320, 128], [64, 64], scale=1
    ),
    'katana': load_animation_images(
        'katana/spritesheet', [1250, 160], [125, 80], scale=1
    ),
    'skeleton_idle': load_animation_images(
        'mobs/Skeleton/SkeletonIdle', [264, 32], [24, 32], scale=2
    ),
    'skeleton_walk': load_animation_images(
        'mobs/Skeleton/SkeletonWalk', [286, 33], [22, 33], scale=2
    ),
    'skeleton_hit': load_animation_images(
        'mobs/Skeleton/SkeletonHit', [240, 32], [30, 32], scale=2
    ),
    'skeleton_dead': load_animation_images(
        'mobs/Skeleton/SkeletonDead', [495, 32], [33, 32], scale=2
    ),
    'skeleton_attack': load_animation_images(
        'mobs/Skeleton/SkeletonAttack', [774, 37], [43,37], scale=2
    ),
    'skeleton_boss_idle': load_animation_images(
        'mobs/Skeleton/SkeletonIdleBoss', [264, 32], [24, 32], scale=4
    ),
    'skeleton_boss_walk': load_animation_images(
        'mobs/Skeleton/SkeletonWalkBoss', [286, 33], [22, 33], scale=4
    ),
    'skeleton_boss_hit': load_animation_images(
        'mobs/Skeleton/SkeletonHitBoss', [240, 32], [30, 32], scale=4
    ),
    'skeleton_boss_dead': load_animation_images(
        'mobs/Skeleton/SkeletonDeadBoss', [495, 32], [33, 32], scale=4
    ),
    'skeleton_boss_attack': load_animation_images(
        'mobs/Skeleton/SkeletonAttackBoss', [774, 37], [43,37], scale=4
    ),
    'E': load_animation_images(
        'keyboard/Keyboard_E', [32, 15], [16, 15], scale=2
    ),
    'oldman': load_animation_images(
        'oldman/oldman_idle', [960, 96], [96, 96], scale=2
    ),
    'necromancer_idle': load_animation_images(
        'mobs/Necromancer/NecromancerIdle', [1280,128], [160,128], scale=1
    ),
    'necromancer_walk': load_animation_images(
        'mobs/Necromancer/NecromancerWalk', [1280,128], [160,128], scale=1
    ),
    'necromancer_attack': load_animation_images(
        'mobs/Necromancer/NecromancerAttack', [2080, 128], [160,128], scale=1
    ),
    'necromancer_hit': load_animation_images(
        'mobs/Necromancer/NecromancerHit', [800, 128], [160,128], scale=1
    ),
    'necromancer_dead': load_animation_images(
        'mobs/Necromancer/NecromancerDeath', [1440, 128], [160,128], scale=1
    ),
    'necromancer_fireball': load_animation_images(
        'mobs/Necromancer/EnergyBall', [1152, 128], [128,128], scale=1
    ),
    'necromancer_boss_idle': load_animation_images(
        'mobs/Necromancer/NecromancerIdleBoss', [1280,128], [160,128], scale=2
    ),
    'necromancer_boss_walk': load_animation_images(
        'mobs/Necromancer/NecromancerWalkBoss', [1280,128], [160,128], scale=2
    ),
    'necromancer_boss_attack': load_animation_images(
        'mobs/Necromancer/NecromancerAttackBoss', [2080, 128], [160,128], scale=2
    ),
    'necromancer_boss_hit': load_animation_images(
        'mobs/Necromancer/NecromancerHitBoss', [800, 128], [160,128], scale=2
    ),
    'necromancer_boss_dead': load_animation_images(
        'mobs/Necromancer/NecromancerDeathBoss', [1440, 128], [160,128], scale=2
    ),
    'necromancer_boss_fireball': load_animation_images(
        'mobs/Necromancer/EnergyBallBoss', [1152, 128], [128,128], scale=2
    ),
    'golem_idle': load_animation_images(
        'mobs/Golem/GolemIdle', [400, 100], [100, 100], scale=2
    ),
    'golem_walk': load_animation_images(
        'mobs/Golem/GolemIdle', [400, 100], [100, 100], scale=2
    ),
    'golem_attack': load_animation_images(
        'mobs/Golem/GolemAttack', [700, 100], [100, 100], scale=2
    ),
    'golem_hit': load_animation_images(
        'mobs/Golem/GolemBlock', [800, 100], [100, 100], scale=2
    ),
    'golem_block': load_animation_images(
        'mobs/Golem/GolemBlock', [800, 100], [100, 100], scale=2
    ),
    'golem_dead': load_animation_images(
        'mobs/Golem/GolemDead', [1400, 100], [100, 100], scale=2
    ),
    'golem_glowing': load_animation_images(
        'mobs/Golem/GolemGlowing', [800, 100], [100, 100], scale=2
    ),
    'golem_shockwave_attack': load_animation_images(
        'mobs/Golem/GolemLaser', [700, 100], [100, 100], scale=2
    ),
    'golem_arm_shoot': load_animation_images(
        'mobs/Golem/GolemArmShoot', [900, 100], [100, 100], scale=2
    ),
    'golem_arm': load_animation_images(
        'mobs/Golem/Arm', [100, 100], [100, 100], scale=1
    )
}
