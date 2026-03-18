import socket
from _thread import *
import pickle
import pytmx
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def map_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

# TiledMap au lieu de util_pygame.load_pygame → pas besoin de pygame
tmx_data = pytmx.TiledMap(map_path('map/spawn.tmx'))
spawn1 = tmx_data.get_object_by_name("Player1Spawn")
spawn2 = tmx_data.get_object_by_name("Player2Spawn")

server = "192.168.1.30"
port = 5555

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    s.bind((server, port))
except socket.error as e:
    print(e)

s.listen(2)
print("Waiting for connection, Server Started")

players = [
    {"x": spawn1.x, "y": spawn1.y, "dir": "right", "state": "idle"},
    {"x": spawn2.x, "y": spawn2.y, "dir": "right", "state": "idle"}
]

def threaded_client(conn, player):
    print(f"Joueur {player} spawn à x={players[player]['x']}, y={players[player]['y']}")
    conn.send(pickle.dumps(players[player]))

    while True:
        try:
            data = pickle.loads(conn.recv(2048))
            if not data:
                break
            players[player] = data
            reply = players[1 - player]
            conn.sendall(pickle.dumps(reply))
        except:
            break

    conn.close()

currentPlayer = 0
while True:
    conn, addr = s.accept()
    print("Connected to:", addr)
    start_new_thread(threaded_client, (conn, currentPlayer))
    currentPlayer = (currentPlayer + 1) % 2