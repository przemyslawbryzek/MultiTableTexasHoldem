import socket
import select
import sys
import logging
from server.network.table_manager import TableManager
from shared.protocol import Protocol, MessageType


class Server:
    def __init__(self, host: str = '0.0.0.0', port: int = 7777):
        self.host = host
        self.port = port
        self.table_manager = TableManager()
        self.fd_to_socket: dict[int, socket.socket] = {}
        self.fd_to_buffer: dict[int, bytes] = {}
        logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s', stream=sys.stdout)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.setblocking(False)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()

        self.epoll = select.epoll()
        self.epoll.register(self.server_socket.fileno(), select.EPOLLIN)

        logging.info(f"Server started on {self.host}:{self.port}")

    def run(self):
        logging.info("Server running, waiting for connections...")
        try:
            while True:
                events = self.epoll.poll(timeout=1)
                for fileno, event in events:
                    if fileno == self.server_socket.fileno():
                        self._accept_connection()
                    elif event & (select.EPOLLHUP | select.EPOLLERR):
                        self._disconnect_client(fileno)
                    elif event & select.EPOLLIN:
                        self._handle_client_data(fileno)
        finally:
            self._shutdown()

    def _accept_connection(self):
        try:
            client_socket, addr = self.server_socket.accept()
            client_socket.setblocking(False)
            fd = client_socket.fileno()

            self.fd_to_socket[fd] = client_socket
            self.fd_to_buffer[fd] = b""
            self.epoll.register(fd, select.EPOLLIN)

            logging.info(f"New connection from {addr} (fd={fd})")
        except Exception as e:
            logging.error(f"Accept error: {e}")

    def _disconnect_client(self, fileno: int):
        try:
            self.epoll.unregister(fileno)
        except Exception:
            pass

        sock = self.fd_to_socket.pop(fileno, None)
        self.fd_to_buffer.pop(fileno, None)

        if sock:
            self.table_manager.remove_player_by_fd(fileno)
            sock.close()
            logging.info(f"Client disconnected (fd={fileno})")

    def _shutdown(self):
        for sock in self.fd_to_socket.values():
            try:
                sock.close()
            except Exception:
                pass
        try:
            self.epoll.unregister(self.server_socket.fileno())
            self.epoll.close()
        except Exception:
            pass
        self.server_socket.close()
        logging.info("Server shutdown.")

    def _handle_client_data(self, fileno: int):
        sock = self.fd_to_socket.get(fileno)
        if not sock:
            return

        try:
            chunk = sock.recv(4096)
            if not chunk:
                self._disconnect_client(fileno)
                return

            self.fd_to_buffer[fileno] += chunk
            while True:
                msg, self.fd_to_buffer[fileno] = Protocol.extract_message(
                    self.fd_to_buffer[fileno]
                )
                if msg is None:
                    break
                self._handle_message(fileno, msg)

        except ConnectionResetError:
            self._disconnect_client(fileno)
        except Exception as e:
            logging.error(f"Error reading fd={fileno}: {e}")
            self._disconnect_client(fileno)
    def _handle_message(self, fileno: int, msg: dict):
        msg_type = msg.get("type")
        logging.debug(f"fd={fileno} type={msg_type}")

        handlers = {
            MessageType.CREATE_ACCOUNT: self._handle_create_account,
            MessageType.LOGIN:          self._handle_login,
            MessageType.GET_TABLES:     self._handle_get_tables,
            MessageType.CREATE_TABLE:   self._handle_create_table,
            MessageType.JOIN_TABLE:     self._handle_join_table,
            MessageType.START_TABLE:    self._handle_start_table,
            MessageType.ACTION:         self._handle_action,
        }

        handler = handlers.get(msg_type)
        if handler:
            handler(fileno, msg)
        else:
            self._send_error(fileno, f"Unknown message type: {msg_type}")


    def _handle_create_account(self, fileno: int, msg: dict):
        # TODO: implement with SQLite
        # For now: acknowledge
        self._send(fileno, {"type": MessageType.CREATE_ACCOUNT_RESPONSE, "message": "Account created"})

    def _handle_get_tables(self, fileno: int, msg: dict):
        tables = self.table_manager.get_tables()
        self._send(fileno, {"type": MessageType.GET_TABLES_RESPONSE, "tables": tables})

    def _handle_login(self, fileno: int, msg: dict):
        # TODO: implement with SQLite
        # For now: acknowledge
        self._send(fileno, {"type": MessageType.LOGIN_RESPONSE, "message": "Logged in"})

    def _handle_create_table(self, fileno: int, msg: dict):
        try:
            player_name = msg.get("player_name", "Unknown")
            player_id = msg.get("player_id", fileno)
            big_blind = msg.get("big_blind", 20)

            table_id = self.table_manager.create_table(
                owner_fd=fileno,
                owner_id=player_id,
                owner_name=player_name,
                big_blind=big_blind,
            )
            logging.info(f"Table {table_id} created by fd={fileno}")
            self._send(fileno, {
                "type": MessageType.CREATE_TABLE_RESPONSE,
                "success": True,
                "table_id": table_id,
                "error": None,
            })
            self._broadcast_table_state(table_id)

        except Exception as e:
            self._send_error(fileno, str(e))

    def _handle_join_table(self, fileno: int, msg: dict):
        try:
            table_id = msg["table_id"]
            player_name = msg.get("player_name", "Unknown")
            player_id = msg.get("player_id", fileno)

            self.table_manager.add_player_to_table(
                table_id=table_id,
                player_id=player_id,
                player_name=player_name,
                client_fd=fileno,
            )

            self._send(fileno, {
                "type": MessageType.JOIN_TABLE_RESPONSE,
                "success": True,
                "table_id": table_id,
                "error": None,
            })

            table = self.table_manager.get_table(table_id)
            joined_msg = {
                "type": MessageType.PLAYER_JOINED,
                "player": {
                    "id": player_id,
                    "name": player_name,
                    "chips": table.players[-1].chips.total_value(),
                }
            }
            self._broadcast(table_id, joined_msg, exclude_fd=fileno)
            self._broadcast_table_state(table_id)
            logging.info(f"Player {player_name} joined table {table_id}")

        except Exception as e:
            self._send_error(fileno, str(e))

    def _handle_start_table(self, fileno: int, msg: dict):
        try:
            table_id = self.table_manager.get_table_id_by_fd(fileno)
            if table_id is None:
                self._send_error(fileno, "You are not at a table")
                return

            table = self.table_manager.get_table(table_id)
            table.start_new_hand()

            logging.info(f"Hand started at table {table_id}")
            self._broadcast(table_id, {"type": MessageType.GAME_START})
            self._broadcast_table_state(table_id)

        except Exception as e:
            self._send_error(fileno, str(e))

    def _handle_action(self, fileno: int, msg: dict):
        try:
            table_id = self.table_manager.get_table_id_by_fd(fileno)
            if table_id is None:
                self._send_error(fileno, "You are not at a table")
                return

            player_id = self.table_manager.get_player_id_by_fd(fileno)
            action = msg.get("action")
            amount = msg.get("amount", 0)

            table = self.table_manager.get_table(table_id)
            table.process_player_action(player_id, action, amount)

            self._send(fileno, {
                "type": MessageType.ACTION_RESPONSE,
                "success": True,
                "action": action,
                "amount": amount,
                "error": None,
            })

            logging.info(f"Player {player_id} action={action} amount={amount} table={table_id}")


            from shared.enums import GameState
            if table.game_state == GameState.WAITING:
                self._broadcast_hand_end(table_id)
            else:
                self._broadcast_table_state(table_id)

        except ValueError as e:
            self._send_error(fileno, str(e))
        except Exception as e:
            logging.error(f"Action error: {e}")
            self._send_error(fileno, "Internal server error")

    def _broadcast_table_state(self, table_id: int):
        table = self.table_manager.get_table(table_id)
        if not table:
            return

        fds = self.table_manager.get_fds_at_table(table_id)

        for fd in fds:
            player_id = self.table_manager.get_player_id_by_fd(fd)
            state = self._build_state_message(table, viewer_id=player_id)
            self._send(fd, state)

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

    def _send(self, fileno: int, msg: dict):
        sock = self.fd_to_socket.get(fileno)
        if not sock:
            return
        try:
            data = Protocol.encode_message(msg)
            sock.sendall(data)
        except Exception as e:
            logging.error(f"Send error fd={fileno}: {e}")
            self._disconnect_client(fileno)

    def _send_error(self, fileno: int, message: str):
        logging.warning(f"Error to fd={fileno}: {message}")
        self._send(fileno, {
            "type": MessageType.ERROR,
            "message": message,
        })

    def _build_state_message(self, table, viewer_id: int) -> dict:
        players_info = []
        for p in table.players:
            players_info.append({
                "id": p.id,
                "name": p.name,
                "chips": p.chips.total_value(),
                "bet": p.bet_this_round,
                "is_folded": p.is_folded,
                "is_all_in": p.is_all_in,
                "is_active": p.is_active,
                "hand": [str(c) for c in p.hand] if p.id == viewer_id else [],
                "hand_size": len(p.hand),
            })

        return {
            "type": MessageType.STATE,
            "game_state": table.game_state.name,
            "players": players_info,
            "community_cards": [str(c) for c in table.community_cards],
            "pot": table.pot.total_value(),
            "current_player": table.players[table.current_player_idx].id,
            "highest_bet": table.highest_bet,
            "small_blind": table.small_blind,
            "big_blind": table.big_blind,
        }