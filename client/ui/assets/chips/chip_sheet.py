from __future__ import annotations
import pygame
from dataclasses import dataclass
from pathlib import Path
from shared.datatypes import Chip, Chips

SHEET_PATH = Path(__file__).parent.parent / "chips" / "chips.png"
FONT_PATH  = Path(__file__).parent.parent / "assets" / "fonts" / "pixelboy.ttf"

CELL_W      = 48
CELL_H      = 48
SPRITE_W    = 32
SHEET_COLS  = 8
SHEET_ROWS  = 4

COL_OFFSET_TO_STACK = {0: 1, 1: 2, 2: 3, 3: 4}
STACK_TO_COL_OFFSET = {1: 0, 2: 1, 3: 2, 4: 3}

DENOM_TO_SPRITE = {
    5:    (0, 0),   # red
    10:    (0, 1),   # blue
    1:   (1, 0),   # white
    50:   (1, 1),   # purple
    25:   (2, 0),   # green
    500:  (2, 1),   # pink
    100:  (3, 0),   # black
    1000: (3, 1),   # gold
}

TEXT_GOLD   = (255, 215,   0)
TEXT_SHADOW = (255, 255, 255)


class ChipSheet:
    def __init__(self, path: Path | str = SHEET_PATH):
        self._sheet = pygame.image.load(str(path)).convert_alpha()
        self._cache: dict[tuple[int, int], pygame.Surface] = {}
        self._preload()

    def get(
        self,
        denomination: int,
        stack_height: int,
        scale: float = 1.0,
    ) -> pygame.Surface:
        stack_height = max(1, min(4, stack_height))
        key = (denomination, stack_height)

        surf = self._cache.get(key)
        if surf is None:
            surf = self._cut(denomination, stack_height)
            self._cache[key] = surf

        if scale != 1.0:
            w = int(surf.get_width()  * scale)
            h = int(surf.get_height() * scale)
            return pygame.transform.scale(surf, (w, h))
        return surf

    def _cut(self, denomination: int, stack_height: int) -> pygame.Surface:
        row, group = DENOM_TO_SPRITE.get(denomination, (0, 0))
        col_offset = STACK_TO_COL_OFFSET.get(stack_height, 3)
        col = group * 4 + col_offset

        x = col  * CELL_W
        y = row  * CELL_H
        rect = pygame.Rect(x, y, SPRITE_W, CELL_H)

        surf = pygame.Surface((SPRITE_W, CELL_H), pygame.SRCALPHA)
        surf.blit(self._sheet, (0, 0), rect)
        return surf

    def _preload(self):
        for denom in DENOM_TO_SPRITE:
            for stack in range(1, 5):
                key = (denom, stack)
                self._cache[key] = self._cut(denom, stack)

    @staticmethod
    def sprite_size(scale: float = 1.0) -> tuple[int, int]:
        return (int(SPRITE_W * scale), int(CELL_H * scale))
@dataclass
class ChipSprite:
    chip:  Chip
    sheet: ChipSheet
    font:  pygame.font.Font | None = None

    def __post_init__(self):
        if self.font is None:
            self.font = _load_font(14)

    def draw(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        scale: float = 1.0,
        show_label: bool = True,
    ) -> pygame.Rect:
        if self.chip.amount <= 0:
            return pygame.Rect(x, y, 0, 0)

        stack_h = min(self.chip.amount, 4)
        sprite  = self.sheet.get(self.chip.value, stack_h, scale)
        surface.blit(sprite, (x, y))

        sw, sh = sprite.get_width(), sprite.get_height()
        total_w = sw
        if show_label and self.chip.amount >= 5:
            label_x = x + sw + 3
            label_y = y + sh // 2 - (self.font.get_height() // 2)
            label_w = self._draw_label(surface, self.chip.amount, label_x, label_y)
            total_w += 3 + label_w

        return pygame.Rect(x, y, total_w, sh)

    def _draw_label(
        self,
        surface: pygame.Surface,
        amount:  int,
        x:       int,
        y:       int,
    ) -> int:
        text = f"×{amount}"
        shadow = self.font.render(text, False, TEXT_SHADOW)
        surface.blit(shadow, (x + 1, y + 1))
        label = self.font.render(text, False, TEXT_GOLD)
        surface.blit(label, (x, y))

        return label.get_width()

    def total_value(self) -> int:
        return self.chip.value * self.chip.amount

    def __str__(self) -> str:
        return f"ChipSprite(${self.chip.value} × {self.chip.amount})"

@dataclass
class ChipsDisplay:
    chips: Chips
    sheet: ChipSheet
    font:  pygame.font.Font | None = None

    def __post_init__(self):
        if self.font is None:
            self.font = _load_font(12)

    def draw(
        self,
        surface: pygame.Surface,
        x:       int,
        y:       int,
        gap:     int   = 8,
        scale:   float = 1.0,
    ) -> pygame.Rect:
        cursor_x = x
        max_h    = 0
        sorted_chips = sorted(
            [c for c in self.chips._chips.values() if c.amount > 0],
            key=lambda c: -c.value,
        )

        for chip in sorted_chips:
            sprite = ChipSprite(chip=chip, sheet=self.sheet, font=self.font)
            rect   = sprite.draw(surface, cursor_x, y, scale)
            cursor_x += rect.width + gap
            max_h    = max(max_h, rect.height)

        total_w = cursor_x - x - gap if cursor_x > x else 0
        return pygame.Rect(x, y, total_w, max_h)

    def draw_total(
        self,
        surface: pygame.Surface,
        x:       int,
        y:       int,
        prefix:  str = "$",
    ) -> pygame.Rect:
        total = self.chips.total_value()
        text  = f"{prefix}{total:,}"
        font  = _load_font(16)

        shadow = font.render(text, False, TEXT_SHADOW)
        surface.blit(shadow, (x + 1, y + 1))

        label = font.render(text, False, TEXT_GOLD)
        surface.blit(label, (x, y))

        return pygame.Rect(x, y, label.get_width(), label.get_height())
def draw_pot(
    surface: pygame.Surface,
    sheet:   ChipSheet,
    amount:  int,
    x:       int,
    y:       int,
    font:    pygame.font.Font | None = None,
    scale:   float = 1.0,
) -> pygame.Rect:
    if amount <= 0:
        return pygame.Rect(x, y, 0, 0)

    if font is None:
        font = _load_font(14)
    best_denom = 1
    for denom in sorted(DENOM_TO_SPRITE.keys(), reverse=True):
        if amount >= denom:
            best_denom = denom
            break
    ratio      = amount // best_denom
    stack_h    = min(max(1, ratio), 4)

    sprite = sheet.get(best_denom, stack_h, scale)
    surface.blit(sprite, (x, y))

    sw = sprite.get_width()
    sh = sprite.get_height()
    label_x = x + sw + 4
    label_y = y + sh // 2 - font.get_height() // 2
    text    = f"${amount:,}"

    shadow = font.render(text, False, TEXT_SHADOW)
    surface.blit(shadow, (label_x + 1, label_y + 1))
    main = font.render(text, False, TEXT_GOLD)
    surface.blit(main, (label_x, label_y))

    return pygame.Rect(x, y, sw + 4 + main.get_width(), sh)

_font_cache: dict[int, pygame.font.Font] = {}

def _load_font(size: int) -> pygame.font.Font:
    if size in _font_cache:
        return _font_cache[size]

    if FONT_PATH.exists():
        font = pygame.font.Font(str(FONT_PATH), size)
    else:
        font = pygame.font.SysFont("monospace", size)

    _font_cache[size] = font
    return font