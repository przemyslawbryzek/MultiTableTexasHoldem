from pathlib import Path
from shared.datatypes import Card
from client.ui.assets.cards.card_sheet import CardSheet
import pygame

FONT_PATH   = Path(__file__).parent.parent.parent / "assets" / "fonts" / "pixelboy.ttf"
BUTTON_PATH = Path(__file__).parent.parent.parent / "assets" / "sprites" / "button.png"

GOLD        = (255, 215,   0)
WHITE       = (255, 255, 255)
BLACK       = (  0,   0,   0)
GREEN       = ( 60, 210,  80)
DIM         = (160, 160, 170)
RED         = (220, 60, 60)
OVERLAY_BG  = (  0,   0,   0, 180)

SCREEN_W    = 800
SCREEN_H    = 600
PANEL_W     = 680
PANEL_H     = 380
PANEL_X     = (SCREEN_W - PANEL_W) // 2
PANEL_Y     = (SCREEN_H - PANEL_H) // 2

CARD_SCALE  = 1.2
CARD_GAP    = 8
DISMISS_MS  = 8_000

class ShowdownScreen:
    def __init__(self) -> None:
        self._card_sheet = CardSheet()
        self._btn_tex:   pygame.Surface | None = None
        self._btn_cache: dict[tuple[int, int], pygame.Surface] = {}

        font_file = str(FONT_PATH) if FONT_PATH.exists() else None
        self.font       = pygame.font.Font(font_file, 24)
        self.small_font = pygame.font.Font(font_file, 18)
        self.tiny_font  = pygame.font.Font(font_file, 14)

        if BUTTON_PATH.exists():
            try:
                self._btn_tex = pygame.image.load(str(BUTTON_PATH)).convert_alpha()
            except pygame.error:
                pass

        self._winners:    list[dict] = []
        self._timer_ms:   float      = 0.0
        self._active:     bool       = False
        self._dismiss_btn = pygame.Rect(
            PANEL_X + (PANEL_W - 180) // 2,
            PANEL_Y + PANEL_H - 52,
            180, 36,
        )
    @property
    def active(self) -> bool:
        return self._active

    def show(self, winners: list[dict]) -> None:
        self._winners  = winners
        self._timer_ms = DISMISS_MS
        self._active   = True

    def dismiss(self) -> None:
        self._active  = False
        self._winners = []

    def update(self, dt_ms: float) -> None:
        if not self._active:
            return
        self._timer_ms -= dt_ms
        if self._timer_ms <= 0:
            self.dismiss()

    def draw(self, surface: pygame.Surface) -> None:
        if not self._active:
            return

        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill(OVERLAY_BG)
        surface.blit(overlay, (0, 0))

        panel = pygame.Surface((PANEL_W, PANEL_H), pygame.SRCALPHA)
        panel.fill((20, 20, 35, 245))
        surface.blit(panel, (PANEL_X, PANEL_Y))
        pygame.draw.rect(surface, GOLD,
                         pygame.Rect(PANEL_X, PANEL_Y, PANEL_W, PANEL_H),
                         2, border_radius=8)

        title = "SHOWDOWN" if len(self._winners) > 1 else "WINNER!"
        title_surf = self.font.render(title, True, GOLD)
        surface.blit(title_surf, title_surf.get_rect(
            centerx=SCREEN_W // 2, top=PANEL_Y + 14
        ))

        n = len(self._winners)
        if n == 0:
            return

        cw, ch = self._card_sheet.get_card_size(CARD_SCALE)

        cards_per_player = max(len(w.get("hand", [])) for w in self._winners) or 2
        player_block_w   = cards_per_player * (cw + CARD_GAP) - CARD_GAP + 20
        total_w          = n * player_block_w + (n - 1) * 30
        start_x          = SCREEN_W // 2 - total_w // 2
        block_y          = PANEL_Y + 60

        for i, winner in enumerate(self._winners):
            bx = start_x + i * (player_block_w + 30)
            name_surf = self.small_font.render(
                winner.get("name", "?"), True, GOLD
            )
            surface.blit(name_surf, name_surf.get_rect(
                centerx=bx + player_block_w // 2,
                top=block_y,
            ))

            hand = winner.get("hand", [])
            card_y = block_y + name_surf.get_height() + 10
            for j, card_str in enumerate(hand):
                card_x = bx + j * (cw + CARD_GAP)
                try:
                    card = Card.str_to_card(card_str)
                    surf = self._card_sheet.get_card(card.rank, card.suit, CARD_SCALE)
                    surface.blit(surf, (card_x, card_y))
                except Exception:
                    fb_rect = pygame.Rect(card_x, card_y, cw, ch)
                    pygame.draw.rect(surface, (60, 60, 70), fb_rect, border_radius=4)
                    fb = self.tiny_font.render(card_str, True, WHITE)
                    surface.blit(fb, fb.get_rect(center=fb_rect.center))

            chips = winner.get("chips", 0)
            chips_surf = self.tiny_font.render(f"${chips}", True, GREEN)
            surface.blit(chips_surf, chips_surf.get_rect(
                centerx=bx + player_block_w // 2,
                top=card_y + ch + 8,
            ))

        frac   = max(0.0, self._timer_ms / DISMISS_MS)
        bar_w  = int((PANEL_W - 40) * frac)
        bar_y  = PANEL_Y + PANEL_H - 66
        pygame.draw.rect(surface, (50, 50, 60),
                         pygame.Rect(PANEL_X + 20, bar_y, PANEL_W - 40, 4),
                         border_radius=2)
        if bar_w > 0:
            color = GOLD if frac > 0.3 else RED if frac > 0.1 else (200, 60, 60)
            pygame.draw.rect(surface, color,
                             pygame.Rect(PANEL_X + 20, bar_y, bar_w, 4),
                             border_radius=2)

        self._draw_button(surface, self._dismiss_btn, "Continue")

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self._active:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._dismiss_btn.collidepoint(event.pos):
                self.dismiss()
            else:
                self.dismiss()
            return True
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
            self.dismiss()
            return True
        return True

    def _get_scaled_btn(self, w: int, h: int) -> pygame.Surface | None:
        key = (w, h)
        if key not in self._btn_cache and self._btn_tex:
            self._btn_cache[key] = pygame.transform.smoothscale(self._btn_tex, key)
        return self._btn_cache.get(key)

    def _draw_button(self, surface: pygame.Surface, rect: pygame.Rect, text: str) -> None:
        scaled = self._get_scaled_btn(rect.w, rect.h)
        if scaled:
            surface.blit(scaled, rect.topleft)
        else:
            pygame.draw.rect(surface, (70, 70, 90), rect, border_radius=4)
        ts = self.small_font.render(text, True, WHITE)
        tr = ts.get_rect(center=rect.center)
        tr.centery -= 2
        surface.blit(ts, tr)