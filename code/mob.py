import pygame
import animation
from pathfinding import astar, build_collision_set

DETECTION_RADIUS = 400
ATTACK_RADIUS = 40
PATHFIND_INTERVAL = 500
WAYPOINT_THRESHOLD = 16
MAX_HP = 150
HIT_FLASH_DURATION = 200
ATTACK_HIT_FRAME = 7
ATTACK_LEFT_OFFSET = -30
ATTACK_LEFT_OFFSET_Y = -10

NECROMANCER_MAX_HP = 100
NECROMANCER_SPEED = 2.2
NECROMANCER_SHOOT_RADIUS = 270
NECROMANCER_TOO_CLOSE = 145
NECROMANCER_ATTACK_FRAME = 8
NECROMANCER_ATTACK_COOLDOWN = 1100
NECROMANCER_PROJECTILE_SPEED = 5.0
NECROMANCER_PROJECTILE_LIFE = 1800
NECROMANCER_PROJECTILE_SIZE = (36, 36)


class NecromancerProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_position):
        super().__init__()
        self.position = pygame.math.Vector2(x, y)
        target = pygame.math.Vector2(target_position)
        direction = target - self.position
        if direction.length_squared() == 0:
            direction = pygame.math.Vector2(1, 0)
        self.velocity = direction.normalize() * NECROMANCER_PROJECTILE_SPEED
        self.frames = animation.animations.get("necromancer_fireball", [])
        self._frame_index = 0
        self._last_frame_ms = pygame.time.get_ticks()
        self.spawned_ms = self._last_frame_ms
        self.facing_left = self.velocity.x < 0
        self.image = self._get_image()
        self.rect = self.image.get_rect(center=self.position)
        self.hitbox = pygame.Rect(0, 0, 24, 24)
        self.hitbox.center = self.position
        self._added_to_group = False
        self.active = True

    def _get_image(self):
        if not self.frames:
            return pygame.Surface(NECROMANCER_PROJECTILE_SIZE, pygame.SRCALPHA)

        frame = self.frames[self._frame_index % len(self.frames)]
        frame = pygame.transform.smoothscale(frame, NECROMANCER_PROJECTILE_SIZE)
        if self.facing_left:
            frame = pygame.transform.flip(frame, True, False)
        return frame

    def update(self, collisions=None):
        now = pygame.time.get_ticks()
        self.position += self.velocity
        self.rect.center = self.position
        self.hitbox.center = self.position

        if self.frames and now - self._last_frame_ms > 70:
            self._last_frame_ms = now
            self._frame_index = (self._frame_index + 1) % len(self.frames)
            self.image = self._get_image()
            self.rect = self.image.get_rect(center=self.position)

        if now - self.spawned_ms > NECROMANCER_PROJECTILE_LIFE:
            self.kill()
            return
        if collisions and self.hitbox.collidelist(collisions) > -1:
            self.kill()

    def kill(self):
        self.active = False
        super().kill()


class Mob(animation.AnimateSprite):
    def __init__(self, name, x, y, animation_speed):
        super().__init__(name, animation_speed)
        self.mob_type = name
        self.anim_prefix = name
        self.position = pygame.math.Vector2(x, y)
        self.rect.center = self.position
        self.speed = NECROMANCER_SPEED if name == "necromancer" else 2.0
        self.feet = pygame.Rect(0, 0, max(1, self.rect.width * 0.5), 12)
        hitbox_size = 42 if name == "necromancer" else 32
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.state = "idle"
        self.path = []
        self.blocked_cells = set()
        self._last_pathfind_ms = 0
        self.old_position = self.position.copy()
        self._frame_index = 0
        self._last_frame_ms = pygame.time.get_ticks()

        self.hp = NECROMANCER_MAX_HP if name == "necromancer" else MAX_HP
        self.alive = True
        self.dead = False

        self.is_hit = False
        self.hit_anim_until = 0
        self._position_hitbox()

        self._prev_state = "idle"
        self._attack_hit_done = False
        self.projectiles = []
        self._projectile_shot_done = False
        self._last_projectile_ms = -NECROMANCER_ATTACK_COOLDOWN
        self._attack_target = self.position.copy()

    def init_pathfinding(self, collisions):
        self.blocked_cells = build_collision_set(collisions)

    def update_ai(self, player_position, collisions, now_ms, other_mobs=None):
        if not self.alive:
            return
        if self.mob_type == "necromancer":
            self._update_necromancer_ai(player_position, collisions, now_ms, other_mobs)
            return

        try:
            dist = self.position.distance_to(player_position)
        except Exception:
            return

        if dist <= ATTACK_RADIUS:
            self.state = "attack"
        elif dist <= DETECTION_RADIUS:
            self.state = "chase"
        else:
            self.state = "idle"
            self.path = []

        if self.state == "chase":
            self._chase(player_position, collisions, now_ms, other_mobs)
        elif self.state == "attack":
            self.path = []
            dx = player_position.x - self.position.x
            self.set_direction("left" if dx < 0 else "right")

    def _update_necromancer_ai(self, player_position, collisions, now_ms, other_mobs=None):
        try:
            player_position = pygame.math.Vector2(player_position)
            dist = self.position.distance_to(player_position)
        except Exception:
            return

        dx = player_position.x - self.position.x
        self.set_direction("left" if dx < 0 else "right")

        if dist > DETECTION_RADIUS:
            self.state = "idle"
            self.path = []
            return

        if dist < NECROMANCER_TOO_CLOSE:
            self.state = "flee"
            self.path = []
            self._move_directly(self.position - player_position, collisions, other_mobs)
            return

        if dist > NECROMANCER_SHOOT_RADIUS:
            self.state = "chase"
            self._chase(player_position, collisions, now_ms, other_mobs)
            return

        self.state = "attack"
        self.path = []
        self._attack_target = player_position.copy()

    def _chase(self, player_position, collisions, now_ms, other_mobs=None):
        if now_ms - self._last_pathfind_ms > PATHFIND_INTERVAL or not self.path:
            self._last_pathfind_ms = now_ms
            try:
                new_path = astar(
                    (self.position.x, self.position.y),
                    (player_position.x, player_position.y),
                    self.blocked_cells,
                )
                self.path = new_path if new_path else []
            except Exception:
                self.path = []

        if not self.path:
            return

        target = pygame.math.Vector2(self.path[0])
        direction_vec = target - self.position

        if direction_vec.length() < WAYPOINT_THRESHOLD:
            self.path.pop(0)
            if not self.path:
                return
            target = pygame.math.Vector2(self.path[0])
            direction_vec = target - self.position

        self._move_directly(direction_vec, collisions, other_mobs)

        if direction_vec.x < -0.1:
            self.set_direction("left")
        elif direction_vec.x > 0.1:
            self.set_direction("right")

    def _move_directly(self, direction_vec, collisions, other_mobs=None):
        if direction_vec.length_squared() == 0:
            return
        direction_vec = direction_vec.normalize()
        self.old_position = self.position.copy()

        self.position.x += direction_vec.x * self.speed
        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom
        self._position_hitbox()
        if (collisions and self.feet.collidelist(collisions) > -1) or self._collides_with_mobs(other_mobs):
            self.position.x = self.old_position.x
            self.rect.center = self.position
            self.feet.midbottom = self.rect.midbottom
            self._position_hitbox()

        self.position.y += direction_vec.y * self.speed
        self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom
        self._position_hitbox()
        if (collisions and self.feet.collidelist(collisions) > -1) or self._collides_with_mobs(other_mobs):
            self.position.y = self.old_position.y
            self.rect.center = self.position
            self.feet.midbottom = self.rect.midbottom
            self._position_hitbox()

    def update(self):
        now = pygame.time.get_ticks()

        if self.dead:
            finished = self._animate_once(f"{self.anim_prefix}_dead")
            if finished:
                self.kill()
            self._position_rect()
            return

        if self.is_hit:
            self._animate_frames(f"{self.anim_prefix}_hit")
            if now > self.hit_anim_until:
                self.is_hit = False
                self._frame_index = 0
            self._position_rect()
            return

        if self.state == "attack":
            if self._prev_state != "attack":
                self._frame_index = 0
                self._last_frame_ms = now
                self._attack_hit_done = False
                self._projectile_shot_done = False
            self._prev_state = "attack"
            self._animate_frames(f"{self.anim_prefix}_attack")
            self._shoot_projectile_if_ready(now)
            self._position_rect(attacking=True)
            return

        self._prev_state = self.state

        if self.state in ("chase", "flee"):
            self._animate_frames(f"{self.anim_prefix}_walk")
        else:
            self._animate_frames(f"{self.anim_prefix}_idle")
        self._position_rect()

    @property
    def is_attack_hit_frame(self):
        if self.mob_type != "skeleton":
            return False
        if self.state != "attack" or self._attack_hit_done:
            return False
        if self._frame_index == ATTACK_HIT_FRAME:
            self._attack_hit_done = True
            return True
        return False

    @property
    def is_ranged(self):
        return self.mob_type == "necromancer"

    def _position_rect(self, attacking=False):
        if self.mob_type == "necromancer":
            self.rect.center = self.position
        elif attacking and self.direction == "left":
            self.rect.center = (self.position.x + ATTACK_LEFT_OFFSET, self.position.y + ATTACK_LEFT_OFFSET_Y)
        elif attacking:
            self.rect.center = (self.position.x, self.position.y + ATTACK_LEFT_OFFSET_Y)
        else:
            self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom
        self._position_hitbox()

    def _position_hitbox(self):
        self.hitbox.center = self.position

    def _collides_with_mobs(self, other_mobs):
        if not other_mobs:
            return False
        for mob in other_mobs:
            if mob is self or not mob.alive or mob.dead:
                continue
            if self.hitbox.colliderect(mob.hitbox):
                return True
        return False

    def _animate_frames(self, anim_key):
        frames = animation.animations.get(anim_key)
        if not frames:
            return

        now = pygame.time.get_ticks()
        if now - self._last_frame_ms > self.animation_speed:
            self._last_frame_ms = now
            next_index = (self._frame_index + 1) % len(frames)
            if anim_key.endswith("_attack") and next_index == 0:
                self._attack_hit_done = False
                self._projectile_shot_done = False
            self._frame_index = next_index

        self._frame_index = self._frame_index % len(frames)
        raw_frame = frames[self._frame_index]
        self.image = pygame.transform.flip(raw_frame, True, False) if self.direction == "left" else raw_frame

    def _animate_once(self, anim_key):
        frames = animation.animations.get(anim_key)
        if not frames:
            return True

        now = pygame.time.get_ticks()
        if now - self._last_frame_ms > self.animation_speed:
            self._last_frame_ms = now
            self._frame_index += 1

        clamped = min(self._frame_index, len(frames) - 1)
        raw_frame = frames[clamped]
        self.image = pygame.transform.flip(raw_frame, True, False) if self.direction == "left" else raw_frame
        return self._frame_index >= len(frames)

    def _shoot_projectile_if_ready(self, now):
        if self.mob_type != "necromancer" or self._projectile_shot_done:
            return
        if self._frame_index != NECROMANCER_ATTACK_FRAME:
            return
        if now - self._last_projectile_ms < NECROMANCER_ATTACK_COOLDOWN:
            return
        self._projectile_shot_done = True
        self._last_projectile_ms = now
        self.projectiles.append(
            NecromancerProjectile(
                self.position.x,
                self.position.y - 12,
                self._attack_target,
            )
        )

    def take_damage(self, amount=1):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.dead = True
            self._frame_index = 0
            self._last_frame_ms = pygame.time.get_ticks()
        else:
            self.is_hit = True
            self.hit_anim_until = pygame.time.get_ticks() + HIT_FLASH_DURATION
            self._frame_index = 0
