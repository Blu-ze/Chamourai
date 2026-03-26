import socket
import pickle

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class Network:
    def __init__(self, server_ip=None):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = server_ip if server_ip else get_local_ip()
        self.port   = 5555
        self.client.connect((self.server, self.port))

    def send_raw(self, data):
        self.client.sendall(pickle.dumps(data))

    def recv_raw(self):
        return pickle.loads(self.client.recv(4096))

    def create_salon(self):
        self.send_raw("CREATE")
        return self.recv_raw()

    def join_salon(self, code):
        self.send_raw({"type": "JOIN", "code": code})
        return self.recv_raw()

    def ping(self):
        self.send_raw("PING")
        return self.recv_raw()

    def start_game(self):
        self.send_raw("START")
        return self.recv_raw()

    def send(self, data):
        try:
            self.client.sendall(pickle.dumps(data))
            return pickle.loads(self.client.recv(4096))
        except socket.error as e:
            print(e)