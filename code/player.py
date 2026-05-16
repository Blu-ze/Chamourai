import pygame
import animation
from weapon import Weapon

MAX_HP = 1000

class Player(animation.AnimateSprite):
    def __init__(self, x, y, animation_speed):
        super().__init__('player', animation_speed)
        self.position = pygame.math.Vector2(x, y)
        self.old_position = self.position.copy()
        self.speed = 4
        self.state = "idle"
        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 20)
        self.weapon = Weapon('katana', x, y, 35)

        self.hp = MAX_HP
        self.alive = True

    def save_location(self):
        self.old_position = self.position.copy()

    def get_center(self):
        return pygame.math.Vector2(
            self.position.x + self.image.get_width() / 2,
            self.position.y + self.image.get_height() / 2
        )

    def take_damage(self, amount=1):
        if not self.alive:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.alive = False
            self.state = "idle"

    def move(self, map_manager):
        # Si mort, on ne bouge plus mais on continue à mettre à jour l'arme visuellement
        if not self.alive:
            self.weapon.move(self.position.x, self.position.y)
            self.weapon.rotate(self.position, map_manager)
            self.update_animation()
            self.update()
            return

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
