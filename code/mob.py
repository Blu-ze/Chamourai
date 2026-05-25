import pygame
import animation
from pathfinding import astar, build_collision_set

DETECTION_RADIUS   = 400
ATTACK_RADIUS      = 40
PATHFIND_INTERVAL  = 500
WAYPOINT_THRESHOLD = 16
MAX_HP             = 150
HIT_FLASH_DURATION = 200  # ms
ATTACK_HIT_FRAME   = 7    # index de la frame qui inflige les dégâts
ATTACK_LEFT_OFFSET = -30   # décalage horizontal (px) du rect quand attaque vers la gauche
ATTACK_LEFT_OFFSET_Y = -10  # décalage vertical (px) du rect quand attaque vers la gauche

class Mob(animation.AnimateSprite):

    def __init__(self, name, x, y, animation_speed):
        super().__init__(name, animation_speed)
        self.position    = pygame.math.Vector2(x, y)
        self.rect.center = self.position
        self.speed       = 2.0
        self.feet        = pygame.Rect(0, 0, max(1, self.rect.width * 0.5), 12)
        self.hitbox      = pygame.Rect(0, 0, 32, 32)
        self.state       = 'idle'
        self.path        = []
        self.blocked_cells     = set()
        self._last_pathfind_ms = 0
        self.old_position      = self.position.copy()
        self._frame_index      = 0
        self._last_frame_ms    = pygame.time.get_ticks()

        self.hp    = MAX_HP
        self.alive = True          # encore en vie (peut agir)
        self.dead  = False         # animation de mort en cours / terminée

        self.is_hit         = False
        self.hit_anim_until = 0
        self._position_hitbox()

        self._prev_state      = 'idle'  # pour détecter les transitions d'état
        self._attack_hit_done = False   # True après avoir infligé les dégâts de ce cycle

    # ── Pathfinding ────────────────────────────────────────────────────────────

    def init_pathfinding(self, collisions):
        self.blocked_cells = build_collision_set(collisions)

    # ── IA ─────────────────────────────────────────────────────────────────────

    def update_ai(self, player_position, collisions, now_ms, other_mobs=None):
        if not self.alive:
            return
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
            self._chase(player_position, collisions, now_ms, other_mobs)
        elif self.state == 'attack':
            self.path = []
            dx = player_position.x - self.position.x
            self.set_direction('left' if dx < 0 else 'right')

    def _chase(self, player_position, collisions, now_ms, other_mobs=None):
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

        target        = pygame.math.Vector2(self.path[0])
        direction_vec = target - self.position

        if direction_vec.length() < WAYPOINT_THRESHOLD:
            self.path.pop(0)
            if not self.path:
                return
            target        = pygame.math.Vector2(self.path[0])
            direction_vec = target - self.position

        length = direction_vec.length()
        if length == 0:
            return
        direction_vec = direction_vec / length

        self.old_position = self.position.copy()

        self.position.x += direction_vec.x * self.speed
        self.rect.center    = self.position
        self.feet.midbottom = self.rect.midbottom
        self._position_hitbox()
        if (collisions and self.feet.collidelist(collisions) > -1) or self._collides_with_mobs(other_mobs):
            self.position.x = self.old_position.x
            self.rect.center    = self.position
            self.feet.midbottom = self.rect.midbottom
            self._position_hitbox()

        self.position.y += direction_vec.y * self.speed
        self.rect.center    = self.position
        self.feet.midbottom = self.rect.midbottom
        self._position_hitbox()
        if (collisions and self.feet.collidelist(collisions) > -1) or self._collides_with_mobs(other_mobs):
            self.position.y = self.old_position.y
            self.rect.center    = self.position
            self.feet.midbottom = self.rect.midbottom
            self._position_hitbox()

        if direction_vec.x < -0.1:
            self.set_direction('left')
        elif direction_vec.x > 0.1:
            self.set_direction('right')

    # ── Update principal ───────────────────────────────────────────────────────

    def update(self):
        now = pygame.time.get_ticks()

        # 1. Animation de mort : priorité absolue, non interruptible
        if self.dead:
            finished = self._animate_once('skeleton_dead')
            if finished:
                self.kill()   # retire le sprite du groupe seulement ici
            self._position_rect()
            return

        # 2. Animation de hit : priorité haute mais courte
        if self.is_hit:
            self._animate_frames('skeleton_hit')
            if now > self.hit_anim_until:
                self.is_hit = False
                self._frame_index = 0
            self._position_rect()
            return

        # 3. Attaque : joue skeleton_attack depuis le début à chaque entrée dans l'état
        if self.state == 'attack':
            if self._prev_state != 'attack':
                self._frame_index    = 0
                self._last_frame_ms  = now
                self._attack_hit_done = False
            self._prev_state = 'attack'
            self._animate_frames('skeleton_attack')
            self._position_rect(attacking=True)
            return

        self._prev_state = self.state

        # 4. Déplacement / idle
        if self.state == 'chase':
            self._animate_frames('skeleton_walk')
        else:
            self._animate_frames('skeleton_idle')
        self._position_rect()

    @property
    def is_attack_hit_frame(self):
        """True uniquement sur la frame de coup de l'attaque, une seule fois par cycle."""
        if self.state != 'attack' or self._attack_hit_done:
            return False
        if self._frame_index == ATTACK_HIT_FRAME:
            self._attack_hit_done = True   # consommé pour ce cycle
            return True
        return False

    # ── Positionnement du rect ────────────────────────────────────────────────

    def _position_rect(self, attacking=False):
        """Ancre le rect à self.position.
        Attaque vers la gauche : ancrage depuis le coin bas-droit de l'image
        (le squelette occupe la partie droite du sprite, l'espace vide est à gauche).
        Tous les autres cas : ancrage centre classique.
        """
        if attacking and self.direction == 'left':
            self.rect.center = (self.position.x + ATTACK_LEFT_OFFSET, self.position.y + ATTACK_LEFT_OFFSET_Y)
        elif attacking:
            self.rect.center = (self.position.x, self.position.y + ATTACK_LEFT_OFFSET_Y)
        else:
            self.rect.center = self.position
        self.feet.midbottom = self.rect.midbottom
        self._position_hitbox()

    # ── Helpers d'animation ────────────────────────────────────────────────────

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
        """Joue une animation en boucle infinie."""
        frames = animation.animations.get(anim_key)
        if not frames:
            return

        now = pygame.time.get_ticks()
        if now - self._last_frame_ms > self.animation_speed:
            self._last_frame_ms = now
            next_index = (self._frame_index + 1) % len(frames)
            # Nouveau cycle d'attaque : on réarme le coup
            if anim_key == 'skeleton_attack' and next_index == 0:
                self._attack_hit_done = False
            self._frame_index = next_index

        self._frame_index = self._frame_index % len(frames)
        raw_frame = frames[self._frame_index]

        self.image = (pygame.transform.flip(raw_frame, True, False)
                      if self.direction == 'left' else raw_frame)

    def _animate_once(self, anim_key):
        """Joue une animation une seule fois. Retourne True quand elle est terminée."""
        frames = animation.animations.get(anim_key)
        if not frames:
            return True   # pas de frames → on considère l'anim terminée

        now = pygame.time.get_ticks()
        if now - self._last_frame_ms > self.animation_speed:
            self._last_frame_ms = now
            self._frame_index  += 1

        # Clamp pour ne pas dépasser
        clamped = min(self._frame_index, len(frames) - 1)
        raw_frame = frames[clamped]
        self.image = (pygame.transform.flip(raw_frame, True, False)
                      if self.direction == 'left' else raw_frame)

        # Terminé quand on a dépassé la dernière frame
        return self._frame_index >= len(frames)

    # ── Dégâts / mort ──────────────────────────────────────────────────────────

    def take_damage(self, amount=1, interface=None):
        if not self.alive:
            return
        self.hp -= amount
        if self.hp <= 0:
            self.hp    = 0
            self.alive = False
            self.dead  = True
            if interface and 'kill' in interface.sounds:
                interface.sounds['kill'].play()
            # Réinitialise l'index pour jouer skeleton_dead depuis le début
            self._frame_index   = 0
            self._last_frame_ms = pygame.time.get_ticks()
        else:
            self.is_hit        = True
            self.hit_anim_until = pygame.time.get_ticks() + HIT_FLASH_DURATION
            self._frame_index   = 0
