import pygame
import sys
import os
from network import Network
from player import Player, MAX_HP
from map import MapManager
from interface import Interface
pygame.init()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def asset_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

win           = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Chamouraï")

screen_size = (1280, 720)
interface   = Interface(screen_size, win)
KEY_ICON = pygame.transform.scale(
    pygame.image.load(asset_path("assets/key/key.png")).convert_alpha(),
    (44, 24)
)


class ObjectiveTracker:
    def __init__(self):
        self.step = 0
        self.progress = 0

    def _complete_progress_objective(self, target):
        if self.progress >= target:
            self.step += 1
            self.progress = 0

    def record_attack(self):
        if self.step == 0:
            self.progress += 1
            self._complete_progress_objective(3)

    def record_dodge(self):
        if self.step == 1:
            self.progress += 1
            self._complete_progress_objective(3)

    def update_forest_skeleton_kills(self, killed):
        if self.step == 2:
            self.progress = min(3, killed)
            self._complete_progress_objective(3)

    def can_enter_dungeon(self):
        return self.step >= 3

    def entered_dungeon(self):
        if self.step == 3:
            self.step = 4
            self.progress = 0

    def opened_map(self):
        if self.step == 4:
            self.step = 5
            self.progress = 0

    def update_keys(self, key_count):
        if self.step == 5:
            self.progress = min(2, key_count)

    def label_and_progress(self):
        if self.step == 0:
            return "Frapper 3 fois", f"{self.progress}/3"
        if self.step == 1:
            return "Esquiver 3 fois", f"{self.progress}/3"
        if self.step == 2:
            return "Tuer 3 squelettes dans la foret", f"{self.progress}/3"
        if self.step == 3:
            return "Entrer dans le donjon", ""
        if self.step == 4:
            return "Appuyer sur M pour ouvrir la carte", ""
        return "Trouver les 2 cles", f"{self.progress}/2"


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

def victory_button_rect(surface):
    return pygame.Rect(0, 0, 280, 56).move(
        surface.get_width() // 2 - 140,
        surface.get_height() // 2 + 72
    )

def draw_victory_screen(surface):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))
    surface.blit(overlay, (0, 0))

    title_font = pygame.font.Font(None, 104)
    subtitle_font = pygame.font.Font(None, 38)
    button_font = pygame.font.Font(None, 31)
    title = title_font.render("VICTOIRE", True, (232, 190, 65))
    subtitle = subtitle_font.render("Le golem est vaincu", True, (242, 239, 229))
    button = victory_button_rect(surface)
    hovered = button.collidepoint(pygame.mouse.get_pos())
    pygame.draw.rect(surface, (176, 133, 41) if hovered else (132, 99, 33), button, border_radius=6)
    pygame.draw.rect(surface, (238, 202, 102), button, width=2, border_radius=6)
    label = button_font.render("Retour au menu principal", True, (255, 252, 242))

    surface.blit(title, title.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 68)))
    surface.blit(subtitle, subtitle.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 + 5)))
    surface.blit(label, label.get_rect(center=button.center))

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

def draw_grid_message(surface, map_manager, player):
    if not map_manager.is_near_grid(player):
        return
    if player.key_count >= 2:
        message = "Appuyez sur E pour ouvrir la grille"
    else:
        message = f"Il faut 2 cles pour ouvrir la grille ({player.key_count}/2)"
    font = pygame.font.Font(None, 34)
    text = font.render(message, True, (255, 255, 255))
    padding = 12
    box = text.get_rect(center=(surface.get_width() // 2, surface.get_height() - 88))
    background = box.inflate(padding * 2, padding * 2)
    pygame.draw.rect(surface, (20, 20, 22), background, border_radius=6)
    pygame.draw.rect(surface, (174, 144, 52), background, width=2, border_radius=6)
    surface.blit(text, box)

def draw_key_inventory(surface, map_manager, player):
    if map_manager.current_map != "level":
        return

    slot_w, slot_h = 58, 42
    start_x = surface.get_width() - (slot_w * 2) - 28
    y = 20
    for index in range(2):
        rect = pygame.Rect(start_x + index * slot_w, y, slot_w - 8, slot_h)
        pygame.draw.rect(surface, (22, 24, 28), rect, border_radius=6)
        pygame.draw.rect(surface, (112, 115, 111), rect, width=2, border_radius=6)
        if index < player.key_count:
            surface.blit(KEY_ICON, KEY_ICON.get_rect(center=rect.center))

def draw_objective_panel(surface, objectives):
    label, progress = objectives.label_and_progress()
    font_title = pygame.font.Font(None, 24)
    font_text = pygame.font.Font(None, 28)
    title = font_title.render("OBJECTIF", True, (218, 177, 69))
    suffix = f"  {progress}" if progress else ""
    text = font_text.render(label + suffix, True, (247, 245, 236))
    rect = pygame.Rect(20, 20, max(285, text.get_width() + 28), 72)
    pygame.draw.rect(surface, (20, 20, 22), rect, border_radius=6)
    pygame.draw.rect(surface, (174, 144, 52), rect, width=2, border_radius=6)
    surface.blit(title, (rect.left + 14, rect.top + 8))
    surface.blit(text, (rect.left + 14, rect.top + 35))


def draw_invincible_indicator(surface, player):
    if not player.invincible_mode:
        return
    font = pygame.font.Font(None, 30)
    label = font.render("Invincible", True, (255, 236, 121))
    rect = label.get_rect(topleft=(20, 104)).inflate(18, 12)
    pygame.draw.rect(surface, (24, 24, 20), rect, border_radius=5)
    pygame.draw.rect(surface, (219, 173, 48), rect, width=2, border_radius=5)
    surface.blit(label, label.get_rect(center=rect.center))

def draw_teleport_waiting_message(surface, map_manager, players, dungeon_unlocked):
    if map_manager.current_map != "spawn" or not dungeon_unlocked:
        return
    players_on_teleport = sum(map_manager.is_on_teleport(player) for player in players)
    if players_on_teleport != 1:
        return
    font = pygame.font.Font(None, 36)
    text = font.render("En attente du 2eme joueur", True, (255, 255, 255))
    box = text.get_rect(center=(surface.get_width() // 2, surface.get_height() - 76))
    background = box.inflate(28, 20)
    pygame.draw.rect(surface, (20, 20, 22), background, border_radius=6)
    pygame.draw.rect(surface, (174, 144, 52), background, width=2, border_radius=6)
    surface.blit(text, box)

def update_mob_projectiles(map_manager, player):
    for mob in map_manager.mobs:
        active_projectiles = []
        for projectile in mob.projectiles:
            if not projectile.active:
                continue
            if not projectile._added_to_group:
                map_manager.add_sprite(projectile, layer=18)
                projectile._added_to_group = True
            projectile.update(map_manager.collisions)
            hits_player = (
                projectile.hits_player(player.rect)
                if hasattr(projectile, "hits_player")
                else projectile.hitbox.colliderect(player.rect)
            )
            if projectile.active and player.alive and hits_player:
                player.take_damage(getattr(projectile, "damage", 1))
                projectile.kill()
                continue
            if projectile.active:
                active_projectiles.append(projectile)
        mob.projectiles = active_projectiles

def run_game(network, spawn_data, player_index=0):
    map_manager = MapManager(screen_size)
    parchment = load_parchment_image()
    parchment_open = False
    map_open = False
    objectives = ObjectiveTracker()
    _prev_map = map_manager.current_map
    _prev_grid = map_manager.grid_open

    my_skin = "player" if player_index == 0 else "player2"
    other_skin = "player2" if player_index == 0 else "player"

    p  = Player(spawn_data["x"], spawn_data["y"], 130, skin=my_skin, interface=interface)
    p2 = Player(0, 0, 130, skin=other_skin)

    map_manager.add_sprite(p,        layer=19)
    map_manager.add_sprite(p2,       layer=19)
    map_manager.add_sprite(p.weapon, layer=18)
    map_manager.add_sprite(p2.weapon, layer=18)

    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        victory = map_manager.is_victory_ready()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                action = interface.run_pause_menu(win)
                if action == "menu":
                    return
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
                p.toggle_invincible_mode()
                continue
            if victory:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if victory_button_rect(win).collidepoint(event.pos):
                        return
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m and map_manager.current_map == "level":
                map_open = not map_open
                if map_open:
                    objectives.opened_map()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if map_open:
                    pass
                if map_manager.try_open_grid(p):
                    pass
                elif parchment_open or is_near_oldman(map_manager, p):
                    parchment_open = not parchment_open
            if not parchment_open and not map_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                previous_attack_id = p.weapon.attack_id
                p.weapon.hit()
                if p.weapon.attack_id != previous_attack_id:
                    objectives.record_attack()

        if not parchment_open and not map_open and not victory:
            p.save_location()
        map_manager.render(win, (p.position.x, p.position.y))

        if not parchment_open and not map_open and not victory:
            was_dodging = p.dodging
            p.move(map_manager)
            if p.dodging and not was_dodging:
                objectives.record_dodge()

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
            **p.get_dodge_state(),
            "hit": p.weapon.animation,
            "weapon_attack_id": p.weapon.attack_id,
            "weapon_rect": weapon_rect,
            "weapon_angle": p.weapon.angle,
            "weapon_dir": p.weapon.direction,
            "skin": my_skin,
            "grid_open": map_manager.grid_open,
            "current_map": map_manager.current_map,
            "collected_keys": list(p.collected_keys),
            "invincible_mode": p.invincible_mode,
            "objective_step": objectives.step,
            "tutorial_ready": objectives.can_enter_dungeon()
        })

        if data and "player" in data:
            if data.get("current_map") == "level" and map_manager.current_map == "spawn":
                map_manager.place_player_on_level(
                    p,
                    [(p, 19), (p2, 19), (p.weapon, 18), (p2.weapon, 18)],
                    player_index=player_index
                )
                objectives.entered_dungeon()
            if data.get("grid_open") and map_manager.current_map == "level":
                map_manager.open_grid()

            # Musique : cave au changement de map, boss à l'ouverture de la grille
            if map_manager.current_map != _prev_map:
                if map_manager.current_map == "level":
                    interface.play_music("cave", fadeout_ms=1000, fadein_ms=500)
                _prev_map = map_manager.current_map
            if map_manager.grid_open and not _prev_grid:
                interface.play_music("boss", fadeout_ms=600, fadein_ms=300)
            _prev_grid = map_manager.grid_open
            map_manager.apply_shared_keys(p, data.get("collected_keys", []))
            objectives.update_forest_skeleton_kills(data.get("forest_skeleton_kills", 0))
            p2.position.x = data["player"]["x"]
            p2.position.y = data["player"]["y"]
            p2.direction  = data["player"]["dir"]
            p2.state      = data["player"]["state"]
            p2.update()
            p2.apply_remote_dodge_animation(
                data["player"].get("dodging", False),
                data["player"].get("dodge_frame", 0)
            )
            other_data = data["player"]
            p2.weapon.apply_remote(
                x         = other_data["x"],
                y         = other_data["y"],
                angle     = other_data.get("weapon_angle", 0),
                direction = other_data.get("weapon_dir", "right"),
                animating = other_data.get("hit", False),
            )

            mobs_data = data.get("mobs")
            if mobs_data is None and "mob" in data:
                mobs_data = [data["mob"]]
            if mobs_data:
                remaining_mobs_data = list(mobs_data)
                for mob in map_manager.mobs:
                    mob_data = next(
                        (
                            candidate for candidate in remaining_mobs_data
                            if candidate.get("type") == mob.mob_type
                        ),
                        None
                    )
                    if mob_data is None:
                        continue
                    remaining_mobs_data.remove(mob_data)
                    server_hp = mob_data.get("hp", mob.hp)
                    if server_hp < mob.hp:
                        damage = mob.hp - server_hp
                        mob.take_damage(damage, interface)
                    # Synchronise position/direction seulement si pas en animation prioritaire
                    if not mob.dead and not mob.is_hit:
                        mob.position.x = mob_data["x"]
                        mob.position.y = mob_data["y"]
                        mob.direction  = mob_data["dir"]
                        mob.state      = mob_data["state"]
                        mob.attack_kind = mob_data.get("attack_kind")
                        target = mob_data.get("attack_target")
                        if target:
                            mob._attack_target = pygame.math.Vector2(target)
                        mob.golem_phase = mob_data.get("golem_phase", mob.golem_phase)
                        mob.damage = mob_data.get("damage", mob.damage)
                    mob.update()
            update_mob_projectiles(map_manager, p)
            for mob in map_manager.mobs:
                if p.alive and mob.is_attack_hit_frame:
                    if mob.position.distance_to(p.position) <= mob.attack_radius:
                        p.take_damage(mob.damage)
                        break
            map_manager.update_progression(p)
            objectives.update_keys(p.key_count)
        victory = map_manager.is_victory_ready()
        draw_health_bar(win, p.hp, MAX_HP)
        draw_grid_message(win, map_manager, p)
        draw_teleport_waiting_message(win, map_manager, [p, p2], objectives.can_enter_dungeon())
        if map_open:
            map_manager.draw_level_map(win, p)
        draw_key_inventory(win, map_manager, p)
        draw_objective_panel(win, objectives)
        draw_invincible_indicator(win, p)

        if not p.alive:
            draw_death_screen(win)
        if parchment_open:
            draw_parchment(win, parchment)
        if victory:
            draw_victory_screen(win)
        pygame.display.update()


# ── Boucle principale ─────────────────────────────────────────────────────────
while True:
    choice = interface.run_main_menu()

    if choice == "solo":
        map_manager = MapManager(screen_size)
        _prev_map = map_manager.current_map
        _prev_grid = map_manager.grid_open
        parchment = load_parchment_image()
        parchment_open = False
        map_open = False
        objectives = ObjectiveTracker()
        p = Player(map_manager.spawn1.x, map_manager.spawn1.y, 130, interface=interface)
        map_manager.add_sprite(p, layer=19)
        map_manager.add_sprite(p.weapon, layer=18)

        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            victory = map_manager.is_victory_ready()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit();
                    sys.exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    action = interface.run_pause_menu(win)
                    if action == "menu":
                        break
                    continue
                if event.type == pygame.KEYDOWN and event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
                    p.toggle_invincible_mode()
                    continue
                if victory:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if victory_button_rect(win).collidepoint(event.pos):
                            break
                    continue
                if event.type == pygame.KEYDOWN and event.key == pygame.K_m and map_manager.current_map == "level":
                    map_open = not map_open
                    if map_open:
                        objectives.opened_map()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                    if map_open:
                        pass
                    elif map_manager.try_open_grid(p):
                        if map_manager.grid_open:
                            interface.play_music("boss", fadeout_ms=600, fadein_ms=300)
                    elif parchment_open or is_near_oldman(map_manager, p):
                        parchment_open = not parchment_open
                if not parchment_open and not map_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    previous_attack_id = p.weapon.attack_id
                    p.weapon.hit()
                    if p.weapon.attack_id != previous_attack_id:
                        objectives.record_attack()
            else:
                if not parchment_open and not map_open and not victory:
                    p.save_location()
                map_manager.render(win, (p.position.x, p.position.y))
                if not parchment_open and not map_open and not victory:
                    was_dodging = p.dodging
                    p.move(map_manager)
                    if p.dodging and not was_dodging:
                        objectives.record_dodge()
                    if objectives.can_enter_dungeon() and map_manager.teleport_to_level_if_needed(
                            p,
                            [(p, 19), (p.weapon, 18)]
                    ):
                        objectives.entered_dungeon()
                        interface.play_music("cave", fadeout_ms=1000, fadein_ms=500)
                # Détection proximité oldman
                update_oldman_prompt(map_manager, p, parchment_open)

                if not victory:
                    now = pygame.time.get_ticks()
                    for mob in map_manager.mobs:
                        if mob.mob_type == "golem" and not map_manager.grid_open:
                            mob.update()
                            continue
                        mob.update_ai(p.position, map_manager.collisions, now, map_manager.mobs)
                        mob.update()
                    update_mob_projectiles(map_manager, p)
                    # Coup du mob sur le joueur (solo) : seulement sur la frame de coup
                    for mob in map_manager.mobs:
                        if p.alive and mob.is_attack_hit_frame:
                            if mob.position.distance_to(p.position) <= mob.attack_radius:
                                p.take_damage(mob.damage)
                                break

                    # Détection de coup
                    can_damage_mobs = map_manager.current_map != "spawn" or objectives.step >= 2
                    if can_damage_mobs and p.weapon.hitbox:
                        for mob in map_manager.mobs:
                            if mob.alive and p.weapon.hitbox.colliderect(mob.hitbox):
                                mob.take_damage(p.damage, interface)

                    map_manager.update_progression(p)
                    if map_manager.current_map == "spawn":
                        objectives.update_forest_skeleton_kills(sum(
                            mob.mob_type == "skeleton" and mob.dead
                            for mob in map_manager.mobs
                        ))
                    objectives.update_keys(p.key_count)
                victory = map_manager.is_victory_ready()
                draw_health_bar(win, p.hp, MAX_HP)
                draw_grid_message(win, map_manager, p)
                if map_open:
                    map_manager.draw_level_map(win, p)
                draw_key_inventory(win, map_manager, p)
                draw_objective_panel(win, objectives)
                draw_invincible_indicator(win, p)

                if not p.alive:
                    draw_death_screen(win)
                if parchment_open:
                    draw_parchment(win, parchment)
                if victory:
                    draw_victory_screen(win)
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