"""
tictactoe_game.py - Local Tic-Tac-Toe implementation adhering to GameAdapter.

The bot plays 'X'. The environment simulates an opponent 'O' that chooses
a random legal move after each bot move.
Board cells are indexed 0 to 8:
 0 | 1 | 2
---+---+---
 3 | 4 | 5
---+---+---
 6 | 7 | 8
"""

import random
from typing import Any, Dict, List, Optional
from bot.game_api import GameAdapter


WINNING_COMBINATIONS = [
    (0, 1, 2),  # Row 0
    (3, 4, 5),  # Row 1
    (6, 7, 8),  # Row 2
    (0, 3, 6),  # Col 0
    (1, 4, 7),  # Col 1
    (2, 5, 8),  # Col 2
    (0, 4, 8),  # Diagonal \
    (2, 4, 6),  # Diagonal /
]


class TicTacToeGame(GameAdapter):
    """
    Tic-Tac-Toe game engine conforming to GameAdapter.
    """

    def __init__(self, seed: Optional[int] = None, opponent_mode: str = "random"):
        """
        Initialize the game. An optional seed can make the opponent's moves reproducible.
        opponent_mode can be 'random' or 'smart_random'.
        """
        self.rng = random.Random(seed)
        self.opponent_mode = opponent_mode
        self.board: List[str] = [" "] * 9
        self.current_player: str = "X"  # 'X' starts
        self.is_game_over: bool = False
        self.result: Optional[str] = None  # 'X', 'O', 'draw', or None
        self.turn_number: int = 1

    def _find_winning_move(self, player: str, legal_moves: List[int]) -> Optional[int]:
        """Check if any legal move immediately completes 3-in-a-row for player."""
        for m in legal_moves:
            self.board[m] = player
            for a, b, c in WINNING_COMBINATIONS:
                if self.board[a] == self.board[b] == self.board[c] == player:
                    self.board[m] = " "
                    return m
            self.board[m] = " "
        return None

    def reset(self) -> Dict[str, Any]:
        """Reset the board to empty and set player to X."""
        self.board = [" "] * 9
        self.current_player = "X"
        self.is_game_over = False
        self.result = None
        self.turn_number = 1
        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        """Return the current raw game state."""
        return {
            "board": list(self.board),
            "current_player": self.current_player,
            "is_game_over": self.is_game_over,
            "result": self.result,
            "turn_number": self.turn_number,
        }

    def get_legal_moves(self) -> List[int]:
        """
        Return list of empty cell indices (0..8).
        If the game is over, no moves are legal.
        """
        if self.is_game_over:
            return []
        return [i for i, cell in enumerate(self.board) if cell == " "]

    def _check_winner(self) -> Optional[str]:
        """
        Check if X or O has won, or if it is a draw.
        Returns 'X', 'O', 'draw', or None if the game continues.
        """
        for a, b, c in WINNING_COMBINATIONS:
            if self.board[a] != " " and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a]

        if " " not in self.board:
            return "draw"

        return None

    def submit_move(self, move: int) -> Dict[str, Any]:
        """
        Submit a move for player 'X'.
        If the game does not end, the opponent ('O') plays (random or smart_random) immediately.
        """
        if self.is_game_over:
            raise ValueError("Game is already over. Reset before playing.")

        legal_moves = self.get_legal_moves()
        if move not in legal_moves:
            raise ValueError(f"Illegal move {move}. Legal moves are: {legal_moves}")

        # 1. Apply bot's move (X)
        self.board[move] = "X"
        winner = self._check_winner()

        if winner is not None:
            self.is_game_over = True
            self.result = winner
            return self.get_state()

        # 2. Opponent (O) turn
        self.current_player = "O"
        o_legal_moves = self.get_legal_moves()
        if o_legal_moves:
            if self.opponent_mode == "smart_random":
                # 2a. Immediate win for O
                win_move = self._find_winning_move("O", o_legal_moves)
                if win_move is not None:
                    o_move = win_move
                else:
                    # 2b. Block immediate win for X
                    block_move = self._find_winning_move("X", o_legal_moves)
                    if block_move is not None:
                        o_move = block_move
                    else:
                        o_move = self.rng.choice(o_legal_moves)
            else:
                o_move = self.rng.choice(o_legal_moves)

            self.board[o_move] = "O"
            winner = self._check_winner()
            if winner is not None:
                self.is_game_over = True
                self.result = winner
                return self.get_state()

        # 3. Ready for next X turn
        self.current_player = "X"
        self.turn_number += 1
        return self.get_state()

    def render_board(self) -> str:
        """Helper to return an ASCII view of the 3x3 board."""
        rows = []
        for r in range(3):
            row_cells = [self.board[r * 3 + c] if self.board[r * 3 + c] != " " else str(r * 3 + c) for c in range(3)]
            rows.append(" " + " | ".join(row_cells) + " ")
        return "\n---+---+---\n".join(rows)
