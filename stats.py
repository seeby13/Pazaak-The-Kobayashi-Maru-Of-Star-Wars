"""
Pazaak: The Kobayashi Maru of Star Wars

Script: simulate_sequence_baseline.py
Author: Sebastian Böker

Monte Carlo baseline simulation for selected sequence-level statistics.

This script estimates how often a fair random draw process would produce
sequence effects at least as extreme as those observed in the gameplay data.

It was used as a sanity check for exploratory findings such as:

    - player receiving the lower card more often in same draw-index comparisons
    - both recordings showing the same draw-index direction
    - NPC opening totals exceeding player opening totals in the money-phase recording

The simulation assumes independent uniform draws from card values 1 through 10.
"""

import random


N_SIM = 100_000

# Observed real-data values used as thresholds.
# "Fun phase" refers to the post-reward recording.
# "Money phase" refers to the credit-wager recording.
FUN_NON_EQUAL = 266
FUN_PLAYER_LOWER = 149
FUN_OPENING_N = 105
FUN_OPENING_DIFF = 10.952 - 11.105  # NPC - Player

MONEY_NON_EQUAL = 401
MONEY_PLAYER_LOWER = 221
MONEY_OPENING_N = 152
MONEY_OPENING_DIFF = 10.888 - 9.974  # NPC - Player


def draw() -> int:
    """Draw one card from a fair infinite deck with values 1 through 10."""
    return random.randint(1, 10)


def simulate_draw_index(non_equal_target: int) -> tuple[int, int]:
    """
    Simulate same draw-index comparisons until enough non-equal pairs exist.

    Ties are ignored, matching the binomial comparison used in the analysis.

    Parameters
    ----------
    non_equal_target:
        Number of non-equal player/NPC comparisons to simulate.

    Returns
    -------
    tuple[int, int]
        Counts for (player_lower, opponent_lower).
    """
    player_lower = 0
    opponent_lower = 0
    non_equal = 0

    while non_equal < non_equal_target:
        player_card = draw()
        opponent_card = draw()

        if player_card == opponent_card:
            continue

        non_equal += 1

        if player_card < opponent_card:
            player_lower += 1
        else:
            opponent_lower += 1

    return player_lower, opponent_lower


def simulate_openings(n_rounds: int) -> tuple[list[int], list[int], float]:
    """
    Simulate two-card opening totals for player and opponent.

    Returns player totals, opponent totals, and the mean difference:

        opponent_mean - player_mean
    """
    player = [draw() + draw() for _ in range(n_rounds)]
    opponent = [draw() + draw() for _ in range(n_rounds)]

    diff = sum(opponent) / n_rounds - sum(player) / n_rounds

    return player, opponent, diff


def main() -> None:
    """Run the fair baseline simulation and print empirical probabilities."""
    draw_index_fun_extreme = 0
    draw_index_money_extreme = 0
    draw_index_both_same_direction_extreme = 0

    opening_money_extreme = 0

    for _ in range(N_SIM):
        fun_player_lower, _ = simulate_draw_index(FUN_NON_EQUAL)
        money_player_lower, _ = simulate_draw_index(MONEY_NON_EQUAL)

        # Test the observed direction: player lower more often.
        if fun_player_lower >= FUN_PLAYER_LOWER:
            draw_index_fun_extreme += 1

        if money_player_lower >= MONEY_PLAYER_LOWER:
            draw_index_money_extreme += 1

        if (
            fun_player_lower >= FUN_PLAYER_LOWER
            and money_player_lower >= MONEY_PLAYER_LOWER
        ):
            draw_index_both_same_direction_extreme += 1

        # Opening total difference, money phase.
        _, _, money_diff = simulate_openings(MONEY_OPENING_N)

        if money_diff >= MONEY_OPENING_DIFF:
            opening_money_extreme += 1

    print(f"Simulations: {N_SIM}")

    print("\nDraw-index asymmetry")
    print("---------------------")
    print(
        f"Fun phase: P(player lower >= {FUN_PLAYER_LOWER}/{FUN_NON_EQUAL}) "
        f"≈ {draw_index_fun_extreme / N_SIM:.4%}"
    )
    print(
        f"Money phase: P(player lower >= {MONEY_PLAYER_LOWER}/{MONEY_NON_EQUAL}) "
        f"≈ {draw_index_money_extreme / N_SIM:.4%}"
    )
    print(
        "Both recordings at least this extreme in same direction "
        f"≈ {draw_index_both_same_direction_extreme / N_SIM:.4%}"
    )

    print("\nOpening totals")
    print("---------------")
    print(
        f"Money phase: P(NPC-player opening diff >= {MONEY_OPENING_DIFF:.3f}) "
        f"≈ {opening_money_extreme / N_SIM:.4%}"
    )


if __name__ == "__main__":
    main()