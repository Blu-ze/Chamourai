import pygame
import animation
from weapon import Weapon

MAX_HP         = 100
DODGE_SPEED    = 8     # vitesse de déplacement pendant l'esquive
DODGE_COOLDOWN = 2000  # ms avant de pouvoir esquiver à nouveau

class Player(animation.AnimateSprite):
    def __init__(self, x, y, animation_speed, skin='player'):
        super().__init__(skin, animation_speed)
        self.position = pygame.math.Vector2(x, y)
        self.old_position = self.position.copy()
        self.speed = 4
        self.state = "idle"
        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 20)
        self.weapon = Weapon('katana', x, y, 35)

        self.hp    = MAX_HP
        self.alive = True

        # ── Esquive ───────────────────────────────────────────────────────────
        self.dodging        = False            # esquive en cours
        self.invincible     = False            # invincibilité pendant l'esquive
        self._dodge_dir     = 0                # -1 = gauche, +1 = droite
        self._dodge_frame   = 0                # frame courante de l'anim jump
        self._dodge_last_ms = 0                # timestamp dernière frame anim
        self._dodge_used_ms = -DODGE_COOLDOWN  # timestamp fin de la dernière esquive

        # Frames de l'animation jump (même structure que walk : moitié droite / moitié gauche)
        self._jump_frames = animation.animations.get('player_jump', [])

    # ── Utilitaires ───────────────────────────────────────────────────────────

    def save_location(self):
        self.old_position = self.position.copy()

    def get_center(self):
        return pygame.math.Vector2(
            self.position.x + self.image.get_width() / 2,
            self.position.y + self.image.get_height() / 2
        )

    def take_damage(self, amount=1):
        if not self.alive or self.invincible:
            return
        self.hp = max(0, self.hp - amount)
        if self.hp <= 0:
            self.alive = False
            self.state = "idle"

    # ── Logique principale ────────────────────────────────────────────────────

    def move(self, map_manager):
        if not self.alive:
            self.weapon.move(self.position.x, self.position.y)
            self.weapon.rotate(self.position, map_manager)
            self.update_animation()
            self.update()
            return

        now = pygame.time.get_ticks()

        # ── Esquive en cours ──────────────────────────────────────────────────
        if self.dodging:
            self._update_dodge(map_manager, now)
            return

        keys   = pygame.key.get_pressed()
        moving = False

        # Axe X
        if keys[pygame.K_q]:
            self.position.x -= self.speed
            self.rect.center = self.position
            self.feet.midbottom = self.rect.midbottom
            if self.feet.collidelist(map_manager.collisions) > -1:
                self.position.x += self.speed
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

        # ── Déclenchement de l'esquive ────────────────────────────────────────
        if keys[pygame.K_SPACE] and now - self._dodge_used_ms >= DODGE_COOLDOWN:
            self._start_dodge(now)
            return

        self.weapon.move(self.position.x, self.position.y)
        new_direction = self.weapon.rotate(self.position, map_manager)
        self.set_direction(new_direction)
        self.weapon.direction = new_direction

        self.update_animation()
        self.weapon.update()
        self.update()

    # ── Esquive ───────────────────────────────────────────────────────────────

    def _start_dodge(self, now):
        self.dodging    = True
        self.invincible = True
        # Direction opposée à celle du regard
        self._dodge_dir   = -1 if self.direction == 'right' else 1
        self._dodge_frame = 0 if self.direction == 'right' else len(self._jump_frames) // 2
        self._dodge_last_ms = now

    def _update_dodge(self, map_manager, now):
        frames    = self._jump_frames
        half      = len(frames) // 2
        frame_end = half if self.direction == 'right' else len(frames)

        # Avance la position
        self.position.x += self._dodge_dir * DODGE_SPEED
        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom
        if self.feet.collidelist(map_manager.collisions) > -1:
            self.position.x -= self._dodge_dir * DODGE_SPEED  # annule si collision

        # Avance l'animation
        if now - self._dodge_last_ms > self.animation_speed:
            self._dodge_last_ms = now
            self._dodge_frame  += 1

        # Fin de l'esquive : dernière frame atteinte
        if self._dodge_frame >= frame_end:
            self.dodging        = False
            self.invincible     = False
            self._dodge_used_ms = now
            self.state          = "idle"
            self.weapon.move(self.position.x, self.position.y)
            new_direction = self.weapon.rotate(self.position, map_manager)
            self.set_direction(new_direction)
            self.weapon.direction = new_direction
            self.update_animation()
            self.weapon.update()
            self.update()
            return

        # Affichage de la frame courante
        idx = min(self._dodge_frame, frame_end - 1)
        if 0 <= idx < len(frames):
            self.image = frames[idx]

        self.weapon.move(self.position.x, self.position.y)
        self.weapon.rotate(self.position, map_manager)
        self.weapon.update()
        self.update()

    # ─────────────────────────────────────────────────────────────────────────

    def update(self):
        self.rect.center = (self.position.x, self.position.y)
        self.feet.midbottom = self.rect.midbottom
