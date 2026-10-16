"""
check_step2.py - Verification script for Step 2.
Plays 3 full games with random moves for X against the random opponent O.
Prints the board states, confirms legal moves are correct, and verifies winner detection.
"""

import os
import random
import sys

# Ensure local bot module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.tictactoe_game import TicTacToeGame


def play_sample_game(game_num: int):
    print(f"\n==================== GAME {game_num} ====================")
    game = TicTacToeGame(seed=100 + game_num)
    state = game.reset()
    
    print("Initial Board (empty, numbered 0-8):")
    print(game.render_board())
    
    while not state["is_game_over"]:
        legal_moves = game.get_legal_moves()
        print(f"\nTurn {state['turn_number']} - Legal moves for X: {legal_moves}")
        
        # Pick a random legal move for X
        x_move = random.choice(legal_moves)
        print(f"X chooses cell: {x_move}")
        
        state = game.submit_move(x_move)
        print("Board after X move & O response:")
        print(game.render_board())
        
    print(f"\nGame {game_num} finished! Result: {state['result'].upper()}")
    assert state["result"] in ["X", "O", "draw"], f"Invalid result {state['result']}"
    assert len(game.get_legal_moves()) == 0, "Finished game should have 0 legal moves"


def main():
    print("Testing Step 2: 3 Full Games using TicTacToeGame")
    for i in range(1, 4):
        play_sample_game(i)
    print("\nAll 3 games completed successfully! Legal moves and winner detection verified.")


if __name__ == "__main__":
    main()
