"""
game_2048_describe.py - Objective factual representations and move facts for 2048.

Strict Hard Rules:
1. Facts only, no hardcoded strategy in Python. Laya makes all choices.
2. Token budget <200 tokens.
3. Factual metrics computed per candidate move:
   - points gained from tile merges (+pts)
   - empty cells remaining (empty)
   - number of merges (merges)
   - max tile value (max_tile)
   - corner: whether the max tile is located in one of the 4 board corners
"""

from typing import Any, Dict, List, Tuple
from bot.game_2048 import MOVE_NAMES, simulate_move


def format_board_compact(board: List[List[int]]) -> str:
    """Compact string representation: e.g. [2,0,4,8]/[0,16,32,0]/[0,0,64,128]/[0,0,0,256]"""
    return "/".join([" ".join(str(c) for c in row) for row in board])


def is_max_tile_in_corner(board: List[List[int]]) -> bool:
    """Checks if the maximum tile on the board is at one of the 4 corners."""
    max_val = max(max(row) for row in board)
    corners = [board[0][0], board[0][3], board[3][0], board[3][3]]
    return max_val in corners


def count_empty_cells(board: List[List[int]]) -> int:
    """Counts number of 0s on board."""
    return sum(row.count(0) for row in board)


def compute_2048_move_facts(board: List[List[int]], move: int) -> Dict[str, Any]:
    """Computes factual metrics for a candidate move by simulation."""
    new_board, points, is_legal = simulate_move(board, move)
    if not is_legal:
        return {"legal": False}

    empty_count = count_empty_cells(new_board)
    max_val = max(max(row) for row in new_board)
    corner = is_max_tile_in_corner(new_board)

    return {
        "legal": True,
        "move": move,
        "name": MOVE_NAMES[move],
        "points": points,
        "empty_cells": empty_count,
        "max_tile": max_val,
        "corner": corner,
    }


def describe_move_plain_2048(board: List[List[int]], move: int) -> str:
    """Factual description for candidate move in Design B."""
    f = compute_2048_move_facts(board, move)
    corner_str = "Max tile stays in corner." if f["corner"] else "Max tile not in corner."
    return (
        f"Move {f['name']}: Scores +{f['points']} points from merges. "
        f"Leaves {f['empty_cells']} empty spaces. Max tile is {f['max_tile']}. {corner_str}"
    )


def compact_move_facts_2048(board: List[List[int]], move: int) -> str:
    """Compact move flag notation for Design K."""
    f = compute_2048_move_facts(board, move)
    c = "Y" if f["corner"] else "N"
    return f"m{move}:[{f['name']},pts:+{f['points']},empty:{f['empty_cells']},max:{f['max_tile']},corner:{c}]"


def describe_2048_state_k(state: Dict[str, Any]) -> str:
    """
    Compact state text for 2048 Design K (<140 tokens).
    2048 4x4. Current Score: 240, Max Tile: 64.
    Board: 2 0 4 8 / 0 16 32 0 / 0 0 64 0 / 0 0 0 0.
    Priority: 1.corner:Y (keep max tile in corner) 2.most empty 3.highest pts.
    """
    board = state["board"]
    score = state.get("score", 0)
    max_tile = state.get("max_tile", 0)
    b_str = format_board_compact(board)

    return (
        f"2048 4x4 grid. Score: {score}, Max Tile: {max_tile}.\n"
        f"Board: {b_str}\n"
        "Priority: 1.corner:Y (keep max tile locked in corner) 2.most empty spaces 3.highest pts."
    )


def describe_2048_state_kf(state: Dict[str, Any]) -> str:
    """
    Fuller rules format for 2048 Design KF.
    """
    board = state["board"]
    score = state.get("score", 0)
    max_tile = state.get("max_tile", 0)
    b_str = format_board_compact(board)

    return (
        "Game 2048: Single-player sliding puzzle on a 4x4 grid.\n"
        "Tiles with the same number merge into one when sliding together, scoring their sum.\n"
        "Objective: Maximize score and survive by creating high-value tiles and keeping board open.\n"
        f"Current Score: {score}, Max Tile: {max_tile}.\n"
        f"Board: {b_str}\n"
        "Priority order: 1.keep max tile in corner (corner:Y) 2.maximize empty cells (empty) 3.maximize points (pts)."
    )
