"""
eight_puzzle_runner.py - Benchmarks Laya across prompt designs on 8-Puzzle to find which mode achieves minimum steps.

Metrics tracked:
- Solved Rate (% solved within step limit)
- Average steps taken on solved puzzles
- Minimum steps achieved
- Efficiency vs Optimal (ratio of actual steps to A* shortest path)
"""

import argparse
import json
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.decide import choose_move
from bot.eight_puzzle_game import EightPuzzleGame, solve_a_star
from bot.logger import GameLogger


def play_random_baseline_puzzle(seed: int, scramble_depth: int, max_steps: int = 50) -> Dict[str, Any]:
    """Pure random move selection baseline (avoiding immediate undo)."""
    game = EightPuzzleGame(seed=seed, scramble_depth=scramble_depth, max_steps=max_steps)
    prev_move = None
    state = game.get_state()
    optimal_steps = state.get("optimal_steps", 0)

    while not state["is_game_over"]:
        legal = game.get_legal_moves()
        if not legal:
            break
        if prev_move is not None:
            opposite = {0: 1, 1: 0, 2: 3, 3: 2}[prev_move]
            non_undo = [m for m in legal if m != opposite]
            candidates = non_undo if non_undo else legal
        else:
            candidates = legal
        m = game.rng.choice(candidates)
        prev_move = m
        state = game.submit_move(m)

    return {
        "solved": state["result"] == "win",
        "steps": state["steps_taken"],
        "optimal": optimal_steps,
    }


def play_bot_puzzle(
    seed: int,
    design: str,
    scramble_depth: int,
    max_steps: int = 50,
    logger: Optional[GameLogger] = None,
    game_index: int = 1,
) -> Dict[str, Any]:
    """Plays one 8-puzzle game with Laya using the specified prompt design."""
    game = EightPuzzleGame(seed=seed, scramble_depth=scramble_depth, max_steps=max_steps)
    state = game.get_state()
    optimal_steps = state.get("optimal_steps", 0)

    if logger:
        logger.log_game_start(game_index=game_index, player="Player")

    history = []
    # Avoid cyclic loops by tracking seen board positions
    while not state["is_game_over"]:
        legal = game.get_legal_moves()
        if not legal:
            break

        if logger:
            logger.log_state(state, legal)

        move, details = choose_move(
            state=state,
            legal_moves=legal,
            design=design,
            history=history,
        )

        if logger:
            logger.log_laya_call(
                state_text=details.get("state_text", ""),
                questions=details.get("questions", {}),
                raw_answer=details.get("raw_response", {}),
                probabilities=details.get("probabilities", {}),
            )
            logger.log_decision(chosen_move=move)
            logger.log_move_sent(move=move)

        state = game.submit_move(move)
        history.append({"move": move, "state": state})

        if logger:
            logger.log_move_result(updated_state=state)

    if logger:
        logger.log_game_end(result=state["result"], total_turns=state["steps_taken"])

    return {
        "solved": state["result"] == "win",
        "steps": state["steps_taken"],
        "optimal": optimal_steps,
    }


def run_eight_puzzle_benchmark(
    seeds: List[int],
    designs: List[str],
    scramble_depth: int = 8,
    max_steps: int = 50,
    session_id: str = "eight_puzzle_eval",
) -> List[Dict[str, Any]]:
    """Runs paired-seed evaluation across 8-puzzle designs."""
    total_puzzles = len(seeds)
    results = []
    logger = GameLogger(session_id=session_id, log_dir="data/logs")

    print(f"\n================================================================================")
    print(f"Running 8-Puzzle Benchmark on {total_puzzles} paired seed(s) (Scramble Depth: {scramble_depth}, Max Steps: {max_steps})")
    print(f"Logging session: {session_id} (data/logs/{session_id}.jsonl)")
    print(f"================================================================================")

    # 1. Baseline: Random Non-Reversing Walker
    print("Evaluating baseline: random-walker...")
    t0 = time.time()
    rand_solved = 0
    rand_steps_list = []
    optimal_steps_list = []

    for s in seeds:
        res = play_random_baseline_puzzle(seed=s, scramble_depth=scramble_depth, max_steps=max_steps)
        optimal_steps_list.append(res["optimal"])
        if res["solved"]:
            rand_solved += 1
            rand_steps_list.append(res["steps"])

    rand_solve_pct = (rand_solved / total_puzzles) * 100
    rand_avg_steps = sum(rand_steps_list) / len(rand_steps_list) if rand_steps_list else max_steps
    avg_opt_steps = sum(optimal_steps_list) / len(optimal_steps_list) if optimal_steps_list else 1
    print(f"  random-walker done in {time.time()-t0:.1f}s -> Solved: {rand_solved}/{total_puzzles} ({rand_solve_pct:.1f}%), Avg Steps: {rand_avg_steps:.1f} (Optimal A*: {avg_opt_steps:.1f})")

    results.append({
        "mode": "random-walker",
        "solved_count": rand_solved,
        "solved%": f"{rand_solve_pct:.1f}%",
        "avg_steps": f"{rand_avg_steps:.1f}",
        "min_steps": min(rand_steps_list) if rand_steps_list else "-",
        "optimal_avg": f"{avg_opt_steps:.1f}",
        "eff_ratio": f"{rand_avg_steps / avg_opt_steps:.2f}x" if rand_steps_list else "N/A",
        "solve_num": rand_solve_pct,
        "step_num": rand_avg_steps,
    })

    # 2. Iterate across requested Laya designs
    for d in designs:
        print(f"\nEvaluating mode: Design {d} ({total_puzzles} puzzles)...")
        t_d = time.time()
        d_solved = 0
        d_steps_list = []

        for idx, s in enumerate(seeds, 1):
            res = play_bot_puzzle(
                seed=s,
                design=d,
                scramble_depth=scramble_depth,
                max_steps=max_steps,
                logger=logger,
                game_index=idx,
            )
            if res["solved"]:
                d_solved += 1
                d_steps_list.append(res["steps"])

            if idx % 10 == 0 or idx == total_puzzles:
                print(f"  ... completed {idx}/{total_puzzles} puzzles")

        d_solve_pct = (d_solved / total_puzzles) * 100
        d_avg_steps = sum(d_steps_list) / len(d_steps_list) if d_steps_list else max_steps
        d_min_steps = min(d_steps_list) if d_steps_list else "-"
        eff = f"{d_avg_steps / avg_opt_steps:.2f}x" if d_steps_list else "N/A"
        dt = time.time() - t_d

        print(f"  Design {d} completed in {dt:.1f}s -> Solved: {d_solved}/{total_puzzles} ({d_solve_pct:.1f}%), Avg Steps: {d_avg_steps:.1f}, Min Steps: {d_min_steps} (vs Opt {avg_opt_steps:.1f})")

        results.append({
            "mode": f"Design {d}",
            "solved_count": d_solved,
            "solved%": f"{d_solve_pct:.1f}%",
            "avg_steps": f"{d_avg_steps:.1f}",
            "min_steps": d_min_steps,
            "optimal_avg": f"{avg_opt_steps:.1f}",
            "eff_ratio": eff,
            "solve_num": d_solve_pct,
            "step_num": d_avg_steps,
        })

    # Print Table
    print("\n" + "=" * 90)
    print(f"{'mode':<18} {'solved%':>10} {'avg_steps':>12} {'min_steps':>12} {'optimal_avg':>14} {'eff_vs_optimal':>16}")
    print("-" * 90)
    for r in results:
        print(f"{r['mode']:<18} {r['solved%']:>10} {r['avg_steps']:>12} {str(r['min_steps']):>12} {r['optimal_avg']:>14} {r['eff_ratio']:>16}")
    print("=" * 90)

    # Find mode that gets minimum steps
    solved_modes = [r for r in results if r["solved_count"] > 0 and r["mode"] != "random-walker"]
    if solved_modes:
        best_mode = min(solved_modes, key=lambda x: x["step_num"])
        print(f"\nMinimum Steps Winner: {best_mode['mode']} with an average of {best_mode['avg_steps']} steps (Min achieved: {best_mode['min_steps']} steps, Solved Rate: {best_mode['solved%']}).")
    else:
        print("\nNo Laya mode solved the puzzles within step cutoff.")

    return results


def main():
    parser = argparse.ArgumentParser(description="8-Puzzle Step Minimization Benchmark for Laya")
    parser.add_argument("--puzzles", type=int, default=50, help="Number of puzzle instances to evaluate")
    parser.add_argument("--depth", type=int, default=8, help="Scramble depth (complexity of initial state)")
    parser.add_argument("--max-steps", type=int, default=40, help="Maximum moves allowed before timeout")
    parser.add_argument("--designs", nargs="+", default=["K", "KF", "B"], help="List of designs to test")
    parser.add_argument("--seeds-file", type=str, default="data/tune_seeds.json", help="Path to seed JSON file")
    parser.add_argument("--session-id", type=str, default="eight_puzzle_eval", help="Logging session ID")

    args = parser.parse_args()

    with open(args.seeds_file, "r", encoding="utf-8") as f:
        seeds = json.load(f)[:args.puzzles]

    run_eight_puzzle_benchmark(
        seeds=seeds,
        designs=args.designs,
        scramble_depth=args.depth,
        max_steps=args.max_steps,
        session_id=args.session_id,
    )


if __name__ == "__main__":
    main()
