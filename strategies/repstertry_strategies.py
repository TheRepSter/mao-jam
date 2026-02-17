from base.classes import BaseCard, Strategy

# Tengo 0 idea de si funciona lol, lo hago ahora para testing.
class Idea_Strategy(Strategy):
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
        if top_card.value == 7: # Peor escenario, roba una vez. Ya es mejor que el resto de veces. 
            if top_card in self.player.cards:
                return top_card
            else:
                return None
        else:
            if top_card in self.player.cards:
                for card in self.player.cards:
                    if card != top_card and card.can_be_played(top_card):
                        return top_card
                return None

    def pick_play_card(self, top_card: BaseCard, direction: int) -> BaseCard | bool:
        for card in self.player.cards:
            if card.can_be_played(top_card):
                return card
        return False

    def discard_card(self, top_card: BaseCard, current_player: int, direction: int) -> BaseCard:
        return self.player.cards[0]
