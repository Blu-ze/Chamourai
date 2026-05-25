import pygame
import animation
import math

class Weapon(animation.AnimateSprite):
    def __init__(self, weapon_name, x, y, animation_speed,  interface=None):
        super().__init__(weapon_name, animation_speed, True)
        self.damage = 0
        self.position = pygame.math.Vector2(x, y)
        self.interface = interface

        self.original_image_right = self.images[0]
        self.original_image_left = self.images[len(self.images) // 2]

        handle_x = 60
        handle_y = 68

        w, h = self.original_image_right.get_size()
        image_center = pygame.math.Vector2(w / 2, h / 2)

        self.handle_offset = pygame.math.Vector2(
            handle_x - image_center.x,
            handle_y - image_center.y
        )

        self.angle = 0

    def move(self, x, y):
        self.position = pygame.math.Vector2(x, y)

    def hit(self):
        if not self.animation:  # on ne relance que si l'animation est terminée
            self.start_animation()
            # Jouer le son du slash
            if self.interface and 'slash' in self.interface.sounds:
                self.interface.sounds['slash'].play()

    def update(self):
        self.animate_hit()
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

        new_direction = 'right' if dx >= 0 else 'left'
        self.direction = new_direction

        if not self.animation:
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

        return new_direction

    def apply_remote(self, x, y, angle, direction, animating):
        """Met à jour l'arme d'un joueur distant (sans souris ni map_manager)."""
        self.position = pygame.math.Vector2(x, y)
        self.direction = direction
        self.angle = angle

        if direction == 'right':
            base_image = self.original_image_right
        else:
            base_image = self.original_image_left

        if animating and not self.animation:
            self.start_animation()

        if not self.animation:
            self.image = pygame.transform.rotate(base_image, self.angle - 90)

        self.animate_hit()

        rotated_offset = self.handle_offset.rotate(-self.angle + 90)
        self.rect = self.image.get_rect(
            center=(
                self.position[0] - rotated_offset.x,
                self.position[1] - rotated_offset.y + 7
            )
        )