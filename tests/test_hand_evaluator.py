import unittest

from server.game.hand_evaluator import HandEvaluator
from shared.datatypes import Card


def c(rank: int, suit: int) -> Card:
    return Card(rank, suit)


class TestHandEvaluator(unittest.TestCase):
    def test_evaluate_hand_high_card(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(14, 0), c(9, 1)], [c(2, 2), c(5, 3), c(7, 0), c(11, 2), c(13, 1)]
            ),
            -1,
        )

    def test_evaluate_hand_one_pair(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(14, 0), c(14, 1)], [c(2, 2), c(5, 3), c(7, 0), c(11, 2), c(13, 1)]
            ),
            0,
        )

    def test_evaluate_hand_two_pair(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(14, 0), c(14, 1)], [c(2, 2), c(2, 3), c(7, 0), c(11, 2), c(13, 1)]
            ),
            1,
        )

    def test_evaluate_hand_three_of_a_kind(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(14, 0), c(14, 1)], [c(14, 2), c(2, 3), c(7, 0), c(11, 2), c(13, 1)]
            ),
            2,
        )

    def test_evaluate_hand_straight(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(9, 0), c(10, 1)], [c(11, 2), c(12, 3), c(13, 0), c(2, 2), c(7, 1)]
            ),
            3,
        )

    def test_evaluate_hand_flush(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(2, 0), c(9, 0)], [c(4, 0), c(7, 0), c(11, 0), c(3, 1), c(13, 2)]
            ),
            4,
        )

    def test_evaluate_hand_full_house(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(14, 0), c(14, 1)], [c(14, 2), c(2, 3), c(2, 0), c(11, 2), c(13, 1)]
            ),
            5,
        )

    def test_evaluate_hand_full_house_three_and_two_pattern(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(10, 0), c(10, 1)], [c(10, 2), c(4, 3), c(4, 0), c(11, 2), c(13, 1)]
            ),
            5,
        )

    def test_evaluate_hand_four_of_a_kind(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(14, 0), c(14, 1)], [c(14, 2), c(14, 3), c(2, 0), c(11, 2), c(13, 1)]
            ),
            6,
        )

    def test_evaluate_hand_straight_flush(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(9, 0), c(10, 0)], [c(11, 0), c(12, 0), c(13, 0), c(2, 2), c(7, 1)]
            ),
            7,
        )

    def test_evaluate_hand_royal_flush(self):
        self.assertEqual(
            HandEvaluator.evaluate_hand(
                [c(10, 0), c(11, 0)], [c(12, 0), c(13, 0), c(14, 0), c(2, 2), c(7, 1)]
            ),
            8,
        )

    def test_ace_low_straight_is_supported(self):
        cards = [c(14, 0), c(2, 1), c(3, 2), c(4, 3), c(5, 0), c(9, 1), c(11, 2)]
        self.assertTrue(HandEvaluator.is_straight(cards))
        self.assertEqual(HandEvaluator.get_straight_high_card(cards), 5)

    def test_hand_comparator_pair_high_card_breaks_tie(self):
        public_cards = [c(2, 2), c(7, 0), c(9, 1), c(11, 2), c(13, 3)]
        hand1 = [c(14, 0), c(14, 1)]
        hand2 = [c(12, 0), c(12, 1)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_pair_second_kicker_breaks_tie(self):
        public_cards = [c(14, 2), c(13, 0), c(8, 1), c(5, 2), c(2, 3)]
        hand1 = [c(14, 0), c(12, 1)]
        hand2 = [c(14, 3), c(11, 1)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_two_pair_kicker_breaks_tie(self):
        public_cards = [c(14, 2), c(13, 0), c(13, 1), c(9, 2), c(2, 3)]
        hand1 = [c(14, 0), c(12, 1)]
        hand2 = [c(14, 3), c(11, 1)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_three_of_a_kind_kickers_break_tie(self):
        public_cards = [c(2, 2), c(7, 0), c(9, 1), c(11, 2), c(13, 3)]
        hand1 = [c(14, 0), c(14, 1)]
        hand2 = [c(13, 0), c(13, 1)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_full_house_trip_rank_breaks_tie(self):
        public_cards = [c(14, 2), c(14, 3), c(13, 0), c(13, 1), c(2, 3)]
        hand1 = [c(14, 0), c(9, 1)]
        hand2 = [c(13, 2), c(8, 1)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_full_house_pair_rank_breaks_tie(self):
        public_cards = [c(14, 2), c(14, 3), c(13, 0), c(12, 1), c(2, 3)]
        hand1 = [c(14, 0), c(13, 1)]
        hand2 = [c(14, 1), c(12, 0)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_full_house_equal_hands_tie(self):
        public_cards = [c(9, 2), c(9, 3), c(4, 0), c(4, 1), c(2, 3)]
        hand1 = [c(9, 0), c(14, 1)]
        hand2 = [c(9, 1), c(13, 0)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 0)

    def test_hand_comparator_four_of_a_kind_kicker_breaks_tie(self):
        public_cards = [c(14, 2), c(14, 3), c(14, 1), c(14, 0), c(2, 3)]
        hand1 = [c(13, 1), c(9, 0)]
        hand2 = [c(12, 1), c(8, 0)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_straight_flush_equal_high_card_is_tie(self):
        public_cards = [c(10, 0), c(11, 0), c(12, 0), c(13, 0), c(9, 1)]
        hand1 = [c(2, 2), c(3, 3)]
        hand2 = [c(4, 1), c(5, 2)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 0)

    def test_hand_comparator_wheel_straight_beats_lower_straight(self):
        public_cards = [c(2, 1), c(3, 2), c(4, 0), c(5, 3), c(9, 1)]
        hand1 = [c(14, 0), c(8, 1)]
        hand2 = [c(6, 0), c(7, 1)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), -1)

    def test_hand_comparator_wheel_straight_flush_should_lose_to_higher_straight_flush(
        self,
    ):
        public_cards = [c(2, 0), c(3, 0), c(4, 0), c(5, 0), c(9, 2)]
        hand1 = [c(14, 0), c(8, 1)]
        hand2 = [c(6, 0), c(7, 1)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), -1)

    def test_hand_comparator_flush_high_card_breaks_tie(self):
        public_cards = [c(2, 0), c(5, 0), c(7, 0), c(9, 0), c(11, 1)]
        hand1 = [c(14, 0), c(13, 0)]
        hand2 = [c(12, 0), c(10, 0)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_straight_high_card_breaks_tie(self):
        public_cards = [c(2, 1), c(3, 2), c(4, 0), c(5, 3), c(9, 1)]
        hand1 = [c(6, 0), c(14, 1)]
        hand2 = [c(7, 0), c(13, 1)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_royal_flush_always_ties(self):
        public_cards = [c(10, 0), c(11, 0), c(12, 0), c(13, 0), c(14, 0)]
        hand1 = [c(2, 1), c(3, 2)]
        hand2 = [c(4, 1), c(5, 2)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 0)

    def test_hand_comparator_flush_second_card_breaks_tie(self):
        public_cards = [c(14, 0), c(12, 0), c(10, 0), c(5, 0), c(13, 1)]
        hand1 = [c(11, 0), c(9, 0)]
        hand2 = [c(13, 0), c(8, 0)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), -1)

    def test_hand_comparator_flush_third_card_breaks_tie(self):
        public_cards = [c(14, 0), c(13, 0), c(9, 0), c(5, 0), c(12, 1)]
        hand1 = [c(12, 0), c(8, 0)]
        hand2 = [c(11, 0), c(10, 0)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_flush_identical_ranks_tie(self):
        public_cards = [c(14, 0), c(13, 0), c(12, 0), c(11, 0), c(10, 1)]
        hand1 = [c(9, 0), c(8, 0)]
        hand2 = [c(9, 0), c(7, 0)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 0)

    def test_hand_comparator_flush_fifth_card_breaks_tie(self):
        public_cards = [c(14, 0), c(13, 0), c(11, 0), c(9, 0), c(2, 1)]
        hand1 = [c(8, 0), c(7, 1)]
        hand2 = [c(7, 0), c(6, 0)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 1)

    def test_hand_comparator_flush_different_suits_same_ranks_tie(self):
        public_cards = [c(14, 1), c(13, 1), c(12, 1), c(11, 1), c(10, 0)]
        hand1 = [c(9, 0), c(8, 0)]
        hand2 = [c(9, 1), c(8, 1)]

        self.assertEqual(HandEvaluator.hand_comparator(hand1, hand2, public_cards), 0)


if __name__ == "__main__":
    unittest.main()
