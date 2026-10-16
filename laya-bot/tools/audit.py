"""
audit.py - Log auditor that enforces Hard Rule 1 & Rule 7.

Validates that:
1. Every 'move_sent' event has an immediately preceding 'decision' and 'laya_call'.
2. The move in 'move_sent' strictly matches the move in 'decision'.
3. The chosen move had the highest probability among all evaluated legal moves in the 'laya_call'.
4. Timestamps are monotonic: timestamp(laya_call) <= timestamp(decision) <= timestamp(move_sent).
5. Fails loudly with an exit code of 1 if any rule is violated.
"""

import json
import os
import sys
from typing import Dict, List, Optional


def audit_log_file(filepath: str) -> bool:
    """
    Audit a single JSONL log file.
    Returns True if log passes all checks, raises an AssertionError / returns False otherwise.
    """
    print(f"Auditing log file: {filepath}")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Log file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    if not lines:
        raise ValueError(f"Log file {filepath} is empty.")

    pending_laya_call: Optional[Dict] = None
    pending_decision: Optional[Dict] = None
    verified_moves_count = 0
    games_count = 0

    for line_num, line in enumerate(lines, 1):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            raise AssertionError(f"Line {line_num}: Invalid JSON - {e}")

        event = entry.get("event")
        data = entry.get("data", {})
        ts = entry.get("timestamp", 0)

        if event == "game_start":
            games_count += 1
            pending_laya_call = None
            pending_decision = None

        elif event == "laya_call":
            pending_laya_call = {"data": data, "timestamp": ts, "line": line_num}

        elif event == "decision":
            if not pending_laya_call:
                raise AssertionError(
                    f"Line {line_num}: 'decision' event found without prior 'laya_call'!"
                )
            if ts < pending_laya_call["timestamp"]:
                raise AssertionError(
                    f"Line {line_num}: 'decision' timestamp ({ts}) predates 'laya_call' ({pending_laya_call['timestamp']})!"
                )
            pending_decision = {
                "chosen_move": data.get("chosen_move"),
                "timestamp": ts,
                "line": line_num,
            }

        elif event == "move_sent":
            sent_move = data.get("move")
            if not pending_laya_call:
                raise AssertionError(
                    f"Line {line_num}: 'move_sent' ({sent_move}) has NO preceding 'laya_call'!"
                )
            if not pending_decision:
                raise AssertionError(
                    f"Line {line_num}: 'move_sent' ({sent_move}) has NO preceding 'decision'!"
                )
            if sent_move != pending_decision["chosen_move"]:
                raise AssertionError(
                    f"Line {line_num}: 'move_sent' ({sent_move}) does not match 'decision' ({pending_decision['chosen_move']})!"
                )
            if ts < pending_decision["timestamp"]:
                raise AssertionError(
                    f"Line {line_num}: 'move_sent' timestamp ({ts}) predates 'decision' ({pending_decision['timestamp']})!"
                )

            # Verify the chosen move was indeed the highest probability in laya_call
            probs = pending_laya_call["data"].get("probabilities", {})
            if probs:
                max_prob_move = max(probs, key=lambda k: float(probs[k]))
                if str(sent_move) != str(max_prob_move):
                    raise AssertionError(
                        f"Line {line_num}: Laya chose move {max_prob_move} (p={probs[max_prob_move]}), "
                        f"but move_sent was {sent_move}!"
                    )

            verified_moves_count += 1
            # Reset pending state for the next turn
            pending_laya_call = None
            pending_decision = None

    print(
        f"Audit PASSED! Checked {games_count} game(s) and {verified_moves_count} move(s). "
        "Every sent move had a strictly valid, logged Laya decision."
    )
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to latest log in data/logs
        import glob
        logs = glob.glob("data/logs/*.jsonl")
        if not logs:
            print("Usage: python tools/audit.py <path_to_log.jsonl>")
            sys.exit(1)
        target = max(logs, key=os.path.getmtime)
    else:
        target = sys.argv[1]

    try:
        audit_log_file(target)
    except AssertionError as err:
        print(f"\nAUDIT FAILED! {err}", file=sys.stderr)
        sys.exit(1)
