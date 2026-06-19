import pygame
import logging
from pathlib import Path
import math
from shared.game_state import GameState, GamePhase, PlayerState
from shared.datatypes import Card
from client.ui.assets.cards.card_sheet import CardSheet
from client.ui.assets.avatars.avatar_sheet import (
    AvatarSheetCache,
    AvatarSprite,
    AvatarView,
)

BG_PATH   = Path(__file__).parent.parent.parent / "assets" / "sprites" / "top_bg.png"
FONT_PATH = Path(__file__).parent.parent.parent / "assets" / "fonts" / "pixelboy.ttf"

CARDS_SCALE = 0.8

WHITE = (255, 255, 255)
GOLD  = (255, 215, 0)
RED   = (220, 60, 60)
DIM   = (160, 160, 170)

TABLE_CENTER_X = 399
TABLE_CENTER_Y = 247

SEAT_RADIUS_X = 280
SEAT_RADIUS_Y = 120
N_SEATS = 9

SEATS_FRONT = frozenset({0, 1, 2, 7, 8})
SEATS_BACK  = frozenset({3, 4, 5, 6})

LEFT_LABEL_SEATS = frozenset({5, 6, 7, 8})

MIRROR_SEATS = frozenset({3, 4, 7, 8})

def view_for_seat(position: int) -> AvatarView:
    return AvatarView.FRONT if position in SEATS_FRONT else AvatarView.BACK

def _seat_anchor(position: int) -> tuple[int, int, float]:
    angle = (position / N_SEATS) * 2 * math.pi - (math.pi / 2)
    x = TABLE_CENTER_X + int(SEAT_RADIUS_X * math.cos(angle))
    y = TABLE_CENTER_Y + int(SEAT_RADIUS_Y * math.sin(angle))
    depth_t = (y - (TABLE_CENTER_Y - SEAT_RADIUS_Y)) / (2 * SEAT_RADIUS_Y)
    scale = 0.45 + 0.35 * depth_t
    return x, y, scale

SEAT_ANCHORS = {pos: _seat_anchor(pos) for pos in range(N_SEATS)}


class TopScreen:
    def __init__(self):
        self.card_sheet = CardSheet()
        self.bg = None
        if BG_PATH.exists():
            self.bg = pygame.image.load(str(BG_PATH)).convert()
            self.bg = pygame.transform.scale(self.bg, (800, 400))
        else:
            self.bg = None

        if FONT_PATH.exists():
            self.font       = pygame.font.Font(str(FONT_PATH), 22)
            self.small_font = pygame.font.Font(str(FONT_PATH), 16)
            self.tiny_font  = pygame.font.Font(str(FONT_PATH), 13)
        else:
            self.font       = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
            self.tiny_font  = pygame.font.Font(None, 14)

        self.state = None
        self.player_id = None
        self._avatar_cache = AvatarSheetCache()
        self._player_avatars = {}

    def update(self, state: GameState, player_id: int, dt_ms: float = 16.0):
        self.state = state
        self.player_id = player_id
        self._sync_avatars(state.players)
        for av in self._player_avatars.values():
            av.update(dt_ms)

    def _sync_avatars(self, players: list[PlayerState]):
        seen = set()
        for p in players:
            seen.add(p.id)
            view = view_for_seat(p.position)
            av = self._player_avatars.get(p.id)
            if av is None:
                sheet = self._avatar_cache.get(p.avatar)
                self._player_avatars[p.id] = AvatarSprite(sheet, view=view, fps=6)
            else:
                if av.sheet.avatar_index != p.avatar:
                    av.sheet = self._avatar_cache.get(p.avatar)
                av.set_view(view)
        for sid in list(self._player_avatars.keys()):
            if sid not in seen:
                del self._player_avatars[sid]

    def draw(self, surface: pygame.Surface):
        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((18, 18, 36))

        if self.state is None:
            return
        self._draw_info_panel(surface)

        self._draw_hole_cards(surface, self.state.community_cards, self.state.phase)
        self._draw_players(surface, self.state.players)

    def _draw_info_panel(self, surface: pygame.Surface):
        my_player = None
        if self.player_id is not None:
            for p in self.state.players:
                if p.id == self.player_id:
                    my_player = p
                    break

        font = self.font
        color = WHITE
        gap = 4
        y_start = 6

        left_lines = []
        if my_player:
            chip_total = sum(v * a for v, a in my_player.chips.items())
            left_lines.append(f"Chips: ${chip_total}")
            left_lines.append(f"Bet: ${my_player.bet_this_round}")
            left_lines.append(f"Total: ${my_player.total_bet_this_hand}")
        left_lines.append(f"Highest: ${self.state.highest_bet}")

        left_x = 8
        left_y = y_start
        for line in left_lines:
            surf = font.render(line, True, color)
            surface.blit(surf, (left_x, left_y))
            left_y += surf.get_height() + gap

        right_lines = [f"Pot: ${self.state.pot}"]
        if self.state.side_pots:
            for sp in self.state.side_pots:
                right_lines.append(f"Side: ${sp.amount}")

        right_x = 790
        right_y = y_start
        for line in right_lines:
            surf = font.render(line, True, color)
            rect = surf.get_rect(topright=(right_x, right_y))
            surface.blit(surf, rect)
            right_y += surf.get_height() + gap

        left_total = len(left_lines) * (font.get_height() + gap) - gap
        right_total = len(right_lines) * (font.get_height() + gap) - gap
        total_height = max(left_total, right_total, 0)
        center_y = y_start + total_height // 2 - font.get_height() // 2

        phase_text = f"--- {self.state.phase.name} ---"
        phase_surf = font.render(phase_text, True, color)
        phase_rect = phase_surf.get_rect(center=(400, center_y))
        surface.blit(phase_surf, phase_rect)

    def _draw_hole_cards(self, surface: pygame.Surface, cards: list[str], game_phase: GamePhase):
        card_scale = CARDS_SCALE
        card_w, card_h = self.card_sheet.get_card_size(card_scale)
        gap = 10
        total_w = len(cards) * card_w + max(0, len(cards) - 1) * gap
        start_x = TABLE_CENTER_X - total_w // 2
        y = TABLE_CENTER_Y - card_h // 2

        for i, card_str in enumerate(cards):
            try:
                x = start_x + i * (card_w + gap)
                if (game_phase == GamePhase.FLOP and i <= 2) or \
                   (game_phase == GamePhase.TURN and i <= 3) or \
                   (game_phase == GamePhase.RIVER):
                    card = Card.str_to_card(card_str)
                    surf = self.card_sheet.get_card(card.rank, card.suit, card_scale)
                    surface.blit(surf, (x, y))
                else:
                    back = self.card_sheet.get_back(0, card_scale)
                    surface.blit(back, (x, y))
            except Exception as e:
                logging.warning(f"Cannot parse card {card_str}: {e}")

    def _draw_players(self, surface: pygame.Surface, players: list[PlayerState]):
        ordered = sorted(players, key=lambda p: SEAT_ANCHORS[p.position][1])
        is_current_turn = self.state.current_player_id if self.state else None

        for p in ordered:
            av = self._player_avatars.get(p.id)
            if av is None:
                continue

            x, y, scale = SEAT_ANCHORS.get(p.position, (TABLE_CENTER_X, TABLE_CENTER_Y, 0.7))

            frame = av.sheet.get_frame(av.current_frame_index(), scale)
            if p.position in MIRROR_SEATS:
                frame = pygame.transform.flip(frame, True, False)

            w, h = frame.get_size()
            pos = (x - w // 2, y - h // 2)
            surface.blit(frame, pos)
            rect = pygame.Rect(pos[0], pos[1], w, h)

            if p.id == is_current_turn and p.is_active and not p.is_folded:
                pygame.draw.ellipse(surface, GOLD, rect.inflate(6, 6), 2)

            label_align = 'left' if p.position in LEFT_LABEL_SEATS else 'right'
            self._draw_player_label(surface, p, rect, label_align)

    def _draw_player_label(self, surface: pygame.Surface, p: PlayerState, avatar_rect: pygame.Rect, align: str):
        chip_total = sum(value * amount for value, amount in p.chips.items())

        if p.is_folded:
            name_color = DIM
        elif p.is_all_in:
            name_color = GOLD
        else:
            name_color = WHITE

        name_text  = self.tiny_font.render(p.name, True, name_color)
        chips_text = self.tiny_font.render(f"${chip_total}", True, GOLD)
        lines = [name_text, chips_text]

        status = None
        if p.is_folded:
            status = ("FOLD", RED)
        elif p.is_all_in:
            status = ("ALL-IN", GOLD)
        elif p.bet_this_round > 0:
            status = (f"BET ${p.bet_this_round}", DIM)

        if status:
            text, color = status
            status_surf = self.tiny_font.render(text, True, color)
            lines.append(status_surf)

        if not lines:
            return
        total_h = sum(line.get_height() for line in lines) + 2 * (len(lines) - 1)
        start_y = avatar_rect.centery - total_h // 2
        offset = 0
        for line in lines:
            if align == 'left':
                rect = line.get_rect(midright=(avatar_rect.left - offset, start_y))
            else:
                rect = line.get_rect(midleft=(avatar_rect.right + offset, start_y))

            surface.blit(line, rect)
            start_y += line.get_height() + 2