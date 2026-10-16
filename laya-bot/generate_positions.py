"""
generate_positions.py - Generates 50 TUNE and 50 TEST non-overlapping Tic-Tac-Toe positions.

Each position:
- Is a valid board reachable in Tic-Tac-Toe where it is X's turn (count(X) == count(O)).
- The game is not already won.
- Has at least one legal move.
- Mixes early, middle, and late game situations, including forks, immediate wins, and blocks.
- Stores optimal moves precalculated with tools/minimax.py for fast evaluation.
"""

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.minimax import check_winner, get_optimal_moves


def generate_all_valid_x_positions():
    """Breadth-first search / simulation to find distinct valid positions where it is X's turn."""
    visited = set()
    positions = []

    def explore(board, turn_player):
        board_tuple = tuple(board)
        if board_tuple in visited:
            return
        visited.add(board_tuple)

        winner = check_winner(board)
        if winner is not None:
            return

        x_count = board.count("X")
        o_count = board.count("O")

        if turn_player == "X" and x_count == o_count:
            legal = [i for i, c in enumerate(board) if c == " "]
            if legal:
                opt_moves, _ = get_optimal_moves(board)
                positions.append({
                    "board": list(board),
                    "legal_moves": legal,
                    "optimal_moves": opt_moves,
                    "x_count": x_count,
                    "empty_count": len(legal)
                })

        legal_moves = [i for i, c in enumerate(board) if c == " "]
        for m in legal_moves:
            board[m] = turn_player
            next_player = "O" if turn_player == "X" else "X"
            explore(board, next_player)
            board[m] = " "

    initial_board = [" "] * 9
    explore(initial_board, "X")
    return positions


def main():
    positions = generate_all_valid_x_positions()
    print(f"Total reachable X-turn positions discovered: {len(positions)}")

    # Shuffle with fixed seed for determinism
    rng = random.Random(42)
    rng.shuffle(positions)

    # Separate into early (empty: 9, 7), mid (empty: 5), late (empty: 3, 1)
    early = [p for p in positions if p["empty_count"] in (9, 7)]
    mid = [p for p in positions if p["empty_count"] == 5]
    late = [p for p in positions if p["empty_count"] in (3, 1)]

    rng.shuffle(early)
    rng.shuffle(mid)
    rng.shuffle(late)

    # Select 50 for TUNE: 15 early, 25 mid, 10 late
    tune_positions = early[:15] + mid[:25] + late[:10]
    
    # Remaining for TEST: 15 early, 25 mid, 10 late (strictly disjoint)
    test_positions = early[15:30] + mid[25:50] + late[10:20]

    for idx, p in enumerate(tune_positions):
        p["id"] = f"tune_{idx+1:03d}"
    for idx, p in enumerate(test_positions):
        p["id"] = f"test_{idx+1:03d}"

    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)

    tune_path = os.path.join(data_dir, "positions_tune.json")
    test_path = os.path.join(data_dir, "positions_test.json")

    with open(tune_path, "w", encoding="utf-8") as f:
        json.dump(tune_positions, f, indent=2)

    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_positions, f, indent=2)

    print(f"Saved {len(tune_positions)} positions to {tune_path}")
    print(f"Saved {len(test_positions)} positions to {test_path}")

    # Confirm zero overlap
    tune_boards = set(tuple(p["board"]) for p in tune_positions)
    test_boards = set(tuple(p["board"]) for p in test_positions)
    overlap = tune_boards.intersection(test_boards)
    print(f"Overlap between TUNE and TEST sets: {len(overlap)} (Must be 0)")
    assert len(overlap) == 0, "Error: TUNE and TEST sets overlap!"


if __name__ == "__main__":
    main()
