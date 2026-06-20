from shared.enums import GameState
from shared.datatypes import Player, Card, Chips, Chip
from server.game.deck import Deck
from server.game.hand_evaluator import HandEvaluator
from dataclasses import dataclass, field


@dataclass
class SidePot:
    amount: int
    eligible_players: list[Player] = field(default_factory=list)


class Table:
    owner: Player
    players: list[Player]
    community_cards: list[Card]
    pot: Chips
    side_pots: list[SidePot]
    deck: Deck
    dealer_position: int
    current_player_idx: int
    small_blind: int
    big_blind: int
    highest_bet: int
    last_raise: int
    game_state: GameState

    def __init__(self, owner: Player, starting_chips: dict[int, int], big_blind: int):
        self.owner = owner
        self.players = [owner]
        self.max_players = 9
        self.community_cards = []
        self.pot = Chips({value: 0 for value in starting_chips.keys()})
        self.side_pots = []
        self.deck = Deck()
        self.dealer_position = 0
        self.current_player_idx = 0
        self.small_blind = big_blind // 2
        self.big_blind = big_blind
        self.highest_bet = 0
        self.last_raise = 0
        self.game_state = GameState.WAITING

    def add_player(self, player: Player):
        if len(self.players) >= self.max_players:
            raise ValueError("Table is full")
        if self.game_state != GameState.WAITING:
            raise ValueError("Cannot join a game in progress")
        self.players.append(player)

    def remove_player(self, player_id: int):
        self.players = [p for p in self.players if p.id != player_id]

    def get_player_by_id(self, player_id: int) -> Player:
        for player in self.players:
            if player.id == player_id:
                return player
        raise ValueError("Player not found")

    def get_active_players(self) -> list[Player]:
        return [
            p
            for p in self.players
            if p.is_active and not p.is_folded and not p.is_all_in
        ]

    def get_players_in_hand(self) -> list[Player]:
        return [p for p in self.players if p.is_active and not p.is_folded]

    def rotate_dealer(self):
        self.dealer_position = (self.dealer_position + 1) % len(self.players)

    def rotate_current_player(self):
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        while (
            not self.players[self.current_player_idx].is_active
            or self.players[self.current_player_idx].is_folded
            or self.players[self.current_player_idx].is_all_in
        ):
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

    def deal_hole_cards(self):
        for player in self.get_active_players():
            player.receive_card(self.deck.deal_card())
        for player in self.get_active_players():
            player.receive_card(self.deck.deal_card())

    def can_start(self, *players) -> bool:
        return sum(1 for p in players if p.chips.total_value() > self.big_blind) >= 2

    def calculate_side_pots(self) -> list[SidePot]:
        players_in_hand = self.get_players_in_hand()

        if not players_in_hand:
            return []
        contributions = {p.id: p.total_bet_this_hand for p in self.players}
        all_in_players = sorted(
            [p for p in self.players if p.is_all_in],
            key=lambda p: p.total_bet_this_hand,
        )

        side_pots = []
        previous_level = 0

        for all_in_player in all_in_players:
            level = all_in_player.total_bet_this_hand
            if level <= previous_level:
                continue
            pot_amount = 0
            for p in self.players:
                contribution = min(contributions[p.id], level) - previous_level
                if contribution > 0:
                    pot_amount += contribution
            eligible = [p for p in players_in_hand if p.total_bet_this_hand >= level]

            if pot_amount > 0:
                side_pots.append(SidePot(amount=pot_amount, eligible_players=eligible))

            previous_level = level
        if previous_level > 0:
            remaining_pot = 0
            for p in self.players:
                contribution = contributions[p.id] - min(
                    contributions[p.id], previous_level
                )
                if contribution > 0:
                    remaining_pot += contribution

            eligible_for_main = [
                p for p in players_in_hand if p.total_bet_this_hand > previous_level
            ]

            if remaining_pot > 0 and eligible_for_main:
                side_pots.append(
                    SidePot(amount=remaining_pot, eligible_players=eligible_for_main)
                )
        else:
            total = sum(contributions.values())
            if total > 0:
                side_pots.append(
                    SidePot(amount=total, eligible_players=players_in_hand)
                )

        return side_pots

    def get_pot_winners(self, side_pot: SidePot) -> list[Player]:
        eligible = side_pot.eligible_players
        if not eligible:
            return []
        if len(eligible) == 1:
            return [eligible[0]]

        best_rank = -2
        winners = []
        for player in eligible:
            rank = HandEvaluator.evaluate_hand(player.hand, self.community_cards)
            if rank > best_rank:
                best_rank = rank
                winners = [player]
            elif rank == best_rank:
                winners.append(player)
        if len(winners) == 1:
            return winners
        tie_winners = [winners[0]]
        for player in winners[1:]:
            result = HandEvaluator.hand_comparator(
                player.hand, tie_winners[0].hand, self.community_cards
            )
            if result > 0:
                tie_winners = [player]
            elif result == 0:
                tie_winners.append(player)

        return tie_winners

    def distribute_pots(self):
        side_pots = self.calculate_side_pots()
        for side_pot in side_pots:
            winners = self.get_pot_winners(side_pot)
            if not winners:
                continue

            share = side_pot.amount // len(winners)
            remainder = side_pot.amount % len(winners)

            for winner in winners:
                winner.chips.add_amount(share)
            if remainder > 0:
                all_players_ordered = (
                    self.players[self.dealer_position + 1 :]
                    + self.players[: self.dealer_position + 1]
                )
                for p in all_players_ordered:
                    if p in winners:
                        p.chips.add_amount(remainder)
                        break

    def eliminate_players_with_no_chips(self):
        for player in self.players:
            if player.chips.total_value() < self.big_blind:
                player.is_active = False

    def post_blinds(self):
        small_blind_player_idx = (self.dealer_position + 1) % len(self.players)
        while (
            not self.players[small_blind_player_idx].is_active
            or self.players[small_blind_player_idx].is_folded
        ):
            small_blind_player_idx = (small_blind_player_idx + 1) % len(self.players)

        big_blind_player_idx = (small_blind_player_idx + 1) % len(self.players)
        while (
            not self.players[big_blind_player_idx].is_active
            or self.players[big_blind_player_idx].is_folded
        ):
            big_blind_player_idx = (big_blind_player_idx + 1) % len(self.players)

        small_blind_player = self.players[small_blind_player_idx]
        big_blind_player = self.players[big_blind_player_idx]

        small_blind_player.chips.remove_amount(self.small_blind)
        big_blind_player.chips.remove_amount(self.big_blind)

        small_blind_player.bet_this_round = self.small_blind
        small_blind_player.total_bet_this_hand = self.small_blind
        big_blind_player.bet_this_round = self.big_blind
        big_blind_player.total_bet_this_hand = self.big_blind

        self.pot.add_amount(self.small_blind)
        self.pot.add_amount(self.big_blind)

        self.current_player_idx = big_blind_player_idx
        self.rotate_current_player()
        self.highest_bet = self.big_blind
        self.last_raise = self.big_blind

    def start_new_hand(self):
        if self.game_state != GameState.WAITING:
            raise ValueError("Hand already in progress")
        self.eliminate_players_with_no_chips()
        if len(self.get_active_players()) < 2:
            raise ValueError("Not enough players to start a hand")
        self.rotate_dealer()
        self.clear_table()
        self.post_blinds()
        self.deal_hole_cards()
        self.game_state = GameState.PRE_FLOP

    def get_available_actions(self, player_id: int) -> list[dict]:
        if self.game_state == GameState.WAITING:
            return []
        if self.players[self.current_player_idx].id != player_id:
            return []
        player = self.get_player_by_id(player_id)
        if not player or player.is_folded or player.is_all_in:
            return []
        actions = []
        if player.bet_this_round < self.highest_bet:
            call_amount = self.highest_bet - player.bet_this_round
            if call_amount <= player.chips.total_value():
                actions.append({
                    "action": "call",
                    "min_amount": call_amount,
                    "max_amount": call_amount,
                    "label": f"Call ${call_amount}",
                })
            else:
                pass
            max_possible = player.chips.total_value() + player.bet_this_round
            if max_possible > self.highest_bet:
                min_raise = self.highest_bet + self.last_raise if self.highest_bet > 0 else self.big_blind
                if min_raise <= max_possible:
                    actions.append({
                        "action": "raise",
                        "min_amount": min_raise,
                        "max_amount": max_possible,
                        "label": "Raise",
                    })
            if player.chips.total_value() > 0:
                actions.append({
                    "action": "all-in",
                    "min_amount": player.chips.total_value(),
                    "max_amount": player.chips.total_value(),
                    "label": f"All-in ${player.chips.total_value()}",
                })
            actions.append({
                "action": "fold",
                "min_amount": 0,
                "max_amount": 0,
                "label": "Fold",
            })

        else:
            actions.append({
                "action": "check",
                "min_amount": 0,
                "max_amount": 0,
                "label": "Check",
            })
            max_possible = player.chips.total_value() + player.bet_this_round
            if max_possible > self.highest_bet:
                min_raise = self.highest_bet + self.last_raise if self.highest_bet > 0 else self.big_blind
                if min_raise <= max_possible:
                    actions.append({
                        "action": "raise",
                        "min_amount": min_raise,
                        "max_amount": max_possible,
                        "label": "Raise",
                    })
            if player.chips.total_value() > 0:
                actions.append({
                    "action": "all-in",
                    "min_amount": player.chips.total_value(),
                    "max_amount": player.chips.total_value(),
                    "label": f"All-in ${player.chips.total_value()}",
                })
            actions.append({
                "action": "fold",
                "min_amount": 0,
                "max_amount": 0,
                "label": "Fold",
            })

        return actions

    def process_player_action(self, player_id: int, action: str, amount: int = 0):
        if player_id != self.players[self.current_player_idx].id:
            raise ValueError("It's not this player's turn")
        player = self.get_player_by_id(player_id)
        if not player.is_active or player.is_folded:
            raise ValueError("Player is not active or has folded")

        if action == "fold":
            player.is_folded = True

        elif action == "check":
            if player.bet_this_round < self.highest_bet:
                raise ValueError("Cannot check, must call or raise")

        elif action == "call":
            call_amount = self.highest_bet - player.bet_this_round
            if call_amount > player.chips.total_value():
                raise ValueError("Not enough chips to call")
            player.chips.remove_amount(call_amount)
            player.bet_this_round += call_amount
            player.total_bet_this_hand += call_amount
            self.pot.add_amount(call_amount)

        elif action == "raise":
            if self.highest_bet == 0:
                min_allowed = self.big_blind
            else:
                min_allowed = self.highest_bet + self.last_raise
            if amount < min_allowed:
                raise ValueError(
                    "Raise amount must be greater than current highest bet and last raise"
                )
            if amount > player.chips.total_value() + player.bet_this_round:
                raise ValueError("Not enough chips to raise")
            raise_amount = amount - player.bet_this_round
            player.chips.remove_amount(raise_amount)
            player.bet_this_round += raise_amount
            player.total_bet_this_hand += raise_amount
            self.pot.add_amount(raise_amount)
            self.last_raise = raise_amount
            self.highest_bet = amount

        elif action == "all-in":
            all_in_amount = player.chips.total_value()
            player.chips.remove_amount(all_in_amount)
            player.bet_this_round += all_in_amount
            player.total_bet_this_hand += all_in_amount
            self.pot.add_amount(all_in_amount)
            if player.bet_this_round > self.highest_bet:
                self.last_raise = player.bet_this_round - self.highest_bet
                self.highest_bet = player.bet_this_round
            player.is_all_in = True

        else:
            raise ValueError("Invalid action")

        player.does_have_acted_this_round = True
        if len(self.get_players_in_hand()) == 1:
            self.distribute_pots()
            self.clear_table()
            self.game_state = GameState.WAITING
            return

        active = self.get_active_players()
        all_players_have_acted = all(
            (p.bet_this_round == self.highest_bet and p.does_have_acted_this_round)
            or p.is_folded
            for p in active
        )

        if all_players_have_acted:
            self.advance_game_state()
        else:
            self.rotate_current_player()

    def advance_game_state(self):
        self.current_player_idx = (self.dealer_position + 1) % len(self.players)
        for p in self.players:
            p.does_have_acted_this_round = False
        while (
            not self.players[self.current_player_idx].is_active
            or self.players[self.current_player_idx].is_folded
        ):
            self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

        self.highest_bet = 0
        self.last_raise = 0
        for player in self.players:
            player.bet_this_round = 0

        if self.game_state == GameState.PRE_FLOP:
            self.game_state = GameState.FLOP
            self.community_cards.extend(self.deck.deal_cards(3))

        elif self.game_state == GameState.FLOP:
            self.game_state = GameState.TURN
            self.community_cards.append(self.deck.deal_card())

        elif self.game_state == GameState.TURN:
            self.game_state = GameState.RIVER
            self.community_cards.append(self.deck.deal_card())

        elif self.game_state == GameState.RIVER:
            self.game_state = GameState.SHOWDOWN
            self.distribute_pots()

            for player in self.players:
                player.is_all_in = False
                player.is_folded = False
                player.total_bet_this_hand = 0

            for player in self.players:
                if player.chips.total_value() < self.big_blind:
                    player.is_active = False

            self.game_state = GameState.WAITING

        else:
            raise ValueError(
                f"Cannot advance game state from current state {self.game_state}"
            )

    def clear_table(self):
        self.community_cards = []
        self.deck.reset()
        self.side_pots = []
        for player in self.players:
            player.clear_hand()
            player.bet_this_round = 0
            player.total_bet_this_hand = 0
            player.is_folded = False
            player.does_have_acted_this_round = False
            player.is_all_in = False
        self.highest_bet = 0
        self.last_raise = 0
        self.pot = Chips({chip.value: 0 for chip in self.pot.chips})
