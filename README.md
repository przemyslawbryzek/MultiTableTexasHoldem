# MultiTableTexasHoldem

## `shared.datatypes`

### `Card`
Represents a single playing card.

| Attribute | Type | Description |
|-----------|------|-------------|
| `rank` | `int` | 2–14 (11=J, 12=Q, 13=K, 14=A) |
| `suit` | `int` | 0=♠, 1=♥, 2=♦, 3=♣ |

```python
from shared.datatypes import Card
c = Card(14, 0)   # Ace of Spades
print(str(c))     # A♠
```

Constructor raises `ValueError` for out-of-range values.

---

### `Chip`
Single chip denomination.

| Attribute | Type | Description |
|-----------|------|-------------|
| `value` | `int` | One of: 1, 5, 10, 25, 50, 100, 500, 1000 |
| `amount` | `int` | Number of chips of this denomination |

---

### `Chips`
Collection of chips across all denominations.

Constructor: `Chips(starting_amount: dict[int, int] | list[Chip] | None)`

| Method | Description |
|--------|-------------|
| `total_value() -> int` | Total cash value |
| `add_chips(value, amount)` | Add chips of one denomination |
| `add_amount(amount: int)` | Add chips auto-broken into denominations |
| `remove_chips(value, amount)` | Remove chips (raises if not enough) |
| `remove_amount(amount: int)` | Remove chips auto-broken into denominations |
| `int_to_chips(amount) -> dict` | Decompose integer into available denominations |
| `to_dict() -> dict` | Serialize to `{value: amount}` dict |

```python
from shared.datatypes import Chips
chips = Chips({100: 5, 50: 10})   # 500 + 500 = 1000
chips.add_amount(75)               # auto-breakdown: 50×1 + 25×1
chips.remove_amount(100)
print(chips.total_value())         # 975
```

---

### `Player`
Represents a player at the table.

Constructor: `Player(id: int, name: str, starting_chips: dict[int, int])`

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | `int` | Unique player ID |
| `name` | `str` | Display name |
| `chips` | `Chips` | Current chip stack |
| `hand` | `list[Card]` | Hole cards (max 2) |
| `bet_this_round` | `int` | Amount bet in current betting round |
| `total_bet_this_hand` | `int` | Total bet across all rounds this hand |
| `is_active` | `bool` | False if eliminated (no chips) |
| `is_folded` | `bool` | True if folded this hand |
| `is_all_in` | `bool` | True if all-in |

| Method | Description |
|--------|-------------|
| `receive_card(card)` | Add card to hand (max 2, raises otherwise) |
| `clear_hand()` | Empty hand |

---

## `shared.enums`

### `GameState`
```python
WAITING    # Between hands
PRE_FLOP   # Hole cards dealt, first betting round
FLOP       # 3 community cards revealed
TURN       # 4th community card
RIVER      # 5th community card
SHOWDOWN   # Hands revealed, pot distributed
```

### `MessageType`
```python
# Client → Server
ACTION           # Game action (fold/check/call/raise/all-in)
JOIN_TABLE       # Join existing table by ID
CREATE_TABLE     # Create new table
START_TABLE      # Owner starts hand
GET_TABLES       # Request list of open tables
CREATE_ACCOUNT   # Register new account
LOGIN            # Login to existing account

# Server → Client (responses)
ACTION_RESPONSE
JOIN_TABLE_RESPONSE
CREATE_TABLE_RESPONSE
GET_TABLES_RESPONSE
LOGIN_RESPONSE
CREATE_ACCOUNT_RESPONSE

# Server → Client (broadcasts)
GAME_STATE       # Full game state (personalised per player)
PLAYER_JOINED    # New player joined table
PLAYER_LEFT      # Player disconnected
GAME_START       # Hand starting
HAND_END         # Hand finished + winners
ERROR            # Error message
```

### `ActionType`
```python
FOLD / CHECK / CALL / RAISE / ALL_IN
```

---

## `shared.protocol`

Length-prefixed JSON framing over TCP.

```
[LENGTH: 4 bytes big-endian][JSON payload: LENGTH bytes]
```

Handles TCP stream fragmentation — messages may arrive split across multiple `recv()` calls.

| Method | Description |
|--------|-------------|
| `Protocol.encode_message(msg: dict) -> bytes` | Serialize dict to framed bytes |
| `Protocol.extract_message(buffer: bytes) -> (dict, bytes)` | Extract one message from buffer, return remainder |

```python
from shared.protocol import Protocol

# Sending
data = Protocol.encode_message({"type": "action", "action": "fold"})
sock.sendall(data)

# Receiving
buffer += sock.recv(4096)
msg, buffer = Protocol.extract_message(buffer)
```

---

## `server.game.deck`

### `Deck`
Standard 52-card deck.

| Method | Description |
|--------|-------------|
| `reset()` | Rebuild and shuffle full 52-card deck |
| `deal_card() -> Card` | Pop one card (raises `ValueError` if empty) |
| `deal_cards(n: int) -> list[Card]` | Deal n cards |

```python
from server.game.deck import Deck
d = Deck()
card = d.deal_card()
```

---

## `server.game.hand_evaluator`

### `HandEvaluator`
All methods are `@staticmethod`.

#### `evaluate_hand(player_cards, community_cards) -> int`
Returns hand rank (higher = stronger):

| Return | Hand |
|--------|------|
| `-1` | High Card |
| `0` | One Pair |
| `1` | Two Pair |
| `2` | Three of a Kind |
| `3` | Straight |
| `4` | Flush |
| `5` | Full House |
| `6` | Four of a Kind |
| `7` | Straight Flush |
| `8` | Royal Flush |

#### `hand_comparator(hand1, hand2, public_cards) -> int`
Tie-break two hands of the same rank. Returns `1` (hand1 wins), `-1` (hand2 wins), `0` (tie).

#### Boolean helpers
`is_royal_flush`, `is_straight_flush`, `is_four_of_a_kind`, `is_full_house`, `is_flush`, `is_straight`, `is_three_of_a_kind`, `is_two_pair`, `is_one_pair`

#### Rank getters
`get_straight_high_card`, `get_straight_flush_high_card`, `get_four_of_a_kind_rank`, `get_flush_ranks`, `get_flush_high_card`, `get_three_of_a_kind_rank`, `get_two_pair_ranks`, `get_one_pair_rank`, `get_full_house_pair_rank`

**Edge cases:**
- Ace-low straight (A-2-3-4-5) is supported; `get_straight_high_card` returns `5`
- Flush comparison uses all 5 flush-suit ranks (not just top card)
- Full house: trips rank compared first, then pair rank

```python
from server.game.hand_evaluator import HandEvaluator
from shared.datatypes import Card

player = [Card(14, 0), Card(14, 1)]
public = [Card(14, 2), Card(2, 3), Card(2, 0), Card(11, 2), Card(13, 1)]
rank = HandEvaluator.evaluate_hand(player, public)
# rank == 5  →  Full House
```

---

## `server.game.table`

### `Table`
Core game logic. Manages one poker hand from start to showdown including side pots.

Constructor: `Table(owner: Player, starting_chips: dict[int, int], big_blind: int)`

#### Key attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `players` | `list[Player]` | All players at table |
| `community_cards` | `list[Card]` | 0–5 revealed cards |
| `pot` | `Chips` | Total chips in main pot |
| `game_state` | `GameState` | Current phase |
| `dealer_position` | `int` | Index of dealer |
| `current_player_idx` | `int` | Index of player to act |
| `highest_bet` | `int` | Current bet to call |
| `last_raise` | `int` | Size of last raise (for min-raise) |
| `small_blind` | `int` | Small blind amount |
| `big_blind` | `int` | Big blind amount |

#### Methods

| Method | Description |
|--------|-------------|
| `add_player(player)` | Add player (max 9, only in WAITING) |
| `remove_player(player_id)` | Remove player by ID |
| `get_player_by_id(player_id)` | Lookup player |
| `get_active_players()` | Players who can still bet (not folded, not all-in) |
| `get_players_in_hand()` | Players still in hand (including all-in) |
| `start_new_hand()` | Begin new hand (deals cards, posts blinds) |
| `process_player_action(player_id, action, amount)` | Handle fold/check/call/raise/all-in |
| `advance_game_state()` | Move to next phase (flop/turn/river/showdown) |
| `get_winner() -> list[Player]` | Determine winner(s) using hand evaluation |
| `calculate_side_pots() -> list[SidePot]` | Compute side pots from all-in situations |
| `distribute_pots()` | Award each side pot to its winner(s) |
| `clear_table()` | Reset for next hand |

#### `process_player_action` valid actions
```python
"fold"    # Give up hand
"check"   # Pass (only if no bet to call)
"call"    # Match current highest bet
"raise"   # Raise to amount (must meet min-raise rule)
"all-in"  # Bet all remaining chips
```

Raises `ValueError` for invalid actions (wrong turn, illegal check, insufficient chips, raise below minimum).

#### Side pot example
```
Alice: all-in  100   →  eligible for pot up to 100×3
Bob:   all-in  300   →  eligible for pot up to 300×3
Carol: bet     500   →  eligible for all pots

Side pot 1:  100 × 3 = 300  (Alice, Bob, Carol)
Side pot 2:  200 × 2 = 400  (Bob, Carol)
Main pot:    200 × 1 = 200  (Carol)
```

```python
from server.game.table import Table
from shared.datatypes import Player

owner = Player(0, "Alice", {100: 10})
table = Table(owner, {100: 10}, big_blind=20)
table.add_player(Player(1, "Bob", {100: 10}))
table.start_new_hand()
table.process_player_action(0, "call", 0)
table.process_player_action(1, "check", 0)
# → advances to FLOP automatically
```

---

## `server.network.server`

### `Server`
Concurrent TCP server using Linux `epoll`.

Constructor: `Server(host='0.0.0.0', port=7777)`

```python
from server.network.server import Server
import logging

logging.basicConfig(level=logging.INFO)
s = Server()
s.run()   # blocking
```

#### Message flow

```
Client                          Server
  │── login ───────────────────►│
  │◄── login_response ──────────│  success + player_id

  │── create_table ────────────►│
  │◄── create_table_response ───│  success + table_id
  │◄── game_state ──────────────│  initial empty table state

  │── join_table ───────────────►│  (second client)
  │◄── join_table_response ─────│
  │◄── player_joined ───────────│  broadcast to others
  │◄── game_state ──────────────│  full state to everyone

  │── start_table ─────────────►│
  │◄── game_start ──────────────│  broadcast
  │◄── game_state ──────────────│  state with hole cards

  │── action (raise 100) ───────►│
  │◄── action_response ─────────│  success=True
  │◄── game_state ──────────────│  broadcast to all

  │── action (invalid) ─────────►│
  │◄── action_response ─────────│  success=False + error
  │  (no game_state broadcast)
```

#### Notes
- Each player receives a **personalised** `game_state` — only their own hole cards are included; opponents show `hand: [], hand_size: 2`
- On disconnect: player is **auto-folded** if it is their turn, then removed
- Empty tables are deleted automatically

---

## `server.network.table_manager`

### `TableManager`
Manages all active tables and maps TCP file descriptors to players.

| Method | Description |
|--------|-------------|
| `create_table(owner_fd, owner_id, owner_name, big_blind)` | Create table, return `table_id` |
| `delete_table(table_id)` | Delete table and clean up all mappings |
| `get_table(table_id)` | Get `Table` by ID |
| `add_player_to_table(table_id, player_id, player_name, client_fd)` | Add player |
| `remove_player_by_fd(fd)` | Handle disconnect (auto-fold + cleanup) |
| `get_table_id_by_fd(fd)` | Which table is this fd at? |
| `get_player_id_by_fd(fd)` | Which player is this fd? |
| `get_fds_at_table(table_id)` | All fds at a table (for broadcast) |
| `get_tables()` | List of joinable tables (WAITING state only) |

---

## Network Protocol

### Framing
```
[LENGTH: 4 bytes, big-endian uint32][JSON payload: LENGTH bytes]
```

### Client → Server messages
```json
{"type": "login", "username": "Alice", "password": "secret"}
{"type": "create_account", "username": "Alice", "password": "secret"}
{"type": "get_tables"}
{"type": "create_table", "player_id": 1, "player_name": "Alice", "big_blind": 20}
{"type": "join_table", "table_id": 3, "player_id": 1, "player_name": "Alice"}
{"type": "start_table"}
{"type": "action", "action": "raise", "amount": 100}
{"type": "action", "action": "fold"}
```

### Server → Client messages
```json
{"type": "login_response", "success": true, "player_id": 42, "player_name": "Alice", "error": null}
{"type": "create_table_response", "success": true, "table_id": 3, "error": null}
{"type": "join_table_response", "success": true, "table_id": 3, "error": null}
{"type": "action_response", "success": true, "action": "raise", "amount": 100, "error": null}
{"type": "action_response", "success": false, "action": "check", "error": "Cannot check, must call or raise"}
{"type": "get_tables_response", "tables": [{"table_id": 1, "owner": "Alice", "num_players": 2, "big_blind": 20, "game_state": "WAITING"}]}
{"type": "game_start"}
{"type": "player_joined", "player": {"id": 2, "name": "Bob", "chips": 1500}}
{"type": "player_left", "player_id": 2, "player_name": "Bob", "reason": "disconnected"}
{"type": "hand_end", "winners": [...], "all_hands": [...]}
{"type": "error", "message": "Table 99 does not exist"}
{"type": "game_state",
  "game_state": "FLOP",
  "players": [
    {"id": 1, "name": "Alice", "chips": 2880, "bet": 100, "is_folded": false,
     "is_all_in": false, "is_active": true, "hand": ["A♠", "K♥"], "hand_size": 2},
    {"id": 2, "name": "Bob",   "chips": 2880, "bet": 100, "is_folded": false,
     "is_all_in": false, "is_active": true, "hand": [],            "hand_size": 2}
  ],
  "community_cards": ["10♠", "J♥", "Q♦"],
  "pot": 230,
  "current_player": 2,
  "highest_bet": 100,
  "small_blind": 10,
  "big_blind": 20,
  "dealer_position": 0
}
```

---

## Starting Chips

Default stack: **1500 chips** (`{100: 5, 50: 10, 10: 50}`)

Blinds: SB = 10, BB = 20