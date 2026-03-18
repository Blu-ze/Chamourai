import pygame
import animation
from pathfinding import astar, build_collision_set

# ─── Constantes IA ─────────────────────────────────────────────────────────────
DETECTION_RADIUS   = 400
ATTACK_RADIUS      = 40
PATHFIND_INTERVAL  = 500
WAYPOINT_THRESHOLD = 16
# ───────────────────────────────────────────────────────────────────────────────


class Mob(animation.AnimateSprite):

    def __init__(self, name, x, y, animation_speed):
        super().__init__(name, animation_speed, False)
        self.position    = pygame.math.Vector2(x, y)
        self.rect.center = self.position
        self.speed       = 2.0

        self.feet = pygame.Rect(0, 0, max(1, self.rect.width  * 0.5), 12)

        self.state             = 'idle'
        self.path              = []
        self.blocked_cells     = set()
        self._last_pathfind_ms = 0
        self.old_position      = self.position.copy()

        self._frame_index   = 0
        self._last_frame_ms = pygame.time.get_ticks()

    # ──────────────────────────────────────────────────────────────────────────

    def init_pathfinding(self, collisions):
        self.blocked_cells = build_collision_set(collisions)

    def update_ai(self, player_position, collisions, now_ms):
        # Garde-fou : position invalide
        try:
            dist = self.position.distance_to(player_position)
        except Exception:
            return

        if dist <= ATTACK_RADIUS:
            self.state = 'attack'
        elif dist <= DETECTION_RADIUS:
            self.state = 'chase'
        else:
            self.state = 'idle'
            self.path  = []

        if self.state == 'chase':
            self._chase(player_position, collisions, now_ms)
        elif self.state == 'attack':
            self.path = []
            dx = player_position.x - self.position.x
            self.change_direction('left' if dx < 0 else 'right')

    # ──────────────────────────────────────────────────────────────────────────

    def _chase(self, player_position, collisions, now_ms):
        # Recalcul périodique du chemin
        if now_ms - self._last_pathfind_ms > PATHFIND_INTERVAL or not self.path:
            self._last_pathfind_ms = now_ms
            try:
                new_path = astar(
                    (self.position.x, self.position.y),
                    (player_position.x, player_position.y),
                    self.blocked_cells
                )
                self.path = new_path if new_path else []
            except Exception:
                self.path = []

        if not self.path:
            return

        # Waypoint courant
        target        = pygame.math.Vector2(self.path[0])
        direction_vec = target - self.position

        # Waypoint atteint → passer au suivant
        if direction_vec.length() < WAYPOINT_THRESHOLD:
            self.path.pop(0)
            if not self.path:
                return
            target        = pygame.math.Vector2(self.path[0])
            direction_vec = target - self.position

        # Normalisation sécurisée (évite ZeroDivisionError)
        length = direction_vec.length()
        if length == 0:
            return
        direction_vec = direction_vec / length

        self.old_position = self.position.copy()

        # Déplacement X avec collision
        self.position.x += direction_vec.x * self.speed
        self.rect.center    = self.position
        self.feet.midbottom = self.rect.midbottom
        if collisions and self.feet.collidelist(collisions) > -1:
            self.position.x = self.old_position.x
            self.rect.center    = self.position
            self.feet.midbottom = self.rect.midbottom

        # Déplacement Y avec collision
        self.position.y += direction_vec.y * self.speed
        self.rect.center    = self.position
        self.feet.midbottom = self.rect.midbottom
        if collisions and self.feet.collidelist(collisions) > -1:
            self.position.y = self.old_position.y
            self.rect.center    = self.position
            self.feet.midbottom = self.rect.midbottom

        # Direction pour le flip
        if direction_vec.x < -0.1:
            self.change_direction('left')
        elif direction_vec.x > 0.1:
            self.change_direction('right')

    # ──────────────────────────────────────────────────────────────────────────

    def update(self):
        self.rect.center    = self.position
        self.feet.midbottom = self.rect.midbottom

        if self.state in ('idle', 'attack'):
            self._animate_frames('skeleton_idle')
        else:
            self._animate_frames('skeleton_walk')

    # ──────────────────────────────────────────────────────────────────────────

    def _animate_frames(self, anim_key):
        frames = animation.animations.get(anim_key)
        # Garde-fou : animation manquante ou vide
        if not frames:
            return

        now = pygame.time.get_ticks()
        if now - self._last_frame_ms > self.animation_speed:
            self._last_frame_ms = now
            self._frame_index   = (self._frame_index + 1) % len(frames)

        # Clamp de sécurité pour éviter l'IndexError
        self._frame_index = self._frame_index % len(frames)
        raw_frame = frames[self._frame_index]

        # Flip horizontal si le mob va à gauche
        if self.direction == 'left':
            self.image = pygame.transform.flip(raw_frame, True, False)
        else:
            self.image = raw_frame
