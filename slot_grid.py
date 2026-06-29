"""
Pazaak: The Kobayashi Maru of Star Wars

Module: slot_grid.py
Author: Sebastian Böker

Central definition of the fixed Pazaak board slot geometry.

The computer-vision pipeline assumes a fixed recording setup. In the original
analysis, gameplay was recorded at 1920x1080 with the Pazaak interface always
appearing at the same screen position.

This module defines:

    - card slot size
    - horizontal and vertical slot spacing
    - player and opponent grid start positions
    - generated 3x3 slot grids for both sides

All extraction and debugging scripts should import PLAYER_SLOTS and
OPPONENT_SLOTS from this module instead of duplicating the slot geometry.
"""

SLOT_W = 146
SLOT_H = 139

DX = 161
DY = 152

PLAYER_START = (364, 268)
OPPONENT_START = (1085, 264)

Slot = tuple[int, int, int, int]


def make_grid(start_x: int, start_y: int) -> list[Slot]:
    """
    Create a 3x3 Pazaak card-slot grid.

    Parameters
    ----------
    start_x:
        X-coordinate of the upper-left slot.

    start_y:
        Y-coordinate of the upper-left slot.

    Returns
    -------
    list[Slot]
        Nine slot rectangles as (x, y, width, height), ordered row-wise.
    """
    return [
        (start_x + col * DX, start_y + row * DY, SLOT_W, SLOT_H)
        for row in range(3)
        for col in range(3)
    ]


PLAYER_SLOTS = make_grid(*PLAYER_START)
OPPONENT_SLOTS = make_grid(*OPPONENT_START)