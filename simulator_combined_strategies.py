from base.classes import NormalCard
from base.logger import get_elapsed_logger
from base.sim import run_simulation
from all_strategies import strategies
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import combinations
import json
import multiprocessing
import os
import time


ITER_PER_SIM = int(1e7)
NUM_DECKS = 2

wins = {strategy.__name__: 0 for strategy in strategies}


def build_deck(main_pile, num_decks: int):
    suits = ["hearts", "diamonds", "clubs", "spades"]
    for _ in range(num_decks):
        for value in range(1, 14):
            for suit in suits:
                main_pile.add_card(NormalCard(value, suit))


def _run_matchup_worker(
    combo_names: tuple[str, ...],
    iters: int,
    num_decks: int,
) -> tuple[tuple[str, ...], list[int]]:
    """Worker subprocess: runs one matchup simulation and returns (combo_names, maos)."""
    from all_strategies import strategies as _all_strategies

    strategy_map = {s.__name__: s for s in _all_strategies}
    combination = tuple(strategy_map[name] for name in combo_names)
    n = len(combination)

    run_simulation(
        n=n,
        iter_max=iters,
        num_decks=num_decks,
        build_deck=build_deck,
        strategies_to_call=combination,
        log_ignores_wrong_cards=True,
        random_first_player=True,
        random_position_players=True,
    )

    json_name = f"simulator_combined_strategies_{n}_{num_decks}_{'_'.join(combo_names)}.json"
    try:
        with open(json_name, "r") as f:
            data = json.load(f)
        maos = data["maos"]
    finally:
        if os.path.exists(json_name):
            os.remove(json_name)

    return combo_names, maos


if __name__ == "__main__":
    t0 = time.perf_counter()
    log = get_elapsed_logger(t0, "Results.txt", results=True, debugging=False, name="simulator_combined_strategies")

    matchups: list[tuple[str, ...]] = []
    for i in range(2, len(strategies) + 1):
        for combination in combinations(strategies, i):
            matchups.append(tuple(strategy.__name__ for strategy in combination))

    num_workers = multiprocessing.cpu_count() or 8
    log.log(25, f"Running {len(matchups)} matchups with {num_workers} workers")

    with ProcessPoolExecutor(
        max_workers=num_workers,
        mp_context=multiprocessing.get_context("fork"),
    ) as executor:
        future_to_names = {
            executor.submit(
                _run_matchup_worker,
                combo_names,
                ITER_PER_SIM,
                NUM_DECKS,
            ): combo_names
            for combo_names in matchups
        }

        for future in as_completed(future_to_names):
            combo_names, maos = future.result()
            names = list(combo_names)
            max_maos = max(enumerate(maos), key=lambda x: x[1])[0]
            wins[names[max_maos]] += 1
            log.log(25, f"Simulated combination: {' vs '.join(names)}")
            log.log(25, f"Maos: {maos}")
            log.log(25, f"Strategy {names[max_maos]} has won the most games with {maos[max_maos]} games, congratulations!")

    log.log(25, "FINAL RESULTS:")
    for strategy, win_count in sorted(wins.items(), key=lambda x: x[1], reverse=True):
        log.log(25, f"{strategy}: {win_count}")