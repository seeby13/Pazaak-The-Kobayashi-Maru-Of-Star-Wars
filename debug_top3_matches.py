"""
Pazaak: The Kobayashi Maru of Star Wars

Script: debug_top3_matches.py
Author: Sebastian Böker

Exports annotated debug frames showing the top three template-matching
candidates for selected draw events.

This utility was mainly used to diagnose ambiguous or suspicious card
classifications, for example cases where 5, 8, and 9 were difficult to
distinguish.

For each selected event, the script:
    - seeks to the corresponding gameplay video frame
    - crops the physical card slot associated with the event
    - computes template-matching scores for all card values
    - overlays the top three matches onto the full frame
    - writes the annotated frame to data/debug/debug_top3/

Input:
    game_recordings/*.mp4
    templates/1.png ... templates/10.png
    data/extracted/pazaak_draw_events.csv

Output:
    data/debug/debug_top3/*.png
"""

from pathlib import Path
import csv
import cv2
from slot_grid import PLAYER_SLOTS, OPPONENT_SLOTS, Slot


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

EXTRACTED_DIR = DATA_DIR / "extracted"
DEBUG_DIR = DATA_DIR / "debug"

TEMPLATE_DIR = BASE_DIR / "templates"
VIDEO_DIR = BASE_DIR / "game_recordings"
EVENT_CSV = EXTRACTED_DIR / "pazaak_draw_events.csv"

OUT_DIR = DEBUG_DIR / "debug_top3"
OUT_DIR.mkdir(parents=True, exist_ok=True)


TemplateMap = dict[int, object]

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


def load_templates() -> dict[int, object]:
    """Load grayscale card templates for values 1 through 10."""
    templates = {}

    for value in range(1, 11):
        path = TEMPLATE_DIR / f"{value}.png"
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)

        if img is None:
            raise FileNotFoundError(f"Could not load template: {path}")

        templates[value] = img

    return templates


def top3_template_matches(slot, templates: dict[int, object]) -> list[tuple[int, float]]:
    """
    Return the three best template-matching candidates for a cropped slot.
    """
    gray = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)

    scores = []

    for value, template in templates.items():
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(result)
        scores.append((value, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:3]


def read_events(
    limit: int | None = 100,
    only_value: int | None = None,
) -> list[dict]:
    """
    Load selected draw events from the extracted event CSV.

    Parameters
    ----------
    limit:
        Maximum number of events to load. If None, all matching events are used.

    only_value:
        Optional card value filter. For example, only_value=9 exports only
        events where the detected card value was 9.
    """
    if not EVENT_CSV.exists():
        raise FileNotFoundError(f"Event CSV not found: {EVENT_CSV}")

    events = []

    with EVENT_CSV.open(newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            value = int(row["card_value"])

            if only_value is not None and value != only_value:
                continue

            events.append({
                "round_id": int(row["round_id"]),
                "time_seconds": float(row["time_seconds"]),
                "frame_index": int(row["frame_index"]),
                "side": row["side"],
                "slot_index": int(row["slot_index"]),
                "card_value": value,
                "event_type": row["event_type"],
                "player_state": row["player_state"],
                "opponent_state": row["opponent_state"],
            })

            if limit is not None and len(events) >= limit:
                break

    return events


def find_event_slot(event: dict) -> tuple[Slot, int]:
    """Return the physical slot rectangle associated with a draw event."""
    slot_index = int(event["slot_index"])
    side = event["side"]

    if side == "player":
        slots = PLAYER_SLOTS
    elif side == "opponent":
        slots = OPPONENT_SLOTS
    else:
        raise ValueError(f"Invalid side: {side}")

    if slot_index < 0 or slot_index >= len(slots):
        raise ValueError(f"Invalid slot_index: {slot_index}")

    return slots[slot_index], slot_index


def draw_label(frame, lines: list[str]) -> None:
    """Draw multiple text lines onto a frame."""
    x, y = 25, 35

    for line in lines:
        cv2.putText(
            frame,
            line,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2,
        )
        y += 30


def main() -> None:
    """Export top-3 template match debug frames for selected events."""
    templates = load_templates()
    video_path = find_video()

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    # Set only_value=9, for example, to inspect suspicious 9 detections.
    events = read_events(limit=100, only_value=9)

    print(f"Video: {video_path.name}")
    print(f"Exporting {len(events)} top-3 debug frames")

    for i, event in enumerate(events, start=1):
        frame_index = event["frame_index"]

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()

        if not ok:
            print(f"Could not read frame {frame_index}")
            continue

        (x, y, w, h), slot_index = find_event_slot(event)
        slot = frame[y:y + h, x:x + w]

        top3 = top3_template_matches(slot, templates)
        top3_text = " | ".join(f"{value}:{score:.3f}" for value, score in top3)

        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 3)

        lines = [
            f"Event {i}",
            f"round={event['round_id']} type={event['event_type']}",
            f"time={event['time_seconds']:.2f}s frame={frame_index}",
            f"{event['side']} drew {event['card_value']}",
            f"slot={slot_index}",
            f"top3: {top3_text}",
        ]

        draw_label(frame, lines)

        out_path = OUT_DIR / (
            f"top3_{i:04d}_{event['event_type']}_{event['side']}_"
            f"{event['card_value']}_frame_{frame_index}.png"
        )

        cv2.imwrite(str(out_path), frame)

    cap.release()

    print(f"Wrote debug images to {OUT_DIR}")


if __name__ == "__main__":
    main()