import pygame
import animation
from weapon import Weapon

class Player(animation.AnimateSprite):
    def __init__(self, x, y, animation_speed, skin='player'):
        super().__init__(skin, animation_speed)
        self.position = pygame.math.Vector2(x, y)
        self.old_position = self.position.copy()
        self.speed = 4
        self.state = "idle"
        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 20)
        self.weapon = Weapon('katana', x, y, 35)

    def save_location(self):
        self.old_position = self.position.copy()

    def get_center(self):
        return pygame.math.Vector2(
            self.position.x + self.image.get_width() / 2,
            self.position.y + self.image.get_height() / 2
        )

    def move(self, map_manager):
        keys = pygame.key.get_pressed()
        moving = False

        # Axe X
        if keys[pygame.K_q]:
            self.position.x -= self.speed
            self.rect.center = self.position
            self.feet.midbottom = self.rect.midbottom
            if self.feet.collidelist(map_manager.collisions) > -1:
                self.position.x += self.speed  # annule le mouvement
            else:
                moving = True

        if keys[pygame.K_d]:
            self.position.x += self.speed
            self.rect.center = self.position
            self.feet.midbottom = self.rect.midbottom
            if self.feet.collidelist(map_manager.collisions) > -1:
                self.position.x -= self.speed
            else:
                moving = True

        # Axe Y
        if keys[pygame.K_z]:
            self.position.y -= self.speed
            self.rect.center = self.position
            self.feet.midbottom = self.rect.midbottom
            if self.feet.collidelist(map_manager.collisions) > -1:
                self.position.y += self.speed
            else:
                moving = True

        if keys[pygame.K_s]:
            self.position.y += self.speed
            self.rect.center = self.position
            self.feet.midbottom = self.rect.midbottom
            if self.feet.collidelist(map_manager.collisions) > -1:
                self.position.y -= self.speed
            else:
                moving = True

        if moving:
            self.state = "walk"
        else:
            self.state = "idle"
            self.current_image = 0

        self.weapon.move(self.position.x, self.position.y)

        new_direction = self.weapon.rotate(self.position, map_manager)
        self.set_direction(new_direction)
        self.weapon.direction = new_direction

        self.update_animation()
        self.weapon.update()
        self.update()

    def update(self):
        self.rect.center = (self.position.x, self.position.y)
        self.feet.midbottom = self.rect.midbottom