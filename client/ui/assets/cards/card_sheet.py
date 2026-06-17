import pygame
from pathlib import Path
from shared.datatypes import Card
SHEET_PATH = Path(__file__).parent / "1_2_Poker_cards.png"

CARD_W = 48
CARD_H = 64

BACK_W  = 48
BACK_H  = 64
BACK_Y  = CARD_H * 4
N_BACKS = 8

SHEET_ROW_TO_SUIT = {
    0: 1,
    1: 2,
    2: 0,
    3: 3,
}

RANK_TO_COL = {
    14: 0,
    2:  1,
    3:  2,
    4:  3,
    5:  4,
    6:  5,
    7:  6,
    8:  7,
    9:  8,
    10: 9,
    11: 10,
    12: 11,
    13: 12,
}
SUIT_TO_ROW = {v: k for k, v in SHEET_ROW_TO_SUIT.items()}


class CardSheet:
    def __init__(self, path: Path | str = SHEET_PATH):
        self._sheet = pygame.image.load(str(path)).convert_alpha()
        self._cache:      dict[tuple[int, int], pygame.Surface] = {}
        self._back_cache: dict[int, pygame.Surface]             = {}
        self._preload()
    def get_card(
        self,
        rank: int,
        suit: int,
        scale: float = 1.0,
    ) -> pygame.Surface:
        key = (rank, suit)
        surf = self._cache.get(key)
        if surf is None:
            surf = self._cut_card(rank, suit)
            self._cache[key] = surf

        if scale != 1.0:
            w = int(surf.get_width()  * scale)
            h = int(surf.get_height() * scale)
            return pygame.transform.scale(surf, (w, h))
        return surf
    def get_back(
        self,
        variant: int = 0,
        scale: float = 1.0,
    ) -> pygame.Surface:
        variant = max(0, min(variant, N_BACKS - 1))
        surf = self._back_cache.get(variant)
        if surf is None:
            surf = self._cut_back(variant)
            self._back_cache[variant] = surf

        if scale != 1.0:
            w = int(surf.get_width()  * scale)
            h = int(surf.get_height() * scale)
            return pygame.transform.scale(surf, (w, h))
        return surf

    def get_card_size(self, scale: float = 1.0) -> tuple[int, int]:
        return (int(CARD_W * scale), int(CARD_H * scale))

    def get_back_size(self, scale: float = 1.0) -> tuple[int, int]:
        return (int(BACK_W * scale), int(BACK_H * scale))

    def _cut_card(self, rank: int, suit: int) -> pygame.Surface:
        col = RANK_TO_COL.get(rank)
        row = SUIT_TO_ROW.get(suit)

        if col is None or row is None:
            raise ValueError(
                f"Invalid card rank={rank} suit={suit}. "
                f"rank must be 2-14, suit must be 0-3."
            )

        x = col * CARD_W
        y = row * CARD_H
        rect = pygame.Rect(x, y, CARD_W, CARD_H)

        surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        surf.blit(self._sheet, (0, 0), rect)
        return surf

    def _cut_back(self, variant: int) -> pygame.Surface:
        x = variant * BACK_W
        y = BACK_Y
        rect = pygame.Rect(x, y, BACK_W, BACK_H)

        surf = pygame.Surface((BACK_W, BACK_H), pygame.SRCALPHA)
        surf.blit(self._sheet, (0, 0), rect)
        return surf

    def _preload(self):
        for rank in RANK_TO_COL:
            for suit in SUIT_TO_ROW:
                self._cache[(rank, suit)] = self._cut_card(rank, suit)

        for variant in range(N_BACKS):
            self._back_cache[variant] = self._cut_back(variant)

def draw_card_surface(
    surface:    pygame.Surface,
    card_sheet: CardSheet,
    card:      Card,
    x:          int,
    y:          int,
    scale:      float = 1.0,
):
    card = card_sheet.get_card(card.rank, card.suit, scale)
    surface.blit(card, (x, y))


def draw_card_back(
    surface:    pygame.Surface,
    card_sheet: CardSheet,
    x:          int,
    y:          int,
    variant:    int   = 0,
    scale:      float = 1.0,
):
    back = card_sheet.get_back(variant, scale)
    surface.blit(back, (x, y))