import socket
from shared.protocol import Protocol
from shared.enums import MessageType

BUFFER_SIZE = 4096


class Client:
    def __init__(self, host: str = "127.0.0.1", port: int = 7777):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.sock.setblocking(False)
        self.buf = b""

    def poll(self):
        try:
            while True:
                self.buf += self.sock.recv(BUFFER_SIZE)
        except OSError as e:
            if e.errno not in [socket.EAGAIN, socket.EWOULDBLOCK]:
                raise
            if len(self.buf) == 0:
                return None
            msg, self.buf = Protocol.extract_message(self.buf)
            return msg

    def _send(self, msg: dict):
        self.sock.send(Protocol.encode_message(msg))

    def create_account(self, username: str, password: str):
        self._send(
            {
                "type": MessageType.CREATE_ACCOUNT,
                "username": username,
                "password": password,
            }
        )

    def login(self, username: str, password: str):
        self._send(
            {
                "type": MessageType.LOGIN,
                "username": username,
                "password": password,
            }
        )

    def get_tables(self):
        self._send({"type": MessageType.GET_TABLES})

    def create_table(self, big_blind: int):
        self._send({"type": MessageType.CREATE_TABLE, "big_blind": big_blind})

    def join_table(self, table_id: int):
        self._send({"type": MessageType.JOIN_TABLE, "table_id": table_id})

    def start_table(self):
        self._send({"type": MessageType.START_TABLE})

    def action(self, action: str, amount: int | None):
        self._send(
            {
                "type": MessageType.ACTION,
                "action": action,
                "amount": amount,
            }
        )
