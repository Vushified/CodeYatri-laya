"""
evaluate.py - Benchmark and compare question designs on TUNE and TEST sets.

Uses tools/minimax.py ONLY as a referee to score Laya's moves.
Evaluates:
- Good-move rate: fraction of positions where Laya picked a minimax-optimal move.
- Chance level: baseline random accuracy = mean(len(optimal_moves) / len(legal_moves)).
- 4 Question Designs:
    * A: One yes/no (noul) per legal move, with facts (Step 4)
    * B: One multiple-choice (choice) question: "which move is best?"
    * C: Design A without the facts (board text only)
    * D: Design A plus past move history
- Compares A, B, C, D on the TUNE set (50 positions).
- Evaluates the winning design once on the fresh TEST set (50 positions).
- Plays 100 full games against random opponent to measure win/draw/loss.
"""

import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.describe import describe_board, describe_move, describe_state_and_moves
from bot.laya_client import ask
from bot.tictactoe_game import TicTacToeGame
from tools.minimax import get_optimal_moves


# --- Design Implementations ---

def decide_design_a(board: List[str], legal_moves: List[int]) -> int:
    """Design A: noul per legal move with facts."""
    state = {"board": board}
    state_text = describe_state_and_moves(state, legal_moves)
    questions = {
        f"move_{m}": {"type": "noul", "instructions": f"Is playing cell {m} a good move for X?"}
        for m in legal_moves
    }
    resp = ask(state_text, questions)
    probs = {m: float(resp["answers"][f"move_{m}"]["noul"]) for m in legal_moves}
    return max(probs, key=probs.get)


def decide_design_b(board: List[str], legal_moves: List[int]) -> int:
    """Design B: single multiple-choice question."""
    state = {"board": board}
    state_text = describe_state_and_moves(state, legal_moves)
    criteria = {f"c_{m}": f"Cell {m}" for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move is best for X?",
            "criteria": criteria,
        }
    }
    resp = ask(state_text, questions)
    choice_str = resp["answers"]["best_move"]["choice"]
    chosen_m = int(choice_str.split("_")[1])
    return chosen_m


def decide_design_c(board: List[str], legal_moves: List[int]) -> int:
    """Design C: noul per legal move WITHOUT facts (board only)."""
    state = {"board": board}
    state_text = describe_board(state)
    questions = {
        f"move_{m}": {"type": "noul", "instructions": f"Is playing cell {m} a good move for X?"}
        for m in legal_moves
    }
    resp = ask(state_text, questions)
    probs = {m: float(resp["answers"][f"move_{m}"]["noul"]) for m in legal_moves}
    return max(probs, key=probs.get)


def decide_design_d(board: List[str], legal_moves: List[int]) -> int:
    """Design D: Design A plus synthetic history of past moves."""
    state = {"board": board}
    x_placed = [i for i, c in enumerate(board) if c == "X"]
    o_placed = [i for i, c in enumerate(board) if c == "O"]
    history_tokens = []
    for turn_idx, (x_m, o_m) in enumerate(zip(x_placed, o_placed), 1):
        history_tokens.append(f"Turn {turn_idx}: X played {x_m}, O played {o_m}")
    history_text = "Past move history: " + ("; ".join(history_tokens) if history_tokens else "None (Opening).") + ". "

    state_text = history_text + describe_state_and_moves(state, legal_moves)
    questions = {
        f"move_{m}": {"type": "noul", "instructions": f"Is playing cell {m} a good move for X?"}
        for m in legal_moves
    }
    resp = ask(state_text, questions)
    probs = {m: float(resp["answers"][f"move_{m}"]["noul"]) for m in legal_moves}
    return max(probs, key=probs.get)


# --- Evaluation Engine ---

def evaluate_dataset(positions: List[Dict], decide_fn, desc: str) -> Dict[str, float]:
    """Evaluate a decision function across a position dataset."""
    total = len(positions)
    optimal_count = 0
    chance_sum = 0.0

    print(f"  Evaluating {desc} on {total} positions...")
    t0 = time.time()
    for idx, pos in enumerate(positions):
        board = pos["board"]
        legal = pos["legal_moves"]
        optimal = pos["optimal_moves"]

        chance_sum += len(optimal) / len(legal)
        chosen = decide_fn(board, legal)

        if chosen in optimal:
            optimal_count += 1

    dt = time.time() - t0
    rate = optimal_count / total
    chance = chance_sum / total
    print(f"    Done in {dt:.1f}s | Score: {optimal_count}/{total} ({rate*100:.1f}%) | Chance: {chance*100:.1f}%")

    return {
        "optimal_count": optimal_count,
        "total": total,
        "rate": rate,
        "chance": chance,
    }


def play_100_games(decide_fn) -> Dict[str, int]:
    """Play 100 full games of tic-tac-toe against random opponent."""
    results = {"X": 0, "O": 0, "draw": 0}
    print("  Playing 100 full games against random opponent...")
    for i in range(1, 101):
        game = TicTacToeGame(seed=5000 + i)
        state = game.reset()
        while not state["is_game_over"]:
            legal = game.get_legal_moves()
            if not legal:
                break
            move = decide_fn(state["board"], legal)
            state = game.submit_move(move)
        res = state["result"]
        results[res] = results.get(res, 0) + 1
    return results


def main():
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    tune_path = os.path.join(data_dir, "positions_tune.json")
    test_path = os.path.join(data_dir, "positions_test.json")

    with open(tune_path, "r", encoding="utf-8") as f:
        tune_positions = json.load(f)
    with open(test_path, "r", encoding="utf-8") as f:
        test_positions = json.load(f)

    print("=" * 70)
    print("STEP 6: EVALUATION EXPERIMENTS (TUNE SET)")
    print("=" * 70)

    designs = {
        "Design A (noul + facts)": decide_design_a,
        "Design B (choice best)": decide_design_b,
        "Design C (noul, board only)": decide_design_c,
        "Design D (noul + facts + history)": decide_design_d,
    }

    tune_results = {}
    for name, fn in designs.items():
        res = evaluate_dataset(tune_positions, fn, name)
        tune_results[name] = res

    # Pick best design strictly based on TUNE score
    best_design_name = max(tune_results, key=lambda k: tune_results[k]["rate"])
    best_fn = designs[best_design_name]
    print("\n" + "=" * 70)
    print(f"BEST DESIGN ON TUNE SET: {best_design_name} (Score: {tune_results[best_design_name]['rate']*100:.1f}%)")
    print("Running winning design ONCE on fresh TEST set (No tuning on test set)...")
    print("=" * 70)

    test_result = evaluate_dataset(test_positions, best_fn, f"{best_design_name} on TEST")

    print("\n" + "=" * 70)
    print("RUNNING 100 GAMES FOR BEST DESIGN")
    print("=" * 70)
    record = play_100_games(best_fn)
    print(f"  100-Game Record: X Wins: {record.get('X',0)}, Draws: {record.get('draw',0)}, O Wins: {record.get('O',0)}")

    summary = {
        "tune_results": {k: {"rate": v["rate"], "chance": v["chance"]} for k, v in tune_results.items()},
        "best_design": best_design_name,
        "test_result": {"rate": test_result["rate"], "chance": test_result["chance"]},
        "game_record_100": record,
    }

    summary_file = os.path.join(data_dir, "evaluation_summary.json")
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSummary saved to {summary_file}")


if __name__ == "__main__":
    main()
