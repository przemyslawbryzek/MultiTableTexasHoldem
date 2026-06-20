from pathlib import Path
from typing import NamedTuple
import pygame
from client.ui.assets.avatars.avatar_sheet import AvatarSheet, AvatarSheetCache, AvatarSprite, AvatarView

_ASSETS     = Path(__file__).parent.parent / "assets"
BG_PATH     = _ASSETS / "sprites" / "bg.png"
FONT_PATH   = _ASSETS / "fonts"   / "pixelboy.ttf"
BUTTON_PATH = _ASSETS / "sprites" / "button.png"

WHITE    = (255, 255, 255)
GOLD     = (255, 215,   0)
RED      = (220,  60,  60)
GREEN    = ( 60, 210,  80)
DIM      = (160, 160, 170)
BG_COLOR = ( 30,  30,  50)
PANEL    = ( 25,  25,  40)
PANEL_HI = ( 55,  55,  80)
BORDER   = ( 80,  80, 110)
BORDER_SEL = (180, 150,  60)


SCREEN_W, SCREEN_H = 800, 600
CENTER_X = SCREEN_W // 2

TABLES_X      = 20
TABLES_Y      = 50
TABLES_W      = SCREEN_W - 40
TABLES_H      = 220
TABLE_ROW_H   = 36
TABLE_COLS    = [10, 80, 230, 340, 430]

BOTTOM_Y      = TABLES_Y + TABLES_H + 20
BOTTOM_H      = SCREEN_H - BOTTOM_Y - 70

AVATAR_X      = 20
AVATAR_W      = 260
AVATAR_H      = BOTTOM_H

CREATE_X      = AVATAR_X + AVATAR_W + 20
CREATE_W      = SCREEN_W - CREATE_X - 20
CREATE_H      = BOTTOM_H

AVATAR_THUMB  = 80
AVATAR_SCALE  = AVATAR_THUMB / 186.0
AVATAR_COUNT  = 2

BTN_W, BTN_H  = 200, 50

class TableInfo(NamedTuple):
    table_id:    int
    owner:       str
    players:     int
    max_players: int
    big_blind:   int
    status:      str

    @staticmethod
    def from_server_dict(d: dict) -> "TableInfo":
        return TableInfo(
            table_id=d["table_id"],
            owner=d.get("owner", "?"),
            players=d.get("num_players", 0),
            max_players=d.get("max_players", 6),
            big_blind=d.get("big_blind", 0),
            status=d.get("game_state", "WAITING"),
        )

Action = tuple[str, object] | None


class LobbyScreen:
    CURSOR_BLINK_MS = 1000
    CURSOR_WIDTH    = 2

    def __init__(self) -> None:
        self.tables:          list[TableInfo] = []
        self.selected_table:  int | None      = None
        self.avatar_index:    int             = 1
        self.status:          str             = "Welcome to the lobby"
        self.big_blind_str:   str             = "20"
        self.focus_bb:        bool            = False

        self._cursor_timer:   float = 0.0
        self._table_scroll:   int   = 0
        self._visible_rows:   int   = max(1, (TABLES_H - TABLE_ROW_H) // TABLE_ROW_H)

        self._table_rows:     list[tuple[pygame.Rect, int]] = []

        self._panel_tables  = pygame.Rect(TABLES_X, TABLES_Y, TABLES_W, TABLES_H)
        self._panel_avatar  = pygame.Rect(AVATAR_X, BOTTOM_Y, AVATAR_W, AVATAR_H)
        self._panel_create  = pygame.Rect(CREATE_X, BOTTOM_Y, CREATE_W, CREATE_H)

        self._bb_rect = pygame.Rect(
            CREATE_X + 10, BOTTOM_Y + 60, CREATE_W - 20, 25
        )
        self._create_btn = pygame.Rect(
            CREATE_X + (CREATE_W - BTN_W) // 2, BOTTOM_Y + 110, BTN_W, BTN_H
        )
        self._refresh_btn = pygame.Rect(
            TABLES_X + TABLES_W - BTN_W - 8, TABLES_Y - 40, BTN_W, BTN_H - 6
        )
        self._join_btn = pygame.Rect(
            TABLES_X + 8, TABLES_Y - 40, BTN_W, BTN_H - 6
        )
        self._logout_btn = pygame.Rect(
            CREATE_X + (CREATE_W - BTN_W) // 2, BOTTOM_Y + BOTTOM_H - BTN_H - 10,
            BTN_W, BTN_H
        )
        _arr_y  = BOTTOM_Y + AVATAR_H - 40
        _arr_cx = AVATAR_X + AVATAR_W // 2
        self._prev_btn = pygame.Rect(_arr_cx - 70, _arr_y, 40, 28)
        self._next_btn = pygame.Rect(_arr_cx + 30, _arr_y, 40, 28)

        self._load_fonts()
        self._load_textures()
        self._load_avatars()

    def _load_fonts(self) -> None:
        font_file = str(FONT_PATH) if FONT_PATH.exists() else None
        self.font       = pygame.font.Font(font_file, 22)
        self.small_font = pygame.font.Font(font_file, 18)
        self.tiny_font  = pygame.font.Font(font_file, 14)

    def _load_textures(self) -> None:
        if BG_PATH.exists():
            raw = pygame.image.load(str(BG_PATH)).convert()
            self.bg: pygame.Surface | None = pygame.transform.scale(raw, (SCREEN_W, SCREEN_H))
        else:
            self.bg = None

        self._btn_tex:   pygame.Surface | None = None
        self._btn_cache: dict[tuple[int, int], pygame.Surface] = {}
        if BUTTON_PATH.exists():
            try:
                self._btn_tex = pygame.image.load(str(BUTTON_PATH)).convert_alpha()
            except pygame.error:
                pass

    def _load_avatars(self) -> None:
        self._cache = AvatarSheetCache()
        self._sprites: dict[int, AvatarSprite] = {}
        for i in range(1, AVATAR_COUNT + 1):
            try:
                sheet = self._cache.get(i)
                self._sprites[i] = AvatarSprite(sheet, view=AvatarView.FRONT)
            except Exception:
                self._sprites[i] = None

    def set_tables(self, tables: list[TableInfo]) -> None:
        self.tables = tables
        self._table_scroll = 0
        self.selected_table = None

    def set_status(self, msg: str) -> None:
        self.status = msg

    def update(self, dt_ms: float) -> None:
        self._cursor_timer = (self._cursor_timer + dt_ms) % self.CURSOR_BLINK_MS
        for sprite in self._sprites.values():
            if sprite:
                sprite.update(dt_ms)

    def draw(self, surface: pygame.Surface) -> None:
        if self.bg:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill(BG_COLOR)

        self._draw_status(surface)
        self._draw_tables_panel(surface)
        self._draw_avatar_panel(surface)
        self._draw_create_panel(surface)

    def _draw_status(self, surface: pygame.Surface) -> None:
        if any(k in self.status.lower() for k in ("error", "fail")):
            color = RED
        elif any(k in self.status.lower() for k in ("created", "joined", "success")):
            color = GREEN
        else:
            color = GOLD
        surf = self.small_font.render(self.status, True, color)
        surface.blit(surf, surf.get_rect(center=(CENTER_X, 22)))

    def _draw_tables_panel(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, PANEL, self._panel_tables, border_radius=6)
        pygame.draw.rect(surface, BORDER, self._panel_tables, 1, border_radius=6)

        hdr_y = TABLES_Y + 8
        for text, x_off in zip(
            ["ID", "Owner", "Players", "Blind", "Status"],
            TABLE_COLS,
        ):
            s = self.tiny_font.render(text, True, DIM)
            surface.blit(s, (TABLES_X + x_off + 4, hdr_y))

        sep_y = TABLES_Y + TABLE_ROW_H - 2
        pygame.draw.line(surface, BORDER,
                         (TABLES_X + 4, sep_y),
                         (TABLES_X + TABLES_W - 4, sep_y))

        self._table_rows = []
        visible = self.tables[self._table_scroll: self._table_scroll + self._visible_rows]
        for row_i, t in enumerate(visible):
            ry = TABLES_Y + TABLE_ROW_H + row_i * TABLE_ROW_H
            rect = pygame.Rect(TABLES_X + 4, ry, TABLES_W - 8, TABLE_ROW_H - 2)

            bg = PANEL_HI if self.selected_table == t.table_id else PANEL
            pygame.draw.rect(surface, bg, rect, border_radius=4)
            if self.selected_table == t.table_id:
                pygame.draw.rect(surface, BORDER_SEL, rect, 1, border_radius=4)

            cells = [
                str(t.table_id),
                t.owner,
                f"{t.players}/{t.max_players}",
                str(t.big_blind),
                t.status,
            ]
            status_colors = {"waiting": GREEN, "in_progress": GOLD}
            for col_i, (cell, x_off) in enumerate(zip(cells, TABLE_COLS)):
                color = status_colors.get(cell, WHITE) if col_i == 4 else WHITE
                cs = self.tiny_font.render(cell, True, color)
                surface.blit(cs, (TABLES_X + x_off + 8, ry + (TABLE_ROW_H - cs.get_height()) // 2))

            self._table_rows.append((rect, t.table_id))

        if not self.tables:
            msg = self.tiny_font.render("No tables found — create one!", True, DIM)
            surface.blit(msg, msg.get_rect(center=(CENTER_X, TABLES_Y + TABLES_H // 2)))

        if len(self.tables) > self._visible_rows:
            total = len(self.tables)
            bar_h = max(20, int(TABLES_H * self._visible_rows / total))
            bar_y = int(TABLES_Y + (TABLES_H - bar_h) * self._table_scroll / (total - self._visible_rows))
            bar_x = TABLES_X + TABLES_W - 8
            pygame.draw.rect(surface, BORDER, pygame.Rect(bar_x, bar_y, 4, bar_h), border_radius=2)

        self._draw_button(surface, self._join_btn, "Join",
                          enabled=self.selected_table is not None)
        self._draw_button(surface, self._refresh_btn, "Refresh")

    def _draw_avatar_panel(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, PANEL, self._panel_avatar, border_radius=6)
        pygame.draw.rect(surface, BORDER, self._panel_avatar, 1, border_radius=6)

        label = self.small_font.render("Choose Avatar", True, GOLD)
        surface.blit(label, label.get_rect(
            centerx=AVATAR_X + AVATAR_W // 2,
            top=BOTTOM_Y + 10,
        ))

        total_w   = AVATAR_COUNT * AVATAR_THUMB + (AVATAR_COUNT - 1) * 16
        start_x   = AVATAR_X + (AVATAR_W - total_w) // 2
        thumb_y   = BOTTOM_Y + 46

        for i in range(1, AVATAR_COUNT + 1):
            tx = start_x + (i - 1) * (AVATAR_THUMB + 16)
            selected = self.avatar_index == i

            box = pygame.Rect(tx - 4, thumb_y - 4, AVATAR_THUMB + 8, AVATAR_THUMB + 8)
            border_color = BORDER_SEL if selected else BORDER
            pygame.draw.rect(surface, PANEL_HI if selected else PANEL, box, border_radius=4)
            pygame.draw.rect(surface, border_color, box, 2, border_radius=4)

            sprite = self._sprites.get(i)
            if sprite:
                sprite.draw(surface, tx + AVATAR_THUMB // 2, thumb_y + AVATAR_THUMB // 2,
                            scale=AVATAR_SCALE, center=True)
            else:
                pygame.draw.rect(surface, PANEL_HI, pygame.Rect(tx, thumb_y, AVATAR_THUMB, AVATAR_THUMB))
                fb = self.font.render(str(i), True, DIM)
                surface.blit(fb, fb.get_rect(center=(tx + AVATAR_THUMB // 2, thumb_y + AVATAR_THUMB // 2)))

            name_surf = self.tiny_font.render(f"Avatar {i}", True, GOLD if selected else DIM)
            surface.blit(name_surf, name_surf.get_rect(
                centerx=tx + AVATAR_THUMB // 2,
                top=thumb_y + AVATAR_THUMB + 6,
            ))

        self._draw_button(surface, self._prev_btn, "<")
        self._draw_button(surface, self._next_btn, ">")

        sel_text = self.tiny_font.render(
            f"Selected: Avatar {self.avatar_index}", True, WHITE
        )
        surface.blit(sel_text, sel_text.get_rect(
            centerx=AVATAR_X + AVATAR_W // 2,
            top=self._prev_btn.bottom + 6,
        ))

    def _draw_create_panel(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, PANEL, self._panel_create, border_radius=6)
        pygame.draw.rect(surface, BORDER, self._panel_create, 1, border_radius=6)

        label = self.small_font.render("Create Table", True, GOLD)
        surface.blit(label, label.get_rect(
            centerx=CREATE_X + CREATE_W // 2,
            top=BOTTOM_Y + 10,
        ))

        bb_label = self.tiny_font.render("Big Blind", True, DIM)
        surface.blit(bb_label, (self._bb_rect.x, self._bb_rect.y - 18))

        border_color = WHITE if self.focus_bb else BORDER
        pygame.draw.rect(surface, border_color, self._bb_rect, 2)
        bb_surf = self.small_font.render(self.big_blind_str, True, WHITE)
        surface.blit(bb_surf, (self._bb_rect.x + 6, self._bb_rect.y + 4))

        if self.focus_bb and self._cursor_timer < self.CURSOR_BLINK_MS // 2:
            cx = self._bb_rect.x + 6 + self.small_font.size(self.big_blind_str)[0]
            cy = self._bb_rect.y + 4
            ch = self._bb_rect.h - 8
            pygame.draw.line(surface, WHITE, (cx, cy), (cx, cy + ch), self.CURSOR_WIDTH)

        self._draw_button(surface, self._create_btn, "Create")
        self._draw_button(surface, self._logout_btn, "Logout")

    def _get_scaled_button(self, w: int, h: int) -> pygame.Surface | None:
        key = (w, h)
        if key not in self._btn_cache and self._btn_tex:
            self._btn_cache[key] = pygame.transform.smoothscale(self._btn_tex, key)
        return self._btn_cache.get(key)

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
            color = (70, 70, 90) if enabled else (50, 50, 55)
            pygame.draw.rect(surface, color, rect, border_radius=4)

        text_color = WHITE if enabled else (120, 120, 120)
        ts = self.small_font.render(text, True, text_color)
        tr = ts.get_rect(center=rect.center)
        tr.centery -= 2
        surface.blit(ts, tr)

    def handle_event(self, event: pygame.event.Event) -> Action:
        if event.type == pygame.KEYDOWN:
            return self._handle_key(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos)
        if event.type == pygame.MOUSEWHEEL:
            self._scroll(event.y)
        return None

    def _handle_key(self, event: pygame.event.Event) -> Action:
        if not self.focus_bb:
            return None
        if event.key == pygame.K_BACKSPACE:
            self.big_blind_str = self.big_blind_str[:-1]
        elif event.key == pygame.K_RETURN:
            return self._try_create()
        elif event.unicode.isdigit():
            self.big_blind_str += event.unicode
        return None

    def _handle_click(self, pos: tuple[int, int]) -> Action:
        for rect, tid in self._table_rows:
            if rect.collidepoint(pos):
                self.selected_table = tid
                self.status = f"Selected table {tid}"
                return ("select_table", tid)

        if self._join_btn.collidepoint(pos):
            if self.selected_table is not None:
                return ("join", self.selected_table)
            self.status = "Select a table first"
            return None

        if self._refresh_btn.collidepoint(pos):
            self.status = "Refreshing..."
            return ("refresh", None)

        if self._bb_rect.collidepoint(pos):
            self.focus_bb = True
            return ("switch_focus", None)
        else:
            self.focus_bb = False

        if self._create_btn.collidepoint(pos):
            return self._try_create()

        if self._logout_btn.collidepoint(pos):
            return ("logout", None)

        total_w = AVATAR_COUNT * AVATAR_THUMB + (AVATAR_COUNT - 1) * 16
        start_x = AVATAR_X + (AVATAR_W - total_w) // 2
        thumb_y = BOTTOM_Y + 46
        for i in range(1, AVATAR_COUNT + 1):
            tx = start_x + (i - 1) * (AVATAR_THUMB + 16)
            thumb_rect = pygame.Rect(tx - 4, thumb_y - 4, AVATAR_THUMB + 8, AVATAR_THUMB + 8)
            if thumb_rect.collidepoint(pos):
                return self._select_avatar(i)

        if self._prev_btn.collidepoint(pos):
            return self._select_avatar(((self.avatar_index - 2) % AVATAR_COUNT) + 1)
        if self._next_btn.collidepoint(pos):
            return self._select_avatar((self.avatar_index % AVATAR_COUNT) + 1)

        return None

    def _select_avatar(self, index: int) -> Action:
        self.avatar_index = index
        self.status = f"Avatar {index} selected"
        return ("avatar", index)

    def _try_create(self) -> Action:
        try:
            bb = int(self.big_blind_str)
            if bb <= 0:
                raise ValueError
        except ValueError:
            self.status = "Big blind must be a positive number"
            return None
        return ("create", bb)

    def _scroll(self, direction: int) -> None:
        max_scroll = max(0, len(self.tables) - self._visible_rows)
        self._table_scroll = max(0, min(self._table_scroll - direction, max_scroll))