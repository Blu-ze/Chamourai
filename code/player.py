import pygame
import animation

class Player(animation.AnimateSprite):
    def __init__(self, x, y, animation_speed):
        super().__init__('player', animation_speed, False)
        self.position = pygame.math.Vector2(x, y)
        self.velocity = pygame.math.Vector2(0, 0)
        self.speed = 4
        self.old_position = self.position.copy()
        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 20)

    def save_location(self):
        self.old_position = self.position.copy()

    def move(self, collisions):
        moved = False

        # X
        if self.velocity.x != 0:
            self.position.x += self.velocity.x
            self.rect.center = self.position
            self.feet.midbottom = self.rect.midbottom

            if self.feet.collidelist(collisions) > -1:
                self.position.x -= self.velocity.x
            else:
                moved = True

        # Y
        if self.velocity.y != 0:
            self.position.y += self.velocity.y
            self.rect.center = self.position
            self.feet.midbottom = self.rect.midbottom

            if self.feet.collidelist(collisions) > -1:
                self.position.y -= self.velocity.y
            else:
                moved = True

        # update final
        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom

        if moved:
            self.start_animation()

    def update(self):
        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom
        self.animate_walk()

    def move_back(self):
        self.position = self.old_position
        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom