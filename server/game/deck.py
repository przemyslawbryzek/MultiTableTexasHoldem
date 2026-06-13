import random
from shared.datatypes import Card
class Deck:
    cards: list[Card]
    def __init__(self):
        self.cards = [Card(rank, suit) for rank in range(2, 15) for suit in range(4)]
    def shuffle(self):
        random.shuffle(self.cards)
    def deal_card(self) -> Card:
        if not self.cards:
            raise ValueError("No more cards in the deck")
        return self.cards.pop()
    def deal_cards(self, num: int) -> list[Card]:
        if len(self.cards) < num:
            raise ValueError("Not enough cards in the deck")
        return [self.deal_card() for _ in range(num)]
    def reset(self):
        self.__init__()
        self.shuffle()