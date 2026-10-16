"""
check_step5.py - Verification script for Step 5.
Plays 10 full games using Laya via loop.py and logger.py.
Displays:
1. One full game's raw JSONL log lines.
2. The viewer output for the games.
3. The audit result verifying that all moves were chosen by Laya.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.loop import play_one_game
from bot.tictactoe_game import TicTacToeGame
from bot.logger import GameLogger
from tools.viewer import view_log
from tools.audit import audit_log_file


def run_10_games():
    session_id = f"session_step5_{int(time.time())}"
    print(f"Starting 10 full games for session: {session_id}")
    
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logs")
    os.makedirs(log_dir, exist_ok=True)
    logger = GameLogger(session_id=session_id, log_dir=log_dir)

    results = {"X": 0, "O": 0, "draw": 0}

    for game_idx in range(1, 11):
        # We can seed each game to give varied opponent play
        game = TicTacToeGame(seed=2000 + game_idx)
        print(f"Playing game {game_idx}/10...")
        final_state = play_one_game(game=game, logger=logger, game_index=game_idx)
        res = final_state["result"]
        results[res] = results.get(res, 0) + 1
        print(f"  Game {game_idx} finished in {final_state['turn_number']} turns: Result = {res}")

    logger.close()
    print(f"\nCompleted 10 games! Record: {results}")

    log_path = logger.filepath

    # 1. Show Game 1's log lines
    print("\n" + "=" * 60)
    print("STEP 5 CHECK 1: RAW LOG LINES FOR GAME 1")
    print("=" * 60)
    with open(log_path, "r", encoding="utf-8") as f:
        game1_lines = []
        in_game_1 = False
        for line in f:
            data = json.loads(line)
            if data["event"] == "game_start" and data["data"]["game_index"] == 1:
                in_game_1 = True
            if in_game_1:
                game1_lines.append(line.strip())
                if data["event"] == "game_end":
                    break
        for line in game1_lines:
            print(line)

    # 2. Show viewer output
    print("\n" + "=" * 60)
    print("STEP 5 CHECK 2: VIEWER OUTPUT FOR GAMES")
    print("=" * 60)
    view_log(log_path, follow=False)

    # 3. Show audit result
    print("\n" + "=" * 60)
    print("STEP 5 CHECK 3: AUDIT RESULT")
    print("=" * 60)
    audit_passed = audit_log_file(log_path)
    assert audit_passed, "Audit failed!"
    print("\nStep 5 check PASSED successfully!")


if __name__ == "__main__":
    run_10_games()
