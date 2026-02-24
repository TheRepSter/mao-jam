from base.classes import NormalCard
from base.logger import get_elapsed_logger
from base.sim import run_simulation
from all_strategies import strategies
from concurrent.futures import ProcessPoolExecutor, as_completed
from scipy.stats import chisquare, binomtest
import numpy as np
from itertools import combinations
import json
import multiprocessing
import os
import time


ITER_PER_SIM = int(1e4)
MAX_ITER_PER_SIM = int(1e7)
MAX_EXTRA_ROUNDS = 100
P_VALUE_THRESHOLD = 0.05
NUM_DECKS = 2

wins = {strategy.__name__: 0 for strategy in strategies}


def _check_significance(maos: list[int]) -> tuple[bool, float, float, float]:
    """Returns (is_significant, p_bond, p_without_worst, p_best_vs_second)."""
    maos_np = np.array(maos)
    n_players = len(maos)
    total = maos_np.sum()
    expected = np.full(n_players, total / n_players)
    _, p_bond = chisquare(maos_np, expected)

    sorted_indices = np.argsort(maos)
    worst = sorted_indices[0]
    best = sorted_indices[-1]
    second_best = sorted_indices[-2]

    if n_players > 2:
        maos_np_without_worst = np.delete(maos_np, worst)
        total_without_worst = maos_np_without_worst.sum()
        expected_without_worst = np.full(n_players - 1, total_without_worst / (n_players - 1))
        _, p_without_worst = chisquare(maos_np_without_worst, expected_without_worst)
        without_worst_ok = p_without_worst <= P_VALUE_THRESHOLD
    else:
        p_without_worst = float("nan")  # not applicable for 2 players
        without_worst_ok = True

    test = binomtest(int(maos[best]), int(maos[best]) + int(maos[second_best]), alternative="two-sided")
    p_best_vs_second = test.pvalue

    is_significant = p_bond <= P_VALUE_THRESHOLD and without_worst_ok and p_best_vs_second <= P_VALUE_THRESHOLD
    return is_significant, p_bond, p_without_worst, p_best_vs_second


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
) -> tuple[tuple[str, ...], list[int], int]:
    """Worker subprocess: runs one matchup simulation, retrying with extra iterations
    until the result is statistically significant or MAX_EXTRA_ROUNDS is reached.
    Returns (combo_names, accumulated_maos, extra_rounds_run)."""
    from all_strategies import strategies as _all_strategies

    strategy_map = {s.__name__: s for s in _all_strategies}
    combination = tuple(strategy_map[name] for name in combo_names)
    n = len(combination)
    json_name = f"simulator_combined_strategies_{n}_{num_decks}_{'_'.join(combo_names)}.json"

    def _run_and_read(iter_count: int) -> list[int]:
        run_simulation(
            n=n,
            iter_max=iter_count,
            num_decks=num_decks,
            build_deck=build_deck,
            strategies_to_call=combination,
            log_ignores_wrong_cards=True,
            random_first_player=True,
            random_position_players=True,
        )
        try:
            with open(json_name, "r") as f:
                data = json.load(f)
            return data["maos"]
        finally:
            if os.path.exists(json_name):
                os.remove(json_name)

    accumulated_maos = _run_and_read(iters)

    extra_rounds = 0
    while not _check_significance(accumulated_maos)[0] and extra_rounds < MAX_EXTRA_ROUNDS:
        proposed_iterations = min((2 ** extra_rounds) * ITER_PER_SIM, MAX_ITER_PER_SIM)
        log.log(25, f"Extra round with {proposed_iterations:.4g} iterations for combination: {' vs '.join(combo_names)}. p-values: {_check_significance(accumulated_maos)[1:]} for bond, without worst, best vs second. Maos: {accumulated_maos}")
        extra_maos = _run_and_read(proposed_iterations)
        extra_rounds += 1
        accumulated_maos = [a + e for a, e in zip(accumulated_maos, extra_maos)]

    return combo_names, accumulated_maos, extra_rounds


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
            combo_names, maos, extra_rounds = future.result()
            names = list(combo_names)
            sorted_indices = np.argsort(maos)
            max_maos = sorted_indices[-1]
            worst_maos = sorted_indices[0]
            wins[names[max_maos]] += 1

            is_significant, p_bond, p_without_worst, p_best_vs_second = _check_significance(maos)
            total_iters = ITER_PER_SIM + sum(min((2 ** r) * ITER_PER_SIM, MAX_ITER_PER_SIM) for r in range(extra_rounds))

            log.log(25, f"Simulated combination: {' vs '.join(names)}")
            log.log(25, f"Maos: {maos} (total iters: {total_iters:,}, extra rounds: {extra_rounds})")
            if not is_significant:
                log.warning(
                    f"Strategy {names[max_maos]} has won the most games with {maos[max_maos]} games "
                    f"after {extra_rounds} extra round(s), BUT IT'S STILL NOT SIGNIFICANTLY DIFFERENT "
                    f"(cap of {MAX_EXTRA_ROUNDS} extra rounds reached). "
                    f"P-values — bond: {p_bond:.4f}, without worst: {p_without_worst:.4f}, best vs second: {p_best_vs_second:.4f}"
                )
            else:
                extra_note = f" (needed {extra_rounds} extra round(s), {total_iters:,} iters total)" if extra_rounds > 0 else ""
                log.log(25, f"Strategy {names[max_maos]} has won the most games with {maos[max_maos]} games, congratulations!{extra_note}")
    log.log(25, "FINAL RESULTS:")
    for strategy, win_count in sorted(wins.items(), key=lambda x: x[1], reverse=True):
        log.log(25, f"{strategy}: {win_count}")