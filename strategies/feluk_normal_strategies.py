from sys import maxsize
from base.classes import BaseCard, Strategy


class FElixSuper1(Strategy):
    # Remember, you can always access:
    # - self.player: the player's deck
    # - self.discard_pile: the discard pile
    # - self.player_index: the player's index
    # - self.number_of_players: the number of players
    # - self.all_cards: the deck of all cards
    # - self.num_decks: the number of decks
    # - self.num_cards_per_player: the number of cards each player have
    # - self.cards_not_viewed(): the cards that the player has not seen
    def pick_jump_card(self, top_card: BaseCard, current_player: int, direction: int, value_7: int) -> BaseCard | None:
        jump_cards: list[BaseCard] = [card for card in self.player.cards if card.can_be_jumped(top_card)]
        max: int = 0
        max_card: BaseCard = None
        for card in jump_cards:
            tmp_max = 0
            for hand_card in self.player.cards:
                if hand_card == card:
                    continue
                if hand_card.can_be_played(card):
                    tmp_max += 1
            if card.value == 7 and tmp_max > 0:
                max = maxsize
                max_card = card
            if max < tmp_max:
                max = tmp_max
                max_card = card
        return max_card

    def get_cards_next_player(self, direction:int) -> int:
        return self.num_cards_per_player[(self.player_index + direction) % self.number_of_players]

    def pick_play_card(self, top_card: BaseCard, direction: int, value_7: int) -> BaseCard | bool:
        playable_cards: list[BaseCard] = [[card, 0] for card in self.player.cards if card.can_be_played(top_card)]
        if len(playable_cards) == 0:
            return False
        max: int = 0
        tmp_max: int = 0
        max_card: BaseCard = False
        for i in range(len(playable_cards)):
            for hand_card in self.player.cards:
                if playable_cards[i][0].can_be_played(top_card):
                    playable_cards[i][1] += 1

        playable_cards.sort(key=lambda x: x[1], reverse=True)
        if playable_cards[0][0].value == 7 and top_card.value == 7 and len(playable_cards) != 1:
            playable_cards.pop()
        
        if playable_cards[0][0].value == 10 and self.get_cards_next_player(-direction) == 1 and len(playable_cards) != 1:
            playable_cards.pop()

        if len(playable_cards) == 1 and playable_cards[0][0].value == 7 and value_7 > 5:
            return True

        return playable_cards[0][0]

    def discard_card(self, top_card: BaseCard, current_player: int, direction: int, value_7: int) -> BaseCard:
        playable_cards: list[BaseCard] = [[card, 0, 0] for card in self.player.cards]
        for i, cards in enumerate(playable_cards):
            card1, _, _ = cards
            for card2 in self.player.cards:
                if card1 == card2:
                    playable_cards[i][2] += 1
                if card1.can_be_played(card2):
                    playable_cards[i][1] += 1
        
        playable_cards.sort(key = lambda x: (x[2], x[1]), reverse=True)
        return playable_cards.pop()[0]
                    
