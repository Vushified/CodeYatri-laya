"""
viewer.py - Terminal live viewer for Laya game logs.

Tails the newest JSONL log in data/logs/ (or a specified log file) and prints
each decision as it happens:
- Turn number
- Top 3 candidate moves with probabilities
- The chosen move
- Final game outcome
"""

import glob
import json
import os
import sys
import time
from typing import Optional


def get_latest_log_file(log_dir: str = "data/logs") -> Optional[str]:
    """Find the most recently modified .jsonl file in log_dir."""
    files = glob.glob(os.path.join(log_dir, "*.jsonl"))
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def view_log(filepath: str, follow: bool = False):
    """
    Read and display decisions from the specified log file.
    If follow is True, tails the file like tail -f.
    """
    print(f"Viewing log: {filepath}\n" + "=" * 60)
    
    current_game = None
    last_turn = 1
    last_laya_call = None

    with open(filepath, "r", encoding="utf-8") as f:
        while True:
            line = f.readline()
            if not line:
                if follow:
                    time.sleep(0.2)
                    continue
                else:
                    break

            try:
                entry = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            event = entry.get("event")
            data = entry.get("data", {})

            if event == "game_start":
                current_game = data.get("game_index", 1)
                print(f"\n--- GAME {current_game} STARTED (Bot: {data.get('bot_player', 'X')}) ---")

            elif event == "state":
                st = data.get("state", {})
                last_turn = st.get("turn_number", last_turn)

            elif event == "laya_call":
                last_laya_call = data

            elif event == "decision":
                chosen_move = data.get("chosen_move")
                probs = {}
                if last_laya_call and "probabilities" in last_laya_call:
                    probs = {int(k): float(v) for k, v in last_laya_call["probabilities"].items()}

                # Sort moves by probability descending
                sorted_moves = sorted(probs.items(), key=lambda x: x[1], reverse=True)
                top_3 = sorted_moves[:3]
                top_3_str = ", ".join([f"Cell {m}: {p:.3f}" for m, p in top_3])

                print(
                    f"Turn {last_turn} | Chosen: Cell {chosen_move} | "
                    f"Top moves: [{top_3_str}]"
                )

            elif event == "game_end":
                result = data.get("result", "unknown")
                turns = data.get("total_turns", last_turn)
                print(f"--- GAME {current_game} ENDED | Result: {result.upper()} | Turns: {turns} ---\n")

            elif event == "error":
                print(f"ERROR: {data.get('message')}")


if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else get_latest_log_file()
    if not target_file:
        print("No log files found in data/logs/.")
        sys.exit(1)
    view_log(target_file, follow=False)
