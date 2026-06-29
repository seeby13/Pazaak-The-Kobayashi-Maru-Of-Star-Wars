"""
Pazaak: The Kobayashi Maru of Star Wars

Script: analyze_sequences.py
Author: Sebastian Böker

Performs sequence-level analyses on reconstructed Pazaak draw events.

Unlike analyze_draw_events.py, which only tests marginal card frequencies,
this script investigates whether the order of player and NPC draws contains
potential asymmetries.

Input:
    data/extracted/pazaak_draw_events.csv

Expected CSV columns:
    round_id, side, card_value, event_type

Main analyses:
    - Same draw-index comparison
    - Opening two-card totals
    - Extreme high opening pairs
    - Duplicate opening patterns
    - Binomial significance tests
    - Welch t-tests for opening totals
    - NPC response means conditioned on player card
    - Player/NPC draw correlation

The analysis is run twice:
    1. Using all events.
    2. Using only directly observed events.

The second analysis is stricter and avoids relying on reconstructed draw order.
"""

from pathlib import Path
import csv
from collections import defaultdict, Counter
from scipy.stats import binomtest, ttest_ind, pearsonr


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"

IN_CSV = EXTRACTED_DIR / "pazaak_draw_events.csv"

Round = dict[str, list[int]]


def load_rounds(only_observed: bool = False) -> list[Round]:
    """
    Load draw events grouped by round.

    Parameters
    ----------
    only_observed:
        If True, only events with event_type == "observed" are used.
        Reconstructed events are ignored.

    Returns
    -------
    list[Round]
        A list of rounds sorted by round_id. Each round contains a player
        and opponent draw sequence.
    """
    rounds: defaultdict[int, Round] = defaultdict(
        lambda: {"player": [], "opponent": []}
    )

    with IN_CSV.open(newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if only_observed and row["event_type"] != "observed":
                continue

            rid = int(row["round_id"])
            side = row["side"]
            value = int(row["card_value"])

            if side not in ("player", "opponent"):
                continue

            rounds[rid][side].append(value)

    return [rounds[k] for k in sorted(rounds)]


def mean(values: list[int]) -> float:
    """Return the arithmetic mean of a list of values."""
    return sum(values) / len(values) if values else float("nan")


def opening_totals(rounds: list[Round], n: int = 2) -> tuple[list[int], list[int]]:
    """
    Compute opening totals for both sides.

    The opening total is defined as the sum of the first n cards of a round.
    By default, n=2 is used.
    """
    player_totals = []
    opponent_totals = []

    for round_data in rounds:
        if len(round_data["player"]) >= n:
            player_totals.append(sum(round_data["player"][:n]))

        if len(round_data["opponent"]) >= n:
            opponent_totals.append(sum(round_data["opponent"][:n]))

    return player_totals, opponent_totals


def count_same_draw_index(rounds: list[Round]) -> tuple[int, int, int]:
    """
    Compare corresponding player and opponent draws within each round.

    For each draw index i, player[i] is compared against opponent[i].
    Returns counts for:
        player_lower, opponent_lower, equal
    """
    player_lower = 0
    opponent_lower = 0
    equal = 0

    for round_data in rounds:
        pairs = min(len(round_data["player"]), len(round_data["opponent"]))

        for i in range(pairs):
            player_card = round_data["player"][i]
            opponent_card = round_data["opponent"][i]

            if player_card < opponent_card:
                player_lower += 1
            elif opponent_card < player_card:
                opponent_lower += 1
            else:
                equal += 1

    return player_lower, opponent_lower, equal


def compare_same_draw_index(rounds: list[Round]) -> None:
    """Print same draw-index comparison statistics."""
    player_lower, opponent_lower, equal = count_same_draw_index(rounds)
    total = player_lower + opponent_lower + equal

    print("\nSame draw-index comparison")
    print("---------------------------")
    print(f"Compared pairs : {total}")

    if total:
        print(f"Player lower   : {player_lower} ({player_lower / total:.2%})")
        print(f"Opponent lower : {opponent_lower} ({opponent_lower / total:.2%})")
        print(f"Equal          : {equal} ({equal / total:.2%})")
        print("Fair expectation: lower/lower/equal ≈ 45% / 45% / 10%")


def two_card_opening_analysis(rounds: list[Round]) -> None:
    """Print summary statistics for two-card opening totals."""
    player, opponent = opening_totals(rounds, 2)

    print("\nOpening 2-card totals")
    print("----------------------")
    print(f"Player samples  : {len(player)}")
    print(f"Opponent samples: {len(opponent)}")
    print(f"Player mean     : {mean(player):.3f}")
    print(f"Opponent mean   : {mean(opponent):.3f}")

    for threshold in [16, 17, 18, 19, 20]:
        player_count = sum(x >= threshold for x in player)
        opponent_count = sum(x >= threshold for x in opponent)

        print(f"\nOpening total >= {threshold}")

        if player:
            print(
                f"Player   : {player_count}/{len(player)} "
                f"({player_count / len(player):.2%})"
            )
        else:
            print("Player   : n/a")

        if opponent:
            print(
                f"Opponent : {opponent_count}/{len(opponent)} "
                f"({opponent_count / len(opponent):.2%})"
            )
        else:
            print("Opponent : n/a")


def high_pair_patterns(rounds: list[Round]) -> None:
    """Count extreme two-card opening patterns such as 9+10 or 10+10."""
    patterns = {(9, 9), (9, 10), (10, 9), (10, 10)}

    player_count = 0
    opponent_count = 0
    player_samples = 0
    opponent_samples = 0

    for round_data in rounds:
        if len(round_data["player"]) >= 2:
            player_samples += 1
            if tuple(round_data["player"][:2]) in patterns:
                player_count += 1

        if len(round_data["opponent"]) >= 2:
            opponent_samples += 1
            if tuple(round_data["opponent"][:2]) in patterns:
                opponent_count += 1

    print("\nExtreme high opening pairs")
    print("---------------------------")
    print("Patterns: 9+9, 9+10, 10+9, 10+10")

    if player_samples:
        print(
            f"Player   : {player_count}/{player_samples} "
            f"({player_count / player_samples:.2%})"
        )
    else:
        print("Player   : n/a")

    if opponent_samples:
        print(
            f"Opponent : {opponent_count}/{opponent_samples} "
            f"({opponent_count / opponent_samples:.2%})"
        )
    else:
        print("Opponent : n/a")

    print("Fair expectation for these exact ordered pairs: 4%")


def duplicate_opening_analysis(rounds: list[Round]) -> None:
    """Print the most common paired two-card openings."""
    openings = []

    for round_data in rounds:
        player_opening = tuple(round_data["player"][:2])
        opponent_opening = tuple(round_data["opponent"][:2])

        if len(player_opening) == 2 and len(opponent_opening) == 2:
            openings.append((player_opening, opponent_opening))

    counts = Counter(openings)

    print("\nDuplicate opening analysis")
    print("---------------------------")
    print(f"Opening samples: {len(openings)}")
    print(f"Unique openings: {len(counts)}")

    print("\nMost common openings:")
    for (player_opening, opponent_opening), count in counts.most_common(10):
        print(f"{count:>3}x  Player {player_opening}  Opponent {opponent_opening}")


def significance_same_draw_index(rounds: list[Round]) -> None:
    """Run a binomial test on non-equal same draw-index comparisons."""
    player_lower, opponent_lower, equal = count_same_draw_index(rounds)
    non_equal = player_lower + opponent_lower

    print("\nSignificance: same draw-index comparison")
    print("----------------------------------------")
    print(f"Player lower   : {player_lower}")
    print(f"Opponent lower : {opponent_lower}")
    print(f"Equal          : {equal}")
    print(f"Non-equal      : {non_equal}")

    if non_equal == 0:
        print("Binomial p-value: n/a")
        return

    result = binomtest(
        k=player_lower,
        n=non_equal,
        p=0.5,
        alternative="two-sided",
    )

    print(f"Binomial p-value: {result.pvalue:.6f}")


def significance_opening_totals(rounds: list[Round]) -> None:
    """Run a Welch t-test comparing player and opponent opening totals."""
    player, opponent = opening_totals(rounds, 2)

    print("\nSignificance: opening two-card totals")
    print("-------------------------------------")
    print(f"Player mean   : {mean(player):.3f}")
    print(f"Opponent mean : {mean(opponent):.3f}")

    if len(player) < 2 or len(opponent) < 2:
        print("Difference    : n/a")
        print("Welch t-test p-value: n/a")
        return

    result = ttest_ind(player, opponent, equal_var=False)
    diff = mean(opponent) - mean(player)

    print(f"Difference    : {diff:.3f}")
    print(f"Welch t-test p-value: {result.pvalue:.6f}")


def npc_response_to_player_draw(rounds: list[Round]) -> None:
    """Print mean NPC card value conditioned on the corresponding player card."""
    responses: defaultdict[int, list[int]] = defaultdict(list)

    for round_data in rounds:
        pairs = min(len(round_data["player"]), len(round_data["opponent"]))

        for i in range(pairs):
            player_card = round_data["player"][i]
            npc_card = round_data["opponent"][i]

            responses[player_card].append(npc_card)

    print("\nNPC response to player draw")
    print("----------------------------")

    for player_card in range(1, 11):
        values = responses[player_card]

        if not values:
            continue

        npc_mean = mean(values)

        print(
            f"Player drew {player_card:>2}: "
            f"Samples={len(values):>3} "
            f"NPC mean={npc_mean:.3f}"
        )


def draw_correlation(rounds: list[Round]) -> None:
    """Compute Pearson correlation between corresponding player and NPC draws."""
    player_cards = []
    npc_cards = []

    for round_data in rounds:
        pairs = min(len(round_data["player"]), len(round_data["opponent"]))

        for i in range(pairs):
            player_cards.append(round_data["player"][i])
            npc_cards.append(round_data["opponent"][i])

    print("\nPlayer draw vs NPC draw correlation")
    print("-----------------------------------")

    if len(player_cards) < 3:
        print("Not enough samples")
        return

    corr, p = pearsonr(player_cards, npc_cards)

    print(f"Correlation : {corr:.4f}")
    print(f"p-value     : {p:.6f}")


def run_analysis(label: str, rounds: list[Round]) -> None:
    """Run all sequence analyses for one event subset."""
    print("\n" + "=" * 60)
    print(label)
    print("=" * 60)
    print(f"Reconstructed rounds: {len(rounds)}")

    compare_same_draw_index(rounds)
    two_card_opening_analysis(rounds)
    high_pair_patterns(rounds)
    duplicate_opening_analysis(rounds)
    significance_same_draw_index(rounds)
    significance_opening_totals(rounds)
    npc_response_to_player_draw(rounds)
    draw_correlation(rounds)


def main() -> None:
    """Run sequence analysis for all events and directly observed events only."""
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {IN_CSV}")

    all_rounds = load_rounds(only_observed=False)
    observed_rounds = load_rounds(only_observed=True)

    run_analysis("ALL EVENTS", all_rounds)
    run_analysis("ONLY DIRECTLY OBSERVED EVENTS", observed_rounds)


if __name__ == "__main__":
    main()