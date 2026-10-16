"""
check_step3.py - Verification script for Step 3.
Prints the descriptions for 3 different game states to verify that all
statements are completely factual with zero subjective advice or verdicts.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.describe import describe_board, describe_move, describe_state_and_moves


def test_states():
    # State 1: Opening / early move
    state1 = {
        "board": [" ", " ", " ", " ", " ", " ", " ", " ", " "],
        "current_player": "X",
        "is_game_over": False,
        "result": None,
    }
    legal1 = [0, 4, 1]  # Check a corner, centre, and edge

    # State 2: Mid game
    #  X | O |  
    # ---+---+---
    #    | X |  
    # ---+---+---
    #    |   | O
    state2 = {
        "board": ["X", "O", " ", " ", "X", " ", " ", " ", "O"],
        "current_player": "X",
        "is_game_over": False,
        "result": None,
    }
    legal2 = [2, 3, 7]

    # State 3: Late game
    #  X | O | X
    # ---+---+---
    #  O | X | O
    # ---+---+---
    #    |   |  
    state3 = {
        "board": ["X", "O", "X", "O", "X", "O", " ", " ", " "],
        "current_player": "X",
        "is_game_over": False,
        "result": None,
    }
    legal3 = [6, 7, 8]

    states = [
        ("State 1 (Empty Board)", state1, legal1),
        ("State 2 (Mid Game)", state2, legal2),
        ("State 3 (Late Game)", state3, legal3),
    ]

    for label, st, moves in states:
        print(f"\n==================== {label} ====================")
        print("Board Description:")
        print(describe_board(st))
        print("\nMove Descriptions:")
        for m in moves:
            print(f"- {describe_move(st, m)}")
        print("\nCombined State Text for Laya:")
        print(describe_state_and_moves(st, moves))


if __name__ == "__main__":
    test_states()
