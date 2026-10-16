"""
check_step4.py - Verification script for Step 4.
Runs decide_move_design_a across 5 different board states.
Prints the questions asked, Laya's probabilities for each legal move, and the chosen move.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.decide import decide_move_design_a


def run_checks():
    test_cases = [
        (
            "State 1: Empty opening board",
            [" ", " ", " ", " ", " ", " ", " ", " ", " "],
            [0, 1, 2, 3, 4, 5, 6, 7, 8],
        ),
        (
            "State 2: O played centre (cell 4)",
            [" ", " ", " ", " ", "O", " ", " ", " ", " "],
            [0, 1, 2, 3, 5, 6, 7, 8],
        ),
        (
            "State 3: X has 0 and 1 (threat at 2)",
            ["X", "X", " ", " ", "O", " ", " ", " ", " "],
            [2, 3, 5, 6, 7, 8],
        ),
        (
            "State 4: O has 3 and 4 (opponent threat at 5)",
            ["X", " ", " ", "O", "O", " ", "X", " ", " "],
            [1, 2, 5, 7, 8],
        ),
        (
            "State 5: Late game (3 cells remaining)",
            ["X", "O", "X", "O", "X", "O", " ", " ", " "],
            [6, 7, 8],
        ),
    ]

    for label, board, legal in test_cases:
        state = {
            "board": board,
            "current_player": "X",
            "is_game_over": False,
            "result": None,
        }
        print(f"\n==================== {label} ====================")
        decision = decide_move_design_a(state, legal)
        
        print(f"Number of legal moves evaluated: {len(legal)}")
        print("Questions asked:")
        for qid, qdef in decision["questions"].items():
            print(f"  {qid}: '{qdef['instructions']}'")
        
        print("\nLaya Probabilities P(true):")
        # Sort by move number for clear reading
        for m in sorted(decision["probabilities"].keys()):
            p = decision["probabilities"][m]
            marker = " <-- HIGHEST (CHOSEN)" if m == decision["chosen_move"] else ""
            print(f"  Move {m}: {p:.4f} ({p*100:.2f}%){marker}")

        print(f"\n--> Chosen Move: {decision['chosen_move']}")
        assert decision["chosen_move"] in legal, "Chosen move is not legal!"


if __name__ == "__main__":
    run_checks()
