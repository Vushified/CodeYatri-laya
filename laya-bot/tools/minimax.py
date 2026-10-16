"""
minimax.py - Perfect Tic-Tac-Toe referee solver.

HARD RULE 5:
This file is allowed ONLY in evaluation/referee scripts to benchmark Laya.
It must NEVER be imported by any code in bot/.

Given a board state where it is X's turn, minimax determines:
1. The minimax value (-1, 0, +1) of each legal move.
2. The set of 'optimal moves' (moves that achieve the highest minimax value).
"""

from typing import Dict, List, Optional, Tuple

WINNING_COMBINATIONS = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6)
]


def check_winner(board: List[str]) -> Optional[str]:
    """Check if X or O won, or if it is a draw."""
    for a, b, c in WINNING_COMBINATIONS:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    if " " not in board:
        return "draw"
    return None


def _minimax(board: List[str], is_maximizing: bool) -> int:
    """
    Minimax recursive evaluation.
    +1: X wins
    -1: O wins
     0: draw
    """
    winner = check_winner(board)
    if winner == "X":
        return 1
    if winner == "O":
        return -1
    if winner == "draw":
        return 0

    legal_moves = [i for i, c in enumerate(board) if c == " "]
    if is_maximizing:
        best_val = -float("inf")
        for m in legal_moves:
            board[m] = "X"
            val = _minimax(board, False)
            board[m] = " "
            best_val = max(best_val, val)
        return int(best_val)
    else:
        best_val = float("inf")
        for m in legal_moves:
            board[m] = "O"
            val = _minimax(board, True)
            board[m] = " "
            best_val = min(best_val, val)
        return int(best_val)


def get_optimal_moves(board: List[str]) -> Tuple[List[int], Dict[int, int]]:
    """
    For a board where it is X's turn:
    Returns (optimal_moves_list, move_values_dict).
    Optimal moves are all legal moves that tie for the maximum minimax value.
    """
    legal_moves = [i for i, c in enumerate(board) if c == " "]
    if not legal_moves:
        return [], {}

    move_values: Dict[int, int] = {}
    for m in legal_moves:
        board_copy = list(board)
        board_copy[m] = "X"
        # Next turn is O (minimizing)
        val = _minimax(board_copy, False)
        move_values[m] = val

    max_val = max(move_values.values())
    optimal_moves = [m for m, val in move_values.items() if val == max_val]
    return optimal_moves, move_values
