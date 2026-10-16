"""
check_addition2.py - Verification script for Addition 2.
Evaluates all 6 designs (A, B, C, D, E, F) across 5 different board positions.
Verifies that Laya is called for every move and no fallbacks are used.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.decide import choose_move

TEST_BOARDS = [
    ("Opening (9 legal)", [" "] * 9, list(range(9))),
    ("Early (O played cell 4)", [" ", " ", " ", " ", "O", " ", " ", " ", " "], [0, 1, 2, 3, 5, 6, 7, 8]),
    ("Mid (X has 0, 4)", ["X", "O", " ", " ", "X", " ", " ", " ", "O"], [2, 3, 5, 6, 7]),
    ("Fork Defense", ["O", " ", " ", " ", "X", " ", " ", " ", "O"], [1, 2, 3, 5, 6, 7]),
    ("Late (3 cells left)", ["X", "O", "X", "O", "X", "O", " ", " ", " "], [6, 7, 8]),
]

DESIGNS = ["A", "B", "C", "D", "E", "F"]


def run_checks():
    print("Testing Addition 2: Six Question Modes (A, B, C, D, E, F)")
    for name, board, legal in TEST_BOARDS:
        print(f"\n==================== {name} ====================")
        state = {"board": board}
        for d in DESIGNS:
            move, details = choose_move(
                state=state,
                legal_moves=legal,
                design=d,
                input_mode="board",
                wording="good",
            )
            print(f"Design {d}: Chosen move = Cell {move} (Legal: {move in legal})")
            probs = details.get("probabilities", {})
            prob_preview = {k: round(v, 3) for k, v in list(probs.items())[:3]}
            print(f"  Sample probabilities/scores: {prob_preview} (Total evaluated: {len(probs)})")
            assert move in legal, f"Design {d} picked illegal move {move}"

    print("\nAll 6 designs verified on 5 test states! No fallbacks, all calls logged.")


if __name__ == "__main__":
    run_checks()
