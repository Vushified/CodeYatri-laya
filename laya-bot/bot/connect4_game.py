"""
connect4_game.py - Connect Four implementation adhering to GameAdapter.

Grid: 6 rows (0=bottom, 5=top) by 7 columns (0=left, 6=right).
Discs fall to the lowest empty row in the chosen column.
A player wins with 4 discs in a line horizontally, vertically, or diagonally.
"""

import copy
import random
from typing import Any, Dict, List, Optional, Tuple
from bot.game_api import GameAdapter

ROWS = 6
COLS = 7


class Connect4Game(GameAdapter):
    """Connect Four game engine conforming to GameAdapter."""

    def __init__(self, seed: Optional[int] = None, opponent_mode: str = "random"):
        self.rng = random.Random(seed)
        self.opponent_mode = opponent_mode
        # board[row][col]: row 0 is bottom, row 5 is top.
        self.board: List[List[str]] = [["" for _ in range(COLS)] for _ in range(ROWS)]
        self.current_player: str = "X"
        self.is_game_over: bool = False
        self.result: Optional[str] = None  # 'X', 'O', 'draw', or None
        self.turn_number: int = 1

    def reset(self) -> Dict[str, Any]:
        """Reset to empty 6x7 board, X moves first."""
        self.board = [["" for _ in range(COLS)] for _ in range(ROWS)]
        self.current_player = "X"
        self.is_game_over = False
        self.result = None
        self.turn_number = 1
        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        """Return raw game state dictionary."""
        legal = self.get_legal_moves()
        return {
            "board": [list(row) for row in self.board],
            "current_player": self.current_player,
            "legal_moves": legal,
            "game_over": self.is_game_over,
            "is_game_over": self.is_game_over,
            "result": self.result,
            "turn_number": self.turn_number,
        }

    def get_legal_moves(self) -> List[int]:
        """Return list of column indices (0..6) that are not full."""
        if self.is_game_over:
            return []
        return [c for c in range(COLS) if self.board[ROWS - 1][c] == ""]

    def _get_lowest_empty_row(self, col: int) -> Optional[int]:
        """Find the lowest available row in column `col` (0=bottom, 5=top)."""
        for r in range(ROWS):
            if self.board[r][col] == "":
                return r
        return None

    def _check_win_from(self, row: int, col: int, player: str) -> bool:
        """
        Check if the disc at (row, col) belonging to player forms 4 in a row.
        Checks all 4 directions: Horizontal, Vertical, Diagonal-up, Diagonal-down.
        """
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal-up (/)
            (-1, 1),  # Diagonal-down (\)
        ]

        for dr, dc in directions:
            count = 1

            # Count forward
            r, c = row + dr, col + dc
            while 0 <= r < ROWS and 0 <= c < COLS and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc

            # Count backward
            r, c = row - dr, col - dc
            while 0 <= r < ROWS and 0 <= c < COLS and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc

            if count >= 4:
                return True

        return False

    def _find_immediate_winning_move(self, player: str, legal_moves: List[int]) -> Optional[int]:
        """Check if playing in any legal column immediately results in a 4-in-a-row win."""
        for c in legal_moves:
            r = self._get_lowest_empty_row(c)
            if r is not None:
                self.board[r][c] = player
                won = self._check_win_from(r, c, player)
                self.board[r][c] = ""
                if won:
                    return c
        return None

    def submit_move(self, col: int) -> Dict[str, Any]:
        """
        Submit a column move for player 'X'.
        If the game does not end, the opponent ('O') plays (random or smart_random) immediately.
        """
        if self.is_game_over:
            raise ValueError("Game is already over. Reset before playing.")

        legal_moves = self.get_legal_moves()
        if col not in legal_moves:
            raise ValueError(f"Illegal column {col}. Legal columns are: {legal_moves}")

        # 1. Apply bot's move (X)
        row = self._get_lowest_empty_row(col)
        self.board[row][col] = "X"

        if self._check_win_from(row, col, "X"):
            self.is_game_over = True
            self.result = "X"
            return self.get_state()

        if not self.get_legal_moves():
            self.is_game_over = True
            self.result = "draw"
            return self.get_state()

        # 2. Opponent (O) turn
        self.current_player = "O"
        o_legal_moves = self.get_legal_moves()
        if o_legal_moves:
            if self.opponent_mode == "smart_random":
                # 2a. Immediate win for O
                win_col = self._find_immediate_winning_move("O", o_legal_moves)
                if win_col is not None:
                    o_col = win_col
                else:
                    # 2b. Block immediate win for X
                    block_col = self._find_immediate_winning_move("X", o_legal_moves)
                    if block_col is not None:
                        o_col = block_col
                    else:
                        o_col = self.rng.choice(o_legal_moves)
            else:
                o_col = self.rng.choice(o_legal_moves)

            o_row = self._get_lowest_empty_row(o_col)
            self.board[o_row][o_col] = "O"

            if self._check_win_from(o_row, o_col, "O"):
                self.is_game_over = True
                self.result = "O"
                return self.get_state()

            if not self.get_legal_moves():
                self.is_game_over = True
                self.result = "draw"
                return self.get_state()

        # 3. Ready for next X turn
        self.current_player = "X"
        self.turn_number += 1
        return self.get_state()

    def render_board(self) -> str:
        """Helper to return an ASCII view of the 6x7 board (row 5 top, row 0 bottom)."""
        lines = []
        for r in range(ROWS - 1, -1, -1):
            row_str = "| " + " ".join(self.board[r][c] if self.board[r][c] != "" else "." for c in range(COLS)) + " |"
            lines.append(row_str)
        lines.append("+-" + "--" * (COLS - 1) + "-+")
        lines.append("  " + " ".join(str(c) for c in range(COLS)))
        return "\n".join(lines)
