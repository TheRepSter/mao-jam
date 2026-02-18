from collections import Counter

from base.classes import BaseCard, Strategy

class ArnauStrategy(Strategy):
    """
    A strategy that uses card counting and probabilities to make decisions.
    - Prioritizes changing to its strongest suit.
    - Plays disruptive cards when forced to stay in suit.
    - Avoids playing 7s, especially on another 7.
    - Jumps only if a disruptive combo play is possible.
    - Discards the least flexible cards.
    """

    def _get_unseen_counts(self):
        """Helper to count suits and values of cards not seen by the player."""
        unseen_cards = self.cards_not_viewed()
        unseen_suit_counts = Counter(c.suit for c in unseen_cards.cards)
        unseen_value_counts = Counter(c.value for c in unseen_cards.cards)
        return unseen_suit_counts, unseen_value_counts

    def pick_play_card(
        self, top_card: BaseCard, direction: int, value_7: int
    ) -> BaseCard | bool:
        """
        Picks a card to play based on a probabilistic model.
        Avoids playing 7s, especially on another 7 (value_7 > 0).
        If it can change the suit (value match), it switches to the suit it has the most of.
        If it must stay in suit (suit match), it plays the card with the rarest value among unseen cards to disrupt opponents.
        If no other option, plays a 7, avoiding the double penalty if possible.
        If no card is playable, draws a card.
        """
        playable_non_sevens = [
            card
            for card in self.player.cards
            if card.value != 7 and card.can_be_played(top_card)
        ]

        if playable_non_sevens:
            value_matches = [
                card for card in playable_non_sevens if card.value == top_card.value
            ]
            suit_matches = [
                card for card in playable_non_sevens if card.suit == top_card.suit
            ]

            if value_matches:
                hand_suit_counts = Counter(c.suit for c in self.player.cards)
                best_card = max(
                    value_matches, key=lambda card: hand_suit_counts[card.suit]
                )
                return best_card

            if suit_matches:
                _, unseen_value_counts = self._get_unseen_counts()
                best_card = min(
                    suit_matches, key=lambda card: unseen_value_counts[card.value]
                )
                return best_card

        playable_sevens = [
            card
            for card in self.player.cards
            if card.value == 7 and card.can_be_played(top_card)
        ]

        if playable_sevens:
            if value_7 > 0:
                return True
            return playable_sevens[0]

        return False

    def pick_jump_card(
        self, top_card: BaseCard, current_player: int, direction: int, value_7: int
    ) -> BaseCard | None:
        """
        Jumps only if there is a follow-up card that can be played.
        Tries to jump if it enables a disruptive follow-up play for the next player.
        The "best" combo is the one where the follow-up card is rarest among unseen cards, therefore making the next player unable to play a card.
        """
        possible_combos: BaseCard | None = None
        for jump_card in self.player.cards:
            if not jump_card.can_be_jumped(top_card):
                continue
            remaining_cards = [c for c in self.player.cards if c != jump_card]
            for follow_up_card in remaining_cards:
                if not follow_up_card.can_be_played(jump_card):
                    continue
                if follow_up_card.value != 7:
                    possible_combos = jump_card

        return possible_combos

    def discard_card(
        self, top_card: BaseCard, current_player: int, direction: int, value_7: int
    ) -> BaseCard:
        """
        Discards the "least flexible" card in hand.
        Prioritizes discarding 7s.
        Flexibility is measured by how many other cards of the same suit or value are currently in the player's hand. A lower score means less flexible.
        """
        sevens = [card for card in self.player.cards if card.value == 7]
        if sevens:
            return sevens[0]

        hand_suit_counts = Counter(c.suit for c in self.player.cards)
        hand_value_counts = Counter(c.value for c in self.player.cards)

        least_flexible_card = None
        min_score = float("inf")

        for card in self.player.cards:
            score = hand_suit_counts[card.suit] + hand_value_counts[card.value] - 2
            if score < min_score:
                min_score = score
                least_flexible_card = card

        return least_flexible_card or self.player.cards[0]
