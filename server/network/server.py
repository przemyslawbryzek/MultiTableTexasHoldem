import socket
import select
import sys
import logging
from dataclasses import dataclass
from server.utils import kdf
from server.utils.db import DB
from server.network.table_manager import TableManager
from shared import discovery
from shared.protocol import Protocol
from shared.enums import GameState, MessageType, ActionType
from shared.game_state import (
    GameState as GameStateData,
    PlayerState,
    SidePotState,
    AvailableAction,
)

BUFFER_SIZE = 4096
DEFAULT_PORT = 7777


@dataclass
class User:
    id: int
    username: str


@dataclass
class Conn:
    fd: int
    sock: socket.socket
    buf: bytes
    user: User | None


class Server:

    def __init__(self, *, host: str = "0.0.0.0", port: int = DEFAULT_PORT):
        self.db = DB()
        self.host = host
        self.port = port
        self.table_manager = TableManager()
        self.conns: dict[int, Conn] = {}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.discovery_socket = discovery.join_membership(listening_port=port)
        self.epoll = select.epoll()
        self.epoll.register(self.server_socket.fileno(), select.EPOLLIN)
        self.epoll.register(self.discovery_socket.fileno(), select.EPOLLIN)
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] %(levelname)s: %(message)s",
            stream=sys.stdout,
        )
        logging.info(f"server started on {self.host}:{self.port}")

    def run(self):
        logging.info("server running, waiting for connections...")
        try:
            while True:
                events = self.epoll.poll()
                for fd, event in events:
                    if fd == self.server_socket.fileno():
                        self._accept_connection()
                    elif fd == self.discovery_socket.fileno():
                        discovery.probe_response(self.discovery_socket, self.port)
                    elif event & (select.EPOLLHUP | select.EPOLLERR):
                        self._disconnect_client(fd)
                    elif event & select.EPOLLIN:
                        self._handle_client_data(fd)
        finally:
            self._shutdown()

    def _accept_connection(self):
        try:
            client_socket, addr = self.server_socket.accept()
            client_socket.setblocking(False)
            fd = client_socket.fileno()
            self.conns[fd] = Conn(fd, client_socket, b"", None)
            self.epoll.register(fd, select.EPOLLIN)
            logging.info(f"new connection from {addr} (fd={fd})")
        except Exception as e:
            logging.error(f"accept error: {e}")

    def _disconnect_client(self, fd: int):
        try:
            self.epoll.unregister(fd)
        except Exception:
            pass
        conn = self.conns.pop(fd, None)
        if not conn:
            return
        conn.sock.close()
        logging.info(f"client disconnected (fd={fd})")
        if conn.user:
            self.table_manager.remove_player_by_fd(conn.fd)

    def _shutdown(self):
        for conn in self.conns.values():
            try:
                conn.sock.close()
            except Exception:
                pass
        try:
            self.epoll.unregister(self.server_socket.fileno())
            self.epoll.close()
        except Exception:
            pass
        self.server_socket.close()
        logging.info("server shutdown")

    def _handle_client_data(self, fd: int):
        conn = self.conns.get(fd)
        if not conn:
            return
        try:
            chunk = conn.sock.recv(BUFFER_SIZE)
            if not chunk:
                self._disconnect_client(fd)
                return
            conn.buf += chunk
            while True:
                msg, conn.buf = Protocol.extract_message(conn.buf)
                if msg is None:
                    break
                self._handle_message(conn, msg)
        except ConnectionResetError:
            self._disconnect_client(fd)
        except Exception as e:
            logging.error(f"error reading fd={fd}: {e}")
            self._disconnect_client(fd)

    def _extract_field(self, conn: Conn, msg: dict, name: str, t: type):
        v = msg.get(name)
        if type(v) is not t:
            self._send_error(conn.fd, f"Missing or invalid field '{name}'")
            return None
        return v

    def _handle_message(self, conn: Conn, msg: dict):
        msg_type = self._extract_field(conn, msg, "type", str)
        if not msg_type:
            return
        handlers = {
            MessageType.CREATE_ACCOUNT: self._handle_create_account,
            MessageType.LOGIN: self._handle_login,
            MessageType.GET_TABLES: self._handle_get_tables,
            MessageType.CREATE_TABLE: self._handle_create_table,
            MessageType.JOIN_TABLE: self._handle_join_table,
            MessageType.START_TABLE: self._handle_start_table,
            MessageType.ACTION: self._handle_action,
        }
        handler = handlers.get(msg_type)
        if handler is None:
            self._send_error(conn.fd, f"Unknown message type: {msg_type}")
            return
        logging.debug(f"fd={conn.fd} type={msg_type}")
        require_auth = msg_type not in [
            MessageType.CREATE_ACCOUNT,
            MessageType.LOGIN,
        ]
        if require_auth and conn.user is None:
            self._send_error(conn.fd, "Authentication required")
            return
        handler(conn, msg)

    def _handle_create_account(self, conn: Conn, msg: dict):
        username = self._extract_field(conn, msg, "username", str)
        if not username:
            return
        password = self._extract_field(conn, msg, "password", str)
        if not password:
            return
        hash = kdf.hash(password)
        self.db.create_user(username, hash)
        self._send(
            conn.fd,
            {
                "type": MessageType.CREATE_ACCOUNT_RESPONSE,
                "success": True,
                "error": None,
            },
        )

    def _handle_login(self, conn: Conn, msg: dict):
        username = self._extract_field(conn, msg, "username", str)
        if not username:
            return
        password = self._extract_field(conn, msg, "password", str)
        if not password:
            return
        user = self.db.get_user(username)
        ok = False
        if user is None:
            kdf.hash("mock")
        else:
            ok = kdf.verify(password, user.password)
        if ok:
            conn.user = User(user.id, user.username)
            self._send(
                conn.fd,
                {
                    "type": MessageType.LOGIN_RESPONSE,
                    "success": True,
                    "player_id": user.id,
                    "player_name": user.username,
                    "error": None,
                },
            )
        else:
            self._send(
                conn.fd,
                {
                    "type": MessageType.LOGIN_RESPONSE,
                    "success": False,
                    "player_id": None,
                    "player_name": None,
                    "error": "Invalid credentials",
                },
            )

    def _handle_get_tables(self, conn: Conn, _: dict):
        tables = self.table_manager.get_tables()
        self._send(
            conn.fd,
            {
                "type": MessageType.GET_TABLES_RESPONSE,
                "tables": tables,
            },
        )

    def _handle_create_table(self, conn: Conn, msg: dict):
        try:
            big_blind = msg.get("big_blind", 20)
            if not isinstance(big_blind, int) or big_blind <= 0:
                big_blind = 20
            player_avatar = msg.get("avatar", 1)
            if not isinstance(player_avatar, int):
                player_avatar = 1
            table_id = self.table_manager.create_table(
                conn.fd,
                conn.user.id,
                conn.user.username,
                player_avatar,
                big_blind,
            )
            logging.info(f"table {table_id} created by fd={conn.fd}")
            self._send(
                conn.fd,
                {
                    "type": MessageType.CREATE_TABLE_RESPONSE,
                    "success": True,
                    "table_id": table_id,
                    "error": None,
                },
            )
            self._broadcast_table_state(table_id)
        except Exception as e:
            import traceback

            logging.error(f"_handle_create_table error: {traceback.format_exc()}")
            self._send(
                conn.fd,
                {
                    "type": MessageType.CREATE_TABLE_RESPONSE,
                    "success": False,
                    "table_id": None,
                    "error": str(e),
                },
            )

    def _handle_join_table(self, conn: Conn, msg: dict):
        table_id = self._extract_field(conn, msg, "table_id", int)
        if not table_id:
            return
        try:
            player_id = conn.user.id
            player_name = conn.user.username
            player_avatar = self._extract_field(conn, msg, "avatar", int)
            if player_avatar is None:
                player_avatar = 1
            self.table_manager.add_player_to_table(
                table_id, player_id, player_name, player_avatar, conn.fd
            )
            self._send(
                conn.fd,
                {
                    "type": MessageType.JOIN_TABLE_RESPONSE,
                    "success": True,
                    "table_id": table_id,
                    "error": None,
                },
            )
            table = self.table_manager.get_table(table_id)
            joined_msg = {
                "type": MessageType.PLAYER_JOINED,
                "player": {
                    "id": player_id,
                    "name": player_name,
                    "avatar": player_avatar,
                    "chips": table.players[-1].chips.total_value(),
                },
            }
            self._broadcast(table_id, joined_msg, exclude_fd=conn.fd)
            self._broadcast_table_state(table_id)
            logging.info(f"player {player_id} joined table {table_id}")
        except Exception as e:
            self._send(
                conn.fd,
                {
                    "type": MessageType.JOIN_TABLE_RESPONSE,
                    "success": False,
                    "table_id": None,
                    "error": str(e),
                },
            )

    def _handle_start_table(self, conn: Conn, _):
        try:
            table_id = self.table_manager.get_table_id_by_fd(conn.fd)
            if table_id is None:
                self._send_error(conn.fd, "You are not at a table")
                return
            table = self.table_manager.get_table(table_id)
            table.start_new_hand()
            logging.info(f"hand started at table {table_id}")
            self._broadcast(table_id, {"type": MessageType.GAME_START})
            self._broadcast_table_state(table_id)
        except Exception as e:
            self._send_error(conn.fd, str(e))

    def _handle_action(self, conn: Conn, msg: dict):
        action = self._extract_field(conn, msg, "action", str)
        if not action:
            return
        amount = self._extract_field(conn, msg, "amount", int)
        if not amount:
            amount = 0
        try:
            player_id = conn.user.id
            table_id = self.table_manager.get_table_id_by_fd(conn.fd)
            if table_id is None:
                self._send_error(conn.fd, "You are not at a table")
                return
            table = self.table_manager.get_table(table_id)
            table.process_player_action(player_id, action, amount)
            self._send(
                conn.fd,
                {
                    "type": MessageType.ACTION_RESPONSE,
                    "success": True,
                    "action": action,
                    "amount": amount,
                    "error": None,
                },
            )
            logging.info(
                f"player {player_id} action={action} amount={amount} table={table_id}"
            )
            if table.game_state == GameState.WAITING:
                self._broadcast_hand_end(table_id)
            else:
                self._broadcast_table_state(table_id)
        except ValueError as e:
            self._send(
                conn.fd,
                {
                    "type": MessageType.ACTION_RESPONSE,
                    "success": False,
                    "action": action,
                    "amount": amount,
                    "error": str(e),
                },
            )
        except Exception as e:
            logging.error(f"action error: {e}")
            self._send_error(conn.fd, "Internal server error")

    def _broadcast_table_state(self, table_id: int):
        table = self.table_manager.get_table(table_id)
        if not table:
            return
        fds = self.table_manager.get_fds_at_table(table_id)
        for fd in fds:
            player_id = self.table_manager.get_player_id_by_fd(fd)
            try:
                state = self._build_state_message(table, viewer_id=player_id)
                self._send(fd, state)
            except Exception:
                import traceback

                logging.error(
                    f"_broadcast_table_state failed for fd={fd}:{traceback.format_exc()}"
                )

    def _broadcast_hand_end(self, table_id: int):
        table = self.table_manager.get_table(table_id)
        if not table:
            return
        winners = table.get_winner()
        winner_info = [
            {
                "id": w.id,
                "name": w.name,
                "chips": w.chips.total_value(),
                "hand": [str(c) for c in w.hand],
            }
            for w in winners
        ]
        msg = {
            "type": MessageType.HAND_END,
            "winners": winner_info,
        }
        self._broadcast(table_id, msg)
        self._broadcast_table_state(table_id)

    def _broadcast(self, table_id: int, msg: dict, exclude_fd: int = None):
        fds = self.table_manager.get_fds_at_table(table_id)
        for fd in fds:
            if fd != exclude_fd:
                self._send(fd, msg)

    def _send(self, fd: int, msg: dict) -> None:
        conn = self.conns.get(fd)
        if conn is None:
            return
        try:
            data = Protocol.encode_message(msg)
            conn.sock.sendall(data)
        except Exception as e:
            logging.error(f"send error fd={fd}: {e}")
            self._disconnect_client(fd)

    def _send_error(self, fd: int, message: str) -> None:
        logging.warning(f"error to fd={fd}: {message}")
        self._send(fd, {"type": MessageType.ERROR, "message": message})

    def _build_state_message(self, table, viewer_id: int) -> dict:
        players = []
        for p in table.players:
            players.append(
                PlayerState(
                    id=p.id,
                    name=p.name,
                    avatar=p.avatar,
                    chips=p.chips.to_dict(),
                    bet_this_round=p.bet_this_round,
                    total_bet_this_hand=p.total_bet_this_hand,
                    is_active=p.is_active,
                    is_folded=p.is_folded,
                    is_all_in=p.is_all_in,
                    position=table.players.index(p),
                    hand=[str(c) for c in p.hand] if p.id == viewer_id else [],
                    hand_size=len(p.hand),
                )
            )

        side_pots = [
            SidePotState(
                amount=sp.amount,
                eligible_players=[pl.id for pl in sp.eligible_players],
            )
            for sp in table.side_pots
        ]

        available_actions = []
        for act in table.get_available_actions(viewer_id):
            available_actions.append(
                AvailableAction(
                    action=ActionType(act["action"]),
                    min_amount=act["min_amount"],
                    max_amount=act["max_amount"],
                    label=act["label"],
                )
            )

        game_state = GameStateData(
            phase=table.game_state,
            owner_id=table.owner.id,
            hand_number=table.hand_number,
            dealer_position=table.dealer_position,
            current_player_id=(
                table.players[table.current_player_idx].id
                if table.game_state != GameState.WAITING
                else -1
            ),
            small_blind=table.small_blind,
            big_blind=table.big_blind,
            highest_bet=table.highest_bet,
            last_raise=table.last_raise,
            pot=table.pot.total_value(),
            side_pots=side_pots,
            community_cards=[str(c) for c in table.community_cards],
            players=players,
            available_actions=available_actions,
        )
        return game_state.to_dict()
