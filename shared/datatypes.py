STANDARD_CHIP_VALUES = (1000, 500, 100, 50, 25, 10, 5, 1)


class Card:
    rank: int  # 2-14 11: 'J', 12: 'Q', 13: 'K', 14: 'A'
    suit: int  # 0-3

    def __init__(self, rank: int, suit: int):
        if rank < 2 or rank > 14:
            raise ValueError("Rank must be between 2 and 14")
        if suit < 0 or suit > 3:
            raise ValueError("Suit must be between 0 and 3")
        self.rank = rank
        self.suit = suit

    def __str__(self) -> str:
        rank_str = {11: "J", 12: "Q", 13: "K", 14: "A"}.get(self.rank, str(self.rank))
        suit_str = ["♠", "♥", "♦", "♣"][self.suit]
        return f"{rank_str}{suit_str}"


class Chip:
    value: int
    amount: int

    def __init__(self, value: int, amount: int):
        if value not in STANDARD_CHIP_VALUES:
            raise ValueError(
                "Chip value must be one of the standard values: 1, 5, 10, 25, 50, 100, 500, 1000"
            )
        if amount < 0:
            raise ValueError("Chip amount cannot be negative")
        self.value = value
        self.amount = amount


class Chips:
    chips: list[Chip]

    def __init__(self, starting_amount: dict[int, int] | list[Chip] | None = None):
        self.chips = []
        if starting_amount is None:
            return
        if isinstance(starting_amount, list):
            for chip in starting_amount:
                self.add_chips(chip.value, chip.amount)
            return
        for value, amount in starting_amount.items():
            self.add_chips(value, amount)

    def total_value(self) -> int:
        return sum(chip.value * chip.amount for chip in self.chips)

    def add_chips(self, value: int, amount: int):
        if amount < 0:
            raise ValueError("Chip amount cannot be negative")
        for chip in self.chips:
            if chip.value == value:
                chip.amount += amount
                return
        self.chips.append(Chip(value, amount))

    def add_amount(self, amount: int):
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        for value in STANDARD_CHIP_VALUES:
            if amount <= 0:
                break
            count = amount // value
            if count > 0:
                self.add_chips(value, count)
                amount -= count * value

    def remove_chips(self, value: int, amount: int):
        if amount < 0:
            raise ValueError("Chip amount cannot be negative")
        for chip in self.chips:
            if chip.value == value:
                if chip.amount < amount:
                    raise ValueError("Not enough chips to remove")
                chip.amount -= amount
                return
        raise ValueError("Chip value not found")

    def remove_amount(self, amount: int):
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        chip_breakdown = self.int_to_chips(amount)
        for value, count in chip_breakdown.items():
            self.remove_chips(value, count)

    def int_to_chips(self, amount: int) -> dict[int, int]:
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        result = {}
        remaining = amount
        available_chips = sorted(self.chips, key=lambda c: c.value, reverse=True)
        for chip in available_chips:
            if remaining <= 0:
                break
            num_chips = min(chip.amount, remaining // chip.value)
            if num_chips > 0:
                result[chip.value] = num_chips
                remaining -= num_chips * chip.value
        if remaining > 0:
            raise ValueError("Not enough chips to represent the amount")
        return result

    def to_dict(self) -> dict[int, int]:
        return {chip.value: chip.amount for chip in self.chips}


class Player:
    id: int
    name: str
    chips: Chips
    hand: list[Card]
    bet_this_round: int
    total_bet_this_hand: int
    is_active: bool
    is_folded: bool
    is_all_in: bool
    does_have_acted_this_round: bool

    def __init__(self, id: int, name: str, starting_chips: dict[int, int]):
        self.id = id
        self.name = name
        self.chips = Chips(starting_chips)
        self.hand = []
        self.is_active = True
        self.is_folded = False
        self.is_all_in = False
        self.does_have_acted_this_round = False
        self.bet_this_round = 0
        self.total_bet_this_hand = 0

    def receive_card(self, card: Card):
        if len(self.hand) >= 2:
            raise ValueError("Player cannot have more than 2 cards")
        self.hand.append(card)

    def clear_hand(self):
        self.hand = []
