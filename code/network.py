import socket
import pickle
import struct

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
        payload = pickle.dumps(data)
        self.client.sendall(struct.pack("!I", len(payload)) + payload)

    def recv_raw(self):
        header = self._recv_exact(4)
        size = struct.unpack("!I", header)[0]
        return pickle.loads(self._recv_exact(size))

    def _recv_exact(self, size):
        chunks = []
        remaining = size
        while remaining:
            chunk = self.client.recv(remaining)
            if not chunk:
                raise ConnectionError("Connexion interrompue pendant la reception.")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

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
            self.send_raw(data)
            return self.recv_raw()
        except (socket.error, ConnectionError) as e:
            print(e)
