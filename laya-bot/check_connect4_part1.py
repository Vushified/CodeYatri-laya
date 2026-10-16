"""
check_connect4_part1.py - Part 1 check: play 3 full games with both players using random moves.
Print each board after every move in a readable grid. Confirm wins/draws detected correctly.
"""

import random
from bot.connect4_game import Connect4Game

def run_test():
    for game_num in range(1, 4):
        print(f"==================================================")
        print(f"               STARTING GAME {game_num}           ")
        print(f"==================================================")
        game = Connect4Game(seed=1000 + game_num, opponent_mode="random")
        state = game.reset()
        rng_x = random.Random(2000 + game_num)
        turn = 0

        while not state["is_game_over"]:
            turn += 1
            legal = game.get_legal_moves()
            if not legal:
                break
            x_col = rng_x.choice(legal)
            state = game.submit_move(x_col)
            print(f"Turn {turn}: X played col {x_col}")
            print(game.render_board())
            print()

        print(f">>> GAME {game_num} COMPLETED: Result = {state['result']} after {turn} turns.\n")

if __name__ == "__main__":
    run_test()
