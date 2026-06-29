"""
Pazaak: The Kobayashi Maru of Star Wars

Script: extract_pazaak_video.py
Author: Sebastian Böker

Extracts visible Pazaak board states from gameplay recordings.

This script analyzes a KOTOR gameplay video frame by frame. Whenever the
Pazaak board is visible, it reads the fixed player and opponent card slots
using template matching and records every detected board-state change.

The output is not yet a list of individual draw events. Instead, it is a
sequence of visible board states. Individual draw events are reconstructed
later by extract_draw_events.py.

Input:
    game_recordings/*.mp4
    templates/1.png ... templates/10.png

Output:
    data/extracted/pazaak_state_changes.csv
"""

from pathlib import Path
import csv
import cv2
import numpy as np
from slot_grid import PLAYER_SLOTS, OPPONENT_SLOTS, Slot


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"

TEMPLATE_DIR = BASE_DIR / "templates"
VIDEO_DIR = BASE_DIR / "game_recordings"

OUTPUT_CSV = EXTRACTED_DIR / "pazaak_state_changes.csv"

TARGET_ANALYSIS_FPS = 15
MATCH_THRESHOLD = 0.80


BoardState = dict[str, tuple[int | None, ...]]



def load_templates() -> dict[int, np.ndarray]:
    """Load grayscale card templates for card values 1 through 10."""
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
) -> tuple[int, float, list[tuple[int, float]]]:
    """
    Match a cropped card slot against all templates.

    Returns
    -------
    best_value:
        Card value with highest template-matching score.

    best_score:
        Highest normalized template-matching score.

    top3:
        Three best candidate matches, useful for debugging.
    """
    gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)

    scores = []

    for value, template in templates.items():
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(result)
        scores.append((value, score))

    scores.sort(key=lambda x: x[1], reverse=True)

    best_value, best_score = scores[0]
    return best_value, best_score, scores[:3]


def read_side(
    frame: np.ndarray,
    slots: list[Slot],
    templates: dict[int, np.ndarray],
) -> tuple[int | None, ...]:
    """
    Read all nine card slots for one side of the board.

    Empty or low-confidence slots are returned as None.
    """
    values = []

    for x, y, w, h in slots:
        slot = frame[y:y + h, x:x + w]

        if is_slot_empty(slot):
            values.append(None)
            continue

        value, score, _ = match_template(slot, templates)

        if score < MATCH_THRESHOLD:
            values.append(None)
        else:
            values.append(value)

    return tuple(values)


def is_pazaak_screen(frame: np.ndarray) -> bool:
    """
    Detect whether the current frame appears to contain the Pazaak board.

    This uses a simple color heuristic based on orange UI elements that are
    present on the Pazaak board but usually absent in normal gameplay/dialogue.
    """
    crop = frame[150:230, 250:1450]

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    lower_orange = np.array([5, 80, 80])
    upper_orange = np.array([25, 255, 255])

    mask = cv2.inRange(hsv, lower_orange, upper_orange)
    orange_ratio = np.count_nonzero(mask) / mask.size

    return orange_ratio > 0.005


def read_board_state(
    frame: np.ndarray,
    templates: dict[int, np.ndarray],
) -> BoardState:
    """Read player and opponent card-slot states from one frame."""
    return {
        "player": read_side(frame, PLAYER_SLOTS, templates),
        "opponent": read_side(frame, OPPONENT_SLOTS, templates),
    }


def state_values_to_csv(values: tuple[int | None, ...]) -> str:
    """Convert one side's board state to a CSV-friendly string."""
    return ",".join("_" if value is None else str(value) for value in values)


def state_to_string(state: BoardState) -> str:
    """Convert a full board state into a compact display string."""
    player = state_values_to_csv(state["player"])
    opponent = state_values_to_csv(state["opponent"])
    return player + " | " + opponent


def board_is_empty(state: BoardState) -> bool:
    """Return True if no cards are visible on either side of the board."""
    return (
        all(value is None for value in state["player"])
        and all(value is None for value in state["opponent"])
    )


def find_video() -> Path:
    """
    Return the first MP4 gameplay recording found in game_recordings/.

    If multiple videos are present, the first one in sorted order is used.
    """
    videos = sorted(VIDEO_DIR.glob("*.mp4"))

    if not videos:
        raise FileNotFoundError(f"No .mp4 file found in {VIDEO_DIR}")

    if len(videos) > 1:
        print("Multiple videos found, using first:")
        for video in videos:
            print(" ", video.name)

    return videos[0]


def write_state_changes(changes: list[dict]) -> None:
    """Write detected board-state changes to the output CSV."""
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "time_seconds",
                "frame_index",
                "player_state",
                "opponent_state",
            ],
        )
        writer.writeheader()
        writer.writerows(changes)


def main() -> None:
    """Extract Pazaak board-state changes from the first gameplay video."""
    templates = load_templates()
    video_path = find_video()

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    source_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / source_fps if source_fps else 0
    frame_step = max(1, round(source_fps / TARGET_ANALYSIS_FPS))

    print(f"Video: {video_path.name}")
    print(f"Source FPS: {source_fps}")
    print(f"Frames: {frame_count}")
    print(f"Duration: {duration:.1f}s")
    print(f"Analyzing every {frame_step} frame(s)")

    previous_state_string = None
    changes = []

    frame_index = 0

    while True:
        ok, frame = cap.read()

        if not ok:
            break

        if frame_index % frame_step != 0:
            frame_index += 1
            continue

        if not is_pazaak_screen(frame):
            previous_state_string = None
            frame_index += 1
            continue

        time_seconds = frame_index / source_fps if source_fps else 0
        state = read_board_state(frame, templates)

        if board_is_empty(state):
            previous_state_string = None
            frame_index += 1
            continue

        state_string = state_to_string(state)

        if state_string != previous_state_string:
            changes.append({
                "time_seconds": f"{time_seconds:.3f}",
                "frame_index": frame_index,
                "player_state": state_values_to_csv(state["player"]),
                "opponent_state": state_values_to_csv(state["opponent"]),
            })

            print(f"{time_seconds:8.2f}s  {state_string}")

            previous_state_string = state_string

        frame_index += 1

    cap.release()
    write_state_changes(changes)

    print(f"\nWrote {len(changes)} state changes to:")
    print(OUTPUT_CSV)


if __name__ == "__main__":
    main()