import pygame
import pytmx
import pyscroll


class MapManager:

    def __init__(self, screen_size):
        self.tmx_data = pytmx.util_pygame.load_pygame("../map/map.tmx")   #données brutes de la carte
        self.spawn = self.tmx_data.get_object_by_name("PlayerSpawn")      #prend la position de spawn du joueur
        self.map_layer = pyscroll.BufferedRenderer(                       #lit les données de la carte
            pyscroll.data.TiledMapData(self.tmx_data),                    #absorbe les données de la carte (calques)
            screen_size
        )
        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer, default_layer=0)
        #self.map_layer.zoom = 1.2

    def render(self, surface, center):  #fait le rendu des informations de la carte
        self.map_layer.center(center)
        self.group.draw(surface)

    # Donne les coordonnées du joueur sur l'écran en fonction de ses coordonnées sur la map
    def world_to_screen(self, world_pos):
        offset_x, offset_y = self.map_layer.get_center_offset()
        screen_x = world_pos[0] + offset_x
        screen_y = world_pos[1] + offset_y
        return screen_x, screen_y

