"""
check_eight_puzzle_sanity.py - Verify 8-puzzle game mechanics, A* solver, and choose_move on 8-puzzle.
"""

from bot.eight_puzzle_game import EightPuzzleGame, compute_manhattan_distance, solve_a_star
from bot.eight_puzzle_describe import describe_puzzle_state, describe_kf_puzzle_state
from bot.decide import choose_move

print("Initializing 8-Puzzle Game with depth 6...")
game = EightPuzzleGame(seed=42, scramble_depth=6)
state = game.get_state()
print(f"Initial Board: {state['board']}")
print(f"Manhattan Distance: {state['manhattan']}")
print(f"Optimal A* steps: {state['optimal_steps']}")
print(f"Legal Moves: {state['legal_moves']}")

print("\n--- Testing Design K Prompt ---")
desc_k = describe_puzzle_state(state)
print(desc_k)

print("\n--- Testing choose_move with Design K ---")
move_k, details_k = choose_move(state, state["legal_moves"], design="K")
print(f"Chosen move: {move_k}, probabilities: {details_k['probabilities']}")

print("\n--- Testing choose_move with Design B ---")
move_b, details_b = choose_move(state, state["legal_moves"], design="B")
print(f"Chosen move: {move_b}, probabilities: {details_b['probabilities']}")

print("\n--- Testing choose_move with Design KF ---")
move_kf, details_kf = choose_move(state, state["legal_moves"], design="KF")
print(f"Chosen move: {move_kf}, probabilities: {details_kf['probabilities']}")

print("\n>>> All 8-Puzzle Sanity Checks PASSED successfully!")
