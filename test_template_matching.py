"""
Pazaak: The Kobayashi Maru of Star Wars

Script: test_template_matching.py
Author: Sebastian Böker

Tests card-template matching on static screenshots.

This utility reads all screenshots in screenshots/, applies the calibrated
player and opponent slot grid, classifies occupied card slots using template
matching, and writes annotated debug images.

It is mainly used before full video extraction to verify that:

    - slot coordinates are aligned correctly
    - empty slots are detected correctly
    - card templates match the visible card values with reasonable confidence

Input:
    screenshots/*.png
    templates/1.png ... templates/10.png

Output:
    data/debug/debug_matches/match_<screenshot_name>.png
"""

from pathlib import Path
import cv2
import numpy as np
from slot_grid import PLAYER_SLOTS, OPPONENT_SLOTS, Slot


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEBUG_DIR = DATA_DIR / "debug"

TEMPLATE_DIR = BASE_DIR / "templates"
SCREENSHOT_DIR = BASE_DIR / "screenshots"

OUT_DIR = DEBUG_DIR / "debug_matches"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_templates() -> dict[int, np.ndarray]:
    """Load grayscale templates for card values 1 through 10."""
    templates = {}

    for value in range(1, 11):
        path = TEMPLATE_DIR / f"{value}.png"
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)

        if img is None:
            raise FileNotFoundError(f"Could not load template: {path}")

        templates[value] = img

    return templates


def is_slot_empty(slot: np.ndarray) -> bool:
    """
    Determine whether a card slot appears empty.

    Occupied card slots contain a visible yellow card region. Empty slots are
    mostly dark/grey. The yellow pixel ratio is used as a simple heuristic.
    """
    hsv = cv2.cvtColor(slot, cv2.COLOR_BGR2HSV)

    lower_yellow = np.array([15, 50, 80])
    upper_yellow = np.array([45, 255, 255])

    mask = cv2.inRange(hsv, lower_yellow, upper_yellow)
    yellow_ratio = np.count_nonzero(mask) / mask.size

    return yellow_ratio < 0.03


def match_template(
    slot: np.ndarray,
    templates: dict[int, np.ndarray],
) -> tuple[int, float]:
    """
    Match a cropped slot against all card templates.

    Returns the best card value and its normalized matching score.
    """
    gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)

    best_value = -1
    best_score = -1.0

    for value, template in templates.items():
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(result)

        if score > best_score:
            best_score = score
            best_value = value

    return best_value, best_score


def read_slots(
    frame: np.ndarray,
    slots: list[Slot],
    templates: dict[int, np.ndarray],
) -> list[tuple[int, int | None, float]]:
    """
    Read all slots for one side of the board.

    Returns a list of:
        (slot_index, detected_value, match_score)
    """
    results = []

    for idx, (x, y, w, h) in enumerate(slots):
        slot = frame[y:y + h, x:x + w]

        if is_slot_empty(slot):
            results.append((idx, None, 0.0))
            continue

        value, score = match_template(slot, templates)
        results.append((idx, value, score))

    return results


def draw_results(
    frame: np.ndarray,
    slots: list[Slot],
    results: list[tuple[int, int | None, float]],
    color: tuple[int, int, int],
) -> None:
    """Draw detected slot labels and confidence scores onto an image."""
    for (idx, value, score), (x, y, w, h) in zip(results, slots):
        label = "empty" if value is None else f"{value} ({score:.2f})"

        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            frame,
            label,
            (x, y - 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )


def main() -> None:
    """Run template-matching validation on all available screenshots."""
    templates = load_templates()
    screenshots = sorted(SCREENSHOT_DIR.glob("*.png"))

    if not screenshots:
        raise FileNotFoundError(f"No screenshots found in {SCREENSHOT_DIR}")

    for screenshot in screenshots:
        frame = cv2.imread(str(screenshot))

        if frame is None:
            print(f"Skipping unreadable image: {screenshot}")
            continue

        player_results = read_slots(frame, PLAYER_SLOTS, templates)
        opponent_results = read_slots(frame, OPPONENT_SLOTS, templates)

        print(f"\n{screenshot.name}")

        print("Player:")
        for idx, value, score in player_results:
            print(f"  P{idx}: {value}  score={score:.3f}")

        print("Opponent:")
        for idx, value, score in opponent_results:
            print(f"  O{idx}: {value}  score={score:.3f}")

        debug = frame.copy()
        draw_results(debug, PLAYER_SLOTS, player_results, (0, 255, 0))
        draw_results(debug, OPPONENT_SLOTS, opponent_results, (0, 0, 255))

        out_path = OUT_DIR / f"match_{screenshot.name}"
        cv2.imwrite(str(out_path), debug)

    print(f"\nDebug images written to: {OUT_DIR}")


if __name__ == "__main__":
    main()