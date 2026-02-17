from base.classes import NormalCard
from base.logger import get_elapsed_logger
from base.sim import run_simulation
from all_strategies import strategies
from itertools import combinations
import json
import time
t0 = time.perf_counter()
log = get_elapsed_logger(t0, "Results.txt", results=True, debugging=False, name="simulator_combined_strategies")
file = open("Results.txt", "w")

def build_deck(main_pile, num_decks: int):
    suits = ["hearts", "diamonds", "clubs", "spades"]
    for _ in range(num_decks):
        for value in range(1, 14):
            for suit in suits:
                main_pile.add_card(NormalCard(value, suit))

for i in range(2, len(strategies) + 1):
    for combination in combinations(strategies, i):
        run_simulation(
            n=i,
            iter_max=int(1e3),
            num_decks=2,
            build_deck=build_deck,
            strategies_to_call=combination,
            ignore_wrong_cards=True
        )
        names = [strategy.__name__ for strategy in combination]
        file.write(f"Simulated combination: {' vs '.join(names)}\n")
        with open(f"simulator_combined_strategies_{i}_2_{'_'.join(names)}.json", "r") as f:
            combination_data = json.load(f)
            maos = combination_data["maos"]
            file.write(f"Maos: {maos}\n")
            max_maos = max(enumerate(maos), key=lambda x: x[1])[0]
            file.write(f"Strategy {names[max_maos]} has won the most games with {maos[max_maos]} games, congratulations!\n")
            file.flush()
            print(f"Simulated combination: {' vs '.join(names)}")
            print(f"Maos: {maos}")
            print(f"Strategy {names[max_maos]} has won the most games with {maos[max_maos]} games, congratulations!")
file.close()
