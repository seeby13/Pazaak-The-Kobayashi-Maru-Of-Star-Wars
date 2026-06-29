"""
Pazaak: The Kobayashi Maru of Star Wars

Script: extract_draw_events.py
Author: Sebastian Böker

Converts detected Pazaak board-state changes into individual draw events.

The input CSV is produced by extract_pazaak_video.py and contains complete
player/opponent board states whenever the visible board state changes.

This script reconstructs draw events by comparing consecutive board states:

    - If exactly one new card appears, the event is marked as "observed".
    - If a new round is first seen with multiple cards already present, the
      missing events are reconstructed from physical slot order and marked as
      "reconstructed".

This distinction is important for later sequence analyses, because directly
observed events are more reliable than inferred events.

Input:
    data/extracted/pazaak_state_changes.csv

Output:
    data/extracted/pazaak_draw_events.csv
"""

from pathlib import Path
import csv


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
EXTRACTED_DIR = DATA_DIR / "extracted"

IN_CSV = EXTRACTED_DIR / "pazaak_state_changes.csv"
OUT_CSV = EXTRACTED_DIR / "pazaak_draw_events.csv"

EMPTY_STATE = [None] * 9


def parse_state(state_string: str) -> list[int | None]:
    """
    Convert a comma-separated board-state string into a list of card values.

    Example:
        "3,_,_,_,_,_,_,_,_" -> [3, None, None, None, ...]
    """
    values = []

    for part in state_string.split(","):
        part = part.strip()
        values.append(None if part == "_" else int(part))

    return values


def state_to_text(state: list[int | None]) -> str:
    """Convert a board state into a compact human-readable string."""
    return " ".join("_" if value is None else str(value) for value in state)


def occupied_count(state: list[int | None]) -> int:
    """Return the number of occupied card slots in one board state."""
    return sum(value is not None for value in state)


def state_is_empty(
    player_state: list[int | None],
    opponent_state: list[int | None],
) -> bool:
    """Return True if both player and opponent boards are empty."""
    return occupied_count(player_state) == 0 and occupied_count(opponent_state) == 0


def is_reset_transition(
    old_player: list[int | None],
    old_opponent: list[int | None],
    new_player: list[int | None],
    new_opponent: list[int | None],
) -> bool:
    """
    Detect whether a transition likely indicates a new round.

    A reset is assumed if an already occupied slot changes its value.
    In normal within-round progression, cards should only be added to empty
    slots, not replaced.
    """
    old_combined = old_player + old_opponent
    new_combined = new_player + new_opponent

    for old_value, new_value in zip(old_combined, new_combined):
        if old_value is not None and old_value != new_value:
            return True

    return False


def new_slots(
    old_state: list[int | None],
    new_state: list[int | None],
) -> list[tuple[int, int]] | None:
    """
    Return newly occupied slots between two states.

    Returns
    -------
    list[tuple[int, int]]
        A list of (slot_index, card_value) pairs.

    None
        Returned if an already occupied slot changed value, which means the
        transition cannot be interpreted as a simple card addition.
    """
    added = []

    for i, (old_value, new_value) in enumerate(zip(old_state, new_state)):
        if old_value is None and new_value is not None:
            added.append((i, new_value))
        elif old_value is not None and new_value != old_value:
            return None

    return added


def add_event(
    events: list[dict],
    round_id: int,
    row: dict,
    side: str,
    slot_index: int,
    card_value: int,
    player_state: list[int | None],
    opponent_state: list[int | None],
    event_type: str,
) -> None:
    """Append one reconstructed draw event to the event list."""
    events.append({
        "round_id": round_id,
        "time_seconds": row["time_seconds"],
        "frame_index": row["frame_index"],
        "side": side,
        "slot_index": slot_index,
        "card_value": card_value,
        "event_type": event_type,
        "player_state": state_to_text(player_state),
        "opponent_state": state_to_text(opponent_state),
    })


def add_reconstructed_reset_events(
    events: list[dict],
    round_id: int,
    row: dict,
    player_added: list[tuple[int, int]],
    opponent_added: list[tuple[int, int]],
    player_state: list[int | None],
    opponent_state: list[int | None],
) -> None:
    """
    Add inferred opening events for a newly detected round.

    If a round first appears with multiple occupied slots, the exact timing
    of those draws was not observed. The order is therefore inferred from
    physical slot order:

        player slot 0, opponent slot 0,
        player slot 1, opponent slot 1,
        ...

    These events are marked as "reconstructed".
    """
    for slot in range(9):
        for side, added in [
            ("player", player_added),
            ("opponent", opponent_added),
        ]:
            for slot_index, card_value in added:
                if slot_index == slot:
                    add_event(
                        events,
                        round_id,
                        row,
                        side,
                        slot_index,
                        card_value,
                        player_state,
                        opponent_state,
                        "reconstructed",
                    )


def add_observed_single_event(
    events: list[dict],
    round_id: int,
    row: dict,
    player_added: list[tuple[int, int]],
    opponent_added: list[tuple[int, int]],
    player_state: list[int | None],
    opponent_state: list[int | None],
) -> None:
    """
    Add a directly observed event if exactly one new card appeared.
    """
    total_added = len(player_added) + len(opponent_added)

    if total_added != 1:
        return

    for slot_index, card_value in player_added:
        add_event(
            events,
            round_id,
            row,
            "player",
            slot_index,
            card_value,
            player_state,
            opponent_state,
            "observed",
        )

    for slot_index, card_value in opponent_added:
        add_event(
            events,
            round_id,
            row,
            "opponent",
            slot_index,
            card_value,
            player_state,
            opponent_state,
            "observed",
        )


def write_events(events: list[dict]) -> None:
    """Write reconstructed draw events to the output CSV."""
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

    with OUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "round_id",
                "time_seconds",
                "frame_index",
                "side",
                "slot_index",
                "card_value",
                "event_type",
                "player_state",
                "opponent_state",
            ],
        )
        writer.writeheader()
        writer.writerows(events)


def print_summary(events: list[dict], round_count: int) -> None:
    """Print a short summary of the reconstructed event dataset."""
    player_draws = [event for event in events if event["side"] == "player"]
    opponent_draws = [event for event in events if event["side"] == "opponent"]

    observed = [event for event in events if event["event_type"] == "observed"]
    reconstructed = [
        event for event in events if event["event_type"] == "reconstructed"
    ]

    print(f"Wrote {len(events)} draw events to:")
    print(OUT_CSV)

    print(f"Reconstructed rounds: {round_count}")
    print(f"Player draws       : {len(player_draws)}")
    print(f"Opponent draws     : {len(opponent_draws)}")
    print(f"Observed events    : {len(observed)}")
    print(f"Reconstructed events: {len(reconstructed)}")


def main() -> None:
    """Read board-state changes and reconstruct individual draw events."""
    if not IN_CSV.exists():
        raise FileNotFoundError(f"Input CSV not found: {IN_CSV}")

    events = []

    previous_player = EMPTY_STATE.copy()
    previous_opponent = EMPTY_STATE.copy()
    round_id = -1

    with IN_CSV.open(newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            player_state = parse_state(row["player_state"])
            opponent_state = parse_state(row["opponent_state"])

            if state_is_empty(player_state, opponent_state):
                previous_player = EMPTY_STATE.copy()
                previous_opponent = EMPTY_STATE.copy()
                continue

            reset = (
                round_id == -1
                or is_reset_transition(
                    previous_player,
                    previous_opponent,
                    player_state,
                    opponent_state,
                )
            )

            if reset:
                round_id += 1
                previous_player = EMPTY_STATE.copy()
                previous_opponent = EMPTY_STATE.copy()

            player_added = new_slots(previous_player, player_state)
            opponent_added = new_slots(previous_opponent, opponent_state)

            if player_added is None or opponent_added is None:
                previous_player = player_state
                previous_opponent = opponent_state
                continue

            if reset:
                add_reconstructed_reset_events(
                    events,
                    round_id,
                    row,
                    player_added,
                    opponent_added,
                    player_state,
                    opponent_state,
                )
            else:
                add_observed_single_event(
                    events,
                    round_id,
                    row,
                    player_added,
                    opponent_added,
                    player_state,
                    opponent_state,
                )

            previous_player = player_state
            previous_opponent = opponent_state

    write_events(events)
    print_summary(events, round_count=round_id + 1)


if __name__ == "__main__":
    main()