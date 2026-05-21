import pygame
import pytmx
import pyscroll
import os
from mob import Mob

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def map_path(relative_path: str) -> str:
    return os.path.join(BASE_DIR, relative_path)

class MapManager:

    def __init__(self, screen_size):
        self.tmx_data = pytmx.util_pygame.load_pygame(map_path('map/spawn.tmx'))

        self.spawn1    = self.tmx_data.get_object_by_name("Player1Spawn")
        self.spawn2    = self.tmx_data.get_object_by_name("Player2Spawn")
        self.mob_spawn = self.tmx_data.get_object_by_name("MobSpawn")

        self.map_layer = pyscroll.BufferedRenderer(
            pyscroll.data.TiledMapData(self.tmx_data),
            screen_size
        )
        self.map_layer.zoom = 2

        self.group = pyscroll.PyscrollGroup(
            map_layer=self.map_layer,
            default_layer=0
        )

        self.collisions = []
        for obj in self.tmx_data.objects:
            if obj.type == "collision":
                self.collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # Mob affiché côté client (pas d'IA, juste le rendu)
        self.skeleton = Mob('skeleton', self.mob_spawn.x, self.mob_spawn.y, 100)
        self.group.add(self.skeleton, layer=18)

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