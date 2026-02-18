from base.classes import NormalCard, FirstStrategy, RandomStrategy
from base.sim import run_simulation
from strategies.feluk_normal_strategies import FElixSuper1

# Please, change 'my' to your alias, and 'MyStrategy' to your strategy class name
# Example: 
# from RepSter_Strategy import BogoSorter_Strategy
from my_strategies import MyStrategy1, MyStrategy2

# You might want to change this to test more players
N = 4

# Don't change this function, it's the deck builder.
def build_deck(main_pile, num_decks: int):
    suits = ["hearts", "diamonds", "clubs", "spades"]
    for _ in range(num_decks):
        for value in range(1, 14):
            for suit in suits:
                main_pile.add_card(NormalCard(value, suit))


run_simulation(
    n=N,
    iter_max=int(1e6),
    num_decks=1,
    build_deck=build_deck,
    strategies_to_call = [FElixSuper1] + [FirstStrategy] * (N-1),
)

# Not recommended, as you will always win (if your strategy isn't more random than this)
"""
run_simulation(
    n=N,
    iter_max=int(1e8),
    num_decks=1,
    build_deck=build_deck,
    strategies_to_call = [MyStrategy] + [RandomStrategy] * (N-1),
)
"""