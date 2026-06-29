"""
Pazaak: The Kobayashi Maru of Star Wars

Module: result.py
Author: Sebastian Böker

Defines possible outcomes of a simulated Pazaak round.

The simulator distinguishes between:

    - Player 1 victory
    - Player 2 victory
    - Draw

Using an enumeration improves readability compared to using raw integers
throughout the simulation code.
"""

from enum import Enum


class Result(Enum):
    """
    Possible outcomes of a Pazaak round.

    Attributes
    ----------
    PLAYER1
        Player 1 wins the round.

    PLAYER2
        Player 2 wins the round.

    DRAW
        Neither player wins.
    """

    PLAYER1 = 1
    PLAYER2 = 2
    DRAW = 3