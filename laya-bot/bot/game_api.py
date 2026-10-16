"""
game_api.py - Defines the abstract GameAdapter interface.

Any game played by our bot (whether local tic-tac-toe or a remote hackathon API)
must follow this exact contract. Moves always come from the game, never guessed by the bot.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class GameAdapter(ABC):
    """
    Abstract interface for games.
    The bot interacts exclusively through these four methods.
    """

    @abstractmethod
    def reset(self) -> Dict[str, Any]:
        """
        Reset the game to the starting state and return the initial state dictionary.
        """
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """
        Return the current raw game state:
        {
            "board": List[str],      # Representation of the board (e.g. 9 cells)
            "current_player": str,   # Whose turn it is (e.g. "X" or "O")
            "is_game_over": bool,    # True if the game has ended
            "result": Optional[str]  # None, "X", "O", or "draw"
        }
        """
        pass

    @abstractmethod
    def get_legal_moves(self) -> List[int]:
        """
        Return the list of legal move identifiers (e.g. cell indices 0..8).
        Critical rule: moves originate strictly from the game environment.
        """
        pass

    @abstractmethod
    def submit_move(self, move: int) -> Dict[str, Any]:
        """
        Apply a move made by the player.
        Returns the updated state dictionary.
        """
        pass
