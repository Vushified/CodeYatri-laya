"""
test_design_b_puzzles.py - Test Design B on depth 1, 2, 3 puzzles.
"""

from bot.eight_puzzle_game import EightPuzzleGame
from bot.decide import choose_move

for depth in [1, 2, 3, 4]:
    print(f"\n================ Testing Design B on Scramble Depth {depth} ================")
    game = EightPuzzleGame(seed=42, scramble_depth=depth, max_steps=15)
    state = game.get_state()
    print(f"Start board: {state['board']}, Manhattan: {state['manhattan']}, Optimal: {state['optimal_steps']}")
    
    for step in range(1, 16):
        legal = game.get_legal_moves()
        move, details = choose_move(state, legal, design="B")
        move_name = ["UP", "DOWN", "LEFT", "RIGHT"][move]
        print(f"Step {step}: chosen {move} ({move_name}), probs: {details['probabilities']}")
        state = game.submit_move(move)
        print(f"  New Board: {state['board']}, Manhattan: {state['manhattan']}, Result: {state['result']}")
        if state["is_game_over"]:
            print(f">>> Result: {state['result']} in {step} steps (Optimal was {game.optimal_steps})!")
            break
