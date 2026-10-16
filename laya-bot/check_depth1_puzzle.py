"""
check_depth1_puzzle.py - Test Laya on 1-step, 2-step, and 3-step 8-puzzles.
"""

from bot.eight_puzzle_game import EightPuzzleGame
from bot.decide import choose_move

for depth in [1, 2, 3]:
    print(f"\n================ Testing Scramble Depth {depth} ================")
    game = EightPuzzleGame(seed=42, scramble_depth=depth, max_steps=10)
    state = game.get_state()
    print(f"Start board: {state['board']}, Manhattan: {state['manhattan']}, Optimal: {state['optimal_steps']}")
    
    for step in range(1, 11):
        legal = game.get_legal_moves()
        move, details = choose_move(state, legal, design="K")
        print(f"Step {step}: chosen {move} ({['UP','DOWN','LEFT','RIGHT'][move]}), probs: {details['probabilities']}")
        state = game.submit_move(move)
        print(f"  New Board: {state['board']}, Manhattan: {state['manhattan']}, Over: {state['is_game_over']}, Result: {state['result']}")
        if state["is_game_over"]:
            break
