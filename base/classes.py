from __future__ import annotations

from abc import ABC, abstractmethod
from random import choice, shuffle
from typing import Callable


class BaseCard(ABC):
    def __init__(self, value: int, suit: str):
        self.value = value
        self.suit = suit

    def __str__(self) -> str:
        return f"{self.value} of {self.suit}"

    def __repr__(self) -> str:
        return f"Card('{self.value}', '{self.suit}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseCard):
            return NotImplemented
        return self.value == other.value and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.value, self.suit))

    @abstractmethod
    def can_be_played(self, other: BaseCard) -> bool:
        """Return whether this card can be played on top of other."""

    @abstractmethod
    def can_be_jumped(self, other: BaseCard) -> bool:
        """Return whether this card can jump (cut in) over other."""

class NormalCard(BaseCard):
    def can_be_played(self, other: NormalCard) -> bool:
        return self.value == other.value or self.suit == other.suit

    def can_be_jumped(self, other: NormalCard) -> bool:
        return self.value == other.value and self.suit == other.suit

class Deck:
    def __init__(self):
        self.cards: list[BaseCard] = []

    def add_card(self, card: BaseCard) -> None:
        self.cards.append(card)

    def remove_card(self, card: BaseCard) -> BaseCard:
        try:
            self.cards.remove(card)
            return card
        except ValueError:
            raise ValueError(f"Card {card} not found in deck")

    def remove_top_card(self) -> BaseCard:
        return self.cards.pop()

    def __repr__(self) -> str:
        return f"Deck({self.cards})"

    def __str__(self) -> str:
        return f"Deck({self.cards})"

    def __len__(self) -> int:
        return len(self.cards)

    def shuffle(self) -> None:
        shuffle(self.cards)

class Strategy(ABC):
    def __init__(
        self,
        player: Deck,
        discard_pile: Deck,
        player_index: int,
        number_of_players: int,
        build_deck: Callable[[Deck, int], None],
        num_decks: int,
        num_cards_per_player: list[int]
    ) -> None:
        """Base strategy class used to implement different player behaviours."""
        self.player: Deck = player
        self.player_index: int = player_index
        self.number_of_players: int = number_of_players
        self.discarded_pile: Deck = discard_pile
        self.num_cards_per_player: list[int] = num_cards_per_player
        self.all_cards: Deck = Deck()
        self.build_deck: Callable[[Deck, int], None] = build_deck
        self.num_decks: int = num_decks
        self.build_deck(self.all_cards, self.num_decks)

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"
    
    def cards_not_viewed(self) -> Deck:
        """Return the cards that the player has not seen. Notice this means the player hand is also not viewed."""
        not_viewed = Deck()
        cards_viewed = Deck()
        cards_viewed.cards = self.player.cards + self.discarded_pile.cards
        for card in self.all_cards.cards:
            if card not in cards_viewed.cards:
                not_viewed.add_card(card)
            else:
                cards_viewed.remove_card(card) # Es treu per que hi han repetits en cas de que sigui més d'un deck
        return not_viewed

    @abstractmethod
    def pick_jump_card(
        self,
        top_card: BaseCard,
        current_player: int,
        direction: int,
        value_7: int,
    ) -> BaseCard | None:
        """Return the jump card to play, or None if no jump is played."""

    @abstractmethod
    def pick_play_card(self, top_card: BaseCard, direction: int, value_7: int) -> BaseCard | bool:
        """Return the regular card to play.

        Return False if none is playable, True if the player wants to skip the turn.
        """
    
    @abstractmethod
    def discard_card(
        self,
        top_card: BaseCard,
        current_player: int,
        direction: int,
        value_7: int,
    ) -> BaseCard:
        """Return the card to discard."""

class RandomStrategy(Strategy):
    def pick_jump_card(
        self,
        top_card: BaseCard,
        current_player: int,
        direction: int,
        value_7: int,
    ) -> BaseCard | None:
        return choice(self.player.cards)

    def pick_play_card(self, top_card: BaseCard, direction: int, value_7: int) -> BaseCard | bool:
        return choice(self.player.cards)

    def discard_card(
        self,
        top_card: BaseCard,
        current_player: int,
        direction: int,
        value_7: int,
    ) -> BaseCard:
        return choice(self.player.cards)

class FirstStrategy(Strategy):
    def pick_jump_card(
        self,
        top_card: BaseCard,
        current_player: int,
        direction: int,
        value_7: int,
    ) -> BaseCard | None:
        for card in self.player.cards:
            if card.can_be_jumped(top_card):
                return card
        return None

    def pick_play_card(self, top_card: BaseCard, direction: int, value_7: int) -> BaseCard | bool:
        for card in self.player.cards:
            if card.can_be_played(top_card):
                return card
        return False

    def discard_card(
        self,
        top_card: BaseCard,
        current_player: int,
        direction: int,
        value_7: int,
    ) -> BaseCard:
        return self.player.cards[0]