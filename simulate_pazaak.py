"""
Pazaak: The Kobayashi Maru of Star Wars

Script: simulate_pazaak.py
Author: Sebastian Böker

Monte Carlo simulator for a simplified version of KOTOR Pazaak.

The simulator models:

    - infinite main deck
    - uniformly distributed card values from 1 to 10
    - no side-deck cards
    - alternating turns
    - Player 1 always acts first
    - closest total to 20 wins

Several decision policies are implemented:

    - Threshold strategy
    - Safe-probability strategy
    - Recursive dynamic-programming response strategy

The simulator was used to establish a theoretical baseline for turn-order
effects before analyzing real gameplay recordings.

Related report sections:
    - Simplified Simulation Rules
    - Strategies Tested
    - Current Results
    - Interpretation
"""

import random
from functools import lru_cache
from collections import Counter

from player import Player
from result import Result
from stats import Stats


Strategy = callable


def draw_card() -> int:
    """Draw one card from the simplified infinite main deck."""
    return random.randint(1, 10)


def stand_ev(total: int, opponent_total: int) -> float:
    """
    Return the expected value of standing against an opponent total.

    Values:
        1.0 -> win
        0.5 -> draw
        0.0 -> loss
    """
    if total > opponent_total:
        return 1.0

    if total == opponent_total:
        return 0.5

    return 0.0


@lru_cache(maxsize=None)
def best_ev(my_total: int, opponent_total: int) -> float:
    """
    Compute the optimal expected value for the current player.

    This recursive dynamic-programming function assumes that the opponent
    has already stood. The current player may either stand immediately or
    draw another card.

    Since all draw probabilities are known exactly, the value can be computed
    directly instead of learned through reinforcement learning.
    """
    if my_total > 20:
        return 0.0

    stand = stand_ev(my_total, opponent_total)

    draw = 0.0
    for card in range(1, 11):
        draw += best_ev(my_total + card, opponent_total)
    draw /= 10.0

    return max(stand, draw)


@lru_cache(maxsize=None)
def best_action(my_total: int, opponent_total: int) -> str:
    """
    Return the optimal action against a standing opponent.

    The returned action is either "draw" or "stand".
    """
    stand = stand_ev(my_total, opponent_total)

    draw = 0.0
    for card in range(1, 11):
        draw += best_ev(my_total + card, opponent_total)
    draw /= 10.0

    return "draw" if draw > stand else "stand"


def threshold_17_strategy(player: Player, opponent: Player) -> str:
    """Draw until reaching at least 17, then stand."""
    return "draw" if player.total < 17 else "stand"


def safe_probability_strategy(player: Player, opponent: Player) -> str:
    """
    Draw if the probability of not busting is at least 50%.

    This strategy maximizes short-term survival probability, but not
    necessarily win probability.
    """
    safe_cards = max(0, 20 - player.total)
    p_safe = min(safe_cards, 10) / 10.0

    return "draw" if p_safe >= 0.5 else "stand"


def recursive_response_strategy(player: Player, opponent: Player) -> str:
    """
    Use dynamic programming once the opponent has stood.

    Before the opponent stands, the strategy falls back to the threshold-17
    rule because the opponent's final total is not yet known.
    """
    if opponent.stood:
        return best_action(player.total, opponent.total)

    return threshold_17_strategy(player, opponent)


def player_turn(player: Player, opponent: Player, strategy, stats: Stats) -> None:
    """Execute one player's turn according to the selected strategy."""
    if player.stood or player.bust:
        return

    decision = strategy(player, opponent)

    if decision == "stand":
        player.stood = True
        stats.record_stand(player.name, player.total)
        return

    card = draw_card()
    player.total += card
    stats.record_draw(player.name, card, player.total)

    if player.total > 20:
        player.bust = True
        stats.record_bust(player.name)


def round_finished(player_1: Player, player_2: Player) -> bool:
    """Return True if the round has reached a terminal state."""
    return (
        player_1.bust
        or player_2.bust
        or (player_1.stood and player_2.stood)
    )


def evaluate(player_1: Player, player_2: Player) -> Result:
    """Evaluate the final round outcome."""
    if player_1.bust and player_2.bust:
        return Result.DRAW

    if player_1.bust:
        return Result.PLAYER2

    if player_2.bust:
        return Result.PLAYER1

    if player_1.total > player_2.total:
        return Result.PLAYER1

    if player_2.total > player_1.total:
        return Result.PLAYER2

    return Result.DRAW


def play_round(p1_strategy, p2_strategy, stats: Stats, debug: bool = False) -> Result:
    """
    Simulate one simplified Pazaak round.

    Player 1 always acts first, mirroring the structural asymmetry of KOTOR 1
    Pazaak.
    """
    player_1 = Player("P1")
    player_2 = Player("P2")

    while True:
        player_turn(player_1, player_2, p1_strategy, stats)

        if debug:
            print(
                f"P1 total={player_1.total} "
                f"stood={player_1.stood} bust={player_1.bust}"
            )

        if round_finished(player_1, player_2):
            break

        player_turn(player_2, player_1, p2_strategy, stats)

        if debug:
            print(
                f"P2 total={player_2.total} "
                f"stood={player_2.stood} bust={player_2.bust}"
            )

        if round_finished(player_1, player_2):
            break

    if not player_1.bust:
        stats.record_final_total("P1", player_1.total)

    if not player_2.bust:
        stats.record_final_total("P2", player_2.total)

    return evaluate(player_1, player_2)


def simulate(n_rounds: int, p1_strategy, p2_strategy, label: str = "") -> None:
    """
    Run a Monte Carlo simulation and print summary statistics.
    """
    results = {
        Result.PLAYER1: 0,
        Result.PLAYER2: 0,
        Result.DRAW: 0,
    }

    stats = Stats()

    for _ in range(n_rounds):
        result = play_round(p1_strategy, p2_strategy, stats)
        results[result] += 1

    p1_win_rate = results[Result.PLAYER1] / n_rounds
    p2_win_rate = results[Result.PLAYER2] / n_rounds
    draw_rate = results[Result.DRAW] / n_rounds

    decisive_total = p1_win_rate + p2_win_rate
    p1_decisive = p1_win_rate / decisive_total if decisive_total else 0
    p2_decisive = p2_win_rate / decisive_total if decisive_total else 0

    print_simulation_summary(
        label,
        p1_win_rate,
        p2_win_rate,
        draw_rate,
        p1_decisive,
        p2_decisive,
        stats,
    )


def mean(values: list[int]) -> float:
    """Return the arithmetic mean of a list of values."""
    return sum(values) / len(values) if values else float("nan")


def print_card_distribution(draws: list[int]) -> None:
    """Print card-value frequencies for values 1 through 10."""
    counts = Counter(draws)
    total = len(draws)

    for card in range(1, 11):
        percentage = counts[card] / total if total else 0
        print(f"    {card}: {counts[card]:>8}  {percentage:.3%}")


def print_total_distribution(totals: list[int]) -> None:
    """Print total-score distribution for scores between 0 and 20."""
    counts = Counter(totals)
    total = len(totals)

    for score in range(0, 21):
        if counts[score]:
            percentage = counts[score] / total if total else 0
            print(f"    {score:>2}: {counts[score]:>8}  {percentage:.3%}")


def print_simulation_summary(
    label: str,
    p1_win_rate: float,
    p2_win_rate: float,
    draw_rate: float,
    p1_decisive: float,
    p2_decisive: float,
    stats: Stats,
) -> None:
    """Print all simulation results and diagnostic statistics."""
    print(f"\n{label}")
    print(f"P1 wins        : {p1_win_rate:.3%}")
    print(f"P2 wins        : {p2_win_rate:.3%}")
    print(f"Draws          : {draw_rate:.3%}")
    print(f"P1 decisive    : {p1_decisive:.3%}")
    print(f"P2 decisive    : {p2_decisive:.3%}")

    print("\nDraw statistics")
    print(f"P1 draw count  : {len(stats.draws['P1'])}")
    print(f"P2 draw count  : {len(stats.draws['P2'])}")
    print(f"P1 mean draw   : {mean(stats.draws['P1']):.3f}")
    print(f"P2 mean draw   : {mean(stats.draws['P2']):.3f}")

    print("\nBusts")
    print(f"P1 busts       : {stats.busts['P1']}")
    print(f"P2 busts       : {stats.busts['P2']}")

    print("\nNatural 20s")
    print(f"P1 natural 20s : {stats.natural_20s['P1']}")
    print(f"P2 natural 20s : {stats.natural_20s['P2']}")

    print("\nP1 card distribution")
    print_card_distribution(stats.draws["P1"])

    print("\nP2 card distribution")
    print_card_distribution(stats.draws["P2"])

    print("\nStand totals")
    print(f"P1 stand count : {len(stats.stand_totals['P1'])}")
    print(f"P2 stand count : {len(stats.stand_totals['P2'])}")
    print(f"P1 mean stand  : {mean(stats.stand_totals['P1']):.3f}")
    print(f"P2 mean stand  : {mean(stats.stand_totals['P2']):.3f}")

    print("\nP1 stand total distribution")
    print_total_distribution(stats.stand_totals["P1"])

    print("\nP2 stand total distribution")
    print_total_distribution(stats.stand_totals["P2"])

    print("\nFinal surviving totals")
    print(f"P1 final count : {len(stats.final_totals['P1'])}")
    print(f"P2 final count : {len(stats.final_totals['P2'])}")
    print(f"P1 mean final  : {mean(stats.final_totals['P1']):.3f}")
    print(f"P2 mean final  : {mean(stats.final_totals['P2']):.3f}")

    print("\nP1 final total distribution")
    print_total_distribution(stats.final_totals["P1"])

    print("\nP2 final total distribution")
    print_total_distribution(stats.final_totals["P2"])


def main() -> None:
    """Run the default simulation experiments."""
    n_rounds = 1_000_000

    simulate(
        n_rounds,
        threshold_17_strategy,
        threshold_17_strategy,
        "Threshold 17 vs Threshold 17",
    )

    # Additional strategy comparisons used during development:
    #
    # simulate(
    #     n_rounds,
    #     safe_probability_strategy,
    #     safe_probability_strategy,
    #     "Safe probability vs Safe probability",
    # )
    #
    # simulate(
    #     n_rounds,
    #     recursive_response_strategy,
    #     recursive_response_strategy,
    #     "Recursive response vs Recursive response",
    # )
    #
    # simulate(
    #     n_rounds,
    #     threshold_17_strategy,
    #     recursive_response_strategy,
    #     "P1 threshold vs P2 recursive",
    # )
    #
    # simulate(
    #     n_rounds,
    #     recursive_response_strategy,
    #     threshold_17_strategy,
    #     "P1 recursive vs P2 threshold",
    # )


if __name__ == "__main__":
    main()