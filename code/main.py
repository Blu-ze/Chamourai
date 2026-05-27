import os
import sys

import pygame

from interface import Interface
from map import MapManager
from network import Network
from player import MAX_HP, Player


pygame.init()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)


desktop_sizes = pygame.display.get_desktop_sizes()
screen_size = desktop_sizes[0] if desktop_sizes else (1280, 720)
# Une fenêtre sans bordure à la taille du bureau évite les bandes ajoutées
# par certains écrans en plein écran exclusif.
win = pygame.display.set_mode(screen_size, pygame.NOFRAME)
pygame.display.set_caption("Chamourai")
interface = Interface(screen_size, win)
KEY_ICON = pygame.transform.scale(
    pygame.image.load(asset_path("assets/key/key.png")).convert_alpha(),
    (44, 24),
)


class ObjectiveTracker:
    def __init__(self):
        self.step = 0
        self.progress = 0

    def _advance_at(self, target):
        if self.progress >= target:
            self.step += 1
            self.progress = 0

    def talked_to_oldman(self):
        if self.step == 0:
            self.step = 1
            self.progress = 0

    def record_attack(self):
        if self.step == 1:
            self.progress += 1
            self._advance_at(3)

    def record_dodge(self):
        if self.step == 2:
            self.progress += 1
            self._advance_at(3)

    def update_forest_skeleton_kills(self, killed):
        if self.step == 3:
            self.progress = min(3, killed)
            self._advance_at(3)

    def can_enter_dungeon(self):
        return self.step >= 4

    def entered_dungeon(self):
        if self.step == 4:
            self.step = 5
            self.progress = 0

    def opened_map(self):
        if self.step == 5:
            self.step = 6
            self.progress = 0

    def update_keys(self, count):
        if self.step == 6:
            self.progress = min(2, count)

    def label_and_progress(self):
        objectives = (
            ("Parler au vieil homme", None),
            ("Frapper 3 fois", 3),
            ("Esquiver 3 fois", 3),
            ("Tuer 3 squelettes dans la foret", 3),
            ("Entrer dans le donjon", None),
            ("Appuyer sur M pour ouvrir la carte", None),
            ("Trouver les 2 cles", 2),
        )
        label, target = objectives[min(self.step, len(objectives) - 1)]
        return label, f"{self.progress}/{target}" if target else ""


def draw_health_bar(surface, hp, max_hp):
    x, y, width, height = 20, surface.get_height() - 40, 220, 22
    pygame.draw.rect(surface, (30, 30, 30), (x - 3, y - 3, width + 6, height + 6), border_radius=8)
    pygame.draw.rect(surface, (100, 20, 20), (x, y, width, height), border_radius=6)
    ratio = max(0, hp / max_hp)
    if ratio:
        color = (int(220 + 35 * ratio), int(200 * min(1, ratio * 2)), 40)
        pygame.draw.rect(surface, color, (x, y, int(width * ratio), height), border_radius=6)
    text = pygame.font.Font(None, 26).render(f"PV  {hp} / {max_hp}", True, (255, 255, 255))
    surface.blit(text, (x + 6, y + 3))


def draw_button(surface, rect, text, colors=((92, 42, 39), (126, 54, 47))):
    color = colors[1] if rect.collidepoint(pygame.mouse.get_pos()) else colors[0]
    pygame.draw.rect(surface, color, rect, border_radius=6)
    pygame.draw.rect(surface, (217, 173, 66), rect, width=2, border_radius=6)
    label = pygame.font.Font(None, 28).render(text, True, (255, 252, 242))
    surface.blit(label, label.get_rect(center=rect.center))


def paired_buttons(surface, y):
    return (
        pygame.Rect(surface.get_width() // 2 - 298, y, 280, 56),
        pygame.Rect(surface.get_width() // 2 + 18, y, 280, 56),
    )


def draw_solo_defeat(surface):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))
    surface.blit(overlay, (0, 0))
    title = pygame.font.Font(None, 100).render("Vous etes mort.", True, (220, 50, 50))
    surface.blit(title, title.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 46)))
    menu, restart = paired_buttons(surface, surface.get_height() // 2 + 58)
    draw_button(surface, menu, "Retour au menu principal")
    draw_button(surface, restart, "Recommencer", ((91, 80, 33), (132, 108, 38)))


def victory_button_rect(surface):
    return pygame.Rect(surface.get_width() // 2 - 140, surface.get_height() // 2 + 72, 280, 56)


def draw_victory_screen(surface):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))
    surface.blit(overlay, (0, 0))
    title = pygame.font.Font(None, 104).render("VICTOIRE", True, (232, 190, 65))
    subtitle = pygame.font.Font(None, 38).render("Le golem est vaincu", True, (242, 239, 229))
    surface.blit(title, title.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 68)))
    surface.blit(subtitle, subtitle.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 + 5)))
    draw_button(surface, victory_button_rect(surface), "Retour au menu principal", ((132, 99, 33), (176, 133, 41)))


def spectator_menu_button_rect(surface):
    return pygame.Rect(surface.get_width() - 214, 20, 194, 46)


def draw_spectator_controls(surface):
    label = pygame.font.Font(None, 30).render("Vous observez la partie", True, (240, 240, 236))
    surface.blit(label, label.get_rect(midtop=(surface.get_width() // 2, 22)))
    draw_button(surface, spectator_menu_button_rect(surface), "Retour au menu")


def defeat_button_rects(surface):
    return paired_buttons(surface, surface.get_height() // 2 + 74)


def draw_multiplayer_defeat(surface, restart_vote, restart_votes):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    surface.blit(overlay, (0, 0))
    title = pygame.font.Font(None, 102).render("DEFAITE", True, (205, 56, 52))
    subtitle = pygame.font.Font(None, 37).render("Les deux joueurs sont tombes", True, (242, 239, 229))
    surface.blit(title, title.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 75)))
    surface.blit(subtitle, subtitle.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 5)))
    menu, restart = defeat_button_rects(surface)
    draw_button(surface, menu, "Retour au menu principal")
    label = "Vote envoye" if restart_vote else "Voter pour recommencer"
    draw_button(surface, restart, label, ((91, 80, 33), (132, 108, 38)))
    votes = pygame.font.Font(None, 26).render(f"Votes : {restart_votes}/2", True, (238, 203, 105))
    surface.blit(votes, votes.get_rect(center=(restart.centerx, restart.bottom + 20)))


def load_parchment_image():
    image = pygame.image.load(asset_path("assets/oldman/parchemin.png")).convert_alpha()
    scale = min(screen_size[0] * 0.8 / image.get_width(), screen_size[1] * 0.85 / image.get_height())
    return pygame.transform.smoothscale(image, (int(image.get_width() * scale), int(image.get_height() * scale)))


def draw_parchment(surface, parchment):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 130))
    surface.blit(overlay, (0, 0))
    surface.blit(parchment, parchment.get_rect(center=surface.get_rect().center))


def is_near_oldman(map_manager, player, interact_radius=80):
    return bool(map_manager.oldman and player.position.distance_to(map_manager.oldman.position) <= interact_radius)


def update_oldman_prompt(map_manager, player, parchment_open):
    if not parchment_open and is_near_oldman(map_manager, player):
        map_manager.ekey.show(map_manager.oldman.position.x, map_manager.oldman.position.y)
    else:
        map_manager.ekey.hide()


def draw_grid_message(surface, map_manager, player):
    if not map_manager.is_near_grid(player):
        return
    message = (
        "Appuyez sur E pour ouvrir la grille"
        if player.key_count >= 2
        else f"Il faut 2 cles pour ouvrir la grille ({player.key_count}/2)"
    )
    text = pygame.font.Font(None, 34).render(message, True, (255, 255, 255))
    rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() - 88))
    background = rect.inflate(24, 24)
    pygame.draw.rect(surface, (20, 20, 22), background, border_radius=6)
    pygame.draw.rect(surface, (174, 144, 52), background, width=2, border_radius=6)
    surface.blit(text, rect)


def draw_key_inventory(surface, map_manager, player):
    if map_manager.current_map != "level":
        return
    start_x = surface.get_width() - 144
    for index in range(2):
        rect = pygame.Rect(start_x + index * 58, 20, 50, 42)
        pygame.draw.rect(surface, (22, 24, 28), rect, border_radius=6)
        pygame.draw.rect(surface, (112, 115, 111), rect, width=2, border_radius=6)
        if index < player.key_count:
            surface.blit(KEY_ICON, KEY_ICON.get_rect(center=rect.center))


def draw_objective_panel(surface, objectives):
    label, progress = objectives.label_and_progress()
    title = pygame.font.Font(None, 24).render("OBJECTIF", True, (218, 177, 69))
    text = pygame.font.Font(None, 28).render(label + (f"  {progress}" if progress else ""), True, (247, 245, 236))
    rect = pygame.Rect(20, 20, max(285, text.get_width() + 28), 72)
    pygame.draw.rect(surface, (20, 20, 22), rect, border_radius=6)
    pygame.draw.rect(surface, (174, 144, 52), rect, width=2, border_radius=6)
    surface.blit(title, (rect.left + 14, rect.top + 8))
    surface.blit(text, (rect.left + 14, rect.top + 35))


def draw_teleport_waiting_message(surface, map_manager, players, dungeon_unlocked):
    if map_manager.current_map != "spawn" or not dungeon_unlocked:
        return
    if sum(map_manager.is_on_teleport(player) for player in players) != 1:
        return
    text = pygame.font.Font(None, 36).render("En attente du 2eme joueur", True, (255, 255, 255))
    rect = text.get_rect(center=(surface.get_width() // 2, surface.get_height() - 76))
    background = rect.inflate(28, 20)
    pygame.draw.rect(surface, (20, 20, 22), background, border_radius=6)
    pygame.draw.rect(surface, (174, 144, 52), background, width=2, border_radius=6)
    surface.blit(text, rect)


def update_mob_projectiles(map_manager, player):
    for mob in map_manager.mobs:
        remaining = []
        for projectile in mob.projectiles:
            if not projectile.active:
                continue
            if not projectile._added_to_group:
                map_manager.add_sprite(projectile, layer=18)
                projectile._added_to_group = True
            projectile.update(map_manager.collisions)
            hits = projectile.hits_player(player.rect) if hasattr(projectile, "hits_player") else projectile.hitbox.colliderect(player.rect)
            if projectile.active and player.alive and hits:
                player.take_damage(getattr(projectile, "damage", 1))
                projectile.kill()
            elif projectile.active:
                remaining.append(projectile)
        mob.projectiles = remaining


def set_player_visible(map_manager, player, visible):
    if visible:
        if not map_manager.group.has(player):
            map_manager.add_sprite(player, layer=19)
        if not map_manager.group.has(player.weapon):
            map_manager.add_sprite(player.weapon, layer=18)
    else:
        map_manager.group.remove(player)
        map_manager.group.remove(player.weapon)


def restart_multiplayer_dungeon(map_manager, player, other_player, player_index, objectives):
    for current in (player, other_player):
        current.hp = MAX_HP
        current.alive = True
        current.weapon.animation = False
        current.weapon.hitbox = None
    player.dodging = False
    player.invincible = False
    player.key_count = 0
    player.collected_keys.clear()
    map_manager.place_player_on_level(
        player,
        [(player, 19), (other_player, 19), (player.weapon, 18), (other_player.weapon, 18)],
        player_index=player_index,
    )
    objectives.step = 5
    objectives.progress = 0


def restart_solo_dungeon():
    manager = MapManager(screen_size)
    player = Player(manager.spawn1.x, manager.spawn1.y, 130, interface=interface)
    manager.place_player_on_level(player, [(player, 19), (player.weapon, 18)])
    objectives = ObjectiveTracker()
    objectives.step = 5
    return manager, player, objectives


def run_game(network, spawn_data, player_index=0):
    map_manager = MapManager(screen_size)
    interface.set_walk_surface("grass")
    parchment = load_parchment_image()
    parchment_open = False
    map_open = False
    objectives = ObjectiveTracker()
    defeat = False
    restart_vote = False
    restart_votes = 0
    restart_id = 0
    boss_music_started = False
    my_skin = "player" if player_index == 0 else "player2"
    other_skin = "player2" if player_index == 0 else "player"
    p = Player(spawn_data["x"], spawn_data["y"], 130, skin=my_skin, interface=interface)
    p2 = Player(0, 0, 130, skin=other_skin)
    for sprite, layer in ((p, 19), (p2, 19), (p.weapon, 18), (p2.weapon, 18)):
        map_manager.add_sprite(sprite, layer=layer)
    clock = pygame.time.Clock()

    while True:
        clock.tick(60)
        victory = map_manager.is_victory_ready()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if defeat:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    menu, restart = defeat_button_rects(win)
                    if menu.collidepoint(event.pos):
                        interface.set_walk_surface("grass")
                        return
                    if restart.collidepoint(event.pos):
                        restart_vote = True
                continue
            if not p.alive:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and spectator_menu_button_rect(win).collidepoint(event.pos):
                    interface.set_walk_surface("grass")
                    return
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if interface.run_pause_menu(win) == "menu":
                    interface.set_walk_surface("grass")
                    return
                continue
            if victory:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and victory_button_rect(win).collidepoint(event.pos):
                    interface.set_walk_surface("grass")
                    return
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m and map_manager.current_map == "level":
                map_open = not map_open
                if map_open:
                    objectives.opened_map()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if not map_open and not map_manager.try_open_grid(p) and (parchment_open or is_near_oldman(map_manager, p)):
                    opening_parchment = not parchment_open
                    parchment_open = not parchment_open
                    if opening_parchment:
                        objectives.talked_to_oldman()
            if not parchment_open and not map_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                before = p.weapon.attack_id
                p.weapon.hit()
                if p.weapon.attack_id != before:
                    objectives.record_attack()

        if p.alive and not parchment_open and not map_open and not victory:
            p.save_location()
        set_player_visible(map_manager, p, p.alive)
        set_player_visible(map_manager, p2, p2.alive)
        camera = p2 if not p.alive and p2.alive else p
        map_manager.render(win, (camera.position.x, camera.position.y))
        if p.alive and not parchment_open and not map_open and not victory:
            dodging = p.dodging
            p.move(map_manager)
            if p.dodging and not dodging:
                objectives.record_dodge()
        if p.alive:
            update_oldman_prompt(map_manager, p, parchment_open)
        else:
            map_manager.ekey.hide()

        weapon_rect = None
        if p.alive and p.weapon.hitbox:
            rect = p.weapon.hitbox
            weapon_rect = (rect.x, rect.y, rect.width, rect.height)
        data = network.send({
            "x": p.position.x, "y": p.position.y, "dir": p.direction, "state": p.state,
            **p.get_dodge_state(), "hit": p.alive and p.weapon.animation,
            "weapon_attack_id": p.weapon.attack_id, "weapon_rect": weapon_rect,
            "weapon_angle": p.weapon.angle, "weapon_dir": p.weapon.direction, "skin": my_skin,
            "grid_open": map_manager.grid_open, "current_map": map_manager.current_map,
            "collected_keys": list(p.collected_keys),
            "objective_step": objectives.step, "tutorial_ready": objectives.can_enter_dungeon(),
            "alive": p.alive, "hp": p.hp, "restart_vote": restart_vote, "restart_id": restart_id,
        })
        if data and "player" in data:
            server_restart_id = data.get("restart_id", restart_id)
            if server_restart_id != restart_id:
                restart_id = server_restart_id
                restart_vote = False
                defeat = False
                parchment_open = False
                map_open = False
                boss_music_started = False
                restart_multiplayer_dungeon(map_manager, p, p2, player_index, objectives)
                interface.play_music("cave", fadeout_ms=800, fadein_ms=1200)
                interface.set_walk_surface("cave")
            if data.get("current_map") == "level" and map_manager.current_map == "spawn":
                map_manager.place_player_on_level(p, [(p, 19), (p2, 19), (p.weapon, 18), (p2.weapon, 18)], player_index=player_index)
                objectives.entered_dungeon()
                interface.play_music("cave", fadeout_ms=800, fadein_ms=1200)
                interface.set_walk_surface("cave")
            if data.get("grid_open") and map_manager.current_map == "level":
                map_manager.open_grid()
            if map_manager.grid_open and not boss_music_started:
                boss_music_started = True
                interface.play_music("boss", fadeout_ms=600, fadein_ms=800)
            map_manager.apply_shared_keys(p, data.get("collected_keys", []))
            objectives.update_forest_skeleton_kills(data.get("forest_skeleton_kills", 0))
            other = data["player"]
            p2.position.update(other["x"], other["y"])
            p2.direction = other["dir"]
            p2.state = other["state"]
            p2.alive = other.get("alive", True)
            p2.hp = other.get("hp", p2.hp)
            set_player_visible(map_manager, p2, p2.alive)
            if p2.alive:
                p2.update()
                p2.apply_remote_dodge_animation(other.get("dodging", False), other.get("dodge_frame", 0))
                p2.weapon.apply_remote(other["x"], other["y"], other.get("weapon_angle", 0), other.get("weapon_dir", "right"), other.get("hit", False))
            remaining = list(data.get("mobs", []))
            for mob in map_manager.mobs:
                mob_data = next((item for item in remaining if item.get("type") == mob.mob_type), None)
                if not mob_data:
                    continue
                remaining.remove(mob_data)
                server_hp = mob_data.get("hp", mob.hp)
                server_max = mob_data.get("max_hp", mob.max_hp)
                if mob.max_hp != server_max:
                    mob.max_hp, mob.hp = server_max, server_hp
                elif server_hp < mob.hp:
                    mob.take_damage(mob.hp - server_hp, interface)
                elif server_hp > mob.hp:
                    mob.hp = server_hp
                if not mob.dead and not mob.is_hit:
                    mob.position.update(mob_data["x"], mob_data["y"])
                    mob.direction, mob.state = mob_data["dir"], mob_data["state"]
                    mob.attack_kind = mob_data.get("attack_kind")
                    target = mob_data.get("attack_target")
                    if target:
                        mob._attack_target = pygame.math.Vector2(target)
                    mob.golem_phase = mob_data.get("golem_phase", mob.golem_phase)
                    mob.damage = mob_data.get("damage", mob.damage)
                mob.update()
            update_mob_projectiles(map_manager, p)
            for mob in map_manager.mobs:
                if p.alive and mob.is_attack_hit_frame and mob.position.distance_to(p.position) <= mob.attack_radius:
                    p.take_damage(mob.damage)
                    break
            if p.alive:
                map_manager.update_progression(p)
            objectives.update_keys(p.key_count)
            defeat = data.get("defeat", False)
            restart_votes = data.get("restart_votes", 0)

        victory = map_manager.is_victory_ready()
        if p.alive:
            draw_health_bar(win, p.hp, MAX_HP)
        draw_grid_message(win, map_manager, p)
        draw_teleport_waiting_message(win, map_manager, [p, p2], objectives.can_enter_dungeon())
        if map_open:
            map_manager.draw_level_map(win, p)
        draw_key_inventory(win, map_manager, p)
        if not map_open:
            draw_objective_panel(win, objectives)
        if not p.alive and not defeat:
            draw_spectator_controls(win)
        if parchment_open:
            draw_parchment(win, parchment)
        if victory:
            draw_victory_screen(win)
        if defeat:
            draw_multiplayer_defeat(win, restart_vote, restart_votes)
        pygame.display.update()


def run_solo():
    map_manager = MapManager(screen_size)
    interface.set_walk_surface("grass")
    parchment = load_parchment_image()
    parchment_open = False
    map_open = False
    objectives = ObjectiveTracker()
    boss_music_started = False
    p = Player(map_manager.spawn1.x, map_manager.spawn1.y, 130, interface=interface)
    map_manager.add_sprite(p, layer=19)
    map_manager.add_sprite(p.weapon, layer=18)
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        victory = map_manager.is_victory_ready()
        leave = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if not p.alive:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    menu, restart = paired_buttons(win, win.get_height() // 2 + 58)
                    if menu.collidepoint(event.pos):
                        interface.set_walk_surface("grass")
                        return
                    if restart.collidepoint(event.pos):
                        map_manager, p, objectives = restart_solo_dungeon()
                        parchment_open = False
                        map_open = False
                        boss_music_started = False
                        interface.play_music("cave", fadeout_ms=800, fadein_ms=1200)
                        interface.set_walk_surface("cave")
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if interface.run_pause_menu(win) == "menu":
                    interface.set_walk_surface("grass")
                    return
                continue
            if victory:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and victory_button_rect(win).collidepoint(event.pos):
                    interface.set_walk_surface("grass")
                    return
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_m and map_manager.current_map == "level":
                map_open = not map_open
                if map_open:
                    objectives.opened_map()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if not map_open and not map_manager.try_open_grid(p) and (parchment_open or is_near_oldman(map_manager, p)):
                    opening_parchment = not parchment_open
                    parchment_open = not parchment_open
                    if opening_parchment:
                        objectives.talked_to_oldman()
            if not parchment_open and not map_open and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                before = p.weapon.attack_id
                p.weapon.hit()
                if p.weapon.attack_id != before:
                    objectives.record_attack()
        if leave:
            return
        if p.alive and not parchment_open and not map_open and not victory:
            p.save_location()
        map_manager.render(win, (p.position.x, p.position.y))
        if p.alive and not parchment_open and not map_open and not victory:
            dodging = p.dodging
            p.move(map_manager)
            if p.dodging and not dodging:
                objectives.record_dodge()
            if objectives.can_enter_dungeon() and map_manager.teleport_to_level_if_needed(p, [(p, 19), (p.weapon, 18)]):
                objectives.entered_dungeon()
                interface.play_music("cave", fadeout_ms=800, fadein_ms=1200)
                interface.set_walk_surface("cave")
        if p.alive:
            update_oldman_prompt(map_manager, p, parchment_open)
        else:
            map_manager.ekey.hide()
        if map_manager.grid_open and not boss_music_started:
            boss_music_started = True
            interface.play_music("boss", fadeout_ms=600, fadein_ms=800)
        if p.alive and not victory:
            now = pygame.time.get_ticks()
            for mob in map_manager.mobs:
                if mob.mob_type == "golem" and not map_manager.grid_open:
                    mob.update()
                    continue
                mob.update_ai(p.position, map_manager.collisions, now, map_manager.mobs)
                mob.update()
            update_mob_projectiles(map_manager, p)
            for mob in map_manager.mobs:
                if p.alive and mob.is_attack_hit_frame and mob.position.distance_to(p.position) <= mob.attack_radius:
                    p.take_damage(mob.damage)
                    break
            if p.weapon.hitbox:
                for mob in map_manager.mobs:
                    if mob.alive and p.weapon.hitbox.colliderect(mob.hitbox):
                        mob.take_damage(p.damage, interface)
            map_manager.update_progression(p)
            if map_manager.current_map == "spawn":
                objectives.update_forest_skeleton_kills(sum(mob.mob_type == "skeleton" and mob.dead for mob in map_manager.mobs))
            objectives.update_keys(p.key_count)
        draw_health_bar(win, p.hp, MAX_HP)
        draw_grid_message(win, map_manager, p)
        if map_open:
            map_manager.draw_level_map(win, p)
        draw_key_inventory(win, map_manager, p)
        if not map_open:
            draw_objective_panel(win, objectives)
        if not p.alive:
            draw_solo_defeat(win)
        if parchment_open:
            draw_parchment(win, parchment)
        if victory:
            draw_victory_screen(win)
        pygame.display.update()


while True:
    choice = interface.run_main_menu()
    if choice == "solo":
        run_solo()
    elif choice == "options":
        interface.run_options()
    elif choice == "multi":
        action = interface.run_multi_menu()
        if action == "back":
            continue
        if action == "create":
            network = Network()
            result = interface.run_create_salon(network)
            if result and result.get("status") == "start":
                run_game(network, result["spawn"])
        elif action == "join":
            server_ip = interface.run_enter_ip()
            if not server_ip:
                continue
            network = Network(server_ip=server_ip)
            result = interface.run_join_salon(network)
            if result and result.get("status") == "back":
                network.client.close()
                continue
            if result and result.get("status") == "ok":
                start_msg = interface.run_waiting_for_host(network)
                if start_msg and start_msg.get("status") == "start":
                    network.send_raw({"status": "ready"})
                    run_game(network, start_msg["spawn"], player_index=1)
