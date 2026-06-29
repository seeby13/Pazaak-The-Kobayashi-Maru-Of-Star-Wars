"""
Pazaak: The Kobayashi Maru of Star Wars

Script: debug_draw_events.py
Author: Sebastian Böker

Exports video frames corresponding to reconstructed Pazaak draw events.

This utility is used to manually validate whether detected draw events in
data/extracted/pazaak_draw_events.csv match the original gameplay video.

For each selected event, the script:
    - seeks to the corresponding video frame
    - overlays event metadata on the frame
    - writes the annotated frame to data/debug/debug_draw_events/

Input:
    game_recordings/*.mp4
    data/extracted/pazaak_draw_events.csv

Output:
    data/debug/debug_draw_events/*.png
"""

from pathlib import Path
import csv
import cv2


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

EXTRACTED_DIR = DATA_DIR / "extracted"
DEBUG_DIR = DATA_DIR / "debug"

VIDEO_DIR = BASE_DIR / "game_recordings"
EVENT_CSV = EXTRACTED_DIR / "pazaak_draw_events.csv"

OUT_DIR = DEBUG_DIR / "debug_draw_events"
OUT_DIR.mkdir(parents=True, exist_ok=True)


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


def read_events(
    limit: int | None = None,
    only_value: int | None = None,
) -> list[dict]:
    """
    Load draw events from the extracted event CSV.

    Parameters
    ----------
    limit:
        Maximum number of matching events to load. If None, all events are loaded.

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
            card_value = int(row["card_value"])

            if only_value is not None and card_value != only_value:
                continue

            events.append({
                "round_id": int(row["round_id"]),
                "time_seconds": float(row["time_seconds"]),
                "frame_index": int(row["frame_index"]),
                "side": row["side"],
                "slot_index": int(row["slot_index"]),
                "card_value": card_value,
                "event_type": row["event_type"],
                "player_state": row["player_state"],
                "opponent_state": row["opponent_state"],
            })

            if limit is not None and len(events) >= limit:
                break

    return events


def draw_event_label(frame, event: dict, event_index: int):
    """Overlay event metadata onto a video frame."""
    text_lines = [
        f"Event {event_index}",
        f"round={event['round_id']} type={event['event_type']}",
        f"time={event['time_seconds']:.2f}s frame={event['frame_index']}",
        f"{event['side']} drew {event['card_value']} in slot {event['slot_index']}",
        f"P: {event['player_state']}",
        f"O: {event['opponent_state']}",
    ]

    x, y = 30, 40

    for line in text_lines:
        cv2.putText(
            frame,
            line,
            (x, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2,
        )
        y += 32

    return frame


def main() -> None:
    """Export annotated debug frames for selected draw events."""
    video_path = find_video()
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    # Start with a limited sample.
    # Set only_value=9 to debug suspicious 9s, for example.
    events = read_events(limit=100, only_value=None)

    print(f"Video: {video_path.name}")
    print(f"Exporting {len(events)} debug event frames")

    for i, event in enumerate(events, start=1):
        frame_index = event["frame_index"]

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()

        if not ok:
            print(f"Could not read frame {frame_index}")
            continue

        frame = draw_event_label(frame, event, i)

        side = event["side"]
        value = event["card_value"]
        event_type = event["event_type"]

        out_path = OUT_DIR / (
            f"event_{i:04d}_{event_type}_{side}_{value}_"
            f"frame_{frame_index}.png"
        )

        cv2.imwrite(str(out_path), frame)

    cap.release()

    print("Debug frames written to:")
    print(OUT_DIR)


if __name__ == "__main__":
    main()