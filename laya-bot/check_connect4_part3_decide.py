"""
check_connect4_part3_decide.py - Verify that Design K and Design E both run on a Connect Four state without errors.
"""

from bot.connect4_game import Connect4Game
from bot.decide import choose_move

game = Connect4Game(seed=42)
state = game.get_state()
legal = game.get_legal_moves()

print("Testing Design K on Connect Four state...")
move_k, details_k = choose_move(state, legal, design="K")
print(f"Design K chosen move: column {move_k}")
print(f"Design K probabilities: {details_k['probabilities']}")
print(">>> Design K PASSED on Connect Four state!\n")

print("Testing Design E on Connect Four state...")
move_e, details_e = choose_move(state, legal, design="E")
print(f"Design E chosen move: column {move_e}")
print(f"Design E probabilities: {details_e['probabilities']}")
print(">>> Design E PASSED on Connect Four state!\n")
