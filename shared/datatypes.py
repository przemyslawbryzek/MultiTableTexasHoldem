class Card:
    rank: int      # 2-14 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
    suit: int      # 0-3

    def __init__(self, rank: int, suit: int):
        if rank < 2 or rank > 14:
            raise ValueError("Rank must be between 2 and 14")
        if suit < 0 or suit > 3:
            raise ValueError("Suit must be between 0 and 3")
        self.rank = rank
        self.suit = suit
    
    def __str__(self) -> str:
        rank_str = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}.get(self.rank, str(self.rank))
        suit_str = ['♠', '♥', '♦', '♣'][self.suit]
        return f"{rank_str}{suit_str}"
class Chip:
    value: int
    amount: int
    def __init__(self, value: int, amount: int):
        if value not in (1, 5, 10, 25, 50, 100, 500, 1000):
            raise ValueError("Chip value must be one of the standard values: 1, 5, 10, 25, 50, 100, 500, 1000")
        if amount < 0:
            raise ValueError("Chip amount cannot be negative")
        self.value = value
        self.amount = amount

class Chips:
    chips: list[Chip]
    def __init__(self, starting_amount: dict[int, int]):
        self.chips = []
        for value, amount in starting_amount.items():
            self.chips.append(Chip(value, amount))
    def total_value(self) -> int:
        return sum(chip.value * chip.amount for chip in self.chips)
    def add_chips(self, value: int, amount: int):
        for chip in self.chips:
            if chip.value == value:
                chip.amount += amount
                return
        self.chips.append(Chip(value, amount))
    def remove_chips(self, value: int, amount: int):
        for chip in self.chips:
            if chip.value == value:
                if chip.amount < amount:
                    raise ValueError("Not enough chips to remove")
                chip.amount -= amount
                return
        raise ValueError("Chip value not found")
    def int_to_chips(self, amount: int) -> dict[int, int]:
        result = {}
        for chip in sorted(self.chips, key=lambda c: c.value, reverse=True):
            if amount <= 0:
                break
            num_chips = min(chip.amount, amount // chip.value)
            if num_chips > 0:
                result[chip.value] = num_chips
                amount -= num_chips * chip.value
        if amount > 0:
            raise ValueError("Not enough chips to represent the amount")
        return result

class Player:
    name: str
    chips: Chips
    hand: list[Card]
    bet_this_round: int
    def __init__(self, name: str, starting_chips: dict[int, int]):
        self.name = name
        self.chips = Chips(starting_chips)
        self.hand = []
        self.bet_this_round = 0
        
    def receive_card(self, card: Card):
        if len(self.hand) >= 2:
            raise ValueError("Player cannot have more than 2 cards")
        self.hand.append(card)
    def clear_hand(self):
        self.hand = []