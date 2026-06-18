import pygame
from pathlib import Path
from shared.game_state import GameState, GamePhase
from client.ui.screens.game_screens.top_screen import TopScreen
from client.ui.screens.game_screens.bottom_screen import GameBottomScreen

BUTTON_PATH = Path(__file__).parent.parent / "assets" / "sprites" / "button.png"

class ScreenManager:
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
    
if __name__ == "__main__":
    from shared.game_state import PlayerState, SidePotState, AvailableAction
    from shared.enums import ActionType

    pygame.init()
    screen = pygame.display.set_mode((800, 710))
    pygame.display.set_caption("Bottom Screen Test")
    clock = pygame.time.Clock()

    sample_players = [
        PlayerState(
            id=1,
            name="x",
            avatar=1,
            chips={100: 5,25:6, 10: 10, 5: 50},
            bet_this_round=200,
            total_bet_this_hand=500,
            is_active=True,
            is_folded=False,
            is_all_in=False,
            position=0,
            hand=["A♠", "K♥"],
            hand_size=2,
        ),
        PlayerState(
            id=2,
            name="y",
            avatar=2,
            chips={100: 10},
            bet_this_round=40,
            total_bet_this_hand=40,
            is_active=True,
            is_folded=False,
            is_all_in=False,
            position=1,
            hand=[],
            hand_size=2,
        ),
        PlayerState(
            id=3,
            name="z",
            avatar=1,
            chips={100: 8},
            bet_this_round=40,
            total_bet_this_hand=40,
            is_active=True,
            is_folded=True,
            is_all_in=False,
            position=2,
            hand=[],
            hand_size=2,
        ),
            PlayerState(
                id=4,
                name="w",
                avatar=2,
                chips={100: 2},
                bet_this_round=40,
                total_bet_this_hand=40,
                is_active=True,
                is_folded=False,
                is_all_in=True,
                position=3,
                hand=[],
                hand_size=2,
            ),
            PlayerState(
                id=5,
                name="v",
                avatar=1,
                chips={100: 20},
                bet_this_round=40,
                total_bet_this_hand=40,
                is_active=False,
                is_folded=False,
                is_all_in=False,
                position=4,
                hand=[],
                hand_size=2,
            ),
            PlayerState(
                id=6,
                name="u",
                avatar=2,
                chips={100: 20},
                bet_this_round=40,
                total_bet_this_hand=40,
                is_active=True,
                is_folded=False,
                is_all_in=False,
                position=5,
                hand=[],
                hand_size=2,
            ),
            PlayerState(
                id=7,
                name="t",
                avatar=1,
                chips={100: 20},
                bet_this_round=40,
                total_bet_this_hand=40,
                is_active=True,
                is_folded=False,
                is_all_in=False,
                position=6,
                hand=[],
                hand_size=2,
            ),
            PlayerState(
                id=8,
                name="s",
                avatar=2,
                chips={100: 20},
                bet_this_round=40,
                total_bet_this_hand=40,
                is_active=True,
                is_folded=False,
                is_all_in=False,
                position=7,
                hand=[],
                hand_size=2,
            ),
            PlayerState(
                id=9,
                name="r",
                avatar=1,
                chips={100: 20},
                bet_this_round=40,
                total_bet_this_hand=40,
                is_active=True,
                is_folded=False,
                is_all_in=False,
                position=8,
                hand=[],
                hand_size=2,
            )
    ]

    sample_actions = [
        AvailableAction(action=ActionType.CALL, min_amount=40, max_amount=40, label="Call $40"),
        AvailableAction(action=ActionType.RAISE, min_amount=80, max_amount=1500, label="Raise"),
        AvailableAction(action=ActionType.ALL_IN, min_amount=1500, max_amount=1500, label="All-in $1500"),
        AvailableAction(action=ActionType.FOLD, min_amount=0, max_amount=0, label="Fold"),
    ]

    test_state = GameState(
        phase=GamePhase.WAITING,
        hand_number=1,
        dealer_position=2,
        owner_id=1,
        current_player_id=1,
        small_blind=10,
        big_blind=20,
        highest_bet=40,
        last_raise=20,
        pot=120,
        side_pots=[],
        community_cards=["10♠", "J♠", "Q♠","10♠","A♠"],
        players=sample_players,
        available_actions=sample_actions,
    )

    bottom_screen = GameBottomScreen()
    top_screen = TopScreen()
    screen_manager = ScreenManager(top_screen, bottom_screen)
    running = True
    while running:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            result = screen_manager.handle_event(event)
            if result:
                action, amount = result
                print(f"Kliknięto: {action} {amount}")

        screen_manager.update(test_state, player_id=1, dt_ms=dt)
        screen_manager.draw(screen)
        pygame.display.flip()

    pygame.quit()