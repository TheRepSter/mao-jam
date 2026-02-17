from base.classes import BaseCard, Strategy

class MyStrategy1(Strategy):
    # Remember, you can always access:
    # - self.player: the player's deck
    # - self.discard_pile: the discard pile
    # - self.player_index: the player's index
    # - self.number_of_players: the number of players
    # - self.all_cards: the deck of all cards
    # - self.num_decks: the number of decks
    # - self.num_cards_per_player: the number of cards each player have
    # - self.cards_not_viewed(): the cards that the player has not seen
    def pick_jump_card(self, top_card: BaseCard, current_player: int, direction: int) -> BaseCard | None:
        return None

    def pick_play_card(self, top_card: BaseCard, direction: int) -> BaseCard | bool:
        return None

    def discard_card(self, top_card: BaseCard, current_player: int, direction: int) -> BaseCard:
        return None