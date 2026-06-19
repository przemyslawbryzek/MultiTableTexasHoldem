from shared.datatypes import Card


class HandEvaluator:
    # HAND RANKS (return values):
    # -1: High Card
    #  0: One Pair
    #  1: Two Pair
    #  2: Three of a Kind
    #  3: Straight
    #  4: Flush
    #  5: Full House
    #  6: Four of a Kind
    #  7: Straight Flush
    #  8: Royal Flush
    @staticmethod
    def evaluate_hand(player_cards: list[Card], community_cards: list[Card]) -> int:
        cards = player_cards + community_cards
        if HandEvaluator.is_royal_flush(cards):
            return 8
        elif HandEvaluator.is_straight_flush(cards):
            return 7
        elif HandEvaluator.is_four_of_a_kind(cards):
            return 6
        elif HandEvaluator.is_full_house(cards):
            return 5
        elif HandEvaluator.is_flush(cards):
            return 4
        elif HandEvaluator.is_straight(cards):
            return 3
        elif HandEvaluator.is_three_of_a_kind(cards):
            return 2
        elif HandEvaluator.is_two_pair(cards):
            return 1
        elif HandEvaluator.is_one_pair(cards):
            return 0
        return -1  # High Card

    @staticmethod
    def hand_comparator(
        hand1: list[Card], hand2: list[Card], public_cards: list[Card]
    ) -> int:
        # return 1 if hand1 wins, -1 if hand2 wins, 0 if tie used for tie-breaking when both hands have the same rank
        cards1 = hand1 + public_cards
        cards2 = hand2 + public_cards
        if HandEvaluator.is_royal_flush(cards1):
            return 0
        elif HandEvaluator.is_straight_flush(cards1):
            if HandEvaluator.get_straight_flush_high_card(
                cards1
            ) > HandEvaluator.get_straight_flush_high_card(cards2):
                return 1
            elif HandEvaluator.get_straight_flush_high_card(
                cards1
            ) < HandEvaluator.get_straight_flush_high_card(cards2):
                return -1
            return 0
        elif HandEvaluator.is_four_of_a_kind(cards1):
            if HandEvaluator.get_four_of_a_kind_rank(
                cards1
            ) > HandEvaluator.get_four_of_a_kind_rank(cards2):
                return 1
            elif HandEvaluator.get_four_of_a_kind_rank(
                cards1
            ) < HandEvaluator.get_four_of_a_kind_rank(cards2):
                return -1
            elif max(
                card.rank
                for card in cards1
                if card.rank != HandEvaluator.get_four_of_a_kind_rank(cards1)
            ) > max(
                card.rank
                for card in cards2
                if card.rank != HandEvaluator.get_four_of_a_kind_rank(cards2)
            ):
                return 1
            elif max(
                card.rank
                for card in cards1
                if card.rank != HandEvaluator.get_four_of_a_kind_rank(cards1)
            ) < max(
                card.rank
                for card in cards2
                if card.rank != HandEvaluator.get_four_of_a_kind_rank(cards2)
            ):
                return -1
            return 0
        elif HandEvaluator.is_full_house(cards1):
            if HandEvaluator.get_three_of_a_kind_rank(
                cards1
            ) > HandEvaluator.get_three_of_a_kind_rank(cards2):
                return 1
            elif HandEvaluator.get_three_of_a_kind_rank(
                cards1
            ) < HandEvaluator.get_three_of_a_kind_rank(cards2):
                return -1
            elif HandEvaluator.get_full_house_pair_rank(
                cards1
            ) > HandEvaluator.get_full_house_pair_rank(cards2):
                return 1
            elif HandEvaluator.get_full_house_pair_rank(
                cards1
            ) < HandEvaluator.get_full_house_pair_rank(cards2):
                return -1
            return 0
        elif HandEvaluator.is_flush(cards1):
            if HandEvaluator.get_flush_ranks(cards1) > HandEvaluator.get_flush_ranks(
                cards2
            ):
                return 1
            elif HandEvaluator.get_flush_ranks(cards1) < HandEvaluator.get_flush_ranks(
                cards2
            ):
                return -1
            return 0
        elif HandEvaluator.is_straight(cards1):
            if HandEvaluator.get_straight_high_card(
                cards1
            ) > HandEvaluator.get_straight_high_card(cards2):
                return 1
            elif HandEvaluator.get_straight_high_card(
                cards1
            ) < HandEvaluator.get_straight_high_card(cards2):
                return -1
            return 0
        elif HandEvaluator.is_three_of_a_kind(cards1):
            if HandEvaluator.get_three_of_a_kind_rank(
                cards1
            ) > HandEvaluator.get_three_of_a_kind_rank(cards2):
                return 1
            elif HandEvaluator.get_three_of_a_kind_rank(
                cards1
            ) < HandEvaluator.get_three_of_a_kind_rank(cards2):
                return -1
            cards1_kickers = sorted(
                (
                    card.rank
                    for card in cards1
                    if card.rank != HandEvaluator.get_three_of_a_kind_rank(cards1)
                ),
                reverse=True,
            )[:2]
            cards2_kickers = sorted(
                (
                    card.rank
                    for card in cards2
                    if card.rank != HandEvaluator.get_three_of_a_kind_rank(cards2)
                ),
                reverse=True,
            )[:2]
            if cards1_kickers > cards2_kickers:
                return 1
            elif cards1_kickers < cards2_kickers:
                return -1
            return 0
        elif HandEvaluator.is_two_pair(cards1):
            if HandEvaluator.get_two_pair_ranks(
                cards1
            ) > HandEvaluator.get_two_pair_ranks(cards2):
                return 1
            elif HandEvaluator.get_two_pair_ranks(
                cards1
            ) < HandEvaluator.get_two_pair_ranks(cards2):
                return -1
            cards1_kicker = max(
                card.rank
                for card in cards1
                if card.rank not in HandEvaluator.get_two_pair_ranks(cards1)
            )
            cards2_kicker = max(
                card.rank
                for card in cards2
                if card.rank not in HandEvaluator.get_two_pair_ranks(cards2)
            )
            if cards1_kicker > cards2_kicker:
                return 1
            elif cards1_kicker < cards2_kicker:
                return -1
            return 0
        elif HandEvaluator.is_one_pair(cards1):
            if HandEvaluator.get_one_pair_rank(
                cards1
            ) > HandEvaluator.get_one_pair_rank(cards2):
                return 1
            elif HandEvaluator.get_one_pair_rank(
                cards1
            ) < HandEvaluator.get_one_pair_rank(cards2):
                return -1
            cards1_kickers = sorted(
                (
                    card.rank
                    for card in cards1
                    if card.rank != HandEvaluator.get_one_pair_rank(cards1)
                ),
                reverse=True,
            )[:3]
            cards2_kickers = sorted(
                (
                    card.rank
                    for card in cards2
                    if card.rank != HandEvaluator.get_one_pair_rank(cards2)
                ),
                reverse=True,
            )[:3]
            if cards1_kickers > cards2_kickers:
                return 1
            elif cards1_kickers < cards2_kickers:
                return -1
            return 0
        elif max(card.rank for card in cards1) > max(card.rank for card in cards2):
            return 1
        elif max(card.rank for card in cards1) < max(card.rank for card in cards2):
            return -1
        return 0

    @staticmethod
    def is_royal_flush(cards: list[Card]) -> bool:
        royal_ranks = {10, 11, 12, 13, 14}
        for suit in range(4):
            suit_cards = [card for card in cards if card.suit == suit]
            suit_ranks = {card.rank for card in suit_cards}
            if royal_ranks.issubset(suit_ranks):
                return True
        return False

    @staticmethod
    def is_straight_flush(cards: list[Card]) -> bool:
        for suit in range(4):
            suit_cards = [card for card in cards if card.suit == suit]
            if HandEvaluator.is_straight(suit_cards):
                return True
        return False

    @staticmethod
    def is_four_of_a_kind(cards: list[Card]) -> bool:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        return 4 in rank_counts.values()

    @staticmethod
    def is_full_house(cards: list[Card]) -> bool:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        return 3 in rank_counts.values() and 2 in rank_counts.values()

    @staticmethod
    def is_flush(cards: list[Card]) -> bool:
        suit_counts = {}
        for card in cards:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
        return any(count >= 5 for count in suit_counts.values())

    @staticmethod
    def is_straight(cards: list[Card]) -> bool:
        ranks = {card.rank for card in cards}
        for start in range(2, 11):
            if all(rank in ranks for rank in range(start, start + 5)):
                return True
        # Check for Ace-low straight (A-2-3-4-5)
        return all(rank in ranks for rank in [14, 2, 3, 4, 5])

    @staticmethod
    def is_three_of_a_kind(cards: list[Card]) -> bool:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        return 3 in rank_counts.values()

    @staticmethod
    def is_two_pair(cards: list[Card]) -> bool:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        pairs = [rank for rank, count in rank_counts.items() if count >= 2]
        return len(pairs) >= 2

    @staticmethod
    def is_one_pair(cards: list[Card]) -> bool:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        return any(count >= 2 for count in rank_counts.values())

    @staticmethod
    def get_straight_flush_high_card(cards: list[Card]) -> int:
        for suit in range(4):
            suit_cards = [card for card in cards if card.suit == suit]
            if HandEvaluator.is_straight(suit_cards):
                return HandEvaluator.get_straight_high_card(suit_cards)
        return 0

    @staticmethod
    def get_four_of_a_kind_rank(cards: list[Card]) -> int:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        for rank, count in rank_counts.items():
            if count == 4:
                return rank
        return 0

    @staticmethod
    def get_flush_high_card(cards: list[Card]) -> int:
        flush_ranks = HandEvaluator.get_flush_ranks(cards)
        if flush_ranks:
            return flush_ranks[0]
        return 0

    @staticmethod
    def get_flush_ranks(cards: list[Card]) -> list[int]:
        suit_counts = {}
        for card in cards:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1
        for suit, count in suit_counts.items():
            if count >= 5:
                return sorted(
                    (card.rank for card in cards if card.suit == suit), reverse=True
                )[:5]
        return []

    @staticmethod
    def get_straight_high_card(cards: list[Card]) -> int:
        ranks = {card.rank for card in cards}
        for start in range(10, 1, -1):
            if all(rank in ranks for rank in range(start, start + 5)):
                return start + 4
        # Check for Ace-low straight (A-2-3-4-5)
        if all(rank in ranks for rank in [14, 2, 3, 4, 5]):
            return 5
        return 0

    @staticmethod
    def get_three_of_a_kind_rank(cards: list[Card]) -> int:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        for rank, count in rank_counts.items():
            if count == 3:
                return rank
        return 0

    @staticmethod
    def get_two_pair_ranks(cards: list[Card]) -> list[int]:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        pairs = [rank for rank, count in rank_counts.items() if count >= 2]
        return sorted(pairs, reverse=True)[:2]

    @staticmethod
    def get_full_house_pair_rank(cards: list[Card]) -> int:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        trip_rank = HandEvaluator.get_three_of_a_kind_rank(cards)
        pair_ranks = [
            rank
            for rank, count in rank_counts.items()
            if rank != trip_rank and count >= 2
        ]
        if pair_ranks:
            return max(pair_ranks)
        return 0

    @staticmethod
    def get_one_pair_rank(cards: list[Card]) -> int:
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        for rank, count in rank_counts.items():
            if count >= 2:
                return rank
        return 0
