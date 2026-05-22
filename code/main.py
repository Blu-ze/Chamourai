import pygame
import sys
import os
from network import Network
from player import Player
from map import MapManager
from interface import Interface
from player import MAX_HP
from mob import ATTACK_RADIUS
pygame.init()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def asset_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

win           = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Chamouraï")

screen_size = (1280, 720)
interface   = Interface(screen_size, win)


def draw_health_bar(surface, hp, max_hp):
    """Dessine la barre de vie en bas à gauche."""
    bar_x, bar_y   = 20, surface.get_height() - 40
    bar_w, bar_h   = 220, 22
    border_radius  = 6
    padding        = 3

    # Fond sombre (contour)
    pygame.draw.rect(surface, (30, 30, 30),
                     (bar_x - padding, bar_y - padding,
                      bar_w + padding * 2, bar_h + padding * 2),
                     border_radius=border_radius + 2)

    # Fond rouge foncé (vide)
    pygame.draw.rect(surface, (100, 20, 20),
                     (bar_x, bar_y, bar_w, bar_h),
                     border_radius=border_radius)

    # Remplissage selon les PV
    ratio = max(0, hp / max_hp)
    fill_w = int(bar_w * ratio)
    if fill_w > 0:
        if ratio > 0.5:
            r = int(255 * (1 - ratio) * 2)
            g = 200
        else:
            r = 220
            g = int(200 * ratio * 2)
        pygame.draw.rect(surface, (r, g, 40),
                         (bar_x, bar_y, fill_w, bar_h),
                         border_radius=border_radius)

    # Texte PV
    font = pygame.font.Font(None, 26)
    txt  = font.render(f"PV  {hp} / {max_hp}", True, (255, 255, 255))
    surface.blit(txt, (bar_x + 6, bar_y + 3))


def draw_death_screen(surface):
    """Affiche le message de mort en semi-transparent."""
    W, H = surface.get_size()
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 140))
    surface.blit(overlay, (0, 0))

    font_big = pygame.font.Font(None, 100)
    font_sub = pygame.font.Font(None, 40)

    txt = font_big.render("Vous êtes mort.", True, (220, 50, 50))
    sub = font_sub.render("Appuyez sur Échap pour revenir au menu", True, (200, 200, 200))

    surface.blit(txt, txt.get_rect(center=(W // 2, H // 2 - 30)))
    surface.blit(sub, sub.get_rect(center=(W // 2, H // 2 + 55)))

def load_parchment_image():
    image = pygame.image.load(asset_path("assets/oldman/parchemin.png")).convert_alpha()
    max_w = int(screen_size[0] * 0.8)
    max_h = int(screen_size[1] * 0.85)
    scale = min(max_w / image.get_width(), max_h / image.get_height())
    new_size = (int(image.get_width() * scale), int(image.get_height() * scale))
    return pygame.transform.smoothscale(image, new_size)

def draw_parchment(surface, parchment):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 130))
    surface.blit(overlay, (0, 0))
    surface.blit(parchment, parchment.get_rect(center=surface.get_rect().center))

def is_near_oldman(map_manager, player, interact_radius=80):
    if not map_manager.oldman:
        return False
    return player.position.distance_to(map_manager.oldman.position) <= interact_radius

def update_oldman_prompt(map_manager, player, parchment_open):
    if not parchment_open and is_near_oldman(map_manager, player):
        map_manager.ekey.show(
            map_manager.oldman.position.x,
            map_manager.oldman.position.y
        )
    else:
        map_manager.ekey.hide()

def run_game(network, spawn_data, player_index=0):
    map_manager = MapManager(screen_size)
    parchment = load_parchment_image()
    parchment_open = False

    my_skin = "player" if player_index == 0 else "player2"
    other_skin = "player2" if player_index == 0 else "player"

    p  = Player(spawn_data["x"], spawn_data["y"], 130, skin=my_skin)
    p2 = Player(0, 0, 130, skin=other_skin)

    map_manager.add_sprite(p,        layer=19)
    map_manager.add_sprite(p2,       layer=19)
    map_manager.add_sprite(p.weapon, layer=18)
    map_manager.add_sprite(p2.weapon, layer=18)

    clock = pygame.time.Clock()

    while True:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if parchment_open or is_near_oldman(map_manager, p):
                    parchment_open = not parchment_open
            if not parchment_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                p.weapon.hit()

        if not parchment_open:
            p.save_location()
        map_manager.render(win, (p.position.x, p.position.y))

        if not parchment_open:
            p.move(map_manager)
            map_manager.teleport_to_level_if_needed(
                p,
                [(p, 19), (p2, 19), (p.weapon, 18)]
            )

        # Détection proximité oldman
        update_oldman_prompt(map_manager, p, parchment_open)

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
            "weapon_rect": weapon_rect,
            "weapon_angle": p.weapon.angle,
            "weapon_dir": p.weapon.direction,
            "skin": my_skin
        })

        if data and "player" in data:
            p2.position.x = data["player"]["x"]
            p2.position.y = data["player"]["y"]
            p2.direction  = data["player"]["dir"]
            p2.state      = data["player"]["state"]
            p2.update()

            other_data = data["player"]
            p2.weapon.apply_remote(
                x         = other_data["x"],
                y         = other_data["y"],
                angle     = other_data.get("weapon_angle", 0),
                direction = other_data.get("weapon_dir", "right"),
                animating = other_data.get("hit", False),
            )

            mob = map_manager.skeleton
            if mob and "mob" in data:
                mob_data = data["mob"]
                server_hp = mob_data.get("hp", mob.hp)
                # Déclenche les animations via take_damage si le HP a baissé
                if server_hp < mob.hp:
                    damage = mob.hp - server_hp
                    mob.take_damage(damage)
                # Synchronise position/direction seulement si pas en animation prioritaire
                if not mob.dead and not mob.is_hit:
                    mob.position.x = mob_data["x"]
                    mob.position.y = mob_data["y"]
                    mob.direction  = mob_data["dir"]
                    mob.state      = mob_data["state"]
                mob.update()

        p2.update_animation()
        draw_health_bar(win, p.hp, MAX_HP)

        if not p.alive:
            draw_death_screen(win)
        if parchment_open:
            draw_parchment(win, parchment)
        pygame.display.update()


# ── Boucle principale ─────────────────────────────────────────────────────────
while True:
    choice = interface.run_main_menu()

    if choice == "solo":
        map_manager = MapManager(screen_size)
        parchment = load_parchment_image()
        parchment_open = False
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
                    break
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    if parchment_open or is_near_oldman(map_manager, p):
                        parchment_open = not parchment_open
                if not parchment_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    p.weapon.hit()
            else:
                if not parchment_open:
                    p.save_location()
                map_manager.render(win, (p.position.x, p.position.y))
                if not parchment_open:
                    p.move(map_manager)
                    map_manager.teleport_to_level_if_needed(
                        p,
                        [(p, 19), (p.weapon, 18)]
                    )
                # Détection proximité oldman
                update_oldman_prompt(map_manager, p, parchment_open)

                now = pygame.time.get_ticks()
                if map_manager.skeleton:
                    map_manager.skeleton.update_ai(p.position, map_manager.collisions, now)
                    map_manager.skeleton.update()
                # Coup du mob sur le joueur (solo) : seulement sur la frame de coup
                if p.alive and map_manager.skeleton and map_manager.skeleton.is_attack_hit_frame :
                    if map_manager.skeleton.position.distance_to(p.position) <= ATTACK_RADIUS:
                        p.take_damage(1)

                # Détection de coup
                if p.weapon.hitbox and map_manager.skeleton and map_manager.skeleton.alive:
                    if p.weapon.hitbox.colliderect(map_manager.skeleton.rect):
                        map_manager.skeleton.take_damage(1)

                draw_health_bar(win, p.hp, MAX_HP)

                if not p.alive:
                    draw_death_screen(win)
                if parchment_open:
                    draw_parchment(win, parchment)
                pygame.display.update()
                continue
            break

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