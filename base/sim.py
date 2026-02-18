import __main__
import json
import os
import random
import signal
import time
from typing import Callable

from base.classes import BaseCard, Deck, Strategy
from base.logger import get_elapsed_logger

ENSURE_PILE_LENGTH: bool = True


def _load_state(log, filepath: str, num_players: int) -> tuple[dict[int, list[int]], list[list[int]], list[int], list[int]]:
    if not os.path.exists(filepath):
        log.warning(f"File {filepath} does not exist")
        return {}, [], [0 for _ in range(num_players)], []
    with open(filepath, "r") as f:
        data = json.load(f)

    cards_prob_raw = data.get("dict_cartes_prob", {})
    cards_prob: dict[int, list[int]] = {int(k): v for k, v in cards_prob_raw.items()}
    pauses = data.get("pauses", [])
    maos = data.get("maos", [0 for _ in range(num_players)])
    iter_partides = data.get("iter_partides", [])
    return cards_prob, pauses, maos, iter_partides


def _save_state(
    filepath: str,
    cards_prob: dict[int, list[int]],
    pauses: list[list[int]],
    maos: list[int],
    iter_partides: list[int],
) -> None:
    with open(filepath, "w") as f:
        json.dump(
            {
                "dict_cartes_prob": cards_prob,
                "pauses": pauses,
                "maos": maos,
                "iter_partides": iter_partides,
            },
            f,
        )


def _print_final_stats(
    log,
    cards_prob: dict[int, list[int]],
    pauses: list[list[int]],
    maos: list[int],
    iter_partides: list[int],
    num_players: int,
) -> None:
    string_prob = "Final probabilities:\n"
    _, maximo_mostra, _ = max(cards_prob.values(), key=lambda x: x[1])
    _, _, maximo_picades = max(cards_prob.values(), key=lambda x: x[2])
    cartes_mostrades = 0
    all_mostres = 0
    for prob in sorted(cards_prob.keys()):
        total_mostra = cards_prob[prob][1]
        cartes_mostrades += prob * total_mostra
        all_mostres += total_mostra
        prob_jugable = cards_prob[prob][0] / total_mostra if total_mostra else 0.0
        string_prob += (
            f"\tAmb {prob:2d} cartes: {prob_jugable:.8f} "
            f"amb {cards_prob[prob][2]:{len(str(maximo_picades))}d} picades (mostra {total_mostra:{len(str(maximo_mostra))}d})\n"
        )
    log.info(string_prob)
    log.info(f"Mitjana de cartes: {cartes_mostrades / all_mostres}")

    if pauses:
        sum_pauses = [0 for _ in range(num_players)]
        for pause in pauses:
            for i in range(num_players):
                sum_pauses[i] += pause[i]
        for i in range(num_players):
            sum_pauses[i] /= len(pauses)
        log.info(f"Mitjanes de cartes per jugadors en pauses: {sum_pauses}")
        log.info(f"Mitjanes de cartes en pausa: {sum(sum_pauses) / num_players}")
        log.info(f"Mitjana de pauses per partida: {len(pauses)/sum(maos)}")

    log.info(f"MAOS per jugadors: {maos}")
    log.info(f"Mitjanes de iteracions per partida: {sum(iter_partides) / len(iter_partides)}")

def pausa(
    log,
    iter_number: int,
    n: int,
    players: list[Deck],
    strategies: list[Strategy],
    top_card: BaseCard,
    discard_pile: Deck,
    main_pile: Deck,
    current_player: int,
    direction: int,
    pauses: list[list[int]],
    num_cards_per_player: list[int],
    value_7: int,
) -> tuple[Deck, Deck]:
    log.debug(f"Iter {iter_number}: Entrem a la pausa!")
    to_append = num_cards_per_player.copy()
    for i in range(n):
        while num_cards_per_player[i] > 5:
            card_to_discard = strategies[i].discard_card(top_card, current_player, direction, value_7)
            main_pile.add_card(card_to_discard) # canvi de discard_pile a main_pile per fer que no tinguin extra info de descartar la resta.
            players[i].remove_card(card_to_discard)
            num_cards_per_player[i] -= 1
            log.debug(f"Player {i} ha descartat {str(card_to_discard)}")
    while len(main_pile) > 0:
        discard_pile.add_card(main_pile.remove_top_card())
    discard_pile.shuffle()
    pauses.append(to_append)
    return main_pile, discard_pile

def run_simulation(
    *,
    n: int,
    iter_max: int,
    num_decks: int,
    build_deck: Callable[[Deck, int], None],
    strategies_to_call: list[type[Strategy]],
    log_ignores_wrong_cards: bool = False,
    random_first_player: bool = False,
    random_position_players: bool = False,
) -> None:
    debug_mode = iter_max == 1
    t0 = time.perf_counter()
    if n == 1:
        log = get_elapsed_logger(t0, "stupid.log", debugging=debug_mode, name=__name__)
        log.critical(f"Only one player. Maybe you are stupid.")
        return
    if strategies_to_call and all(st is strategies_to_call[0] for st in strategies_to_call):
        strategy_name = strategies_to_call[0].__name__
    else:
        strategy_name = "_".join(st.__name__ for st in strategies_to_call)
    filename = f"{__main__.__file__.split('.')[0].split('/')[-1]}_{n}_{num_decks}_{strategy_name}"
    log = get_elapsed_logger(t0, filename + ".log", debugging=debug_mode, name=__name__)
    cards_prob, pauses, maos, iter_partides = _load_state(log, filename + ".json", n)

    num_cards_per_player = [0 for _ in range(n)]
    main_pile = Deck()
    discard_pile = Deck()
    players: list[Deck] = [Deck() for _ in range(n)]
    strategies: list[Strategy] = [
        strategy(player, discard_pile, i, n, build_deck, num_decks, num_cards_per_player)
        for i, (player, strategy) in enumerate(zip(players, strategies_to_call))
    ]

    build_deck(main_pile, num_decks)
    original_pile_length = len(main_pile)

    iter_number = 0
    num_avis = min(int(iter_max / 10), 1_000_000) if not debug_mode else 1
    won_last_time = 0
    player_indexes = list(range(n))
    seat_to_player_id = list(range(n))
    stop_after_current_game = False

    def _handle_sigint(_signum, _frame):
        nonlocal stop_after_current_game
        if not stop_after_current_game:
            stop_after_current_game = True
            log.warning("Ctrl+C received. Finishing current game before stopping...")
        else:
            log.warning("Stop already requested. Waiting for current game to finish...")

    previous_sigint_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, _handle_sigint)

    try:
        while iter_number < iter_max:
            main_pile.shuffle()

            for _ in range(3):
                for i in range(n):
                    players[i].add_card(main_pile.remove_top_card())
                    num_cards_per_player[i] += 1
            top_card = main_pile.remove_top_card()
            has_winner = False
            if random_first_player:
                current_player = random.randint(0, n-1) # Could have some "first player" advantage.
            else:
                current_player = 0
            direction = 1
            value_7 = 0
            log.debug(f"Top card: {top_card}")

            while not has_winner:
                if iter_number % num_avis == 0 and not debug_mode:
                    elapsed = time.perf_counter() - t0
                    time_per_iter = iter_number / elapsed if elapsed else 0.0
                    log.info(
                        f"Iter {iter_number}! Queden "
                        f"{iter_max - iter_number if iter_max - iter_number > 0 else 0} iteracions! "
                        f"({time_per_iter:.6e} iter/s)",
                    )

                iter_number += 1
                if (
                    ENSURE_PILE_LENGTH
                    and len(main_pile)
                    + len(discard_pile)
                    + sum(len(player) for player in players)
                    + 1
                    != original_pile_length
                ):
                    log.critical(
                        f"Iter {iter_number} S'ha creat o borrat materia? "
                        f"{len(main_pile) + len(discard_pile) + sum(len(player) for player in players) + 1} "
                        f"vs og {original_pile_length}"
                    )
                    iter_number = iter_max
                    break

                current_hand_size = num_cards_per_player[current_player]
                current_prob = cards_prob.setdefault(current_hand_size, [0, 0, 0])
                current_prob[1] += 1

                strategy = strategies[current_player]
                played_card = strategy.pick_play_card(top_card, direction, value_7)
                if type(played_card) is not bool:
                    if not played_card.can_be_played(top_card):
                        (log.debug if log_ignores_wrong_cards else log.error)(
                            f"Iter {iter_number}: Player {current_player} ha jugat malament! "
                            f"{str(played_card)} no pot jugar! "
                            f"({current_hand_size} -> {current_hand_size + 1})",
                        )
                        players[current_player].add_card(main_pile.remove_top_card())
                        num_cards_per_player[current_player] += 1
                        if len(main_pile) == 0:
                            discard_pile, main_pile = pausa(log, iter_number, n, players, strategies, top_card, discard_pile, main_pile, current_player, direction, pauses, num_cards_per_player, value_7)
                        continue
                        
                    current_prob[0] += 1
                    players[current_player].remove_card(played_card)
                    num_cards_per_player[current_player] -= 1
                    log.debug(f"Iter {iter_number}: Player {current_player} ha jugat {str(played_card)} ({current_hand_size} -> {current_hand_size - 1})")
                    discard_pile.add_card(top_card)
                    top_card = played_card
                    if top_card.value == 10:
                        direction *= -1
                    if top_card.value == 7:
                        value_7 += 1
                        for _ in range(value_7):
                            players[current_player].add_card(main_pile.remove_top_card())
                            num_cards_per_player[current_player] += 1
                            if len(main_pile) == 0:
                                break  # entrara en pausa automaticament
                        log.debug(
                            f"Iter {iter_number}: Player {current_player} ha robat per tirar el 7 "
                            f"({current_hand_size - 1} -> {current_hand_size - 1 + value_7})",
                        )
                    else:
                        value_7 = 0
                else:
                    players[current_player].add_card(main_pile.remove_top_card())
                    num_cards_per_player[current_player] += 1
                    if played_card is True:
                        current_prob[0] += 1
                    log.debug(f"Iter {iter_number}: Player {current_player} ha robat ({current_hand_size} -> {current_hand_size + 1})")

                if num_cards_per_player[current_player] == 0:
                    has_winner = True
                    log.debug(f"Iter {iter_number}: Player {current_player} diu mao!")
                    break

                current_player = (current_player + direction) % n

                if len(main_pile) == 0:
                    discard_pile, main_pile = pausa(log, iter_number, n, players, strategies, top_card, discard_pile, main_pile, current_player, direction, pauses, num_cards_per_player, value_7)

                random.shuffle(player_indexes)
                for i in player_indexes:
                    jump_card = strategies[i].pick_jump_card(top_card, current_player, direction, value_7)
                    if jump_card is not None:
                        jump_hand_size = num_cards_per_player[i]
                        if not jump_card.can_be_jumped(top_card):
                            (log.debug if log_ignores_wrong_cards else log.error)(
                                f"Iter {iter_number}: Player {i} ha saltat malament! "
                                f"{str(jump_card)} no pot saltar! "
                                f"({jump_hand_size} -> {jump_hand_size + 1})",
                            )
                            players[i].add_card(main_pile.remove_top_card())
                            num_cards_per_player[i] += 1
                            if len(main_pile) == 0:
                                discard_pile, main_pile = pausa(log, iter_number, n, players, strategies, top_card, discard_pile, main_pile, current_player, direction, pauses, num_cards_per_player, value_7)
                            continue
                        num_cards_per_player[i] -= 1
                        log.debug(f"Iter {iter_number}: Player {i} ha saltat amb {str(jump_card)} ({jump_hand_size} -> {jump_hand_size - 1})")
                        jump_prob = cards_prob.setdefault(jump_hand_size, [0, 0, 0])
                        jump_prob[2] += 1
                        players[i].remove_card(jump_card)
                        discard_pile.add_card(top_card)
                        top_card = jump_card
                        current_player = i
                        if len(players[i]) == 0:
                            has_winner = True
                            log.debug(f"Iter {iter_number}: Player {i} diu mao!")
                        break

            winner_player_id = seat_to_player_id[current_player]
            maos[winner_player_id] += 1
            iter_partides.append(iter_number - won_last_time)
            won_last_time = iter_number
            for i in range(n):
                while num_cards_per_player[i] > 0:
                    num_cards_per_player[i] -= 1
                    main_pile.add_card(players[i].remove_top_card())
            while len(discard_pile):
                main_pile.add_card(discard_pile.remove_top_card())
            main_pile.add_card(top_card)

            if random_position_players:
                shuffled_positions = list(zip(players, strategies, seat_to_player_id))
                random.shuffle(shuffled_positions)
                players, strategies, seat_to_player_id = map(list, zip(*shuffled_positions))
                for i, strategy in enumerate(strategies):
                    strategy.player_index = i

            if stop_after_current_game:
                break
    finally:
        signal.signal(signal.SIGINT, previous_sigint_handler)

    _print_final_stats(log, cards_prob, pauses, maos, iter_partides, n)
    _save_state(filename + ".json", cards_prob, pauses, maos, iter_partides)
