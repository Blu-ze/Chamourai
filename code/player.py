import pygame
import animation
from weapon import Weapon

MAX_HP         = 50
PLAYER_DAMAGE  = 25
PLAYER_SPEED   = 4
DODGE_SPEED    = 8    # vitesse de déplacement pendant l'esquive
DODGE_COOLDOWN = 1000  # ms avant de pouvoir esquiver à nouveau
DODGE_ANIMATION_SPEED = 60  # ms entre chaque frame de l'esquive

class Player(animation.AnimateSprite):
    def __init__(self, x, y, animation_speed, skin='player', interface=None):
        super().__init__(skin, animation_speed)
        self.position = pygame.math.Vector2(x, y)
        self.old_position = self.position.copy()
        self.speed = PLAYER_SPEED
        self.damage = PLAYER_DAMAGE
        self.state = "idle"
        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 20)
        self.weapon = Weapon('katana', x, y, 35, interface)
        self.interface = interface
        self._last_walk_sound = 0
        self._walk_sound_delay = 400  # ms entre chaque son de pas

        self.hp    = MAX_HP
        self.alive = True
        self.key_count = 0
        self.collected_keys = set()

        # ── Esquive ───────────────────────────────────────────────────────────
        self.dodging        = False            # esquive en cours
        self.invincible     = False            # invincibilité pendant l'esquive
        self._dodge_dir     = pygame.math.Vector2(0, 0)
        self._dodge_frame   = 0                # frame courante de l'anim jump
        self._dodge_last_ms = 0                # timestamp dernière frame anim
        self._dodge_used_ms = -DODGE_COOLDOWN  # timestamp fin de la dernière esquive

        # Frames de l'animation jump (même structure que walk : moitié droite / moitié gauche)
        self._jump_frames = animation.animations.get(f'{skin}_jump', [])

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

    def get_dodge_state(self):
        return {
            "dodging": self.dodging,
            "dodge_frame": self._dodge_frame,
        }

    def apply_remote_dodge_animation(self, dodging, dodge_frame):
        if not dodging:
            self.update_animation()
            return

        frames = self._jump_frames
        if not frames:
            self.update_animation()
            return

        frame = int(dodge_frame or 0)
        frame = max(0, min(frame, len(frames) - 1))
        self.image = frames[frame]

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

        # Declenche l'esquive avant d'appliquer un deplacement classique.
        if keys[pygame.K_SPACE] and now - self._dodge_used_ms >= DODGE_COOLDOWN:
            self._start_dodge(now, map_manager)
            return

        moving = False
        now = pygame.time.get_ticks()

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
            # Jouer le son de marche
            if self.interface and 'walk' in self.interface.sounds:
                if now - self._last_walk_sound > self._walk_sound_delay:
                    self.interface.sounds['walk'].play()
                    self._last_walk_sound = now
        else:
            self.state = "idle"
            self.current_image = 0

        # Mise a jour de l'arme
        self.weapon.move(self.position.x, self.position.y)
        new_direction = self.weapon.rotate(self.position, map_manager)
        self.set_direction(new_direction)
        self.weapon.direction = new_direction

        self.update_animation()
        self.weapon.update()
        self.update()

    # ── Esquive ───────────────────────────────────────────────────────────────

    def _start_dodge(self, now, map_manager):
        self.dodging = True
        self.invincible = True
        self.state = "dodge"
        if self.interface and 'dash' in self.interface.sounds:
            self.interface.sounds['dash'].play()

        # Direction opposée à la souris
        mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
        player_screen_pos = pygame.math.Vector2(map_manager.world_to_screen(self.position))
        dodge_dir = player_screen_pos - mouse_pos
        if dodge_dir.length_squared() == 0:
            dodge_dir = pygame.math.Vector2(-1 if self.direction == 'right' else 1, 0)
        self._dodge_dir = dodge_dir.normalize()

        self._dodge_frame = 0 if self.direction == 'right' else len(self._jump_frames) // 2
        self._dodge_last_ms = now
        self._dodge_last_ms = now

    def _update_dodge(self, map_manager, now):
        frames    = self._jump_frames
        half      = len(frames) // 2
        frame_end = half if self.direction == 'right' else len(frames)

        # Avance la position
        self.position.x += self._dodge_dir.x * DODGE_SPEED
        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom
        if self.feet.collidelist(map_manager.collisions) > -1:
            self.position.x -= self._dodge_dir.x * DODGE_SPEED  # annule si collision

        self.position.y += self._dodge_dir.y * DODGE_SPEED
        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom
        if self.feet.collidelist(map_manager.collisions) > -1:
            self.position.y -= self._dodge_dir.y * DODGE_SPEED

        # Avance l'animation
        if now - self._dodge_last_ms > DODGE_ANIMATION_SPEED:
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

#test
