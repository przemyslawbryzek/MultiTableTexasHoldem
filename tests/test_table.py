import unittest
from unittest.mock import patch, MagicMock
from collections import deque

from shared.enums import GameState
from shared.datatypes import Player, Card, Chips
from server.game.table import Table

STARTING_CHIPS = {1000: 0, 500: 0, 100: 0, 50: 0, 25: 0, 10: 0, 5: 0, 1: 3000}
BIG_BLIND = 20


def make_player(pid: int, name: str, chips: dict = None) -> Player:
    return Player(pid, name, chips or STARTING_CHIPS)


def make_table(*players: Player) -> Table:
    table = Table(players[0], STARTING_CHIPS, BIG_BLIND)
    for p in players[1:]:
        table.add_player(p)
    return table


def patch_deck(table: Table, cards: list[Card]) -> None:
    q = deque(cards)

    def deal_card():
        return q.popleft() if q else Card(2, 0)

    def deal_cards(n):
        return [deal_card() for _ in range(n)]

    table.deck.deal_card = deal_card
    table.deck.deal_cards = deal_cards


def c(rank: int, suit: int) -> Card:
    return Card(rank, suit)


def total_chips(*players: Player) -> int:
    return sum(p.chips.total_value() for p in players)


class TestTableSetup(unittest.TestCase):
    def test_initial_state(self):
        alice = make_player(0, "Alice")
        table = Table(alice, STARTING_CHIPS, BIG_BLIND)
        self.assertEqual(table.game_state, GameState.WAITING)
        self.assertEqual(table.big_blind, 20)
        self.assertEqual(table.small_blind, 10)
        self.assertEqual(len(table.players), 1)

    def test_add_players(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        self.assertEqual(len(table.players), 2)

    def test_cannot_add_player_during_game(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        carol = make_player(2, "Carol")
        table = make_table(alice, bob)
        table.game_state = GameState.PRE_FLOP
        with self.assertRaises(ValueError):
            table.add_player(carol)

    def test_table_full_at_9(self):
        players = [make_player(i, f"P{i}") for i in range(9)]
        table = make_table(*players)
        extra = make_player(9, "Extra")
        with self.assertRaises(ValueError):
            table.add_player(extra)


class TestBlinds(unittest.TestCase):

    def test_blinds_deducted_from_players(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)

        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        chips_after = total_chips(alice, bob)
        self.assertEqual(chips_after, 3000 * 2 - 30)

    def test_pot_equals_blinds(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        self.assertEqual(table.pot.total_value(), 30)

    def test_state_is_preflop_after_start(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        self.assertEqual(table.game_state, GameState.PRE_FLOP)

    def test_each_player_has_2_hole_cards(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        self.assertEqual(len(alice.hand), 2)
        self.assertEqual(len(bob.hand), 2)


class TestFoldWins(unittest.TestCase):

    def test_fold_preflop_winner_gets_pot(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        acting_player = table.players[table.current_player_idx]
        table.process_player_action(acting_player.id, "fold")

        self.assertEqual(table.game_state, GameState.WAITING)
        non_folder = alice if acting_player == bob else bob
        self.assertGreater(non_folder.chips.total_value(), 3000 - 30)

    def test_total_chips_conserved_after_fold(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        patch_deck(table, [c(2, 0)] * 20)

        initial_total = total_chips(alice, bob)
        table.start_new_hand()

        acting = table.players[table.current_player_idx]
        table.process_player_action(acting.id, "fold")

        self.assertEqual(total_chips(alice, bob), initial_total)


class TestFullHandShowdown(unittest.TestCase):

    def _run_full_hand_to_showdown(self, alice_cards, bob_cards, community):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)

        deck_cards = (
            [
                alice_cards[0],
                bob_cards[0],
                alice_cards[1],
                bob_cards[1],
            ]
            + community
            + [c(2, 0)] * 10
        )

        patch_deck(table, deck_cards)
        table.start_new_hand()

        def act_current(action, amount=0):
            pid = table.players[table.current_player_idx].id
            table.process_player_action(pid, action, amount)

        act_current("call")
        act_current("check")

        self.assertEqual(table.game_state, GameState.FLOP)
        act_current("check")
        act_current("check")

        self.assertEqual(table.game_state, GameState.TURN)
        act_current("check")
        act_current("check")

        self.assertEqual(table.game_state, GameState.RIVER)
        act_current("check")
        act_current("check")

        self.assertEqual(table.game_state, GameState.WAITING)
        return alice, bob, table

    def test_royal_flush_beats_straight(self):

        alice_cards = [c(14, 0), c(13, 0)]
        bob_cards = [c(9, 2), c(8, 2)]
        community = [c(10, 0), c(11, 0), c(12, 0), c(2, 2), c(3, 1)]

        alice, bob, table = self._run_full_hand_to_showdown(
            alice_cards, bob_cards, community
        )

        self.assertGreater(alice.chips.total_value(), 3000)
        self.assertLess(bob.chips.total_value(), 3000)

    def test_total_chips_conserved_at_showdown(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        initial_total = total_chips(alice, bob)

        alice_cards = [c(14, 0), c(13, 0)]
        bob_cards = [c(9, 2), c(8, 2)]
        community = [c(10, 0), c(11, 0), c(12, 0), c(2, 2), c(3, 1)]

        alice, bob, _ = self._run_full_hand_to_showdown(
            alice_cards, bob_cards, community
        )
        self.assertEqual(total_chips(alice, bob), initial_total)

    def test_high_card_wins(self):
        alice_cards = [c(14, 0), c(2, 2)]
        bob_cards = [c(13, 1), c(3, 3)]
        community = [c(5, 0), c(7, 2), c(9, 1), c(11, 0), c(4, 3)]

        alice, bob, _ = self._run_full_hand_to_showdown(
            alice_cards, bob_cards, community
        )
        self.assertGreater(alice.chips.total_value(), bob.chips.total_value())


class TestBettingMechanics(unittest.TestCase):

    def setUp(self):
        self.alice = make_player(0, "Alice")
        self.bob = make_player(1, "Bob")
        self.carol = make_player(2, "Carol")
        self.table = make_table(self.alice, self.bob, self.carol)
        patch_deck(self.table, [c(2, 0)] * 30)
        self.table.start_new_hand()

    def _current_pid(self):
        return self.table.players[self.table.current_player_idx].id

    def test_cannot_act_out_of_turn(self):
        acting = self._current_pid()
        wrong = next(p.id for p in self.table.players if p.id != acting)
        with self.assertRaises(ValueError):
            self.table.process_player_action(wrong, "fold")

    def test_cannot_check_when_bet_exists(self):
        pid = self._current_pid()
        with self.assertRaises(ValueError):
            self.table.process_player_action(pid, "check")

    def test_raise_below_minimum_rejected(self):
        pid = self._current_pid()
        with self.assertRaises(ValueError):
            self.table.process_player_action(pid, "raise", 30)

    def test_call_reduces_chips_correctly(self):
        pid = self._current_pid()
        player = self.table.get_player_by_id(pid)
        chips_before = player.chips.total_value()

        self.table.process_player_action(pid, "call")
        self.assertEqual(player.chips.total_value(), chips_before - 20)

    def test_raise_updates_highest_bet(self):
        pid = self._current_pid()
        self.table.process_player_action(pid, "raise", 100)
        self.assertEqual(self.table.highest_bet, 100)

    def test_pot_grows_with_bets(self):
        self.assertEqual(self.table.pot.total_value(), 30)

        pid = self._current_pid()
        self.table.process_player_action(pid, "call")
        self.assertEqual(self.table.pot.total_value(), 50)


class TestThreePlayerHand(unittest.TestCase):

    def test_two_folds_winner_gets_pot(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        carol = make_player(2, "Carol")
        table = make_table(alice, bob, carol)
        patch_deck(table, [c(2, 0)] * 30)
        initial_total = total_chips(alice, bob, carol)
        table.start_new_hand()

        pid = table.players[table.current_player_idx].id
        table.process_player_action(pid, "fold")

        pid = table.players[table.current_player_idx].id
        table.process_player_action(pid, "fold")
        self.assertEqual(table.game_state, GameState.WAITING)
        self.assertEqual(total_chips(alice, bob, carol), initial_total)

    def test_chips_conserved_three_players_full_hand(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        carol = make_player(2, "Carol")
        table = make_table(alice, bob, carol)

        alice_cards = [c(14, 0), c(13, 0)]
        bob_cards = [c(9, 2), c(8, 2)]
        carol_cards = [c(5, 1), c(4, 3)]
        community = [c(10, 0), c(11, 0), c(12, 0), c(2, 2), c(3, 1)]

        deck_cards = (
            [
                alice_cards[0],
                bob_cards[0],
                carol_cards[0],
                alice_cards[1],
                bob_cards[1],
                carol_cards[1],
            ]
            + community
            + [c(2, 0)] * 10
        )

        patch_deck(table, deck_cards)
        initial_total = total_chips(alice, bob, carol)
        table.start_new_hand()

        def act():
            pid = table.players[table.current_player_idx].id
            table.process_player_action(pid, "call")

        act()
        act()
        act()

        for _ in range(9):
            pid = table.players[table.current_player_idx].id
            table.process_player_action(pid, "check")

        self.assertEqual(table.game_state, GameState.WAITING)
        self.assertEqual(total_chips(alice, bob, carol), initial_total)


class TestSidePots(unittest.TestCase):

    def test_side_pot_calculation_two_all_ins(self):
        alice = make_player(0, "Alice", {100: 1})
        bob = make_player(1, "Bob", {100: 3})
        carol = make_player(2, "Carol", {500: 1})

        table = make_table(alice, bob, carol)
        table.big_blind = 10
        table.small_blind = 5

        alice.total_bet_this_hand = 100
        alice.is_all_in = True
        bob.total_bet_this_hand = 300
        bob.is_all_in = True
        carol.total_bet_this_hand = 500

        alice.is_folded = False
        bob.is_folded = False
        carol.is_folded = False

        pots = table.calculate_side_pots()
        amounts = [p.amount for p in pots]
        total = sum(amounts)

        self.assertEqual(total, 900)

        self.assertEqual(pots[0].amount, 300)
        self.assertIn(alice, pots[0].eligible_players)
        self.assertIn(bob, pots[0].eligible_players)
        self.assertIn(carol, pots[0].eligible_players)

        self.assertEqual(pots[1].amount, 400)
        self.assertNotIn(alice, pots[1].eligible_players)
        self.assertIn(bob, pots[1].eligible_players)
        self.assertIn(carol, pots[1].eligible_players)

        self.assertEqual(pots[2].amount, 200)
        self.assertNotIn(alice, pots[2].eligible_players)
        self.assertNotIn(bob, pots[2].eligible_players)
        self.assertIn(carol, pots[2].eligible_players)

    def test_all_in_player_cannot_win_more_than_eligible(self):
        alice = make_player(0, "Alice", {100: 1})
        bob = make_player(1, "Bob")
        carol = make_player(2, "Carol")
        table = make_table(alice, bob, carol)

        alice.hand = [c(14, 0), c(13, 0)]
        bob.hand = [c(9, 2), c(8, 2)]
        carol.hand = [c(5, 1), c(4, 3)]
        table.community_cards = [c(10, 0), c(11, 0), c(12, 0), c(2, 2), c(3, 1)]

        alice.total_bet_this_hand = 100
        alice.is_all_in = True
        bob.total_bet_this_hand = 300
        carol.total_bet_this_hand = 300

        alice.chips.remove_amount(100)
        bob.chips.remove_amount(300)
        carol.chips.remove_amount(300)

        table.distribute_pots()

        self.assertEqual(alice.chips.total_value(), 300)
        self.assertEqual(
            bob.chips.total_value() + carol.chips.total_value(), 2700 + 2700 + 400
        )

    def test_chips_conserved_with_side_pots(self):
        alice = make_player(0, "Alice", {100: 1})
        bob = make_player(1, "Bob")
        carol = make_player(2, "Carol")

        initial_total = (
            alice.chips.total_value()
            + bob.chips.total_value()
            + carol.chips.total_value()
        )

        alice.hand = [c(14, 0), c(13, 0)]
        bob.hand = [c(9, 2), c(8, 2)]
        carol.hand = [c(5, 1), c(4, 3)]

        table = make_table(alice, bob, carol)
        table.community_cards = [c(10, 0), c(11, 0), c(12, 0), c(2, 2), c(3, 1)]

        alice.total_bet_this_hand = 100
        alice.is_all_in = True
        bob.total_bet_this_hand = 300
        carol.total_bet_this_hand = 300

        alice.chips.remove_amount(100)
        bob.chips.remove_amount(300)
        carol.chips.remove_amount(300)

        table.distribute_pots()

        final_total = (
            alice.chips.total_value()
            + bob.chips.total_value()
            + carol.chips.total_value()
        )

        self.assertEqual(initial_total, final_total)

    def test_folded_player_not_eligible_for_any_pot(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        carol = make_player(2, "Carol")
        table = make_table(alice, bob, carol)

        alice.total_bet_this_hand = 100
        alice.is_folded = True
        bob.total_bet_this_hand = 100
        carol.total_bet_this_hand = 100

        pots = table.calculate_side_pots()
        for pot in pots:
            self.assertNotIn(alice, pot.eligible_players)


class TestMultipleHands(unittest.TestCase):

    def test_dealer_rotates_between_hands(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)

        for hand_num in range(3):
            patch_deck(table, [c(2, 0)] * 20)
            table.start_new_hand()
            dealer_before = table.dealer_position

            pid = table.players[table.current_player_idx].id
            table.process_player_action(pid, "fold")

            self.assertEqual(table.game_state, GameState.WAITING)

    def test_chips_conserved_over_multiple_hands(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        initial_total = total_chips(alice, bob)

        for _ in range(5):
            if not table.can_start(alice, bob):
                break
            patch_deck(table, [c(2, 0)] * 20)
            table.start_new_hand()
            pid = table.players[table.current_player_idx].id
            table.process_player_action(pid, "fold")

        self.assertEqual(total_chips(alice, bob), initial_total)

    def can_start(self, *players):
        return sum(1 for p in players if p.chips.total_value() > 0) >= 2

    def test_player_eliminated_when_no_chips(self):
        alice = make_player(0, "Alice", {1: 3000})
        bob = make_player(1, "Bob", {1: 10})
        table = make_table(alice, bob)
        patch_deck(table, [c(2, 0)] * 20)
        with self.assertRaises(ValueError):
            table.start_new_hand()


class TestEdgeCases(unittest.TestCase):

    def test_cannot_start_with_one_player(self):
        alice = make_player(0, "Alice")
        table = Table(alice, STARTING_CHIPS, BIG_BLIND)
        with self.assertRaises(ValueError):
            table.start_new_hand()

    def test_cannot_start_hand_during_hand(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        with self.assertRaises(ValueError):
            table.start_new_hand()

    def test_community_cards_cleared_between_hands(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)

        alice_cards = [c(14, 0), c(13, 0)]
        bob_cards = [c(9, 2), c(8, 2)]
        community = [c(10, 0), c(11, 0), c(12, 0), c(2, 2), c(3, 1)]
        deck_cards = (
            [
                alice_cards[0],
                bob_cards[0],
                alice_cards[1],
                bob_cards[1],
            ]
            + community
            + [c(2, 0)] * 10
        )
        patch_deck(table, deck_cards)
        table.start_new_hand()

        def act():
            pid = table.players[table.current_player_idx].id
            table.process_player_action(pid, "call")

        act()
        act()  # Pre-flop
        for _ in range(6):
            pid = table.players[table.current_player_idx].id
            table.process_player_action(pid, "check")

        self.assertEqual(table.game_state, GameState.WAITING)

        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()
        self.assertEqual(len(table.community_cards), 0)

    def test_hole_cards_cleared_between_hands(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        pid = table.players[table.current_player_idx].id
        table.process_player_action(pid, "fold")

        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        self.assertEqual(len(alice.hand), 2)
        self.assertEqual(len(bob.hand), 2)

    def test_pot_cleared_between_hands(self):
        alice = make_player(0, "Alice")
        bob = make_player(1, "Bob")
        table = make_table(alice, bob)
        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        pid = table.players[table.current_player_idx].id
        table.process_player_action(pid, "fold")

        patch_deck(table, [c(2, 0)] * 20)
        table.start_new_hand()

        self.assertEqual(table.pot.total_value(), 30)

    def test_all_in_cannot_be_asked_to_act(self):
        alice = make_player(0, "Alice", {1: 25})
        bob = make_player(1, "Bob")
        carol = make_player(2, "Carol")
        table = make_table(alice, bob, carol)
        patch_deck(table, [c(2, 0)] * 30)
        table.start_new_hand()

        if table.players[table.current_player_idx].id == alice.id:
            table.process_player_action(alice.id, "all-in")

        current = table.players[table.current_player_idx]
        if alice.is_all_in:
            self.assertNotEqual(current.id, alice.id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
