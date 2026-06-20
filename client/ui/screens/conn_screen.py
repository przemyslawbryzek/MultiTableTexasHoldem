import socket
from pathlib import Path
import pygame
from shared.discovery import join_membership, probe_request_nb

_ASSETS = Path(__file__).parent.parent / "assets"
BG_PATH     = _ASSETS / "sprites" / "bg.png"
FONT_PATH   = _ASSETS / "fonts"   / "pixelboy.ttf"
BUTTON_PATH = _ASSETS / "sprites" / "button.png"

WHITE     = (255, 255, 255)
GOLD      = (255, 215,   0)
RED       = (220,  60,  60)
GREEN     = ( 60, 210,  80)
DIM       = (160, 160, 170)
BG_COLOR  = ( 30,  30,  50)
PANEL_LO  = ( 40,  40,  50)
PANEL_HI  = ( 70,  70,  90)
BORDER    = (100, 100, 120)
GREY_BTN  = ( 50,  50,  55)
GREY_TEXT = (120, 120, 120)

Action = tuple[str, str | None] | None


class ConnectionScreen:
    SCREEN_W, SCREEN_H = 800, 600
    CENTER_X = SCREEN_W // 2

    FIELD_W, FIELD_H = 240, 25
    FIELD_PADDING = 5

    BUTTON_W, BUTTON_H = 260, 70

    TITLE_Y       = 40
    STATUS_Y      = 110
    SERVER_LIST_Y = 140
    SERVER_H      = 30
    SERVER_GAP    = 40
    CUSTOM_Y      = 420
    CONNECT_BTN_Y = 450
    REFRESH_BTN_Y = 480

    CURSOR_BLINK_MS = 1000
    CURSOR_WIDTH    = 2

    PROBE_INTERVAL_MS = 3_000

    def __init__(self, discovery_socket: socket.socket | None = None) -> None:
        self.servers: list[str] = []
        self.selected_server: str | None = None
        self.custom_address: str = ""
        self.focus_custom: bool = False
        self.status: str = "Looking for servers..."

        self._cursor_timer_ms: float = 0.0
        self._probe_timer_ms:  float = 0.0

        self.discovery_sock: socket.socket | None = discovery_socket
        if self.discovery_sock is None:
            self._init_discovery_socket()

        self._server_rects: list[tuple[pygame.Rect, str]] = []
        self.custom_rect = pygame.Rect(
            self.CENTER_X - self.FIELD_W // 2, self.CUSTOM_Y,
            self.FIELD_W, self.FIELD_H,
        )
        self.connect_btn_rect = pygame.Rect(
            self.CENTER_X - self.BUTTON_W // 2, self.CONNECT_BTN_Y,
            self.BUTTON_W, self.BUTTON_H,
        )
        self.discover_btn_rect = pygame.Rect(
            self.CENTER_X - self.BUTTON_W // 2, self.REFRESH_BTN_Y,
            self.BUTTON_W, self.BUTTON_H,
        )

        self._load_fonts()
        self._load_textures()

    def _init_discovery_socket(self) -> None:
        try:
            self.discovery_sock = join_membership(blocking=False)
            self.discovery_sock.setblocking(False)
            probe_request_nb(self.discovery_sock)
        except Exception as exc:
            self.status = f"Discovery error: {exc}"
            self.discovery_sock = None

    def _load_fonts(self) -> None:
        font_file = str(FONT_PATH) if FONT_PATH.exists() else None
        self.font       = pygame.font.Font(font_file, 22)
        self.small_font = pygame.font.Font(font_file, 18)
        self.tiny_font  = pygame.font.Font(font_file, 14)

    def _load_textures(self) -> None:
        if BG_PATH.exists():
            raw = pygame.image.load(str(BG_PATH)).convert()
            self.bg: pygame.Surface | None = pygame.transform.scale(
                raw, (self.SCREEN_W, self.SCREEN_H)
            )
        else:
            self.bg = None

        self._button_texture: pygame.Surface | None = None
        self._button_cache:   dict[tuple[int, int], pygame.Surface] = {}
        if BUTTON_PATH.exists():
            try:
                self._button_texture = pygame.image.load(str(BUTTON_PATH)).convert_alpha()
            except pygame.error:
                pass

    def _get_scaled_button(self, w: int, h: int) -> pygame.Surface | None:
        key = (w, h)
        if key not in self._button_cache and self._button_texture:
            self._button_cache[key] = pygame.transform.smoothscale(
                self._button_texture, key
            )
        return self._button_cache.get(key)

    def _drain_discovery_socket(self) -> None:
        if not self.discovery_sock:
            return
        try:
            while True:
                data, (ip, _port) = self.discovery_sock.recvfrom(16)
                if data == b"pong" and ip not in self.servers:
                    self.servers.append(ip)
                    self.status = f"Found {len(self.servers)} server(s)"
        except BlockingIOError:
            pass
        except OSError:
            pass

    def _send_probe(self) -> None:
        if self.discovery_sock:
            try:
                probe_request_nb(self.discovery_sock)
            except OSError:
                pass

    def set_status(self, msg: str) -> None:
        self.status = msg

    def add_server(self, ip: str) -> None:
        if ip not in self.servers:
            self.servers.append(ip)
            self.status = f"Found {len(self.servers)} server(s)"

    def update(self, dt_ms: float) -> None:
        self._cursor_timer_ms = (self._cursor_timer_ms + dt_ms) % self.CURSOR_BLINK_MS

        self._probe_timer_ms += dt_ms
        if self._probe_timer_ms >= self.PROBE_INTERVAL_MS:
            self._probe_timer_ms = 0.0
            self._send_probe()

        self._drain_discovery_socket()

    def draw(self, surface: pygame.Surface) -> None:
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(BG_COLOR)

        title_surf = self.small_font.render("Connect to Server", True, GOLD)
        surface.blit(title_surf, title_surf.get_rect(center=(self.CENTER_X, self.TITLE_Y)))

        if any(k in self.status.lower() for k in ("error", "fail")):
            status_color = RED
        elif any(k in self.status.lower() for k in ("found", "connected")):
            status_color = GREEN
        else:
            status_color = WHITE
        status_surf = self.small_font.render(self.status, True, status_color)
        surface.blit(status_surf, status_surf.get_rect(center=(self.CENTER_X, self.STATUS_Y)))

        self._server_rects = []
        y = self.SERVER_LIST_Y

        if not self.servers:
            empty = self.tiny_font.render("(no servers found)", True, DIM)
            surface.blit(empty, empty.get_rect(center=(self.CENTER_X, y + 20)))
        else:
            for ip in self.servers:
                rect = pygame.Rect(self.CENTER_X - 150, y, 300, self.SERVER_H)
                bg_color = PANEL_HI if self.selected_server == ip else PANEL_LO
                pygame.draw.rect(surface, bg_color,  rect, border_radius=4)
                pygame.draw.rect(surface, BORDER,    rect, 1, border_radius=4)

                label = self.small_font.render(f"{ip}:7777", True, WHITE)
                surface.blit(label, label.get_rect(center=rect.center))

                self._server_rects.append((rect, ip))
                y += self.SERVER_GAP

        hint = self.tiny_font.render("Or enter custom address", True, DIM)
        surface.blit(hint, (self.custom_rect.x, self.custom_rect.y - 20))

        pygame.draw.rect(surface, WHITE, self.custom_rect, 2)
        addr_surf = self.small_font.render(self.custom_address, True, WHITE)
        surface.blit(addr_surf, (self.custom_rect.x + self.FIELD_PADDING,
                                  self.custom_rect.y + self.FIELD_PADDING))

        cursor_visible = self.focus_custom and (
            self._cursor_timer_ms < self.CURSOR_BLINK_MS // 2
        )
        if cursor_visible:
            cx = (self.custom_rect.x + self.FIELD_PADDING
                  + self.small_font.size(self.custom_address)[0])
            cy = self.custom_rect.y + self.FIELD_PADDING
            ch = self.FIELD_H - 2 * self.FIELD_PADDING
            pygame.draw.line(surface, WHITE, (cx, cy), (cx, cy + ch), self.CURSOR_WIDTH)

        self._draw_button(surface, self.connect_btn_rect,  "Connect")
        self._draw_button(surface, self.discover_btn_rect, "Refresh Servers")

    def _draw_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        text: str,
        enabled: bool = True,
    ) -> None:
        scaled = self._get_scaled_button(rect.w, rect.h)

        if scaled:
            if enabled:
                surface.blit(scaled, rect.topleft)
            else:
                grey = scaled.copy()
                grey.fill((80, 80, 80, 255), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(grey, rect.topleft)
        else:
            color = (70, 70, 90) if enabled else GREY_BTN
            pygame.draw.rect(surface, color, rect, border_radius=4)

        text_color = WHITE if enabled else GREY_TEXT
        text_surf  = self.small_font.render(text, True, text_color)
        text_rect  = text_surf.get_rect(center=rect.center)
        text_rect.centery -= 2
        surface.blit(text_surf, text_rect)

    def handle_event(self, event: pygame.event.Event) -> Action:
        if event.type == pygame.KEYDOWN and self.focus_custom:
            return self._handle_key(event)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)

        return None

    def _handle_key(self, event: pygame.event.Event) -> Action:
        if event.key == pygame.K_BACKSPACE:
            self.custom_address = self.custom_address[:-1]
        elif event.key == pygame.K_RETURN and self.custom_address:
            self.selected_server = self.custom_address
            return ("connect", self.custom_address)
        else:
            self.custom_address += event.unicode
        return None

    def _handle_click(self, pos: tuple[int, int]) -> Action:
        for rect, ip in self._server_rects:
            if rect.collidepoint(pos):
                self.selected_server = ip
                self.status = f"Selected {ip}"
                return ("select", ip)

        if self.custom_rect.collidepoint(pos):
            self.focus_custom = True
            return ("switch_focus", None)
        self.focus_custom = False

        if self.connect_btn_rect.collidepoint(pos):
            target = self.selected_server or self.custom_address
            if target:
                return ("connect", target)
            self.status = "No server selected"
            return None

        if self.discover_btn_rect.collidepoint(pos):
            self.servers = []
            self.selected_server = None
            self.status = "Scanning..."
            self._send_probe()
            return ("refresh", None)

        return None