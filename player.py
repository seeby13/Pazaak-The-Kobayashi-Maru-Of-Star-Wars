"""
Pazaak: The Kobayashi Maru of Star Wars

Module: player.py
Author: Sebastian Böker

Simple player representation used by the Pazaak simulator.

Each player tracks:

    - current total
    - standing status
    - bust status

The simplified simulation does not model side-deck cards or any hidden
state, so only the information required for decision-making is stored.
"""


class Player:
    """
    Represents one player in a simplified Pazaak round.

    Attributes
    ----------
    name : str
        Player identifier used for logging and statistics.

    total : int
        Current card total.

    stood : bool
        True if the player has chosen to stand.

    bust : bool
        True if the player's total exceeds 20.
    """

    def __init__(self, name: str):
        """
        Create a new player with an empty hand.
        """
        self.name = name
        self.total = 0
        self.stood = False
        self.bust = False

    def __repr__(self) -> str:
        """
        Human-readable debug representation.
        """
        return (
            f"Player("
            f"name='{self.name}', "
            f"total={self.total}, "
            f"stood={self.stood}, "
            f"bust={self.bust}"
            f")"
        )