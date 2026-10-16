"""
runner.py - Paired-seed comparison runner for fair, reproducible evaluations.

Hard Rules Enforced:
1. Every real move comes from a logged Laya call.
2. Fair comparison: Every setting faces the exact same sequence of seeds
   and opponent moves.
3. Every run includes a random-control baseline using the exact same seeds.
4. Errors are never swallowed silently.
"""

import argparse
import copy
import csv
import json
import os
import random
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.decide import choose_move
from bot.logger import GameLogger
from bot.tictactoe_game import TicTacToeGame


def load_or_create_seeds(filepath: str, count: int) -> List[int]:
    """Load seeds from JSON file or create new ones if file does not exist."""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            seeds = json.load(f)
            if len(seeds) < count:
                print(f"Warning: seeds file has {len(seeds)} seeds, requested {count}. Using all.")
                return seeds
            return seeds[:count]
    else:
        print(f"Seeds file '{filepath}' not found. Generating {count} seeds...")
        rng = random.Random(42)
        seeds = [rng.randint(1000, 999999) for _ in range(count)]
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(seeds, f, indent=2)
        return seeds


def play_random_control_game(
    seed: int,
    opponent: str = "random",
    x_player: str = "random",
    game_name: str = "tictactoe",
) -> str:
    """
    Plays one game baseline using the seed.
    If x_player == 'smart_random', X plays smart random (immediate win -> immediate block -> random).
    Opponent O plays according to opponent mode ('random' or 'smart_random').
    """
    if game_name == "connect4":
        from bot.connect4_game import Connect4Game
        game = Connect4Game(seed=seed, opponent_mode=opponent)
    else:
        game = TicTacToeGame(seed=seed, opponent_mode=opponent)

    rng_x = random.Random(seed * 7 + 13)
    state = game.reset()

    while not state["is_game_over"]:
        legal = game.get_legal_moves()
        if not legal:
            break
        if x_player == "smart_random":
            if game_name == "connect4":
                win_move = game._find_immediate_winning_move("X", legal)
                if win_move is not None:
                    x_move = win_move
                else:
                    block_move = game._find_immediate_winning_move("O", legal)
                    if block_move is not None:
                        x_move = block_move
                    else:
                        x_move = rng_x.choice(legal)
            else:
                win_move = game._find_winning_move("X", legal)
                if win_move is not None:
                    x_move = win_move
                else:
                    block_move = game._find_winning_move("O", legal)
                    if block_move is not None:
                        x_move = block_move
                    else:
                        x_move = rng_x.choice(legal)
        else:
            x_move = rng_x.choice(legal)

        state = game.submit_move(x_move)

    return state["result"]


def play_bot_game(
    seed: int,
    design: str,
    input_mode: str,
    wording: str,
    opponent: str = "random",
    game_name: str = "tictactoe",
    logger: Optional[GameLogger] = None,
    game_index: int = 1,
) -> Tuple[str, Optional[str]]:
    """
    Plays one game using Laya with the given configuration against the opponent.
    Returns (result, error_message).
    """
    if game_name == "connect4":
        from bot.connect4_game import Connect4Game
        game = Connect4Game(seed=seed, opponent_mode=opponent)
    else:
        game = TicTacToeGame(seed=seed, opponent_mode=opponent)

    state = game.reset()
    history = []
    turn_count = 0

    if logger:
        logger.log_game_start(game_index=game_index, player="X")

    try:
        while not state["is_game_over"]:
            turn_count += 1
            legal = game.get_legal_moves()
            if not legal:
                break

            if logger:
                logger.log_state(state, legal)

            move, details = choose_move(
                state=state,
                legal_moves=legal,
                design=design,
                input_mode=input_mode,
                wording=wording,
                history=history,
            )

            # Log before acting (Rule 7)
            if logger:
                state_text = details.get("state_text", "")
                questions = details.get("questions") or details.get("round_2", {}).get("questions", {})
                raw_resp = details.get("raw_response") or details.get("round_2", {}).get("raw_response", {})
                probs = details.get("probabilities", {})
                logger.log_laya_call(
                    state_text=state_text,
                    questions=questions,
                    raw_answer=raw_resp,
                    probabilities=probs,
                )
                logger.log_decision(chosen_move=move)
                logger.log_move_sent(move=move)

            history.append({"player": "X", "move": move})
            state = game.submit_move(move)

            if logger:
                logger.log_move_result(updated_state=state)

        if logger:
            logger.log_game_end(result=state["result"], total_turns=turn_count)

        return state["result"], None

    except Exception as e:
        if logger:
            logger.log_error(str(e), {"turn_count": turn_count})
        return "error", str(e)


def run_benchmark(
    seeds: List[int],
    designs: List[str],
    inputs: List[str],
    wordings: List[str],
    opponent: str = "random",
    game: str = "tictactoe",
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Run full benchmark across settings using paired seeds.
    """
    total_games = len(seeds)
    results = []
    baseline_name = "random-control-smart" if opponent == "smart_random" else "random-control"
    log_name = session_id or f"runner_{game}_{opponent}_{int(time.time())}"
    logger = GameLogger(session_id=log_name, log_dir="data/logs")

    print(f"\nRunning benchmark on {total_games} paired seed(s) [Game: {game}] vs opponent '{opponent}'...")
    print(f"Logging session: {log_name} (data/logs/{log_name}.jsonl)")

    # 1. Run Baseline (Random Control)
    print(f"Evaluating baseline: {baseline_name}...")
    t0 = time.time()
    rc_wins = rc_draws = rc_losses = 0
    x_player_mode = "smart_random" if opponent == "smart_random" else "random"
    for s in seeds:
        res = play_random_control_game(s, opponent=opponent, x_player=x_player_mode, game_name=game)
        if res == "X":
            rc_wins += 1
        elif res == "draw":
            rc_draws += 1
        elif res == "O":
            rc_losses += 1

    rc_win_pct = (rc_wins / total_games) * 100
    rc_loss_pct = (rc_losses / total_games) * 100
    print(f"  {baseline_name} done in {time.time()-t0:.1f}s -> {rc_wins}W {rc_draws}D {rc_losses}L ({rc_win_pct:.1f}% Win)")

    # 2. Iterate across all requested settings
    for d in designs:
        for inp in inputs:
            for w in wordings:
                if game == "connect4":
                    setting_name = d
                else:
                    setting_name = f"{d}-{w}-{inp}" if d in ("A", "D", "F") else f"{d}-{inp}"
                print(f"\nEvaluating setting: {setting_name} ({total_games} games)...")
                t_setting = time.time()
                wins = draws = losses = errors = 0

                for idx, s in enumerate(seeds, 1):
                    res, err = play_bot_game(
                        s,
                        design=d,
                        input_mode=inp,
                        wording=w,
                        opponent=opponent,
                        game_name=game,
                        logger=logger,
                        game_index=idx,
                    )
                    if err:
                        errors += 1
                        print(f"  [Error in game {idx} (seed {s})]: {err}", file=sys.stderr)
                    elif res == "X":
                        wins += 1
                    elif res == "draw":
                        draws += 1
                    elif res == "O":
                        losses += 1

                    if idx % 50 == 0 or idx == total_games:
                        print(f"  ... completed {idx}/{total_games} games")

                win_pct = (wins / total_games) * 100
                loss_pct = (losses / total_games) * 100
                margin = win_pct - rc_win_pct
                dt = time.time() - t_setting
                print(f"  Setting {setting_name} completed in {dt:.1f}s -> {wins}W {draws}D {losses}L ({win_pct:.1f}% Win, Errors: {errors})")

                results.append({
                    "setting": setting_name,
                    "design": d,
                    "input": inp,
                    "wording": w,
                    "wins": wins,
                    "draws": draws,
                    "losses": losses,
                    "errors": errors,
                    "win%": f"{win_pct:.1f}%",
                    "loss%": f"{loss_pct:.1f}%",
                    "margin_vs_baseline": f"{margin:+.1f}%",
                    "win_num": win_pct,
                })

    # Add baseline to results
    results.append({
        "setting": baseline_name,
        "design": "baseline",
        "input": "none",
        "wording": "none",
        "wins": rc_wins,
        "draws": rc_draws,
        "losses": rc_losses,
        "errors": 0,
        "win%": f"{rc_win_pct:.1f}%",
        "loss%": f"{rc_loss_pct:.1f}%",
        "margin_vs_baseline": "0.0% (baseline)",
        "win_num": rc_win_pct,
    })

    # Sort real settings by win rate descending (baseline at end)
    real_settings = [r for r in results if r["setting"] != baseline_name]
    real_settings.sort(key=lambda x: x["win_num"], reverse=True)
    ordered_results = real_settings + [r for r in results if r["setting"] == baseline_name]

    # Print Table
    print("\n" + "=" * 80)
    print(f"{'setting':<22} {'wins':>6} {'draws':>6} {'losses':>7} {'win%':>8} {'loss%':>8}  {'margin_vs_baseline':>18}")
    print("-" * 80)
    for r in ordered_results:
        print(f"{r['setting']:<22} {r['wins']:>6} {r['draws']:>6} {r['losses']:>7} {r['win%']:>8} {r['loss%']:>8}  {r['margin_vs_baseline']:>18}")
    print("=" * 80)

    if real_settings:
        best = real_settings[0]
        print(f"\nBest Setting: {best['setting']} with {best['win%']} Win Rate (vs {rc_win_pct:.1f}% baseline, margin {best['margin_vs_baseline']}).")

    # Write CSV if requested
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["setting", "wins", "draws", "losses", "errors", "win%", "loss%", "margin_vs_baseline"]
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in ordered_results:
                writer.writerow(r)
        print(f"Results saved to {output_path}")

    return ordered_results


def main():
    parser = argparse.ArgumentParser(description="Paired-seed runner for Laya bot comparisons.")
    parser.add_argument("--game", type=str, default="tictactoe", choices=["tictactoe", "connect4"], help="Game to play: tictactoe or connect4")
    parser.add_argument("--games", type=int, default=300, help="Number of games to run per setting")
    parser.add_argument("--seeds-file", type=str, default="data/tune_seeds.json", help="Path to seed JSON file")
    parser.add_argument("--designs", nargs="+", default=["A"], help="List of designs to test (A, B, C, D, E, F, I, J, K, KP, EK, KF)")
    parser.add_argument("--opponent", type=str, default="random", choices=["random", "smart_random"], help="Opponent mode: random or smart_random")
    parser.add_argument("--wording", nargs="+", default=["good"], help="List of wordings to test (good, safe, wins, hurts_opponent)")
    parser.add_argument("--input", nargs="+", default=["board"], help="Input representation (board, facts, history)")
    parser.add_argument("--output", type=str, default=None, help="Path to export CSV results")
    parser.add_argument("--session-id", type=str, default=None, help="Custom session ID for logging")

    args = parser.parse_args()

    seeds = load_or_create_seeds(args.seeds_file, args.games)
    run_benchmark(
        seeds=seeds,
        designs=args.designs,
        inputs=args.input,
        wordings=args.wording,
        opponent=args.opponent,
        game=args.game,
        output_path=args.output,
        session_id=args.session_id,
    )


if __name__ == "__main__":
    main()

