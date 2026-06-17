import pygame
import logging
from pathlib import Path
from shared.game_state import GameState, GamePhase
from shared.datatypes import Card
from shared.enums import ActionType
from client.ui.assets.cards.card_sheet import CardSheet

BG_PATH     = Path(__file__).parent.parent.parent / "assets" / "sprites" / "top_bg.png"
FONT_PATH   = Path(__file__).parent.parent.parent / "assets" / "fonts" / "pixelboy.ttf"

CARDS_X = 310
CARDS_Y = 220

class TopScreen:
    def __init__(self):
        self.card_sheet = CardSheet()

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

        self.state:     GameState | None = None

    def draw(self, surface: pygame.Surface):
        if self.bg is not None:
            surface.blit(self.bg, (0, 0))
        else:
            surface.fill((18, 18, 36))
        self._draw_hole_cards(surface, self.state.community_cards, self.state.phase)
    def update(self, state: GameState):
        self.state     = state

    def _draw_hole_cards(self, surface: pygame.Surface, cards: list[str], game_phase: GamePhase):
        card_scale     = 0.6
        card_w, card_h = self.card_sheet.get_card_size(card_scale)
        for i, card_str in enumerate(cards):
            try:
                if (game_phase == GamePhase.FLOP and i <= 2) or (game_phase == GamePhase.TURN and i <= 3) or (game_phase == GamePhase.RIVER):
                    card      = Card.str_to_card(card_str)
                    card_surf = self.card_sheet.get_card(card.rank, card.suit, card_scale)
                    x = CARDS_X + i * (card_w + 10)
                    y = CARDS_Y
                    surface.blit(card_surf, (x, y))
                else:
                    back_surf = self.card_sheet.get_back(0, card_scale)
                    x = CARDS_X + i * (card_w + 10)
                    y = CARDS_Y
                    surface.blit(back_surf, (x, y))

            except Exception as e:
                logging.warning(f"Cannot parse card {card_str}: {e}")