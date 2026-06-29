"""
Pazaak: The Kobayashi Maru of Star Wars

Script: debug_slots.py
Author: Sebastian Böker

Draws the calibrated Pazaak card-slot grid onto all screenshots.

This utility is used to visually verify that the fixed slot coordinates
still align with the Pazaak board at the expected recording resolution.

Input:
    screenshots/*.png

Output:
    data/debug/debug_slots/debug_<screenshot_name>.png

Player slots are drawn in green.
Opponent slots are drawn in red.
"""

from pathlib import Path
import cv2
from slot_grid import PLAYER_SLOTS, OPPONENT_SLOTS


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEBUG_DIR = DATA_DIR / "debug"

SCREENSHOT_DIR = BASE_DIR / "screenshots"
OUT_DIR = DEBUG_DIR / "debug_slots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def draw_slots(frame):
    """Draw player and opponent slot rectangles onto a frame."""
    for i, (x, y, w, h) in enumerate(PLAYER_SLOTS):
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"P{i}",
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

    for i, (x, y, w, h) in enumerate(OPPONENT_SLOTS):
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(
            frame,
            f"O{i}",
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

    return frame


def main() -> None:
    """Write slot-overlay debug images for all screenshots."""
    screenshots = sorted(SCREENSHOT_DIR.glob("*.png"))

    if not screenshots:
        raise FileNotFoundError(f"No PNG screenshots found in {SCREENSHOT_DIR}")

    for path in screenshots:
        frame = cv2.imread(str(path))

        if frame is None:
            print(f"Skipping unreadable image: {path}")
            continue

        debug = draw_slots(frame.copy())
        out_path = OUT_DIR / f"debug_{path.name}"

        cv2.imwrite(str(out_path), debug)
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()