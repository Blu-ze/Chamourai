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
        self.image = self.frames[0] if self.frames else pygame.Surface((16, 15))
        self.rect = self.image.get_rect()
        self.visible = False

    def show(self, x, y):
        self.visible = True
        self.rect.midbottom = (x, y - 10)

    def hide(self):
        self.visible = False

    def update(self):
        if not self.visible or not self.frames:
            return
        now = pygame.time.get_ticks()
        if now - self._last_frame_ms > 150:
            self._last_frame_ms = now
            self._frame_index = (self._frame_index + 1) % len(self.frames)
            self.image = self.frames[self._frame_index]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def map_path(relative_path: str) -> str:
    return os.path.join(BASE_DIR, relative_path)

class MapManager:

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

        self.spawn1    = self.get_object("Player1Spawn")
        self.spawn2    = self.get_object("Player2Spawn")
        self.mob_spawn = self.get_object("MobSpawn")

        self.map_layer = pyscroll.BufferedRenderer(
            pyscroll.data.TiledMapData(self.tmx_data),
            self.screen_size
        )
        self.map_layer.zoom = 2

        self.group = pyscroll.PyscrollGroup(
            map_layer=self.map_layer,
            default_layer=0
        )

        self.collisions = []
        self.teleports = []
        for obj in self.tmx_data.objects:
            if obj.type == "collision":
                self.collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            if obj.name == "teleport" or obj.type == "teleport":
                self.teleports.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # Collisions peintes directement dans le calque de tuiles Walls.
        for layer in self.tmx_data.layers:
            if getattr(layer, "name", None) != "Walls":
                continue
            for x, y, gid in layer:
                if gid:
                    self.collisions.append(
                        pygame.Rect(
                            x * self.tmx_data.tilewidth,
                            y * self.tmx_data.tileheight,
                            self.tmx_data.tilewidth,
                            self.tmx_data.tileheight
                        )
                    )

        # Mob affiché côté client (pas d'IA, juste le rendu)
        self.skeleton = None
        if self.mob_spawn:
            self.skeleton = Mob('skeleton', self.mob_spawn.x, self.mob_spawn.y, 100)
            self.group.add(self.skeleton, layer=18)

        self.oldman_obj = self.get_object("OldMan")
        self.oldman = None
        if self.oldman_obj:
            self.oldman = OldMan(self.oldman_obj.x, self.oldman_obj.y)
            self.group.add(self.oldman, layer=19)

        self.ekey = EKey()
        self.group.add(self.ekey, layer=20)

    def teleport_to_level_if_needed(self, player, sprites_to_add):
        if self.current_map != "spawn":
            return False

        if player.feet.collidelist(self.teleports) == -1:
            return False

        self.load_map("level")

        if self.spawn1:
            player.position.x = self.spawn1.x
            player.position.y = self.spawn1.y
            player.update()
            player.save_location()
            player.weapon.move(player.position.x, player.position.y)

        for sprite, layer in sprites_to_add:
            self.group.add(sprite, layer=layer)

        return True

    def render(self, surface, center):
        self.group.center(center)
        self.group.draw(surface)

    def world_to_screen(self, world_pos):
        offset_x, offset_y = self.map_layer.get_center_offset()
        screen_x = (world_pos[0] + offset_x) * self.map_layer.zoom
        screen_y = (world_pos[1] + offset_y) * self.map_layer.zoom
        return screen_x, screen_y

    def add_sprite(self, sprite, layer=19):
        self.group.add(sprite, layer=layer)
