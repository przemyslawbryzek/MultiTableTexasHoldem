# MultiTableTexasHoldem

- `shared` — common datatypes and enums used by client and server code.
- `server.game` — game logic including `Deck`, `Table` and `HandEvaluator`.
- `tests` — unit tests demonstrating usage and verifying correctness.


## `shared.datatypes` (core datatypes)

Classes:

- `Card`
	- Attributes:
		- `rank: int` — 2..14 (11:J, 12:Q, 13:K, 14:A)
		- `suit: int` — 0..3 (suit encoding is integer-based in this codebase)
	- Constructor: `Card(rank: int, suit: int)` — validates range and raises `ValueError` for invalid values.
	- String: `str(card)` returns human-friendly notation (e.g. `A♠`).
	- Usage example:
		```py
		from shared.datatypes import Card
		c = Card(14, 0)  # Ace of suit 0
		print(str(c))
		```

- `Chip`
	- Attributes: `value: int`, `amount: int`.
	- Constructor validates allowed `value` denominations and non-negative `amount`.

- `Chips`
	- Represents a collection of `Chip` objects.
	- Constructor: `Chips(starting_amount: dict[int, int])` where keys are chip values and values are counts.
	- Methods:
		- `total_value() -> int` — returns total cash represented by the chips.
		- `add_chips(value: int, amount: int)` — add chips of a denomination.
		- `remove_chips(value: int, amount: int)` — remove chips (raises if not enough).
		- `int_to_chips(amount: int) -> dict[int,int]` — decompose an integer amount into available chip denominations (raises if impossible).

- `Player`
	- Attributes: `name: str`, `chips: Chips`, `hand: list[Card]`.
	- Constructor: `Player(name: str, starting_chips: dict[int,int])`.
	- Methods:
		- `receive_card(card: Card)` — appends up to two cards in `hand` (raises if >2).
		- `clear_hand()` — empties player's hand.

---

## `shared.enums`

Enums:

- `GameState` — game phase states used by table/game flow:
	- `PRE_FLOP`, `FLOP`, `TURN`, `RIVER`, `SHOWDOWN`.

---

## `server.game.deck` — `Deck`

Class: `Deck`

- Attributes:
	- `cards: list[Card]` — populated with 52 `Card(rank, suit)` entries on construction.
- Methods:
	- `shuffle()` — shuffles `cards` in-place.
	- `deal_card() -> Card` — pops and returns one `Card`; raises `ValueError` if deck empty.

Usage example:
```py
from server.game.deck import Deck
from shared.datatypes import Card

d = Deck()
d.shuffle()
card = d.deal_card()
```

---

## `server.game.table` — `Table`

Class: `Table`

- Attributes:
	- `players: list[Player]` — list of `Player` instances.
	- `community_cards: list[Card]` — the shared community cards (0..5 during play).
	- `pot: Chips` — representation of chips in the pot (uses `Chips`).
	- `deck: Deck` — a `Deck` instance used to deal cards.
- Constructor: `Table(players: list[Player], starting_chips: dict[int,int], big_blind: int)`
- Methods:
	- `deal_card(player_name: str, card: Card)` — gives a `Card` to a named player (uses `Player.receive_card`).
	- `deal_community_card(card: Card)` — appends a card to `community_cards` (max 5, otherwise raises `ValueError`).
	- `clear_table()` — clears community cards and all players' hands.

Example:
```py
from server.game.table import Table
from shared.datatypes import Player, Card

players = [Player('Alice', {100:1}), Player('Bob', {100:1})]
t = Table(players, {100:0})
t.deal_community_card(Card(2,0))
```

---

## `server.game.hand_evaluator` — `HandEvaluator`

Class: `HandEvaluator` (all methods are static helpers)

Purpose: evaluate a player's best 5-card poker hand from their 2 hole cards + up to 5 community cards, and compare two hands for tie-breaking.

- `evaluate_hand(player_cards: list[Card], community_cards: list[Card]) -> int`
	- Returns a numeric rank indicating the best hand type (higher = stronger):
		- `-1` High Card
		- `0` One Pair
		- `1` Two Pair
		- `2` Three of a Kind
		- `3` Straight
		- `4` Flush
		- `5` Full House
		- `6` Four of a Kind
		- `7` Straight Flush
		- `8` Royal Flush

- `hand_comparator(hand1: list[Card], hand2: list[Card], public_cards: list[Card]) -> int`
	- Returns `1` if `hand1` wins, `-1` if `hand2` wins, `0` for tie.
	- Uses the evaluator helpers for tie-breaking within the same hand rank (compares ranks, then kickers where applicable).

Helper methods (useful for tests and reasoning):

- `is_royal_flush(cards)` / `is_straight_flush(cards)` / `is_four_of_a_kind(cards)` /
	`is_full_house(cards)` / `is_flush(cards)` / `is_straight(cards)` / `is_three_of_a_kind(cards)` /
	`is_two_pair(cards)` / `is_one_pair(cards)` — boolean predicates.

- `get_straight_flush_high_card(cards)` — returns the high card rank of the best straight flush found, or `0`.
- `get_four_of_a_kind_rank(cards)` — rank of the four-of-a-kind if present, else `0`.
- `get_flush_high_card(cards)` / `get_flush_ranks(cards)` — highest flush rank(s); `get_flush_ranks` returns list of top-5 ranks for the flush suit.
- `get_straight_high_card(cards)` — highest rank of any straight found (handles Ace-low wheel straight as 5).
- `get_three_of_a_kind_rank(cards)`, `get_two_pair_ranks(cards)`, `get_one_pair_rank(cards)` — utility accessors.
- `get_full_house_pair_rank(cards)` — returns the pair rank that composes the full house (the pair component, excluding the trips).

Notes and edge-cases:
- Straights are detected inclusive of the Ace-low wheel (A-2-3-4-5) and the straight-high helper returns `5` in that case.
- Flush comparison compares the full list of five flush ranks (kickers) descendingly, not only the single top card.
- Full house comparison first compares the trips rank, then the pair rank (the pair is chosen excluding trip rank).

Example usage:
```py
from server.game.hand_evaluator import HandEvaluator
from shared.datatypes import Card

player = [Card(14,0), Card(14,1)]
public = [Card(14,2), Card(2,3), Card(2,0), Card(11,2), Card(13,1)]
rank = HandEvaluator.evaluate_hand(player, public)
# rank == 5 -> Full House
```

---

## Testing

Unit tests live under `tests/` and use Python's built-in `unittest` runner. Run the suite with:

```bash
python3 -m unittest discover -s tests -v
```