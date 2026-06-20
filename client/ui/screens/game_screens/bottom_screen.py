import pygame
import logging
from pathlib import Path
from shared.game_state import GameState, GamePhase
from shared.datatypes import Card
from shared.enums import ActionType
from client.ui.assets.cards.card_sheet import CardSheet
from client.ui.assets.chips.chip_sheet import ChipSheet

BG_PATH     = Path(__file__).parent.parent.parent / "assets" / "sprites" / "bottom_bg.png"
BUTTON_PATH = Path(__file__).parent.parent.parent / "assets" / "sprites" / "button.png"
FONT_PATH   = Path(__file__).parent.parent.parent / "assets" / "fonts" / "pixelboy.ttf"

GOLD         = (255, 215, 0)
WHITE        = (255, 255, 255)
RED          = (220, 60, 60)
GREEN        = (60, 210, 80)
DIM          = (160, 160, 170)
BTN_DISABLED = (90, 90, 95)
OWNER_BTN_COLOR = (50, 130, 200)

RIGHT_STACK_X  = 800 - 30
STACK_Y        = 10
CENTER_X       = 400
BET_STACK_Y    = 74

CARDS_X = 30
CARDS_Y = 10

BUTTON_AREA_Y = 240
BUTTON_W      = 150
BUTTON_H      = 60
BUTTON_GAP    = 10


class GameBottomScreen:
    def __init__(self, player_id: int | None = None):
        self.card_sheet = CardSheet()
        self.chip_sheet = ChipSheet()

        if BG_PATH.exists():
            self.bg = pygame.image.load(str(BG_PATH)).convert()
            self.bg = pygame.transform.scale(self.bg, (800, 300))
        else:
            self.bg = None

        self._button_base: pygame.Surface | None = self._load_button_sprite()
        self._button_cache: dict[tuple[int, int], pygame.Surface] = {}

        if FONT_PATH.exists():
            self.font       = pygame.font.Font(str(FONT_PATH), 22)
            self.small_font = pygame.font.Font(str(FONT_PATH), 16)
            self.tiny_font  = pygame.font.Font(str(FONT_PATH), 13)
        else:
            self.font       = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
            self.tiny_font  = pygame.font.Font(None, 14)

        self.state:     GameState | None = None
        self.player_id: int | None       = player_id
        self.owner_id:  int | None       = None
        self.bet_chips: dict[int, int]   = {}

        self._right_chip_rects: list[tuple[pygame.Rect, int]] = []
        self._bet_chip_rects:   list[tuple[pygame.Rect, int]] = []
        self._button_rects:     dict[str, pygame.Rect]        = {}
        self._enabled_actions:  set[str]                      = set()

    def _load_button_sprite(self) -> pygame.Surface | None:
        if BUTTON_PATH.exists():
            try:
                return pygame.image.load(str(BUTTON_PATH)).convert_alpha()
            except pygame.error:
                pass
        return None

    def _get_scaled_button(self, w: int, h: int) -> pygame.Surface | None:
        key = (w, h)
        if key not in self._button_cache and self._button_base:
            self._button_cache[key] = pygame.transform.smoothscale(self._button_base, key)
        return self._button_cache.get(key)

    def _draw_button_bg(self, surface: pygame.Surface, rect: pygame.Rect, enabled: bool, color_override=None):
        scaled = self._get_scaled_button(rect.w, rect.h)
        if scaled is not None:
            if not enabled:
                dark = scaled.copy()
                dark.fill((90, 90, 90, 255), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(dark, rect.topleft)
            elif color_override:
                colored = scaled.copy()
                colored.fill((*color_override, 255), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(colored, rect.topleft)
            else:
                surface.blit(scaled, rect.topleft)
        else:
            color = color_override if (color_override and enabled) else ((70, 70, 90) if enabled else (40, 40, 45))
            pygame.draw.rect(surface, color, rect, border_radius=4)
            pygame.draw.rect(surface, (0, 0, 0), rect, 1, border_radius=4)

    def update(self, state: GameState, player_id: int):
        prev_player_id = self.player_id
        self.state     = state
        self.player_id = player_id
        self.owner_id  = state.owner_id

        if state.current_player_id != player_id:
            self.bet_chips = {}
        if prev_player_id != player_id:
            self.bet_chips = {}

    def _my_player(self):
        if not self.state:
            return None
        for p in self.state.players:
            if p.id == self.player_id:
                return p
        return None

    def _bet_total(self) -> int:
        return sum(value * amount for value, amount in self.bet_chips.items())

    def _move_to_bet(self, value: int):
        my_player = self._my_player()
        if not my_player:
            return
        available = my_player.chips.get(value, 0) - self.bet_chips.get(value, 0)
        if available > 0:
            self.bet_chips[value] = self.bet_chips.get(value, 0) + 1

    def _move_from_bet(self, value: int):
        if self.bet_chips.get(value, 0) > 0:
            self.bet_chips[value] -= 1
            if self.bet_chips[value] == 0:
                del self.bet_chips[value]

    def _clear_bet(self):
        self.bet_chips = {}

    def _remaining_chips(self, my_player) -> dict[int, int]:
        remaining = dict(my_player.chips)
        for value, amount in self.bet_chips.items():
            remaining[value] = remaining.get(value, 0) - amount
        return {v: a for v, a in remaining.items() if a > 0}

    def _available_action_set(self) -> set[str]:
        if not self.state:
            return set()

        if self.state.phase == GamePhase.WAITING:
            return set()

        my_player = self._my_player()
        if not my_player:
            return set()

        if self.state.current_player_id != self.player_id:
            return set()

        my_chip_total  = sum(v * a for v, a in my_player.chips.items())
        to_call        = max(0, self.state.highest_bet - my_player.bet_this_round)

        actions = {"fold", "all-in"}

        if to_call == 0:
            actions.add("check")
        elif to_call <= my_chip_total:
            actions.add("call")

        if my_chip_total > to_call:
            actions.add("raise")

        return actions

    def draw(self, surface: pygame.Surface):
        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((18, 18, 36))

        self._right_chip_rects = []
        self._bet_chip_rects   = []
        self._button_rects     = {}

        if not self.state or self.player_id is None:
            text = self.font.render("Connecting...", True, WHITE)
            surface.blit(text, (50, 50))
            return

        my_player = self._my_player()
        if not my_player:
            text = self.font.render("Player not found", True, RED)
            surface.blit(text, (50, 50))
            return

        self._draw_hole_cards(surface, my_player)
        self._draw_side_stacks(surface, my_player)
        self._draw_bet_stack(surface)
        self._draw_buttons(surface)

    def _draw_hole_cards(self, surface: pygame.Surface, my_player):
        hand = my_player.hand
        if not hand:
            return
        card_scale     = 2
        card_w, card_h = self.card_sheet.get_card_size(card_scale)
        for i, card_str in enumerate(hand):
            try:
                card      = Card.str_to_card(card_str)
                card_surf = self.card_sheet.get_card(card.rank, card.suit, card_scale)
                x = CARDS_X + i * (card_w + 10)
                y = CARDS_Y
                surface.blit(card_surf, (x, y))
            except Exception as e:
                logging.warning(f"Cannot parse card {card_str}: {e}")

    def _draw_side_stacks(self, surface: pygame.Surface, my_player):
        remaining = self._remaining_chips(my_player)
        sorted_values = sorted(remaining.keys(), reverse=True)
        y = STACK_Y
        for value in sorted_values:
            amount = remaining[value]
            rect = self._draw_chip_stack(surface, RIGHT_STACK_X, y, value, amount, align="right")
            self._right_chip_rects.append((rect, value))
            y += 36

    def _draw_bet_stack(self, surface: pygame.Surface):
        label = self.small_font.render("BET", True, GOLD)
        surface.blit(label, (CENTER_X - label.get_width() // 2, BET_STACK_Y - 24))

        sorted_values = sorted(self.bet_chips.keys(), reverse=True)
        total_w = len(sorted_values) * 40
        x = CENTER_X - total_w // 2
        for value in sorted_values:
            amount = self.bet_chips[value]
            rect = self._draw_chip_stack(surface, x, BET_STACK_Y, value, amount, align="left", compact=True)
            self._bet_chip_rects.append((rect, value))
            x += 40

        total_text = self.small_font.render(f"${self._bet_total()}", True, GOLD)
        surface.blit(total_text, (CENTER_X - total_text.get_width() // 2, BET_STACK_Y + 50))

    def _draw_chip_stack(
        self,
        surface: pygame.Surface,
        x: int, y: int,
        value: int, amount: int,
        align: str = "left",
        compact: bool = False,
    ) -> pygame.Rect:
        stack_height = max(1, min(amount, 4))
        chip_surf    = self.chip_sheet.get(value, stack_height)
        cw, ch       = chip_surf.get_size()

        draw_x = x if align != "right" else x - cw
        surface.blit(chip_surf, (draw_x, y))

        label_text = f"{amount}" if compact else f"${value} ×{amount}"
        label = self.tiny_font.render(label_text, True, GOLD)
        shadow = self.tiny_font.render(label_text, True, WHITE)

        label_x = draw_x + cw + 4 if align != "right" else draw_x - label.get_width() - 4
        label_y = y + ch // 2 - label.get_height() // 2
        surface.blit(shadow, (label_x + 1, label_y + 1))
        surface.blit(label,  (label_x, label_y))

        left   = min(draw_x, label_x)
        right  = max(draw_x + cw, label_x + label.get_width())
        top    = y
        bottom = y + max(ch, label.get_height())
        full_rect = pygame.Rect(left, top, right - left, bottom - top)
        return full_rect

    def _draw_buttons(self, surface: pygame.Surface):
        if self.state.phase == GamePhase.WAITING:
            if self.owner_id == self.player_id:
                rect = pygame.Rect(CENTER_X - BUTTON_W // 2, BUTTON_AREA_Y, BUTTON_W, BUTTON_H)
                self._draw_button_bg(surface, rect, enabled=True, color_override=OWNER_BTN_COLOR)
                text = self.small_font.render("START", True, WHITE)
                text_rect = text.get_rect(center=rect.center)
                text_rect.centery -= 2
                surface.blit(text, text_rect)
                self._button_rects["start"] = rect
                self._enabled_actions = {"start"}
            else:
                self._enabled_actions = set()
            return

        if self.state.current_player_id != self.player_id:
            self._enabled_actions = set()
            return

        available  = self._available_action_set()
        bet_amount = self._bet_total()

        my_player = self._my_player()
        to_call   = max(0, self.state.highest_bet - my_player.bet_this_round) if my_player else 0

        defs = [
            ("fold",   "FOLD",                          "fold"   in available),
            ("check",  "CHECK",                         "check"  in available),
            ("call",   f"CALL ${to_call}",               "call"   in available and bet_amount >= to_call),
            ("raise",  f"RAISE ${bet_amount}" if bet_amount else "RAISE",
                                                          "raise"  in available and bet_amount > to_call),
            ("all-in", "ALL IN",                         "all-in" in available),
        ]

        n = len(defs)
        total_w = n * BUTTON_W + (n - 1) * BUTTON_GAP
        start_x = CENTER_X - total_w // 2

        for i, (action_key, label, enabled) in enumerate(defs):
            x = start_x + i * (BUTTON_W + BUTTON_GAP)
            rect = pygame.Rect(x, BUTTON_AREA_Y, BUTTON_W, BUTTON_H)
            self._draw_button_bg(surface, rect, enabled)

            color = WHITE if enabled else BTN_DISABLED
            text  = self.small_font.render(label, True, color)
            text_rect = text.get_rect(center=rect.center)
            text_rect.centery -= 2
            surface.blit(text, text_rect)

            self._button_rects[action_key] = rect

        self._enabled_actions = {k for k, _, e in defs if e}

    def handle_event(self, event: pygame.event.Event) -> tuple[str, int] | None:
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        pos = event.pos

        for rect, value in self._right_chip_rects:
            if rect.collidepoint(pos):
                self._move_to_bet(value)
                return None

        for rect, value in self._bet_chip_rects:
            if rect.collidepoint(pos):
                self._move_from_bet(value)
                return None

        for action_key, rect in self._button_rects.items():
            if rect.collidepoint(pos) and action_key in self._enabled_actions:
                amount = self._bet_total()

                if action_key == "start":
                    self._clear_bet()
                    return ("start", 0)

                if action_key == "fold":
                    self._clear_bet()
                    return ("fold", 0)

                if action_key == "check":
                    self._clear_bet()
                    return ("check", 0)

                if action_key == "call":
                    self._clear_bet()
                    my_player = self._my_player()
                    to_call = max(0, self.state.highest_bet - my_player.bet_this_round)
                    return ("call", to_call)

                if action_key == "raise":
                    if amount <= 0:
                        return None
                    self._clear_bet()
                    return ("raise", amount)

                if action_key == "all-in":
                    self._clear_bet()
                    my_player = self._my_player()
                    total = sum(v * a for v, a in my_player.chips.items())
                    return ("all-in", total)

        return None