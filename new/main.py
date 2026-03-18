import pygame
from network import Network
from player import Player
from map import MapManager

pygame.init()

WIDTH, HEIGHT = 1280, 720
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Game")

map_manager = MapManager((WIDTH, HEIGHT))

def redrawWindow(win, player, player2, map_manager):
    map_manager.render(win, (player.position.x, player.position.y))
    # Épée dessinée AVANT le joueur → derrière
    win.blit(player.weapon.image, player.weapon.rect)
    pygame.display.update()

def main():
    run = True
    n = Network()
    data = n.getP()

    p = Player(data["x"], data["y"], 130)
    p2 = Player(0, 0, 130)

    # Joueurs sur layer 19, arme sur layer 18 → derrière le joueur
    map_manager.add_sprite(p, layer=19)
    map_manager.add_sprite(p2, layer=19)
    map_manager.add_sprite(p.weapon, layer=18)

    clock = pygame.time.Clock()

    while run:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                    pygame.quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    p.weapon.hit()

        p.save_location()  # sauvegarde la position avant le mouvement

        map_manager.render(win, (p.position.x, p.position.y))
        p.move(map_manager)

        data = n.send({
            "x": p.position.x,
            "y": p.position.y,
            "dir": p.direction,
            "state": p.state
        })

        if data:
            p2.position.x = data["x"]
            p2.position.y = data["y"]
            p2.direction = data["dir"]
            p2.state = data["state"]
            p2.update()

        p2.update_animation()
        pygame.display.update()

main()