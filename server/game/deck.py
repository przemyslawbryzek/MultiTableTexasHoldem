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