import pygame
import pytmx
import pyscroll


class MapManager:

    def __init__(self, screen_size):
        self.tmx_data = pytmx.util_pygame.load_pygame("../map/map.tmx")     #données brutes de la carte

        self.map_layer = pyscroll.BufferedRenderer(                         #lit les données de la carte
            pyscroll.data.TiledMapData(self.tmx_data),                      #absorbe les données de la carte (calques)
            screen_size
        )
        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer, default_layer=1)
        self.map_layer.zoom = 1.2

    def render(self, surface, center):                                      #fait le rendu des informations de la carte
        self.map_layer.center(center)
        self.group.draw(surface)

