import pygame
import animation
import math
from pathfinding import astar, build_collision_set

DETECTION_RADIUS = 400
ATTACK_RADIUS = 40
PATHFIND_INTERVAL = 500
WAYPOINT_THRESHOLD = 16
FINAL_APPROACH_RADIUS = 56
MAX_HP = 150
HIT_FLASH_DURATION = 200
ATTACK_HIT_FRAME = 7
ATTACK_LEFT_OFFSET = -30
ATTACK_LEFT_OFFSET_Y = -10
SKELETON_SPEED = 2.4
SKELETON_ATTACK_SPEED_MULTIPLIER = 0.8
SKELETON_RING_SLOTS = 8
SKELETON_RING_DISTANCE = 34
SKELETON_RING_GAP = 38

NECROMANCER_MAX_HP = 100
NECROMANCER_SPEED = 2.2
NECROMANCER_SHOOT_RADIUS = 270
NECROMANCER_TOO_CLOSE = 145
NECROMANCER_ATTACK_FRAME = 8
NECROMANCER_ATTACK_COOLDOWN = 1100
NECROMANCER_PROJECTILE_SPEED = 5.0
NECROMANCER_PROJECTILE_LIFE = 1800
NECROMANCER_PROJECTILE_SIZE = (36, 36)
SKELETON_TYPES = {"skeleton", "skeleton_boss"}
NECROMANCER_TYPES = {"necromancer", "necromancer_boss"}
GOLEM_TYPES = {"golem"}
BOSS_TYPES = {"skeleton_boss", "necromancer_boss", "golem"}
KEY_DROP_TYPES = {"skeleton_boss", "necromancer_boss"}
BOSS_HP_MULTIPLIER = 3
BOSS_SPEED_MULTIPLIER = 1.5
BOSS_ANIMATION_SPEED_MULTIPLIER = 0.7
BOSS_ATTACK_COOLDOWN = 700
GOLEM_MAX_HP = 1000
GOLEM_DETECTION_RADIUS = 600
GOLEM_RANGED_RADIUS = 360
GOLEM_MELEE_RADIUS = 108
GOLEM_MELEE_HIT_FRAME = 4
GOLEM_ATTACK_COOLDOWN = 900
GOLEM_ARM_SHOOT_FRAME = 5
GOLEM_ARM_SPEED = 7.0
GOLEM_PROJECTILE_LIFE = 2200
GOLEM_SHOCKWAVE_FRAME = 4
GOLEM_SHOCKWAVE_SPEED = 4
GOLEM_SHOCKWAVE_MAX_RADIUS = 370
GOLEM_SHOCKWAVE_THICKNESS = 18
GOLEM_SHOCKWAVE_HALF_ANGLE = 62
GOLEM_DEATH_ANIMATION_SPEED = 160
GOLEM_PHASE_TWO_SPEED_MULTIPLIER = 1.5
GOLEM_PHASE_TWO_ATTACK_COOLDOWN = 550
GOLEM_PHASE_TWO_DAMAGE = 2


class NecromancerProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_position, animation_key="necromancer_fireball"):
        super().__init__()
        self.position = pygame.math.Vector2(x, y)
        target = pygame.math.Vector2(target_position)
        direction = target - self.position
        if direction.length_squared() == 0:
            direction = pygame.math.Vector2(1, 0)
        self.velocity = direction.normalize() * NECROMANCER_PROJECTILE_SPEED
        self.frames = animation.animations.get(animation_key, [])
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


class GolemProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, target_position, animation_key, size, speed, hitbox_size, damage=1):
        super().__init__()
        self.position = pygame.math.Vector2(x, y)
        direction = pygame.math.Vector2(target_position) - self.position
        if direction.length_squared() == 0:
            direction = pygame.math.Vector2(1, 0)
        self.velocity = direction.normalize() * speed
        self.frames = animation.animations.get(animation_key, [])
        self.size = size
        self._frame_index = 0
        self._last_frame_ms = pygame.time.get_ticks()
        self.spawned_ms = self._last_frame_ms
        self.angle = pygame.math.Vector2(1, 0).angle_to(self.velocity)
        self.image = self._get_image()
        self.rect = self.image.get_rect(center=self.position)
        self.hitbox = pygame.Rect(0, 0, hitbox_size[0], hitbox_size[1])
        self.hitbox.center = self.position
        self._added_to_group = False
        self.active = True
        self.damage = damage

    def _get_image(self):
        if not self.frames:
            return pygame.Surface(self.size, pygame.SRCALPHA)
        frame = pygame.transform.smoothscale(
            self.frames[self._frame_index % len(self.frames)],
            self.size
        )
        return pygame.transform.rotate(frame, self.angle)

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
        if now - self.spawned_ms > GOLEM_PROJECTILE_LIFE:
            self.kill()
            return
        if collisions and self.hitbox.collidelist(collisions) > -1:
            self.kill()

    def kill(self):
        self.active = False
        super().kill()


class GolemShockwave(pygame.sprite.Sprite):
    def __init__(self, x, y, target_position, damage=1):
        super().__init__()
        self.position = pygame.math.Vector2(x, y)
        direction = pygame.math.Vector2(target_position) - self.position
        if direction.length_squared() == 0:
            direction = pygame.math.Vector2(1, 0)
        self.direction = direction.normalize()
        self.radius = 24
        self.active = True
        self.damage = damage
        self._added_to_group = False
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self._refresh_image()

    def _refresh_image(self):
        padding = GOLEM_SHOCKWAVE_THICKNESS + 5
        size = (GOLEM_SHOCKWAVE_MAX_RADIUS + padding) * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        arc_rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)
        arc_rect.center = (center, center)
        heading = math.atan2(-self.direction.y, self.direction.x)
        half_angle = math.radians(GOLEM_SHOCKWAVE_HALF_ANGLE)
        pygame.draw.arc(
            self.image,
            (48, 171, 255, 230),
            arc_rect,
            heading - half_angle,
            heading + half_angle,
            GOLEM_SHOCKWAVE_THICKNESS,
        )
        self.rect = self.image.get_rect(center=self.position)

    def update(self, collisions=None):
        self.radius += GOLEM_SHOCKWAVE_SPEED
        if self.radius > GOLEM_SHOCKWAVE_MAX_RADIUS:
            self.kill()
            return
        self._refresh_image()

    def hits_player(self, player_rect):
        to_player = pygame.math.Vector2(player_rect.center) - self.position
        if to_player.length_squared() == 0:
            return True
        player_extent = max(player_rect.width, player_rect.height) / 2
        if abs(to_player.length() - self.radius) > GOLEM_SHOCKWAVE_THICKNESS + player_extent:
            return False
        return abs(self.direction.angle_to(to_player)) <= GOLEM_SHOCKWAVE_HALF_ANGLE

    def kill(self):
        self.active = False
        super().kill()


class Mob(animation.AnimateSprite):
    def __init__(self, name, x, y, animation_speed):
        super().__init__(name, animation_speed)
        self.mob_type = name
        self.anim_prefix = name
        self.is_boss = name in BOSS_TYPES
        self.drops_key = name in KEY_DROP_TYPES
        self.key_dropped = False
        self.position = pygame.math.Vector2(x, y)
        self.rect.center = self.position
        if name in NECROMANCER_TYPES:
            base_speed = NECROMANCER_SPEED
        elif name in SKELETON_TYPES:
            base_speed = SKELETON_SPEED
        else:
            base_speed = 2.0
        self.speed = base_speed * BOSS_SPEED_MULTIPLIER if self.is_boss else base_speed
        if self.is_boss:
            self.animation_speed = max(1, int(self.animation_speed * BOSS_ANIMATION_SPEED_MULTIPLIER))
        self.feet = pygame.Rect(0, 0, max(1, self.rect.width * 0.5), 12)
        hitbox_size = 42 if name in NECROMANCER_TYPES else 32
        if self.is_boss:
            hitbox_size = int(hitbox_size * 1.5)
        if name == "golem":
            hitbox_size = 72
        self.hitbox = pygame.Rect(0, 0, hitbox_size, hitbox_size)
        self.state = "idle"
        self.path = []
        self.blocked_cells = set()
        self._last_pathfind_ms = 0
        self.old_position = self.position.copy()
        self._frame_index = 0
        self._last_frame_ms = pygame.time.get_ticks()

        base_hp = NECROMANCER_MAX_HP if name in NECROMANCER_TYPES else MAX_HP
        self.max_hp = base_hp * BOSS_HP_MULTIPLIER if self.is_boss else base_hp
        if name == "golem":
            self.max_hp = GOLEM_MAX_HP
        self.hp = self.max_hp
        self.alive = True
        self.dead = False
        self.death_animation_finished = False

        self.is_hit = False
        self.hit_anim_until = 0
        self._position_hitbox()

        self._prev_state = "idle"
        self._attack_hit_done = False
        self.projectiles = []
        self._projectile_shot_done = False
        self.attack_cooldown = BOSS_ATTACK_COOLDOWN if self.is_boss else NECROMANCER_ATTACK_COOLDOWN
        self._last_projectile_ms = -self.attack_cooldown
        self._attack_target = self.position.copy()
        self.attack_kind = None
        self.golem_phase = 1
        self._phase_transition = False
        self._last_golem_attack_ms = -GOLEM_ATTACK_COOLDOWN
        self.golem_attack_cooldown = GOLEM_ATTACK_COOLDOWN
        self._next_golem_ranged = "arm"
        self.damage = 1

    def init_pathfinding(self, collisions):
        self.blocked_cells = build_collision_set(collisions)

    def update_ai(self, player_position, collisions, now_ms, other_mobs=None):
        if not self.alive:
            return
        if self.mob_type == "golem":
            self._update_golem_ai(player_position, collisions, now_ms, other_mobs)
            return
        if self.mob_type in NECROMANCER_TYPES:
            self._update_necromancer_ai(player_position, collisions, now_ms, other_mobs)
            return
        if self.mob_type in SKELETON_TYPES:
            self._update_skeleton_ai(player_position, collisions, now_ms, other_mobs)
            return

    def _update_skeleton_ai(self, player_position, collisions, now_ms, other_mobs=None):
        try:
            player_position = pygame.math.Vector2(player_position)
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
            destination = self._skeleton_approach_position(player_position, other_mobs)
            self._chase(destination, collisions, now_ms, other_mobs)
        elif self.state == "attack":
            self.path = []
            dx = player_position.x - self.position.x
            self.set_direction("left" if dx < 0 else "right")

    def _skeleton_approach_position(self, player_position, other_mobs):
        skeletons = [
            mob for mob in (other_mobs or [self])
            if mob.alive and not mob.dead and mob.mob_type in SKELETON_TYPES
            and mob.position.distance_to(player_position) <= DETECTION_RADIUS
        ]
        skeletons.sort(key=lambda mob: mob.position.distance_to(player_position))
        if len(skeletons) <= 1:
            return player_position
        try:
            index = skeletons.index(self)
        except ValueError:
            return player_position

        ring = index // SKELETON_RING_SLOTS
        slot = index % SKELETON_RING_SLOTS
        slot_count = min(SKELETON_RING_SLOTS, len(skeletons) - ring * SKELETON_RING_SLOTS)
        angle = (2 * math.pi * slot / slot_count) + (ring % 2) * (math.pi / SKELETON_RING_SLOTS)
        radius = SKELETON_RING_DISTANCE + ring * SKELETON_RING_GAP
        return player_position + pygame.math.Vector2(math.cos(angle), math.sin(angle)) * radius

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

        if dist < NECROMANCER_TOO_CLOSE and self.mob_type != "necromancer_boss":
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

    def _update_golem_ai(self, player_position, collisions, now_ms, other_mobs=None):
        if self._phase_transition or self.state == "glowing":
            return
        try:
            player_position = pygame.math.Vector2(player_position)
            dist = self.position.distance_to(player_position)
        except Exception:
            return

        dx = player_position.x - self.position.x
        self.set_direction("left" if dx < 0 else "right")
        if self.state == "attack":
            return
        if dist > GOLEM_DETECTION_RADIUS:
            self.state = "idle"
            self.path = []
            return
        if dist > GOLEM_RANGED_RADIUS:
            self.state = "chase"
            self._chase(player_position, collisions, now_ms, other_mobs)
            return
        if now_ms - self._last_golem_attack_ms < self.golem_attack_cooldown:
            if dist > GOLEM_MELEE_RADIUS:
                self.state = "chase"
                self._chase(player_position, collisions, now_ms, other_mobs)
            else:
                self.state = "idle"
                self.path = []
            return

        self._last_golem_attack_ms = now_ms
        self._attack_target = player_position.copy()
        if dist <= GOLEM_MELEE_RADIUS:
            self.attack_kind = "melee"
        elif self.golem_phase == 2 and self._next_golem_ranged == "shockwave":
            self.attack_kind = "shockwave"
            self._next_golem_ranged = "arm"
        else:
            self.attack_kind = "arm"
            if self.golem_phase == 2:
                self._next_golem_ranged = "shockwave"
        self.state = "attack"

    def _chase(self, player_position, collisions, now_ms, other_mobs=None):
        destination = pygame.math.Vector2(player_position)
        if now_ms - self._last_pathfind_ms > PATHFIND_INTERVAL or not self.path:
            self._last_pathfind_ms = now_ms
            try:
                new_path = astar(
                    (self.position.x, self.position.y),
                    (destination.x, destination.y),
                    self.blocked_cells,
                )
                self.path = new_path if new_path else []
            except Exception:
                self.path = []

        if not self.path:
            if self.position.distance_to(destination) <= FINAL_APPROACH_RADIUS:
                self._move_directly(destination - self.position, collisions, other_mobs)
            return

        target = pygame.math.Vector2(self.path[0])
        direction_vec = target - self.position

        if direction_vec.length() < WAYPOINT_THRESHOLD:
            self.path.pop(0)
            if not self.path:
                self._move_directly(destination - self.position, collisions, other_mobs)
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
            frame_speed = GOLEM_DEATH_ANIMATION_SPEED if self.mob_type == "golem" else None
            finished = self._animate_once(f"{self.anim_prefix}_dead", frame_speed)
            if finished:
                self.death_animation_finished = True
                if self.mob_type != "golem":
                    self.kill()
            self._position_rect()
            return

        if self.mob_type == "golem" and self.state == "glowing":
            finished = self._animate_once("golem_glowing")
            if finished:
                self.golem_phase = 2
                self.speed *= GOLEM_PHASE_TWO_SPEED_MULTIPLIER
                self.golem_attack_cooldown = GOLEM_PHASE_TWO_ATTACK_COOLDOWN
                self.damage = GOLEM_PHASE_TWO_DAMAGE
                self._phase_transition = False
                self.state = "idle"
                self._frame_index = 0
                self._last_frame_ms = now
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
            frame_speed = None
            if self.mob_type in SKELETON_TYPES:
                frame_speed = max(1, int(self.animation_speed * SKELETON_ATTACK_SPEED_MULTIPLIER))
            finished = self._animate_frames(self._attack_animation_key(), frame_speed)
            self._shoot_projectile_if_ready(now)
            self._shoot_golem_projectile_if_ready()
            self._position_rect(attacking=True)
            if self.mob_type == "golem" and finished:
                self.state = "idle"
                self.attack_kind = None
                self._prev_state = "idle"
                self._frame_index = 0
            return

        self._prev_state = self.state

        if self.state in ("chase", "flee"):
            self._animate_frames(f"{self.anim_prefix}_walk")
        else:
            self._animate_frames(f"{self.anim_prefix}_idle")
        self._position_rect()

    @property
    def is_attack_hit_frame(self):
        if self.mob_type not in SKELETON_TYPES | GOLEM_TYPES:
            return False
        if self.state != "attack" or self._attack_hit_done:
            return False
        if self.mob_type == "golem" and self.attack_kind != "melee":
            return False
        hit_frame = GOLEM_MELEE_HIT_FRAME if self.mob_type == "golem" else ATTACK_HIT_FRAME
        if self._frame_index == hit_frame:
            self._attack_hit_done = True
            return True
        return False

    @property
    def attack_radius(self):
        return GOLEM_MELEE_RADIUS if self.mob_type == "golem" else ATTACK_RADIUS

    @property
    def is_ranged(self):
        return self.mob_type in NECROMANCER_TYPES

    def _position_rect(self, attacking=False):
        if self.mob_type in NECROMANCER_TYPES | GOLEM_TYPES:
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

    def _animate_frames(self, anim_key, frame_speed=None):
        frames = animation.animations.get(anim_key)
        if not frames:
            return False

        now = pygame.time.get_ticks()
        finished = False
        frame_speed = self.animation_speed if frame_speed is None else frame_speed
        if now - self._last_frame_ms > frame_speed:
            self._last_frame_ms = now
            next_index = (self._frame_index + 1) % len(frames)
            finished = next_index == 0
            if anim_key.endswith("_attack") and next_index == 0:
                self._attack_hit_done = False
                self._projectile_shot_done = False
            self._frame_index = next_index

        self._frame_index = self._frame_index % len(frames)
        raw_frame = frames[self._frame_index]
        self.image = pygame.transform.flip(raw_frame, True, False) if self.direction == "left" else raw_frame
        return finished

    def _animate_once(self, anim_key, frame_speed=None):
        frames = animation.animations.get(anim_key)
        if not frames:
            return True

        now = pygame.time.get_ticks()
        frame_speed = self.animation_speed if frame_speed is None else frame_speed
        if now - self._last_frame_ms > frame_speed:
            self._last_frame_ms = now
            self._frame_index += 1

        clamped = min(self._frame_index, len(frames) - 1)
        raw_frame = frames[clamped]
        self.image = pygame.transform.flip(raw_frame, True, False) if self.direction == "left" else raw_frame
        return self._frame_index >= len(frames)

    def _shoot_projectile_if_ready(self, now):
        if self.mob_type not in NECROMANCER_TYPES or self._projectile_shot_done:
            return
        if self._frame_index != NECROMANCER_ATTACK_FRAME:
            return
        if now - self._last_projectile_ms < self.attack_cooldown:
            return
        self._projectile_shot_done = True
        self._last_projectile_ms = now
        projectile_animation = (
            "necromancer_boss_fireball"
            if self.mob_type == "necromancer_boss"
            else "necromancer_fireball"
        )
        self.projectiles.append(
            NecromancerProjectile(
                self.position.x,
                self.position.y - 12,
                self._attack_target,
                projectile_animation,
            )
        )

    def _attack_animation_key(self):
        if self.mob_type != "golem":
            return f"{self.anim_prefix}_attack"
        if self.attack_kind == "arm":
            return "golem_arm_shoot"
        if self.attack_kind == "shockwave":
            return "golem_shockwave_attack"
        return "golem_attack"

    def _shoot_golem_projectile_if_ready(self):
        if self.mob_type != "golem" or self._projectile_shot_done:
            return
        if self.attack_kind == "arm" and self._frame_index == GOLEM_ARM_SHOOT_FRAME:
            projectile = GolemProjectile(
                self.position.x,
                self.position.y,
                self._attack_target,
                "golem_arm",
                (100, 100),
                GOLEM_ARM_SPEED,
                (46, 46),
                damage=self.damage,
            )
        elif self.attack_kind == "shockwave" and self._frame_index == GOLEM_SHOCKWAVE_FRAME:
            projectile = GolemShockwave(
                self.position.x,
                self.position.y,
                self._attack_target,
                damage=self.damage,
            )
        else:
            return
        self._projectile_shot_done = True
        self.projectiles.append(projectile)

    def take_damage(self, amount=1, interface=None):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            self.dead = True
            if interface and 'kill' in interface.sounds:
                interface.sounds['kill'].play()
            self._frame_index = 0
            self._last_frame_ms = pygame.time.get_ticks()
        else:
            if self.mob_type == "golem" and self.golem_phase == 1 and self.hp <= self.max_hp // 2:
                self._phase_transition = True
                self.state = "glowing"
                self.is_hit = False
                self._frame_index = 0
                self._last_frame_ms = pygame.time.get_ticks()
                return
            if self.mob_type == "golem" and self.state in ("attack", "glowing"):
                return
            self.is_hit = True
            self.hit_anim_until = pygame.time.get_ticks() + HIT_FLASH_DURATION
            self._frame_index = 0
