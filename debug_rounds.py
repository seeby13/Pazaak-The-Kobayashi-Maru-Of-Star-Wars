"""
Pazaak: The Kobayashi Maru of Star Wars

Script: debug_rounds.py
Author: Sebastian Böker

Exports randomly selected reconstructed Pazaak rounds for manual validation.

This utility groups draw events by round_id, selects a random subset of rounds,
and writes both:

    - a textual round summary
    - annotated video frames for each event in the round

The goal is to validate whether the event reconstruction and round grouping
are plausible when compared against the original gameplay video.

Input:
    game_recordings/*.mp4
    data/extracted/pazaak_draw_events.csv

Output:
    data/debug/debug_rounds/round_XXXX/
"""

from pathlib import Path
import csv
import random
import cv2


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

EXTRACTED_DIR = DATA_DIR / "extracted"
DEBUG_DIR = DATA_DIR / "debug"

EVENT_CSV = EXTRACTED_DIR / "pazaak_draw_events.csv"
VIDEO_DIR = BASE_DIR / "game_recordings"

OUT_DIR = DEBUG_DIR / "debug_rounds"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_ROUNDS_TO_EXPORT = 20
RANDOM_SEED = 42


def find_video() -> Path:
    """
    Return the first MP4 gameplay recording found in game_recordings/.

    If multiple videos are present, the first one in sorted order is used.
    """
    videos = sorted(VIDEO_DIR.glob("*.mp4"))

    if not videos:
        raise FileNotFoundError(f"No .mp4 found in {VIDEO_DIR}")

    if len(videos) > 1:
        print("Multiple videos found, using first:")
        for video in videos:
            print(" ", video.name)

    return videos[0]


def load_rounds() -> dict[int, list[dict]]:
    """Load draw events and group them by round_id."""
    if not EVENT_CSV.exists():
        raise FileNotFoundError(f"Event CSV not found: {EVENT_CSV}")

    rounds: dict[int, list[dict]] = {}

    with EVENT_CSV.open(newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            round_id = int(row["round_id"])

            event = {
                "round_id": round_id,
                "time_seconds": float(row["time_seconds"]),
                "frame_index": int(row["frame_index"]),
                "side": row["side"],
                "slot_index": int(row["slot_index"]),
                "card_value": int(row["card_value"]),
                "event_type": row["event_type"],
                "player_state": row["player_state"],
                "opponent_state": row["opponent_state"],
            }

            rounds.setdefault(round_id, []).append(event)

    return rounds


def summarize_round(events: list[dict]) -> tuple[list[int], list[int]]:
    """Return player and opponent card sequences for a round."""
    player = [event["card_value"] for event in events if event["side"] == "player"]
    opponent = [event["card_value"] for event in events if event["side"] == "opponent"]

    return player, opponent


def draw_label(frame, lines: list[str]) -> None:
    """Draw multiple text lines onto a video frame."""
    x, y = 30, 40

    for line in lines:
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


def write_round_summary(round_dir: Path, round_id: int, events: list[dict]) -> None:
    """Write a human-readable text summary for one reconstructed round."""
    player, opponent = summarize_round(events)

    summary_path = round_dir / "summary.txt"

    with summary_path.open("w", encoding="utf-8") as f:
        f.write(f"Round {round_id}\n")
        f.write(f"Player  : {player}\n")
        f.write(f"Opponent: {opponent}\n\n")

        for event in events:
            f.write(
                f"{event['time_seconds']:8.3f}s "
                f"frame={event['frame_index']:>7} "
                f"{event['side']:>8} "
                f"slot={event['slot_index']} "
                f"card={event['card_value']} "
                f"type={event['event_type']} "
                f"P=[{event['player_state']}] "
                f"O=[{event['opponent_state']}]\n"
            )


def export_round_frames(cap, round_id: int, events: list[dict]) -> None:
    """
    Export annotated video frames for all events in a reconstructed round.
    """
    round_dir = OUT_DIR / f"round_{round_id:04d}"
    round_dir.mkdir(parents=True, exist_ok=True)

    write_round_summary(round_dir, round_id, events)

    player, opponent = summarize_round(events)

    for i, event in enumerate(events, start=1):
        frame_index = event["frame_index"]

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()

        if not ok:
            print(f"Could not read frame {frame_index}")
            continue

        lines = [
            f"Round {round_id} Event {i}",
            f"type={event['event_type']}",
            f"time={event['time_seconds']:.2f}s frame={frame_index}",
            f"{event['side']} drew {event['card_value']} in slot {event['slot_index']}",
            f"P: {player}",
            f"O: {opponent}",
        ]

        draw_label(frame, lines)

        out_path = round_dir / (
            f"event_{i:02d}_{event['event_type']}_{event['side']}"
            f"_slot{event['slot_index']}_{event['card_value']}"
            f"_frame{frame_index}.png"
        )

        cv2.imwrite(str(out_path), frame)


def main() -> None:
    """Select random rounds and export annotated validation material."""
    rounds = load_rounds()
    video_path = find_video()

    print(f"Loaded rounds: {len(rounds)}")
    print(f"Video: {video_path.name}")

    valid_round_ids = sorted(rounds.keys())

    random.seed(RANDOM_SEED)
    selected_round_ids = random.sample(
        valid_round_ids,
        min(N_ROUNDS_TO_EXPORT, len(valid_round_ids)),
    )

    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    for round_id in selected_round_ids:
        events = rounds[round_id]
        player, opponent = summarize_round(events)

        print(f"\nRound {round_id}")
        print(f"  Player  : {player}")
        print(f"  Opponent: {opponent}")

        export_round_frames(cap, round_id, events)

    cap.release()

    print("\nDebug rounds written to:")
    print(OUT_DIR)


if __name__ == "__main__":
    main()