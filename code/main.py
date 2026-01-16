# main.py (modifié)
import pygame
from game import Game
from interface import Interface

pygame.init()

screen_size = (1920, 1080)

# Afficher le menu
interface = Interface(screen_size)
choice = interface.run()

if choice == "play":
    # Lancer le jeu
    game = Game(screen_size)
    game.run()

pygame.quit()