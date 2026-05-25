import pygame
import sys
from network import Network
from player import Player
from map import MapManager
from interface import Interface

pygame.init()

win           = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Chamouraï")

screen_size = (1280, 720)
interface   = Interface(screen_size, win)


def run_game(network, spawn_data, player_index=0):
    map_manager = MapManager(screen_size)

    p  = Player(spawn_data["x"], spawn_data["y"], 130)
    p2 = Player(0, 0, 130)

    map_manager.add_sprite(p,        layer=19)
    map_manager.add_sprite(p2,       layer=19)
    map_manager.add_sprite(p.weapon, layer=18)

    clock = pygame.time.Clock()

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                action = interface.run_pause_menu(win)
                if action == "menu":
                    return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                p.weapon.hit()

        p.save_location()
        map_manager.render(win, (p.position.x, p.position.y))
        p.move(map_manager)

        weapon_rect = None
        if p.weapon.hitbox:
            r = p.weapon.hitbox
            weapon_rect = (r.x, r.y, r.width, r.height)

        data = network.send({
            "x": p.position.x,
            "y": p.position.y,
            "dir": p.direction,
            "state": p.state,
            "hit": p.weapon.animation,
            "weapon_rect": weapon_rect
        })

        if data and "player" in data:
            p2.position.x = data["player"]["x"]
            p2.position.y = data["player"]["y"]
            p2.direction  = data["player"]["dir"]
            p2.state      = data["player"]["state"]
            p2.update()

            mob = map_manager.skeleton
            mob.position.x = data["mob"]["x"]
            mob.position.y = data["mob"]["y"]
            mob.direction  = data["mob"]["dir"]
            mob.state      = data["mob"]["state"]
            mob.update()

        p2.update_animation()
        pygame.display.update()

        # Affichage PV du mob
        if data and "mob" in data:
            if not data["mob"].get("alive", True):
                map_manager.skeleton.alive = False
                map_manager.skeleton.kill()


# ── Boucle principale ─────────────────────────────────────────────────────────
while True:
    choice = interface.run_main_menu()

    if choice == "solo":
        map_manager = MapManager(screen_size)
        p = Player(map_manager.spawn1.x, map_manager.spawn1.y, 130)
        map_manager.add_sprite(p, layer=19)
        map_manager.add_sprite(p.weapon, layer=18)

        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    action = interface.run_pause_menu(win)
                    if action == "menu":
                        break
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    p.weapon.hit()
            else:
                p.save_location()
                map_manager.render(win, (p.position.x, p.position.y))
                p.move(map_manager)

                now = pygame.time.get_ticks()
                map_manager.skeleton.update_ai(p.position, map_manager.collisions, now)
                map_manager.skeleton.update()

                # Détection de coup
                if p.weapon.hitbox and map_manager.skeleton.alive:
                    if p.weapon.hitbox.colliderect(map_manager.skeleton.rect):
                        map_manager.skeleton.take_damage(1)


                pygame.display.update()
                continue
            break
    elif choice == "options":
        interface.run_options()
    elif choice == "multi":
        action = interface.run_multi_menu()

        if action == "back":
            continue

        if action == "create":
            network = Network()
            result  = interface.run_create_salon(network)
            if result and result.get("status") == "start":
                run_game(network, result["spawn"])





        elif action == "join":

            server_ip = interface.run_enter_ip()

            network = Network(server_ip=server_ip)

            result = interface.run_join_salon(network)

            if result and result.get("status") == "ok":

                start_msg = interface.run_waiting_for_host(network)

                if start_msg and start_msg.get("status") == "start":
                    network.send_raw({"status": "ready"})

                    run_game(network, start_msg["spawn"], player_index=1)






































