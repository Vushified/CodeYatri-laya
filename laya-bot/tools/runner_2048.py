"""
runner_2048.py - Benchmarks Laya prompt designs on 2048 to evaluate score maximization.

Single-player game with no opponent.
Metrics tracked:
- Average Score achieved
- Maximum Score achieved
- Highest Max-Tile achieved (e.g. 64, 128, 256, 512, 1024, 2048)
- Average Turns survived
- Score multiplier vs Random Baseline
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
from bot.game_2048 import Game2048, MOVE_NAMES
from bot.logger import GameLogger


def play_random_baseline_2048(seed: int, max_steps: int = 500) -> Dict[str, Any]:
    """Random baseline: selects random legal moves until game over."""
    game = Game2048(seed=seed, max_steps=max_steps)
    state = game.get_state()

    while not state["is_game_over"]:
        legal = game.get_legal_moves()
        if not legal:
            break
        m = game.rng.choice(legal)
        state = game.submit_move(m)

    return {
        "score": state["score"],
        "max_tile": state["max_tile"],
        "turns": state["steps_taken"],
    }


def play_bot_2048(
    seed: int,
    design: str,
    max_steps: int = 500,
    logger: Optional[GameLogger] = None,
    game_index: int = 1,
) -> Dict[str, Any]:
    """Plays one full game of 2048 using Laya under the specified design."""
    game = Game2048(seed=seed, max_steps=max_steps)
    state = game.get_state()

    if logger:
        logger.log_game_start(game_index=game_index, player="Player")

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

        if logger:
            logger.log_move_result(updated_state=state)

    if logger:
        logger.log_game_end(result=f"Score: {state['score']}, MaxTile: {state['max_tile']}", total_turns=state["steps_taken"])

    return {
        "score": state["score"],
        "max_tile": state["max_tile"],
        "turns": state["steps_taken"],
    }


def run_2048_benchmark(
    seeds: List[int],
    designs: List[str],
    max_steps: int = 500,
    session_id: str = "eval_2048",
) -> List[Dict[str, Any]]:
    """Runs paired-seed evaluation of 2048 score maximization."""
    total_games = len(seeds)
    results = []
    logger = GameLogger(session_id=session_id, log_dir="data/logs")

    print(f"\n================================================================================")
    print(f"Running 2048 Score Maximization Benchmark on {total_games} paired seed(s) (Max Steps: {max_steps})")
    print(f"Logging session: {session_id} (data/logs/{session_id}.jsonl)")
    print(f"================================================================================")

    # 1. Random Baseline
    print("Evaluating baseline: random moves...")
    t0 = time.time()
    rand_scores = []
    rand_tiles = []
    rand_turns = []

    for s in seeds:
        res = play_random_baseline_2048(seed=s, max_steps=max_steps)
        rand_scores.append(res["score"])
        rand_tiles.append(res["max_tile"])
        rand_turns.append(res["turns"])

    rand_avg_score = sum(rand_scores) / len(rand_scores)
    rand_max_score = max(rand_scores)
    rand_max_tile = max(rand_tiles)
    rand_avg_turns = sum(rand_turns) / len(rand_turns)
    dt_rand = time.time() - t0

    print(f"  random done in {dt_rand:.1f}s -> Avg Score: {rand_avg_score:.1f}, Max Score: {rand_max_score}, Max Tile: {rand_max_tile}, Avg Turns: {rand_avg_turns:.1f}")

    results.append({
        "mode": "random-baseline",
        "avg_score": f"{rand_avg_score:.1f}",
        "max_score": rand_max_score,
        "max_tile": rand_max_tile,
        "avg_turns": f"{rand_avg_turns:.1f}",
        "vs_random": "1.00x",
        "score_val": rand_avg_score,
    })

    # 2. Benchmark each Laya design
    for d in designs:
        print(f"\nEvaluating mode: Design {d} ({total_games} games)...")
        t_d = time.time()
        scores = []
        tiles = []
        turns = []

        for idx, s in enumerate(seeds, 1):
            res = play_bot_2048(
                seed=s,
                design=d,
                max_steps=max_steps,
                logger=logger,
                game_index=idx,
            )
            scores.append(res["score"])
            tiles.append(res["max_tile"])
            turns.append(res["turns"])
            print(f"  Game {idx}/{total_games} (Seed {s}): Score={res['score']}, MaxTile={res['max_tile']}, Turns={res['turns']}")

        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        top_tile = max(tiles)
        avg_turns = sum(turns) / len(turns)
        multiplier = avg_score / rand_avg_score if rand_avg_score > 0 else 1.0
        dt = time.time() - t_d

        print(f"  Design {d} done in {dt:.1f}s -> Avg Score: {avg_score:.1f}, Max Score: {max_score}, Top Tile: {top_tile}, Avg Turns: {avg_turns:.1f} ({multiplier:.2f}x random)")

        results.append({
            "mode": f"Design {d}",
            "avg_score": f"{avg_score:.1f}",
            "max_score": max_score,
            "max_tile": top_tile,
            "avg_turns": f"{avg_turns:.1f}",
            "vs_random": f"{multiplier:.2f}x",
            "score_val": avg_score,
        })

    # Print summary table
    print("\n" + "=" * 80)
    print(f"{'mode':<18} {'avg_score':>12} {'max_score':>12} {'max_tile':>12} {'avg_turns':>12} {'vs_random':>12}")
    print("-" * 80)
    for r in results:
        print(f"{r['mode']:<18} {r['avg_score']:>12} {str(r['max_score']):>12} {str(r['max_tile']):>12} {r['avg_turns']:>12} {r['vs_random']:>12}")
    print("=" * 80)

    # Winner
    bot_results = [r for r in results if r["mode"] != "random-baseline"]
    if bot_results:
        best = max(bot_results, key=lambda x: x["score_val"])
        print(f"\nScore Maximization Winner: {best['mode']} with an average score of {best['avg_score']} (Max Score: {best['max_score']}, Top Tile: {best['max_tile']}, {best['vs_random']} vs random)!\n")

    return results


def main():
    parser = argparse.ArgumentParser(description="2048 Score Maximization Benchmark for Laya")
    parser.add_argument("--games", type=int, default=10, help="Number of games to evaluate")
    parser.add_argument("--max-steps", type=int, default=400, help="Maximum moves per game")
    parser.add_argument("--designs", nargs="+", default=["B", "KF", "A"], help="Designs to test")
    parser.add_argument("--seeds-file", type=str, default="data/tune_seeds.json", help="Path to seed JSON file")
    parser.add_argument("--session-id", type=str, default="eval_2048", help="Logging session ID")

    args = parser.parse_args()

    with open(args.seeds_file, "r", encoding="utf-8") as f:
        seeds = json.load(f)[:args.games]

    run_2048_benchmark(
        seeds=seeds,
        designs=args.designs,
        max_steps=args.max_steps,
        session_id=args.session_id,
    )


if __name__ == "__main__":
    main()
