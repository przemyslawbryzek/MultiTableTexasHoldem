import pygame
from pathlib import Path
from shared.game_state import GameState, GamePhase
from client.ui.screens.game_screens.top_screen import TopScreen
from client.ui.screens.game_screens.bottom_screen import GameBottomScreen

BUTTON_PATH = Path(__file__).parent.parent.parent / "assets" / "sprites" / "button.png"

class GameScreenManager:
    def __init__(self, top_screen: TopScreen, bottom_screen: GameBottomScreen):
        self.top = top_screen
        self.bottom = bottom_screen
        self.top_rect = pygame.Rect(0, 0, 800, 400)
        self.separator_rect = pygame.Rect(0, 400, 800, 10)
        self.bottom_rect = pygame.Rect(0, 410, 800, 290)

        self.separator_texture = None
        if BUTTON_PATH.exists():
            try:
                img = pygame.image.load(str(BUTTON_PATH)).convert_alpha()
                self.separator_texture = pygame.transform.scale(img, (800, 10))
            except Exception:
                self.separator_texture = None

    def update(self, state, player_id: int, dt_ms: float = 16.0):
        self.top.update(state, player_id, dt_ms)
        self.bottom.update(state, player_id)

    def draw(self, surface: pygame.Surface):
        self.top.draw(surface)
        if self.separator_texture:
            surface.blit(self.separator_texture, (0, 400))
        else:
            for i in range(10):
                brightness = 60 + i * 4
                color = (brightness, brightness, brightness + 20)
                pygame.draw.line(surface, color, (0, 400 + i), (800, 400 + i))
        temp_surface = pygame.Surface((800, 300), pygame.SRCALPHA)
        self.bottom.draw(temp_surface)
        surface.blit(temp_surface, (0, 410))

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            adjusted_pos = (event.pos[0], event.pos[1] - 410)
            adjusted_event = pygame.event.Event(event.type, pos=adjusted_pos, button=event.button)
            return self.bottom.handle_event(adjusted_event)
        return self.bottom.handle_event(event)