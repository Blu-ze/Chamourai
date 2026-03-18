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

        self.spawn     = self.tmx_data.get_object_by_name("PlayerSpawn")
        self.mob_spawn = self.tmx_data.get_object_by_name("MobSpawn")

        self.map_layer = pyscroll.BufferedRenderer(
            pyscroll.data.TiledMapData(self.tmx_data),
            screen_size
        )
        self.map_layer.zoom = 2.5

        self.group = pyscroll.PyscrollGroup(
            map_layer=self.map_layer,
            default_layer=0
        )

        # ─── Collisions ───────────────────────────────────────────────────────
        self.collisions = []
        for obj in self.tmx_data.objects:
            if obj.type == "collision":
                self.collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # ─── Ennemis ──────────────────────────────────────────────────────────
        self.mobs = []
        self._spawn_mob('skeleton', self.mob_spawn.x, self.mob_spawn.y, 100)

    def _spawn_mob(self, name, x, y, anim_speed):
        """Crée un mob, initialise son pathfinding et l'ajoute au groupe de rendu."""
        mob = Mob(name, x, y, anim_speed)
        mob.init_pathfinding(self.collisions)   # pré-calcule les cellules bloquées (A*)
        self.mobs.append(mob)
        self.group.add(mob, layer=18)

    def render(self, surface, center):
        self.group.center(center)
        self.group.draw(surface)

    def world_to_screen(self, world_pos):
        """Convertit des coordonnées monde en coordonnées écran."""
        offset_x, offset_y = self.map_layer.get_center_offset()
        screen_x = (world_pos[0] + offset_x) * self.map_layer.zoom
        screen_y = (world_pos[1] + offset_y) * self.map_layer.zoom
        return screen_x, screen_y
