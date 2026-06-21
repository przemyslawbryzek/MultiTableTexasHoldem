import sys
import pygame
from shared.enums import MessageType
from shared.game_state import GameState as GameStateData
from client.network.client import Client
from client.ui.screens.conn_screen import ConnectionScreen
from client.ui.screens.login_screen import LoginScreen
from client.ui.screens.lobby_screen import LobbyScreen, TableInfo
from client.ui.screens.game_screens.game_screen_manager import GameScreenManager
from client.ui.screens.game_screens.top_screen import TopScreen
from client.ui.screens.game_screens.bottom_screen import GameBottomScreen

SCREEN_W, SCREEN_H = 800, 700
FPS = 60


class AppState:
    CONNECTING = "connecting"
    LOGIN = "login"
    LOBBY = "lobby"
    GAME = "game"


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Poker")
        self.clock = pygame.time.Clock()

        self.client: Client | None = None
        self.player_id: int | None = None
        self.player_name: str | None = None
        self.avatar_index: int = 1

        self.state = AppState.CONNECTING
        self.ui: ConnectionScreen | LoginScreen | LobbyScreen | GameScreenManager = (
            ConnectionScreen()
        )

        self.running = True

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS)
            self._handle_events()
            self._poll_server()
            self._update(dt)
            self._draw()

        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if self.ui is None:
                continue

            result = self.ui.handle_event(event)
            if result:
                self._handle_ui_action(*result)

    def _handle_ui_action(self, action: str, data) -> None:
        match self.state:

            case AppState.CONNECTING:
                if action == "connect":
                    self._do_connect(data)

            case AppState.LOGIN:
                if action == "login":
                    username, password = data
                    if username and password:
                        self.client.login(username, password)
                        self.ui.set_status("Logging in…")
                elif action == "create_account":
                    username, password = data
                    if username and password:
                        self.client.create_account(username, password)
                        self.ui.set_status("Creating account…")

            case AppState.LOBBY:
                if action == "join":
                    self.client.join_table(data, avatar=self.avatar_index)
                    self.ui.set_status(f"Joining table {data}…")
                elif action == "create":
                    self.client.create_table(data, avatar=self.avatar_index)
                    self.ui.set_status("Creating table…")
                elif action == "refresh":
                    self.client.get_tables()
                elif action == "avatar":
                    self.avatar_index = data
                elif action == "logout":
                    self._go_login()

            case AppState.GAME:
                if action in ("fold", "check", "call", "raise", "all-in"):
                    self.client.action(action, data)
                elif action == "start":
                    self.client.start_table()
                elif action == "leave":
                    self._go_lobby()

    def _poll_server(self) -> None:
        if self.client is None:
            return
        try:
            messages = self.client.poll()
        except ConnectionError:
            self._handle_disconnect()
            return

        for msg in messages:
            import logging

            logging.debug(
                f"[poll] state={self.state} msg_type={msg.get('type')} keys={list(msg.keys())}"
            )
            self._handle_server_message(msg)

    def _set_status(self, msg: str) -> None:
        if self.state == AppState.GAME:
            if hasattr(self.ui, "top") and hasattr(self.ui.top, "set_status"):
                self.ui.top.set_status(msg)
        elif hasattr(self.ui, "set_status"):
            self.ui.set_status(msg)

    def _handle_server_message(self, msg: dict) -> None:
        t = msg.get("type")

        match t:
            case MessageType.CREATE_ACCOUNT_RESPONSE:
                if msg.get("success"):
                    self._set_status("Account created! You can log in now.")
                else:
                    self._set_status(f"Error: {msg.get('error', 'unknown')}")

            case MessageType.LOGIN_RESPONSE:
                if msg.get("success"):
                    self.player_id = msg["player_id"]
                    self.player_name = msg["player_name"]
                    self._go_lobby()
                else:
                    self._set_status(f"Login failed: {msg.get('error', 'unknown')}")

            case MessageType.GET_TABLES_RESPONSE:
                if self.state == AppState.LOBBY:
                    tables = [
                        TableInfo.from_server_dict(d) for d in msg.get("tables", [])
                    ]
                    self.ui.set_tables(tables)
                    self._set_status(
                        f"{len(tables)} table(s) available"
                        if tables
                        else "No tables - create one!"
                    )

            case MessageType.CREATE_TABLE_RESPONSE:
                if msg.get("success"):
                    self._go_game()
                else:
                    self._set_status(f"Error: {msg.get('error', 'unknown')}")

            case MessageType.JOIN_TABLE_RESPONSE:
                if msg.get("success"):
                    self._go_game()
                else:
                    self._set_status(f"Error: {msg.get('error', 'unknown')}")

            case MessageType.STATE:
                if self.state == AppState.GAME:
                    try:
                        game_state = GameStateData.from_dict(msg)
                        self.ui.update(game_state, self.player_id, dt_ms=0)
                    except Exception:
                        import logging, traceback

                        logging.warning(
                            f"Failed to deserialize game state:\n{traceback.format_exc()}"
                        )

            case MessageType.GAME_START:
                self._set_status("Game started!")

            case MessageType.HAND_END:
                winners = msg.get("winners", [])
                if self.state == AppState.GAME and hasattr(self.ui, "show_showdown"):
                    self.ui.show_showdown(winners)
                else:
                    names = ", ".join(w.get("name", "?") for w in winners)
                    self._set_status(f"Hand over - winner(s): {names}")

            case MessageType.PLAYER_JOINED:
                name = msg.get("player", {}).get("name", "?")
                self._set_status(f"{name} joined the table")

            case MessageType.ACTION_RESPONSE:
                if not msg.get("success"):
                    self._set_status(f"Invalid action: {msg.get('error', '')}")

            case MessageType.ERROR:
                self._set_status(f"Server error: {msg.get('message', 'Unknown error')}")

    def _do_connect(self, addr: str) -> None:
        if ":" in addr:
            ip, port_str = addr.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                self.ui.set_status("Invalid port number")
                return
        else:
            ip, port = addr, 7777

        try:
            self.client = Client(ip, port)
            self.ui.set_status(f"Connected to {ip}:{port}")
            self._go_login()
        except OSError as e:
            self.ui.set_status(f"Connection failed: {e}")

    def _go_login(self) -> None:
        self.state = AppState.LOGIN
        self.ui = LoginScreen()

    def _go_lobby(self) -> None:
        self.state = AppState.LOBBY
        self.ui = LobbyScreen()
        self.client.get_tables()

    def _go_game(self) -> None:
        self.state = AppState.GAME
        top = TopScreen()
        bottom = GameBottomScreen(self.player_id)
        self.ui = GameScreenManager(top, bottom)

    def _handle_disconnect(self) -> None:
        self.client = None
        self.state = AppState.CONNECTING
        self.ui = ConnectionScreen()
        self.ui.set_status("Disconnected from server")

    def _update(self, dt: float) -> None:
        if self.state == AppState.GAME:
            if hasattr(self.ui, "top") and hasattr(self.ui.top, "tick"):
                self.ui.top.tick(dt)
        elif hasattr(self.ui, "update"):
            self.ui.update(dt)

    def _draw(self) -> None:
        self.ui.draw(self.screen)
        pygame.display.flip()


def main() -> None:
    import logging

    logging.basicConfig(
        level=logging.DEBUG, format="[%(asctime)s] %(levelname)s: %(message)s"
    )
    app = App()

    match len(sys.argv):
        case 2:
            app._do_connect(sys.argv[1])
        case 3:
            app._do_connect(f"{sys.argv[1]}:{sys.argv[2]}")
        case x if x > 3:
            print(f"usage: {sys.argv[0]} [HOST [PORT]]", file=sys.stderr)
            sys.exit(1)

    app.run()


if __name__ == "__main__":
    main()
