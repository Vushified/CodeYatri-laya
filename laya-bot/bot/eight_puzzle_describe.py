"""
eight_puzzle_describe.py - Objective factual board descriptions and move facts for 8-Puzzle.

Hard Rules Enforced:
1. Facts only, no strategy or advice in code.
2. Token minimized (<200 tokens).
3. Objective facts per move:
   - move name: UP, DOWN, LEFT, RIGHT
   - moved tile: the numbered tile (1-8) that slides into the empty space
   - closer: whether the move reduces total Manhattan distance to goal
   - dist: resulting Manhattan distance after move
   - is_goal: whether the move solves the puzzle immediately
"""

from typing import Any, Dict, List, Optional, Tuple
from bot.eight_puzzle_game import (
    GOAL_BOARD,
    MOVE_NAMES,
    MOVE_DELTAS,
    compute_manhattan_distance,
    compute_misplaced_tiles,
)


def format_board_compact(board: List[List[int]]) -> str:
    """Format board compactly: e.g. '123/406/758' (where 0 is blank)."""
    rows = ["".join(str(cell) for cell in row) for row in board]
    return "/".join(rows)


OPPOSITE_MOVES: Dict[int, int] = {
    0: 1,  # UP <-> DOWN
    1: 0,
    2: 3,  # LEFT <-> RIGHT
    3: 2,
}


def compute_move_facts(board: List[List[int]], move: int, last_move: Optional[int] = None) -> Dict[str, Any]:
    """Compute factual heuristic metrics for candidate move without altering board."""
    # Find blank
    br = bc = -1
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                br, bc = r, c
                break

    dr, dc = MOVE_DELTAS[move]
    nr, nc = br + dr, bc + dc

    # Simulated swap
    b_sim = [list(row) for row in board]
    b_sim[br][bc], b_sim[nr][nc] = b_sim[nr][nc], b_sim[br][bc]

    dist_before = compute_manhattan_distance(board)
    dist_after = compute_manhattan_distance(b_sim)
    delta_dist = dist_after - dist_before

    misplaced_before = compute_misplaced_tiles(board)
    misplaced_after = compute_misplaced_tiles(b_sim)

    is_goal = (b_sim == GOAL_BOARD)
    moved_tile = board[nr][nc]
    is_undo = (last_move is not None and move == OPPOSITE_MOVES.get(last_move))

    return {
        "move": move,
        "name": MOVE_NAMES[move],
        "moved_tile": moved_tile,
        "is_goal": is_goal,
        "closer": delta_dist < 0,
        "dist": dist_after,
        "delta_dist": delta_dist,
        "misplaced": misplaced_after,
        "is_undo": is_undo,
    }


def compact_move_facts(board: List[List[int]], move: int, last_move: Optional[int] = None) -> str:
    """Format single move facts compactly: m0:[UP,tile:5,win:N,closer:Y,dist:3,undo:N]"""
    f = compute_move_facts(board, move, last_move=last_move)
    w = "Y" if f["is_goal"] else "N"
    c = "Y" if f["closer"] else "N"
    u = "Y" if f["is_undo"] else "N"
    return f"m{move}:[{f['name']},tile:{f['moved_tile']},win:{w},closer:{c},dist:{f['dist']},undo:{u}]"


def describe_puzzle_state(state: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Compact state text format (<120 tokens) for Design K:
    8-Puzzle 3x3. Blank=0. Goal: 123/456/780.
    Board: 123/405/786. Current distance to goal: 2.
    Priority: 1.win:Y 2.closer:Y 3.lowest dist 4.undo:N.
    Moves: m0:[UP,tile:4,win:N,closer:N,dist:3,undo:N] ...
    """
    board = state["board"]
    legal_moves = state.get("legal_moves", [])
    b_str = format_board_compact(board)
    m_dist = compute_manhattan_distance(board)

    last_move = history[-1]["move"] if history else None
    moves_text = "Moves: " + " ".join([compact_move_facts(board, m, last_move=last_move) for m in legal_moves])

    return (
        "8-Puzzle 3x3. Blank is 0. Goal: 123/456/780.\n"
        f"Board: {b_str}. Current distance to goal: {m_dist}.\n"
        "Priority: 1.win:Y 2.closer:Y 3.lowest dist 4.undo:N.\n"
        f"{moves_text}"
    )


def describe_kf_puzzle_state(state: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> str:
    """
    Fuller rules format for Design KF:
    Explains sliding puzzle mechanics + goal state + priority ordering.
    """
    board = state["board"]
    legal_moves = state.get("legal_moves", [])
    b_str = format_board_compact(board)
    m_dist = compute_manhattan_distance(board)

    last_move = history[-1]["move"] if history else None
    moves_text = "Moves: " + " ".join([compact_move_facts(board, m, last_move=last_move) for m in legal_moves])

    return (
        "8-Puzzle sliding tile game on a 3x3 grid.\n"
        "Tiles 1-8 slide into the empty space 0.\n"
        "Objective: Reach goal configuration 123/456/780 in minimum moves.\n"
        f"Current Board: {b_str}. Distance to goal: {m_dist}.\n"
        "Priority order: 1.win:Y (solves puzzle) 2.closer:Y (decreases distance to goal) 3.lowest dist 4.undo:N.\n"
        f"{moves_text}"
    )


def describe_move_plain(board: List[List[int]], move: int, last_move: Optional[int] = None) -> str:
    """Factual description for candidate move in Design B."""
    f = compute_move_facts(board, move, last_move=last_move)
    goal_str = " (SOLVES PUZZLE)" if f["is_goal"] else ""
    undo_str = " (REVERSES PREVIOUS MOVE)" if f["is_undo"] else ""
    return (
        f"Move blank {f['name']} (slides tile {f['moved_tile']} into blank): "
        f"Goal distance becomes {f['dist']} (delta: {f['delta_dist']:+d}, closer: {f['closer']}){goal_str}{undo_str}."
    )
