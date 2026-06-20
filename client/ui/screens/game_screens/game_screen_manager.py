import pygame
from pathlib import Path
from shared.game_state import GameState, GamePhase
from client.ui.screens.game_screens.top_screen import TopScreen
from client.ui.screens.game_screens.bottom_screen import GameBottomScreen

BUTTON_PATH = Path(__file__).parent.parent.parent / "assets" / "sprites" / "button.png"

class GameScreenManager:
    def __init__(self, top_screen: TopScreen, bottom_screen: GameBottomScreen):
        self.top    = top_screen
        self.bottom = bottom_screen

    def update(self, state, player_id: int, dt_ms: float = 16.0):

        if state is not None:
            self.top.update(state, player_id, dt_ms)
            self.bottom.update(state, player_id)
        else:
            self.top.tick(dt_ms)

    BOTTOM_Y = 400
    BOTTOM_H = 300

    def draw(self, surface: pygame.Surface):
        self.top.draw(surface)
        bottom_surf = surface.subsurface(pygame.Rect(0, self.BOTTOM_Y, 800, self.BOTTOM_H))
        self.bottom.draw(bottom_surf)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            adj = pygame.event.Event(event.type, pos=(x, y - self.BOTTOM_Y), button=event.button)
            return self.bottom.handle_event(adj)
        return self.bottom.handle_event(event)