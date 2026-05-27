import pygame
import animation
import math

CHARGE_DURATION_MS = 450
CHARGED_DAMAGE_MULTIPLIER = 4


class Weapon(animation.AnimateSprite):
    def __init__(self, weapon_name, x, y, animation_speed,  interface=None):
        super().__init__(weapon_name, animation_speed, True)
        self.damage = 0
        self.position = pygame.math.Vector2(x, y)
        self.interface = interface

        self.normal_images = self.images
        self.charged_images = animation.animations.get(f'{weapon_name}_charge', self.normal_images)
        self.original_image_right = self.normal_images[0]
        self.original_image_left = self.normal_images[len(self.normal_images) // 2]

        handle_x = 60
        handle_y = 68

        w, h = self.original_image_right.get_size()
        image_center = pygame.math.Vector2(w / 2, h / 2)

        self.handle_offset = pygame.math.Vector2(
            handle_x - image_center.x,
            handle_y - image_center.y
        )

        self.angle = 0
        self.attack_id = 0
        self.charging = False
        self.charge_started_ms = 0
        self.charged_attack = False
        self.attack_damage_multiplier = 1
        self.hit_targets = set()
        self.remote_attack_id = -1

    def move(self, x, y):
        self.position = pygame.math.Vector2(x, y)

    def begin_charge(self):
        if not self.animation:
            self.charging = True
            self.charge_started_ms = pygame.time.get_ticks()

    def cancel_charge(self):
        self.charging = False

    def charge_ratio(self):
        if not self.charging:
            return 0
        elapsed = pygame.time.get_ticks() - self.charge_started_ms
        return min(1, elapsed / CHARGE_DURATION_MS)

    def release_charge(self):
        if not self.charging:
            return False
        held_long_enough = pygame.time.get_ticks() - self.charge_started_ms >= CHARGE_DURATION_MS
        self.charging = False
        return self.hit(charged=held_long_enough)

    def hit(self, charged=False):
        if not self.animation:  # on ne relance que si l'animation est terminée
            self.images = self.charged_images if charged else self.normal_images
            self.charged_attack = charged
            self.attack_damage_multiplier = CHARGED_DAMAGE_MULTIPLIER if charged else 1
            self.hit_targets.clear()
            self.attack_id += 1
            self.start_animation()
            # Jouer le son du slash
            if self.interface and 'slash' in self.interface.sounds:
                self.interface.sounds['slash'].play()
            return True
        return False

    def can_damage(self, mob):
        target_id = id(mob)
        if target_id in self.hit_targets:
            return False
        self.hit_targets.add(target_id)
        return True

    def update(self):
        was_animating = self.animation
        self.animate_hit()
        if was_animating and not self.animation:
            self.images = self.normal_images
            self.charged_attack = False
            self.attack_damage_multiplier = 1
        # Hitbox active seulement pendant l'animation
        if self.animation:
            self.hitbox = self.rect.inflate(-10, -10)
        else:
            self.hitbox = None

    def rotate(self, player_world_pos, map_manager):
        mouse_x, mouse_y = pygame.mouse.get_pos()
        player_screen_x, player_screen_y = map_manager.world_to_screen(player_world_pos)

        dx = mouse_x - player_screen_x
        dy = mouse_y - player_screen_y

        if not self.animation:
            self.direction = 'right' if dx >= 0 else 'left'
            self.angle = math.degrees(math.atan2(-dy, dx))

            if self.direction == 'right':
                base_image = self.original_image_right
            else:
                base_image = self.original_image_left

            self.image = pygame.transform.rotate(base_image, self.angle - 90)

        rotated_offset = self.handle_offset.rotate(-self.angle + 90)

        self.rect = self.image.get_rect(
            center=(
                self.position[0] - rotated_offset.x,
                self.position[1] - rotated_offset.y + 7
            )
        )

        return self.direction

    def apply_remote(self, x, y, angle, direction, animating, charged=False, attack_id=None):
        """Met à jour l'arme d'un joueur distant (sans souris ni map_manager)."""
        self.position = pygame.math.Vector2(x, y)

        is_new_attack = attack_id is None or attack_id != self.remote_attack_id
        if animating and is_new_attack:
            self.direction = direction
            self.angle = angle
            self.images = self.charged_images if charged else self.normal_images
            self.charged_attack = charged
            self.remote_attack_id = attack_id
            self.start_animation()

        if not self.animation:
            self.images = self.normal_images
            self.direction = direction
            self.angle = angle
            if self.direction == 'right':
                base_image = self.original_image_right
            else:
                base_image = self.original_image_left
            self.image = pygame.transform.rotate(base_image, self.angle - 90)

        self.animate_hit()

        rotated_offset = self.handle_offset.rotate(-self.angle + 90)
        self.rect = self.image.get_rect(
            center=(
                self.position[0] - rotated_offset.x,
                self.position[1] - rotated_offset.y + 7
            )
        )
