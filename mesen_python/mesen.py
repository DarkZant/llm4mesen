import socket


class Mesen:
    """Allows Python to communicate with Mesen through sockets"""
    def __init__(self, host: str="localhost", port: int=9999):
        self.server = socket.socket()
        self.server.bind((host, port))


    def connect(self):
        self.server.listen(1)
        print("Waiting for Mesen connection...")
        self.client, addr = self.server.accept()
        print("Mesen connected: ", addr)


    def send(self, message: str=b""):
        self.client.send(message + b"\n")


    def send_string(self, message: str=""):
        self.send(message.encode())


    def send_number(self, number: int):
        self.send_string(str(number))


    def receive_line(self) -> str:
        message = b""
        while not message.endswith(b"\n"):
            chunk = self.client.recv(1)
            if not chunk:
                break
            message += chunk
        return message.decode().strip()
    
    
    def receive_int(self) -> int:
        return int(self.receive_line())
    
    
    def receive_bytes(self, num_bytes: int) -> str:
        message = b""
        while len(message) < num_bytes:
            chunk = self.client.recv(num_bytes - len(message))
            if not chunk:
                break
            message += chunk
        return message
        