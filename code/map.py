import pygame
import pytmx
import pyscroll
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def map_path(relative_path: str) -> str:
    return os.path.join(BASE_DIR, relative_path)

class MapManager:

    def __init__(self, screen_size):
        self.tmx_data = pytmx.util_pygame.load_pygame(map_path('map/spawn.tmx'))   #données brutes de la carte

        self.spawn = self.tmx_data.get_object_by_name("PlayerSpawn")      #prend la position de spawn du joueur
        self.mob_spawn = self.tmx_data.get_object_by_name("MobSpawn")

        self.map_layer = pyscroll.BufferedRenderer(                       #lit les données de la carte
            pyscroll.data.TiledMapData(self.tmx_data),                    #absorbe les données de la carte (calques)
            screen_size
        )
        self.map_layer.zoom = 3.5

        self.group = pyscroll.PyscrollGroup(
            map_layer=self.map_layer,
            default_layer=0
        )

    def render(self, surface, center):
        self.group.center(center)
        self.group.draw(surface)

    # Donne les coordonnées du joueur sur l'écran en fonction de ses coordonnées sur la map
    def world_to_screen(self, world_pos):
        offset_x, offset_y = self.map_layer.get_center_offset()
        screen_x = (world_pos[0] + offset_x) * self.map_layer.zoom
        screen_y = (world_pos[1] + offset_y) * self.map_layer.zoom
        return screen_x, screen_y

