import socket
import selectors
import json
import os

SERVER_IP = "127.0.0.1"

class TCPServer:
    # Swapped out the socket path for IP and port
    def __init__(self, socket_path=("0.0.0.0", 5555)):
        self.socket_path = socket_path
        self.sel = selectors.DefaultSelector()
        self.clients = {}  # Maps socket to buffer
        
        # Swapped AF_UNIX for AF_INET
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.sock.bind(self.socket_path)
        self.sock.listen()
        self.sock.setblocking(False)
        
        self.sel.register(self.sock, selectors.EVENT_READ, data="accept")

    def broadcast(self, msg_dict):
        payload = json.dumps(msg_dict) + "\n"
        for conn in self.clients:
            try:
                conn.sendall(payload.encode('utf-8'))
            except BrokenPipeError:
                pass

    def send_to(self, conn, msg_dict):
        payload = json.dumps(msg_dict) + "\n"
        conn.sendall(payload.encode('utf-8'))

    def poll_events(self, timeout=1.0):
        """Returns a list of (connection, message_dict) tuples."""
        messages = []
        events = self.sel.select(timeout=timeout)
        for key, mask in events:
            if key.data == "accept":
                conn, _ = key.fileobj.accept()
                conn.setblocking(False)
                self.sel.register(conn, selectors.EVENT_READ, data="client")
                self.clients[conn] = ""
            elif key.data == "client":
                conn = key.fileobj
                try:
                    data = conn.recv(1024)
                    if data:
                        self.clients[conn] += data.decode('utf-8')
                        while "\n" in self.clients[conn]:
                            line, self.clients[conn] = self.clients[conn].split("\n", 1)
                            if line.strip():
                                messages.append((conn, json.loads(line)))
                    else:
                        self.sel.unregister(conn)
                        conn.close()
                        del self.clients[conn]
                        messages.append((conn, {"action": "disconnect"}))
                except Exception:
                    pass
        return messages

class TCPClient:
    def __init__(self, socket_path=(SERVER_IP, 5555)):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(socket_path)
        self.buffer = ""

    def send(self, msg_dict):
        payload = json.dumps(msg_dict) + "\n"
        self.sock.sendall(payload.encode('utf-8'))

    def recv_all(self):
        """Non-blocking read, returns a list of received message dicts."""
        self.sock.setblocking(False)
        try:
            data = self.sock.recv(1024)
            if data:
                self.buffer += data.decode('utf-8')
        except BlockingIOError:
            pass

        messages = []
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line.strip():
                messages.append(json.loads(line))
        return messages
