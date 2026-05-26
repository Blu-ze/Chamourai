import socket
from _thread import *
import pickle
import pytmx
import pygame
import os
import threading
import random
from mob import Mob
from player import PLAYER_DAMAGE

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def map_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

pygame.init()

tmx_data  = pytmx.TiledMap(map_path('map/spawn.tmx'))
spawn1    = tmx_data.get_object_by_name("Player1Spawn")
spawn2    = tmx_data.get_object_by_name("Player2Spawn")

def get_optional_object(name):
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
mob_spawns = [
    (MOB_TYPES_BY_OBJECT_NAME[obj.name], obj)
    for obj in tmx_data.objects
    if obj.name in MOB_TYPES_BY_OBJECT_NAME
]
if not mob_spawns:
    legacy_spawn = get_optional_object("MobSpawn")
    if legacy_spawn:
        mob_spawns.append(("skeleton", legacy_spawn))

collisions = []
for obj in tmx_data.objects:
    if obj.type == "collision":
        collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

def mob_to_dict(mob):
    return {
        "x":     mob.position.x,
        "y":     mob.position.y,
        "dir":   mob.direction,
        "state": mob.state,
        "alive": mob.alive,
        "hp":    mob.hp,
        "type":  mob.mob_type,
    }

def spawn_to_dict(spawn_data):
    mob_type, spawn = spawn_data
    return {"x": spawn.x, "y": spawn.y, "dir": "right", "state": "idle", "type": mob_type}

def create_mobs():
    mobs = []
    for mob_type, spawn in mob_spawns:
        mob = Mob(mob_type, spawn.x, spawn.y, 100)
        mob.init_pathfinding(collisions)
        mobs.append(mob)
    return mobs

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

        now_ms = pygame.time.get_ticks()
        positions = [
            pygame.math.Vector2(states[0]["x"], states[0]["y"]),
            pygame.math.Vector2(states[1]["x"], states[1]["y"])
        ]
        for skeleton in skeletons:
            nearest = min(positions, key=lambda p: skeleton.position.distance_to(p))
            skeleton.update_ai(nearest, collisions, now_ms, skeletons)
            skeleton.update()
            for projectile in skeleton.projectiles:
                projectile.update(collisions)
            skeleton.projectiles = [
                projectile for projectile in skeleton.projectiles
                if projectile.active
            ]

        with salons_lock:
            if code in salons:
                salons[code]["mobs"] = [mob_to_dict(skeleton) for skeleton in skeletons]
                salons[code]["mob"] = salons[code]["mobs"][0] if salons[code]["mobs"] else None

def threaded_client(conn):
    try:
        action = pickle.loads(conn.recv(2048))

        if action == "CREATE":
            with salons_lock:
                code = generate_code()
                salons[code] = {
                    "players":   [conn, None],
                    "states":    [
                        {"x": spawn1.x, "y": spawn1.y, "dir": "right", "state": "idle",  "skin": "player"},
                        {"x": spawn2.x, "y": spawn2.y, "dir": "right", "state": "idle",  "skin": "player2"}
                    ],
                    "started":   False,
                    "mobs":      [spawn_to_dict(spawn) for spawn in mob_spawns],
                    "mob":       spawn_to_dict(mob_spawns[0]) if mob_spawns else None,
                    "skeletons": [],
                    "host_conn": conn
                }
            conn.sendall(pickle.dumps({"status": "ok", "code": code, "player": 0}))
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
                    msg = pickle.loads(conn.recv(2048))
                    if msg == "START":
                        with salons_lock:
                            salons[code]["started"] = True
                            skeletons = create_mobs()
                            salons[code]["skeletons"] = skeletons
                            salons[code]["mobs"] = [mob_to_dict(skeleton) for skeleton in skeletons]
                            salons[code]["mob"] = salons[code]["mobs"][0] if salons[code]["mobs"] else None
                            guest_conn = salons[code]["players"][1]

                        # Envoyer spawn aux deux joueurs
                        guest_conn.sendall(pickle.dumps({
                            "status": "start",
                            "spawn":  salons[code]["states"][1]
                        }))
                        conn.sendall(pickle.dumps({
                            "status": "start",
                            "spawn":  salons[code]["states"][0]
                        }))
                        start_new_thread(mob_loop, (code,))
                        break

                    elif msg == "PING":
                        with salons_lock:
                            guest_connected = salons[code]["players"][1] is not None
                        conn.sendall(pickle.dumps({"guest_connected": guest_connected}))
                except:
                    return

            player_index = 0

        elif isinstance(action, dict) and action.get("type") == "JOIN":
            code = action["code"]
            with salons_lock:
                if code not in salons:
                    conn.sendall(pickle.dumps({"status": "error", "msg": "Code invalide"}))
                    return
                if salons[code]["players"][1] is not None:
                    conn.sendall(pickle.dumps({"status": "error", "msg": "Salon plein"}))
                    return
                salons[code]["players"][1] = conn
            conn.sendall(pickle.dumps({"status": "ok", "player": 1}))
            print(f"Joueur 2 rejoint le salon {code}")

            # Attendre le START (envoyé directement par le thread hôte)
            start_msg = pickle.loads(conn.recv(2048))
            # Renvoyer confirmation
            conn.sendall(pickle.dumps({"status": "ready"}))

            player_index = 1
            # start_msg contient déjà {"status": "start", "spawn": {...}}
            # Le spawn a déjà été envoyé, on entre directement en boucle de jeu

        else:
            return

        # ── Boucle de jeu ────────────────────────────────────────────────────
        while True:
            data = pickle.loads(conn.recv(2048))
            if not data:
                break

            with salons_lock:
                if code not in salons:
                    break
                salons[code]["states"][player_index] = data
                other = salons[code]["states"][1 - player_index]
                mobs = salons[code]["mobs"]
                skeletons = salons[code]["skeletons"]

                # Détection de coup : le joueur envoie weapon_rect pendant son animation
                if data.get("hit") and skeletons:
                    weapon_rect = data.get("weapon_rect")
                    if weapon_rect:
                        wr = pygame.Rect(weapon_rect)
                        for index, skeleton in enumerate(skeletons):
                            if not skeleton.alive:
                                continue
                            if wr.colliderect(skeleton.hitbox):
                                skeleton.take_damage(PLAYER_DAMAGE)
                                mobs[index] = mob_to_dict(skeleton)
                                salons[code]["mobs"] = mobs
                                salons[code]["mob"] = mobs[0] if mobs else None

            reply = {"player": other, "mobs": mobs, "mob": mobs[0] if mobs else None}
            conn.sendall(pickle.dumps(reply))

    except Exception as e:
        print(f"Erreur client : {e}")
    finally:
        conn.close()

while True:
    conn, addr = s.accept()
    print(f"Connexion : {addr}")
    start_new_thread(threaded_client, (conn,))
