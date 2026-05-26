import socket
from _thread import *
import pickle
import pytmx
import pygame
import os
import threading
import random
import struct
from mob import Mob
from player import PLAYER_DAMAGE, MAX_HP

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def map_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

pygame.init()

def recv_packet(conn):
    header = recv_exact(conn, 4)
    size = struct.unpack("!I", header)[0]
    return pickle.loads(recv_exact(conn, size))


def recv_exact(conn, size):
    chunks = []
    remaining = size
    while remaining:
        chunk = conn.recv(remaining)
        if not chunk:
            raise ConnectionError("Connexion client interrompue.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_packet(conn, data):
    payload = pickle.dumps(data)
    conn.sendall(struct.pack("!I", len(payload)) + payload)

def get_optional_object(tmx_data, name):
    try:
        return tmx_data.get_object_by_name(name)
    except (KeyError, ValueError):
        return None

MOB_TYPES_BY_OBJECT_NAME = {
    "Skeleton": "skeleton",
    "SkeletonBoss": "skeleton_boss",
    "Necromancer": "necromancer",
    "NecromancerBoss": "necromancer_boss",
    "Golem": "golem",
}
def load_map_config(map_name):
    tmx_data = pytmx.TiledMap(map_path(f"map/{map_name}.tmx"))
    mob_spawns = [
        (MOB_TYPES_BY_OBJECT_NAME[obj.name], obj)
        for obj in tmx_data.objects
        if obj.name in MOB_TYPES_BY_OBJECT_NAME
    ]
    if not mob_spawns:
        legacy_spawn = get_optional_object(tmx_data, "MobSpawn")
        if legacy_spawn:
            mob_spawns.append(("skeleton", legacy_spawn))

    collisions = []
    grid_collisions = []
    teleports = []
    for obj in tmx_data.objects:
        if obj.type == "collision":
            collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
        if obj.name == "teleport" or obj.type == "teleport":
            teleports.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
    for layer in tmx_data.layers:
        layer_name = getattr(layer, "name", "").lower()
        if not isinstance(layer, pytmx.TiledTileLayer) or layer_name not in ("walls", "grid"):
            continue
        for x, y, gid in layer:
            if gid:
                collision = pygame.Rect(
                    x * tmx_data.tilewidth,
                    y * tmx_data.tileheight,
                    tmx_data.tilewidth,
                    tmx_data.tileheight,
                )
                collisions.append(collision)
                if layer_name == "grid":
                    grid_collisions.append(collision)

    return {
        "spawn1": tmx_data.get_object_by_name("Player1Spawn"),
        "spawn2": tmx_data.get_object_by_name("Player2Spawn"),
        "mob_spawns": mob_spawns,
        "collisions": collisions,
        "grid_collisions": grid_collisions,
        "teleports": teleports,
    }


MAP_CONFIGS = {
    "spawn": load_map_config("spawn"),
    "level": load_map_config("level"),
}
spawn1 = MAP_CONFIGS["spawn"]["spawn1"]
spawn2 = MAP_CONFIGS["spawn"]["spawn2"]

def mob_to_dict(mob):
    return {
        "x":     mob.position.x,
        "y":     mob.position.y,
        "dir":   mob.direction,
        "state": mob.state,
        "alive": mob.alive,
        "hp":    mob.hp,
        "max_hp": mob.max_hp,
        "type":  mob.mob_type,
        "attack_kind": mob.attack_kind,
        "attack_target": (mob._attack_target.x, mob._attack_target.y),
        "golem_phase": mob.golem_phase,
        "damage": mob.damage,
    }

def spawn_to_dict(spawn_data):
    mob_type, spawn = spawn_data
    return {"x": spawn.x, "y": spawn.y, "dir": "right", "state": "idle", "type": mob_type}

def create_mobs(map_name):
    config = MAP_CONFIGS[map_name]
    mobs = []
    for mob_type, spawn in config["mob_spawns"]:
        mob = Mob(mob_type, spawn.x, spawn.y, 100)
        mob.max_hp *= 2
        mob.hp = mob.max_hp
        mob.init_pathfinding(config["collisions"])
        mobs.append(mob)
    return mobs


def player_is_on_spawn_teleport(state):
    feet_position = (state["x"], state["y"] + 32)
    return any(rect.collidepoint(feet_position) for rect in MAP_CONFIGS["spawn"]["teleports"])


def enter_level(salon, restart=False):
    config = MAP_CONFIGS["level"]
    salon["current_map"] = "level"
    salon["collisions"] = config["collisions"]
    salon["grid_open"] = False
    if restart:
        salon["collected_keys"].clear()
        salon["last_attack_ids"] = [
            state.get("weapon_attack_id", -1) for state in salon["states"]
        ]
    salon["skeletons"] = create_mobs("level")
    salon["mobs"] = [mob_to_dict(mob) for mob in salon["skeletons"]]
    salon["mob"] = salon["mobs"][0] if salon["mobs"] else None
    for index, spawn in enumerate((config["spawn1"], config["spawn2"])):
        salon["states"][index]["x"] = spawn.x
        salon["states"][index]["y"] = spawn.y
        salon["states"][index]["current_map"] = "level"
        if restart:
            salon["states"][index]["alive"] = True
            salon["states"][index]["hp"] = MAX_HP
            salon["states"][index]["state"] = "idle"
            salon["states"][index]["restart_vote"] = False
            salon["states"][index]["grid_open"] = False
            salon["states"][index]["collected_keys"] = []
            salon["states"][index]["objective_step"] = 5


def open_grid(salon):
    if salon["grid_open"]:
        return
    salon["grid_open"] = True
    grid_ids = {id(collision) for collision in MAP_CONFIGS["level"]["grid_collisions"]}
    salon["collisions"] = [
        collision for collision in salon["collisions"]
        if id(collision) not in grid_ids
    ]
    for mob in salon["skeletons"]:
        mob.init_pathfinding(salon["collisions"])

server = "0.0.0.0"
port   = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    s.bind((server, port))
except socket.error as e:
    print(f"Bind error: {e}")
    raise SystemExit

s.listen(10)
print("Serveur démarré, en attente de connexions...")

# ── Salons ────────────────────────────────────────────────────────────────────
# salons[code] = {
#   "players": [conn_host, conn_guest],
#   "states":  [dict_host, dict_guest],
#   "started": False,
#   "mobs":    [dict_mob, ...],
#   "skeletons": [Mob, ...],
# }
salons = {}
salons_lock = threading.Lock()

def generate_code():
    while True:
        code = str(random.randint(1000, 9999))
        if code not in salons:
            return code

def mob_loop(code):
    """Boucle IA du mob pour un salon donné."""
    clock = pygame.time.Clock()
    while True:
        clock.tick(60)
        with salons_lock:
            if code not in salons:
                break
            salon = salons[code]
            if not salon["started"]:
                continue
            skeletons = salon["skeletons"]
            states   = salon["states"]
            current_collisions = salon["collisions"]
            grid_open = salon["grid_open"]

        now_ms = pygame.time.get_ticks()
        positions = [
            pygame.math.Vector2(state["x"], state["y"])
            for state in states
            if state.get("alive", True)
        ]
        if not positions:
            continue
        for skeleton in skeletons:
            if skeleton.mob_type == "golem" and not grid_open:
                skeleton.update()
                continue
            nearest = min(positions, key=lambda p: skeleton.position.distance_to(p))
            skeleton.update_ai(nearest, current_collisions, now_ms, skeletons)
            skeleton.update()
            for projectile in skeleton.projectiles:
                projectile.update(current_collisions)
            skeleton.projectiles = [
                projectile for projectile in skeleton.projectiles
                if projectile.active
            ]

        with salons_lock:
            if code in salons:
                salon = salons[code]
                if salon["skeletons"] is skeletons:
                    salon["mobs"] = [mob_to_dict(skeleton) for skeleton in skeletons]
                    salon["mob"] = salon["mobs"][0] if salon["mobs"] else None

def threaded_client(conn):
    try:
        action = recv_packet(conn)

        if action == "CREATE":
            with salons_lock:
                code = generate_code()
                salons[code] = {
                    "players":   [conn, None],
                    "states":    [
                        {"x": spawn1.x, "y": spawn1.y, "dir": "right", "state": "idle", "skin": "player", "alive": True, "hp": MAX_HP},
                        {"x": spawn2.x, "y": spawn2.y, "dir": "right", "state": "idle", "skin": "player2", "alive": True, "hp": MAX_HP}
                    ],
                    "started":   False,
                    "current_map": "spawn",
                    "collisions": MAP_CONFIGS["spawn"]["collisions"],
                    "grid_open": False,
                    "mobs":      [spawn_to_dict(spawn) for spawn in MAP_CONFIGS["spawn"]["mob_spawns"]],
                    "mob":       spawn_to_dict(MAP_CONFIGS["spawn"]["mob_spawns"][0]) if MAP_CONFIGS["spawn"]["mob_spawns"] else None,
                    "skeletons": [],
                    "last_attack_ids": [-1, -1],
                    "collected_keys": set(),
                    "forest_skeleton_kills": 0,
                    "restart_votes": set(),
                    "restart_id": 0,
                    "host_conn": conn
                }
            send_packet(conn, {"status": "ok", "code": code, "player": 0})
            print(f"Salon {code} créé")

            # Attendre que le guest rejoigne
            while True:
                with salons_lock:
                    if code not in salons:
                        return
                    guest_ready = salons[code]["players"][1] is not None
                if guest_ready:
                    break
                pygame.time.wait(100)

            # Attendre START de l'hôte
            while True:
                try:
                    msg = recv_packet(conn)
                    if msg == "START":
                        with salons_lock:
                            salons[code]["started"] = True
                            skeletons = create_mobs("spawn")
                            salons[code]["skeletons"] = skeletons
                            salons[code]["mobs"] = [mob_to_dict(skeleton) for skeleton in skeletons]
                            salons[code]["mob"] = salons[code]["mobs"][0] if salons[code]["mobs"] else None
                            guest_conn = salons[code]["players"][1]

                        # Envoyer spawn aux deux joueurs
                        send_packet(guest_conn, {
                            "status": "start",
                            "spawn":  salons[code]["states"][1]
                        })
                        send_packet(conn, {
                            "status": "start",
                            "spawn":  salons[code]["states"][0]
                        })
                        start_new_thread(mob_loop, (code,))
                        break

                    elif msg == "PING":
                        with salons_lock:
                            guest_connected = salons[code]["players"][1] is not None
                        send_packet(conn, {"guest_connected": guest_connected})
                except:
                    return

            player_index = 0

        elif isinstance(action, dict) and action.get("type") == "JOIN":
            code = action["code"]
            with salons_lock:
                if code not in salons:
                    send_packet(conn, {"status": "error", "msg": "Code invalide"})
                    return
                if salons[code]["players"][1] is not None:
                    send_packet(conn, {"status": "error", "msg": "Salon plein"})
                    return
                salons[code]["players"][1] = conn
            send_packet(conn, {"status": "ok", "player": 1})
            print(f"Joueur 2 rejoint le salon {code}")

            # Attendre le START (envoyé directement par le thread hôte)
            start_msg = recv_packet(conn)

            player_index = 1
            # start_msg contient déjà {"status": "start", "spawn": {...}}
            # Le spawn a déjà été envoyé, on entre directement en boucle de jeu

        else:
            return

        # ── Boucle de jeu ────────────────────────────────────────────────────
        while True:
            data = recv_packet(conn)
            if not data:
                break

            with salons_lock:
                if code not in salons:
                    break
                salon = salons[code]
                if data.get("restart_id", 0) != salon["restart_id"]:
                    data = salon["states"][player_index]
                if salon["current_map"] == "level" and data.get("current_map") == "spawn":
                    previous = salon["states"][player_index]
                    data = dict(data, x=previous["x"], y=previous["y"])
                salon["states"][player_index] = data
                if (
                    salon["current_map"] == "spawn"
                    and all(state.get("tutorial_ready", False) for state in salon["states"])
                    and all(player_is_on_spawn_teleport(state) for state in salon["states"])
                ):
                    enter_level(salon)
                if data.get("grid_open") and salon["current_map"] == "level":
                    open_grid(salon)
                salon["collected_keys"].update(data.get("collected_keys", []))
                other = salon["states"][1 - player_index]
                mobs = salon["mobs"]
                skeletons = salon["skeletons"]

                # Détection de coup : le joueur envoie weapon_rect pendant son animation
                attack_id = data.get("weapon_attack_id", -1)
                new_attack = attack_id != salon["last_attack_ids"][player_index]
                if data.get("alive", True) and data.get("hit") and new_attack and skeletons:
                    salon["last_attack_ids"][player_index] = attack_id
                    player_damage = PLAYER_DAMAGE
                    weapon_rect = data.get("weapon_rect")
                    if weapon_rect:
                        wr = pygame.Rect(weapon_rect)
                        for index, skeleton in enumerate(skeletons):
                            if not skeleton.alive:
                                continue
                            if wr.colliderect(skeleton.hitbox):
                                skeleton.take_damage(player_damage)
                                mobs[index] = mob_to_dict(skeleton)
                                salon["mobs"] = mobs
                                salon["mob"] = mobs[0] if mobs else None
                    if salon["current_map"] == "spawn":
                        salon["forest_skeleton_kills"] = sum(
                            mob.mob_type == "skeleton" and mob.dead
                            for mob in skeletons
                        )
                defeat = all(not state.get("alive", True) for state in salon["states"])
                if defeat and data.get("restart_vote"):
                    salon["restart_votes"].add(player_index)
                if defeat and len(salon["restart_votes"]) == 2:
                    salon["restart_id"] += 1
                    salon["restart_votes"].clear()
                    enter_level(salon, restart=True)
                    defeat = False
                    other = salon["states"][1 - player_index]
                    mobs = salon["mobs"]
                current_map = salon["current_map"]
                grid_open = salon["grid_open"]
                collected_keys = list(salon["collected_keys"])
                forest_skeleton_kills = salon["forest_skeleton_kills"]
                restart_votes = len(salon["restart_votes"])
                restart_id = salon["restart_id"]

            reply = {
                "player": other,
                "mobs": mobs,
                "mob": mobs[0] if mobs else None,
                "current_map": current_map,
                "grid_open": grid_open,
                "collected_keys": collected_keys,
                "forest_skeleton_kills": forest_skeleton_kills,
                "defeat": defeat,
                "restart_votes": restart_votes,
                "restart_id": restart_id,
            }
            send_packet(conn, reply)

    except Exception as e:
        print(f"Erreur client : {e}")
    finally:
        conn.close()

while True:
    conn, addr = s.accept()
    print(f"Connexion : {addr}")
    start_new_thread(threaded_client, (conn,))
