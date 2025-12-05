import pygame
import pytmx
import pyscroll


class MapManager:

    def __init__(self, screen_size):
        self.tmx_data = pytmx.util_pygame.load_pygame("../map/spawn.tmx")   #données brutes de la carte
        self.spawn = self.tmx_data.get_object_by_name("PlayerSpawn")      #prend la position de spawn du joueur
        self.map_layer = pyscroll.BufferedRenderer(                       #lit les données de la carte
            pyscroll.data.TiledMapData(self.tmx_data),                    #absorbe les données de la carte (calques)
            screen_size
        )
        self.map_layer.zoom = 2

    def render(self, surface, center, screen_size):
        self.map_layer.center(center)
        screen_rect = pygame.Rect(0, 0, screen_size[0], screen_size[1])
        self.map_layer.draw(surface, screen_rect)

    # Donne les coordonnées du joueur sur l'écran en fonction de ses coordonnées sur la map
    def world_to_screen(self, world_pos):
        offset_x, offset_y = self.map_layer.get_center_offset()
        screen_x = (world_pos[0] + offset_x) * 2
        screen_y = (world_pos[1] + offset_y) * 2
        return screen_x, screen_y

