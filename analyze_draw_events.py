"""
Pazaak: The Kobayashi Maru of Star Wars

Script: analyze_draw_events.py
Author: Sebastian Böker

Analyzes extracted Pazaak draw events and tests whether the observed
main-deck card distribution is consistent with a fair uniform deck.

Input:
    data/extracted/pazaak_draw_events.csv

Expected CSV columns:
    side, card_value

Main output:
    - Player and opponent draw counts
    - Mean draw values
    - Card frequency tables
    - Chi-Square Goodness-of-Fit test against a uniform distribution
"""

from pathlib import Path
import csv
from collections import Counter
from scipy.stats import chisquare


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"

IN_CSV = EXTRACTED_DIR / "pazaak_draw_events.csv"


def load_draws() -> dict[str, list[int]]:
    """Load player and opponent draw values from the extracted event CSV."""
    draws = {
        "player": [],
        "opponent": [],
    }

    with IN_CSV.open(newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            side = row["side"]
            value = int(row["card_value"])

            if side not in draws:
                continue

            draws[side].append(value)

    return draws


def mean(values: list[int]) -> float:
    """Return the arithmetic mean of a list of values."""
    return sum(values) / len(values) if values else float("nan")


def print_distribution(name: str, values: list[int]) -> None:
    """Print count, mean, and card frequency distribution for one sample."""
    counts = Counter(values)
    total = len(values)

    print(f"\n{name}")
    print(f"Count: {total}")
    print(f"Mean : {mean(values):.3f}")

    print("\nCard distribution:")
    for card in range(1, 11):
        count = counts[card]
        pct = count / total if total else 0
        print(f"  {card:>2}: {count:>4}  {pct:>7.3%}")


def print_combined_table(player: list[int], opponent: list[int]) -> None:
    """Print a side-by-side frequency table for player and opponent draws."""
    p_counts = Counter(player)
    o_counts = Counter(opponent)

    p_total = len(player)
    o_total = len(opponent)

    print("\nCombined frequency table")
    print("Card | Player        | Opponent")
    print("--------------------------------")

    for card in range(1, 11):
        p_count = p_counts[card]
        o_count = o_counts[card]

        p_pct = p_count / p_total if p_total else 0
        o_pct = o_count / o_total if o_total else 0

        print(
            f"{card:>4} | "
            f"{p_count:>4} ({p_pct:>6.2%}) | "
            f"{o_count:>4} ({o_pct:>6.2%})"
        )


def run_chi_square_test(values: list[int]) -> None:
    """Run a Chi-Square Goodness-of-Fit test against a uniform 1-10 deck."""
    if not values:
        print("\nChi-Square Goodness-of-Fit Test")
        print("--------------------------------")
        print("No draw events available.")
        return

    counts = Counter(values)

    observed = [counts[i] for i in range(1, 11)]
    expected = [len(values) / 10] * 10

    chi2, p = chisquare(observed, expected)

    print("\nChi-Square Goodness-of-Fit Test")
    print("--------------------------------")
    print(f"Chi² statistic : {chi2:.4f}")
    print(f"p-value        : {p:.6f}")

    if p < 0.05:
        print("Result: Reject H0 (non-uniform distribution detected)")
    else:
        print("Result: Cannot reject H0 (distribution consistent with fairness)")


def main() -> None:
    """Load extracted draw events and run frequency-based fairness analysis."""
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {IN_CSV}")

    draws = load_draws()

    player = draws["player"]
    opponent = draws["opponent"]

    print_distribution("Player draws", player)
    print_distribution("Opponent draws", opponent)
    print_combined_table(player, opponent)

    all_draws = player + opponent
    print_distribution("All draws", all_draws)

    run_chi_square_test(all_draws)


if __name__ == "__main__":
    main()