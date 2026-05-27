import pygame
import pytmx
import pyscroll
import os
from mob import Mob


from animation import AnimateSprite, animations
import pygame

class OldMan(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frames = animations.get('oldman', [])
        self._frame_index = 0
        self._last_frame_ms = pygame.time.get_ticks()
        self.image = self.frames[0] if self.frames else pygame.Surface((96, 96))
        self.rect = self.image.get_rect(center=(x, y))
        self.position = pygame.math.Vector2(x, y)

    def update(self):
        now = pygame.time.get_ticks()
        if not self.frames:
            return
        if now - self._last_frame_ms > 150:
            self._last_frame_ms = now
            self._frame_index = (self._frame_index + 1) % len(self.frames)
            self.image = self.frames[self._frame_index]
        self.rect.center = self.position


class EKey(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.frames = animations.get('E', [])
        self._frame_index = 0
        self._last_frame_ms = pygame.time.get_ticks()
        self._animation_speed = 300
        first_frame = self.frames[0] if self.frames else pygame.Surface((16, 15))
        self.hidden_image = pygame.Surface(first_frame.get_size(), pygame.SRCALPHA)
        self.image = self.hidden_image
        self.rect = self.image.get_rect()
        self.visible = False

    def show(self, x, y):
        self.visible = True
        if self.frames:
            self.image = self.frames[self._frame_index]
        self.rect.midbottom = (x, y - 10)

    def hide(self):
        self.visible = False
        self.image = self.hidden_image

    def update(self):
        if not self.visible or not self.frames:
            return
        now = pygame.time.get_ticks()
        if now - self._last_frame_ms > self._animation_speed:
            self._last_frame_ms = now
            self._frame_index = (self._frame_index + 1) % len(self.frames)
            self.image = self.frames[self._frame_index]


class KeyDrop(pygame.sprite.Sprite):
    def __init__(self, x, y, key_id):
        super().__init__()
        image = pygame.image.load(map_path('assets/key/key.png')).convert_alpha()
        self.image = pygame.transform.scale(image, (image.get_width() * 2, image.get_height() * 2))
        self.rect = self.image.get_rect(center=(x, y))
        self.position = pygame.math.Vector2(x, y)
        self.key_id = key_id


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def map_path(relative_path: str) -> str:
    return os.path.join(BASE_DIR, relative_path)

class MapManager:
    BASE_SCREEN_SIZE = (1280, 720)
    BASE_ZOOM = 2

    def __init__(self, screen_size):
        self.screen_size = screen_size
        self.current_map = None
        self.load_map("spawn")

    def get_object(self, name):
        try:
            return self.tmx_data.get_object_by_name(name)
        except (KeyError, ValueError):
            return None

    def load_map(self, map_name):
        self.current_map = map_name
        self.tmx_data = pytmx.util_pygame.load_pygame(map_path(f'map/{map_name}.tmx'))
        self.grid_open = False
        self.grid_layer = None
        self.grid_collisions = []
        self.grid_interaction_zones = []
        self.key_drops = []
        self.overview_surface = None
        self.overview_scale = 3

        self.spawn1    = self.get_object("Player1Spawn")
        self.spawn2    = self.get_object("Player2Spawn")

        self.map_layer = pyscroll.BufferedRenderer(
            pyscroll.data.TiledMapData(self.tmx_data),
            self.screen_size
        )
        width_ratio = self.screen_size[0] / self.BASE_SCREEN_SIZE[0]
        height_ratio = self.screen_size[1] / self.BASE_SCREEN_SIZE[1]
        self.map_layer.zoom = self.BASE_ZOOM * max(width_ratio, height_ratio)

        self.group = pyscroll.PyscrollGroup(
            map_layer=self.map_layer,
            default_layer=0
        )

        self.collisions = []
        self.teleports = []
        mob_spawns = []
        for obj in self.tmx_data.objects:
            if obj.type == "collision":
                self.collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            if obj.name == "teleport" or obj.type == "teleport":
                self.teleports.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            if obj.name == "Skeleton":
                mob_spawns.append(("skeleton", obj))
            if obj.name == "SkeletonBoss":
                mob_spawns.append(("skeleton_boss", obj))
            if obj.name == "Necromancer":
                mob_spawns.append(("necromancer", obj))
            if obj.name == "NecromancerBoss":
                mob_spawns.append(("necromancer_boss", obj))
            if obj.name == "Golem":
                mob_spawns.append(("golem", obj))

        # Collisions painted directly in blocking tile layers.
        for layer in self.tmx_data.layers:
            layer_name = getattr(layer, "name", "").lower()
            if layer_name == "gridkey" and isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    self.grid_interaction_zones.append(
                        pygame.Rect(obj.x, obj.y, obj.width, obj.height)
                    )
                continue
            if not isinstance(layer, pytmx.TiledTileLayer) or layer_name not in ("walls", "grid"):
                continue
            if layer_name == "grid":
                self.grid_layer = layer
            for x, y, gid in layer:
                if gid:
                    collision = pygame.Rect(
                        x * self.tmx_data.tilewidth,
                        y * self.tmx_data.tileheight,
                        self.tmx_data.tilewidth,
                        self.tmx_data.tileheight
                    )
                    self.collisions.append(collision)
                    if layer_name == "grid":
                        self.grid_collisions.append(collision)

        # Mob affiché côté client (pas d'IA, juste le rendu)
        if not mob_spawns:
            legacy_spawn = self.get_object("MobSpawn")
            if legacy_spawn:
                mob_spawns.append(("skeleton", legacy_spawn))

        self.mobs = []
        for mob_type, spawn in mob_spawns:
            mob = Mob(mob_type, spawn.x, spawn.y, 100)
            mob.init_pathfinding(self.collisions)
            self.mobs.append(mob)
            self.group.add(mob, layer=18)
        self.skeleton = self.mobs[0] if self.mobs else None

        self.oldman_obj = self.get_object("OldMan")
        self.oldman = None
        if self.oldman_obj:
            self.oldman = OldMan(self.oldman_obj.x, self.oldman_obj.y)
            self.group.add(self.oldman, layer=19)

        self.ekey = EKey()
        self.group.add(self.ekey, layer=20)
        self._build_level_overview()

    def is_on_teleport(self, player):
        return (
            self.current_map == "spawn"
            and player.feet.collidelist(self.teleports) != -1
        )

    def place_player_on_level(self, player, sprites_to_add, player_index=0):
        self.load_map("level")
        spawn = self.spawn1 if player_index == 0 else self.spawn2
        if spawn:
            player.position.x = spawn.x
            player.position.y = spawn.y
            player.update()
            player.save_location()
            player.weapon.move(player.position.x, player.position.y)

        for sprite, layer in sprites_to_add:
            self.group.add(sprite, layer=layer)

    def teleport_to_level_if_needed(self, player, sprites_to_add, required_players=None):
        if self.current_map != "spawn":
            return False

        if required_players:
            if not all(self.is_on_teleport(required_player) for required_player in required_players):
                return False
        elif not self.is_on_teleport(player):
            return False

        self.place_player_on_level(player, sprites_to_add)
        return True

    def update_animations(self):
        if self.oldman:
            self.oldman.update()
        self.ekey.update()

    def render(self, surface, center):
        self.update_animations()
        self.group.center(center)
        self.group.draw(surface)
        self.draw_boss_health_bars(surface)
        self.draw_golem_health_bar(surface)

    def draw_boss_health_bars(self, surface):
        for mob in self.mobs:
            if not mob.is_boss or mob.mob_type == "golem" or not mob.alive:
                continue
            # The necromancer sheet has large transparent padding above its visible head.
            head_y = mob.position.y - 10 if mob.mob_type == "necromancer_boss" else mob.rect.top
            center_x, top_y = self.world_to_screen((mob.position.x, head_y))
            bar_w = min(180, max(90, int(mob.rect.width * self.map_layer.zoom * 0.55)))
            bar_h = 10
            x = int(center_x - bar_w / 2)
            y = int(top_y - 18)
            ratio = max(0, mob.hp / mob.max_hp)
            pygame.draw.rect(surface, (22, 22, 25), (x - 2, y - 2, bar_w + 4, bar_h + 4), border_radius=4)
            pygame.draw.rect(surface, (92, 18, 23), (x, y, bar_w, bar_h), border_radius=3)
            fill_w = int(bar_w * ratio)
            if fill_w:
                pygame.draw.rect(surface, (196, 42, 48), (x, y, fill_w, bar_h), border_radius=3)

    def draw_golem_health_bar(self, surface):
        if not self.grid_open:
            return
        golem = next((mob for mob in self.mobs if mob.mob_type == "golem" and mob.alive), None)
        if not golem:
            return

        bar_w, bar_h = 520, 18
        x = (surface.get_width() - bar_w) // 2
        y = 52
        ratio = max(0, golem.hp / golem.max_hp)
        name_font = pygame.font.Font(None, 38)
        name = name_font.render("GOLEM", True, (235, 229, 214))
        surface.blit(name, name.get_rect(center=(surface.get_width() // 2, 29)))
        pygame.draw.rect(surface, (18, 18, 20), (x - 3, y - 3, bar_w + 6, bar_h + 6), border_radius=5)
        pygame.draw.rect(surface, (82, 17, 18), (x, y, bar_w, bar_h), border_radius=3)
        fill_w = int(bar_w * ratio)
        if fill_w:
            pygame.draw.rect(surface, (184, 36, 40), (x, y, fill_w, bar_h), border_radius=3)
        if golem.golem_phase == 2:
            phase_font = pygame.font.Font(None, 24)
            phase = phase_font.render("PHASE II", True, (238, 171, 58))
            surface.blit(phase, phase.get_rect(midtop=(surface.get_width() // 2, y + bar_h + 6)))

    def _build_level_overview(self):
        if self.current_map != "level":
            return

        scale = self.overview_scale
        size = (self.tmx_data.width * scale, self.tmx_data.height * scale)
        self.overview_surface = pygame.Surface(size)
        self.overview_surface.fill((14, 17, 20))
        colors = {"ground": (64, 74, 69)}

        for layer in self.tmx_data.layers:
            layer_name = getattr(layer, "name", "").lower()
            if not isinstance(layer, pytmx.TiledTileLayer) or layer_name not in colors:
                continue
            color = colors[layer_name]
            for x, y, gid in layer:
                if gid:
                    pygame.draw.rect(
                        self.overview_surface,
                        color,
                        (x * scale, y * scale, scale, scale)
                    )

    def draw_level_map(self, surface, player):
        if self.current_map != "level" or not self.overview_surface:
            return

        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((5, 7, 9, 218))
        surface.blit(shade, (0, 0))

        map_rect = self.overview_surface.get_rect(center=surface.get_rect().center)
        panel = map_rect.inflate(28, 62)
        pygame.draw.rect(surface, (20, 23, 27), panel, border_radius=6)
        pygame.draw.rect(surface, (114, 120, 116), panel, width=2, border_radius=6)
        surface.blit(self.overview_surface, map_rect)

        if not self.grid_open:
            for collision in self.grid_collisions:
                tile_x = collision.x // self.tmx_data.tilewidth
                tile_y = collision.y // self.tmx_data.tileheight
                pygame.draw.rect(
                    surface,
                    (202, 157, 53),
                    (
                        map_rect.left + tile_x * self.overview_scale,
                        map_rect.top + tile_y * self.overview_scale,
                        self.overview_scale,
                        self.overview_scale
                    )
                )

        marker_x = map_rect.left + int(player.position.x / self.tmx_data.tilewidth * self.overview_scale)
        marker_y = map_rect.top + int(player.position.y / self.tmx_data.tileheight * self.overview_scale)
        pygame.draw.circle(surface, (255, 255, 255), (marker_x, marker_y), 7)
        pygame.draw.circle(surface, (215, 47, 48), (marker_x, marker_y), 5)

        font = pygame.font.Font(None, 32)
        label = font.render("Carte du niveau", True, (240, 240, 236))
        surface.blit(label, (panel.left + 12, panel.top + 8))

    def update_progression(self, player):
        for mob in self.mobs:
            if mob.drops_key and mob.dead and not mob.key_dropped:
                mob.key_dropped = True
                if mob.mob_type in player.collected_keys:
                    continue
                key = KeyDrop(mob.position.x, mob.position.y, mob.mob_type)
                self.key_drops.append(key)
                self.group.add(key, layer=19)

        for key in list(self.key_drops):
            if player.rect.colliderect(key.rect):
                player.collected_keys.add(key.key_id)
                player.key_count = len(player.collected_keys)
                key.kill()
                self.key_drops.remove(key)

    def apply_shared_keys(self, player, collected_keys):
        player.collected_keys.update(collected_keys)
        player.key_count = len(player.collected_keys)
        for key in list(self.key_drops):
            if key.key_id in player.collected_keys:
                key.kill()
                self.key_drops.remove(key)

    def is_near_grid(self, player):
        if self.grid_open or not self.grid_interaction_zones:
            return False
        return player.feet.collidelist(self.grid_interaction_zones) > -1

    def try_open_grid(self, player):
        if not self.is_near_grid(player):
            return False
        if player.key_count < 2 and not getattr(player, "invincible_mode", False):
            return True

        self.open_grid()
        return True

    def open_grid(self):
        if self.grid_open:
            return
        self.grid_open = True
        grid_ids = {id(collision) for collision in self.grid_collisions}
        self.collisions = [
            collision for collision in self.collisions
            if id(collision) not in grid_ids
        ]
        if self.grid_layer:
            self.grid_layer.visible = False
            self.map_layer.redraw_tiles(self.map_layer._buffer)
        for mob in self.mobs:
            mob.init_pathfinding(self.collisions)

    def is_victory_ready(self):
        if self.current_map != "level":
            return False
        return any(
            mob.mob_type == "golem" and mob.dead and mob.death_animation_finished
            for mob in self.mobs
        )

    def world_to_screen(self, world_pos):
        offset_x, offset_y = self.map_layer.get_center_offset()
        screen_x = (world_pos[0] + offset_x) * self.map_layer.zoom
        screen_y = (world_pos[1] + offset_y) * self.map_layer.zoom
        return screen_x, screen_y

    def add_sprite(self, sprite, layer=19):
        self.group.add(sprite, layer=layer)
