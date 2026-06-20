import socket
from shared.protocol import Protocol
from shared.enums import MessageType

BUFFER_SIZE = 4096


class Client:
    def __init__(self, host: str = "127.0.0.1", port: int = 7777):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.sock.setblocking(False)
        self._buf = b""

    def poll(self) -> list[dict]:
        try:
            while True:
                chunk = self.sock.recv(BUFFER_SIZE)
                if not chunk:
                    raise ConnectionError("Server closed connection")
                self._buf += chunk
        except BlockingIOError:
            pass

        messages = []
        while True:
            msg, self._buf = Protocol.extract_message(self._buf)
            if msg is None:
                break
            messages.append(msg)
        return messages

    def _send(self, msg: dict) -> None:
        self.sock.sendall(Protocol.encode_message(msg))

    def create_account(self, username: str, password: str) -> None:
        self._send({
            "type": MessageType.CREATE_ACCOUNT,
            "username": username,
            "password": password,
        })

    def login(self, username: str, password: str) -> None:
        self._send({
            "type": MessageType.LOGIN,
            "username": username,
            "password": password,
        })

    def get_tables(self) -> None:
        self._send({"type": MessageType.GET_TABLES})

    def create_table(self, big_blind: int, avatar: int = 1) -> None:
        self._send({
            "type": MessageType.CREATE_TABLE,
            "big_blind": big_blind,
            "avatar": avatar,
        })

    def join_table(self, table_id: int, avatar: int = 1) -> None:
        self._send({
            "type": MessageType.JOIN_TABLE,
            "table_id": table_id,
            "avatar": avatar,
        })

    def start_table(self) -> None:
        self._send({"type": MessageType.START_TABLE})

    def action(self, action: str, amount: int = 0) -> None:
        self._send({
            "type": MessageType.ACTION,
            "action": action,
            "amount": amount,
        })