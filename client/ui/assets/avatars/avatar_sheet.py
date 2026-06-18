from __future__ import annotations
import pygame
from enum import Enum
from pathlib import Path

SHEET_DIR = Path(__file__).parent

def sheet_path_for_avatar(avatar_index: int) -> Path:
    return SHEET_DIR / f"avatar_{avatar_index}.png"

FRAME_W = 186
FRAME_H = 186
N_FRAMES_TOTAL = 11

FRONT_START = 0
FRONT_COUNT = 5

BACK_START = 5
BACK_COUNT = 6


class AvatarView(Enum):
    FRONT = "front"
    BACK  = "back" 


class AvatarSheet:
    def __init__(self, avatar_index: int = 0, path: Path | str | None = None):
        self.avatar_index = avatar_index
        load_path = Path(path) if path else sheet_path_for_avatar(avatar_index)
        self._sheet = pygame.image.load(str(load_path)).convert_alpha()
        self._frames: list[pygame.Surface] = []
        self._scaled_cache: dict[tuple[int, float], pygame.Surface] = {}
        self._cut_frames()

    def _cut_frames(self) -> None:
        for i in range(N_FRAMES_TOTAL):
            rect = pygame.Rect(i * FRAME_W, 0, FRAME_W, FRAME_H)
            surf = pygame.Surface((FRAME_W, FRAME_H), pygame.SRCALPHA)
            surf.blit(self._sheet, (0, 0), rect)
            self._frames.append(surf)

    def get_frame(self, index: int, scale: float = 1.0) -> pygame.Surface:
        index = max(0, min(index, N_FRAMES_TOTAL - 1))
        if scale == 1.0:
            return self._frames[index]

        key = (index, scale)
        cached = self._scaled_cache.get(key)
        if cached is None:
            base = self._frames[index]
            w = int(FRAME_W * scale)
            h = int(FRAME_H * scale)
            cached = pygame.transform.scale(base, (w, h))
            self._scaled_cache[key] = cached
        return cached

    @staticmethod
    def frame_size(scale: float = 1.0) -> tuple[int, int]:
        return (int(FRAME_W * scale), int(FRAME_H * scale))


class AvatarSprite:
    def __init__(
        self,
        sheet: AvatarSheet,
        view: AvatarView = AvatarView.FRONT,
        fps: float = 6.0,
    ):
        self.sheet = sheet
        self.fps   = fps

        self._view: AvatarView   = view
        self._local_frame: int   = 0
        self._direction: int     = 1 
        self._accum_ms: float    = 0.0

    @property
    def view(self) -> AvatarView:
        return self._view

    def set_view(self, view: AvatarView) -> None:
        if view != self._view:
            self._view = view
            self._local_frame = 0
            self._direction = 1
            self._accum_ms = 0.0

    def _view_range(self) -> tuple[int, int]:
        if self._view is AvatarView.FRONT:
            return FRONT_START, FRONT_COUNT
        return BACK_START, BACK_COUNT

    def update(self, dt_ms: float) -> None:
        _, count = self._view_range()
        if count <= 1:
            return

        self._accum_ms += dt_ms
        frame_duration = 1000.0 / self.fps

        while self._accum_ms >= frame_duration:
            self._accum_ms -= frame_duration
            self._local_frame += self._direction

            if self._local_frame >= count - 1:
                self._local_frame = count - 1
                self._direction = -1
            elif self._local_frame <= 0:
                self._local_frame = 0
                self._direction = 1

    def current_frame_index(self) -> int:
        start, _ = self._view_range()
        return start + self._local_frame
    
    def draw(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        scale: float = 1.0,
        center: bool = True,
    ) -> pygame.Rect:
        frame = self.sheet.get_frame(self.current_frame_index(), scale)
        w, h = frame.get_size()

        pos = (x - w // 2, y - h // 2) if center else (x, y)
        surface.blit(frame, pos)
        return pygame.Rect(pos[0], pos[1], w, h)

    def get_size(self, scale: float = 1.0) -> tuple[int, int]:
        return AvatarSheet.frame_size(scale)
    
class AvatarSheetCache:
    def __init__(self):
        self._sheets: dict[int, AvatarSheet] = {}

    def get(self, avatar_index: int) -> AvatarSheet:
        sheet = self._sheets.get(avatar_index)
        if sheet is None:
            sheet = AvatarSheet(avatar_index)
            self._sheets[avatar_index] = sheet
        return sheet

BACK_SEAT_POSITIONS  = frozenset({0, 1, 2, 3})
FRONT_SEAT_POSITIONS = frozenset({4, 5, 6, 7, 8})


def view_for_seat(position: int) -> AvatarView:
    return AvatarView.BACK if position in BACK_SEAT_POSITIONS else AvatarView.FRONT
