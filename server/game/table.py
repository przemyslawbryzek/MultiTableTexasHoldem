from shared.enums import GameState
from shared.datatypes import Player, Card, Chips, Chip
from server.game.deck import Deck
class Table:
    players: list[Player]
    community_cards: list[Card]
    pot: Chips
    deck: Deck
    dealer_position: int
    small_blind: int
    big_blind: int
    highest_bet: int
    game_state: GameState

    def __init__(self, players: list[Player], starting_chips: dict[int, int], big_blind: int):
        self.players = players
        self.community_cards = []
        self.pot = Chips([Chip(value, 0) for value in starting_chips.keys()])
        self.deck = Deck()
        self.dealer_position = 0
        self.small_blind = big_blind // 2
        self.big_blind = big_blind
        self.highest_bet = big_blind
        self.game_state = GameState.PRE_FLOP
    
    def clear_table(self):
        self.community_cards = []
        for player in self.players:
            player.clear_hand()
        for player in self.players:
            player.bet_this_round = 0