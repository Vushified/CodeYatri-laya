"""
server.py - Multi-Game Server for the Dark Burgundy Dashboard.

Supports all 4 evaluated games:
1. Tic-Tac-Toe (3x3 grid)
2. Connect Four (7x6 grid)
3. 8-Puzzle (3x3 sliding tile puzzle)
4. 2048 (4x4 tile-merging puzzle)

Features:
- REST API for live game state, single-step Laya inference, auto-play, and reset
- Dedicated endpoint for empirical benchmarks (Table 1 vs Random, Table 2 vs Smart Random)
- Real-time JSONL logging and audit verification
"""

import glob
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from bot.connect4_game import Connect4Game
from bot.decide import choose_move
from bot.eight_puzzle_game import EightPuzzleGame, compute_manhattan_distance, solve_a_star
from bot.game_2048 import Game2048
from bot.logger import GameLogger
from bot.tictactoe_game import TicTacToeGame
from tools.audit import audit_log_file
from tools.minimax import get_optimal_moves

LOG_DIR = os.path.join(PROJECT_ROOT, "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
ACTIVE_LOGGER = GameLogger(session_id="multi_game_dashboard", log_dir=LOG_DIR)

# Global active game instances for dashboard interactive play
GAMES = {
    "tictactoe": TicTacToeGame(seed=42),
    "connect4": Connect4Game(seed=42),
    "eight_puzzle": EightPuzzleGame(seed=42, scramble_depth=4),
    "2048": Game2048(seed=42),
}

LAST_DECISIONS = {
    "tictactoe": None,
    "connect4": None,
    "eight_puzzle": None,
    "2048": None,
}


def get_latest_log_lines(n=30):
    """Retrieve the last n lines from the latest log file."""
    log_files = glob.glob(os.path.join(LOG_DIR, "*.jsonl"))
    if not log_files:
        return []
    latest = max(log_files, key=os.path.getmtime)
    lines = []
    with open(latest, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    lines.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    pass
    return lines[-n:]


def get_game_state_payload(game_name: str):
    """Formats full state payload for the requested game."""
    game = GAMES.get(game_name, GAMES["tictactoe"])
    state = game.get_state()
    legal = game.get_legal_moves()

    payload = {
        "game": game_name,
        "state": state,
        "legal_moves": legal,
        "last_decision": LAST_DECISIONS.get(game_name),
    }

    if game_name == "tictactoe":
        optimal, _ = get_optimal_moves(state["board"]) if not state.get("is_game_over") else ([], {})
        payload["optimal_moves"] = optimal
    elif game_name == "eight_puzzle":
        payload["manhattan"] = compute_manhattan_distance(state["board"])
        payload["optimal_steps"] = state.get("optimal_steps", 0)
    elif game_name == "2048":
        payload["score"] = state.get("score", 0)
        payload["max_tile"] = state.get("max_tile", 0)

    return payload


def get_benchmarks_data():
    """Returns structured benchmark records for Table 1 and Table 2."""
    table_random = [
        # Tic-Tac-Toe
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design E",
            "type": "Shortlist (choice -> noul)",
            "wins": 85, "draws": 8, "losses": 7,
            "win_pct": "85.0%", "loss_pct": "7.0%",
            "margin": "+28.0%", "status": "Winner", "highlight": "gold"
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design K",
            "type": "Compact threat flags (157 tokens)",
            "wins": 76, "draws": 6, "losses": 18,
            "win_pct": "76.0%", "loss_pct": "18.0%",
            "margin": "+19.0%", "status": "Token Winner", "highlight": "green"
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design A",
            "type": "Standard Noul per move",
            "wins": 70, "draws": 10, "losses": 20,
            "win_pct": "70.0%", "loss_pct": "20.0%",
            "margin": "+13.0%", "status": "Competitive", "highlight": ""
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design KP",
            "type": "Rules + Priority Order",
            "wins": 70, "draws": 9, "losses": 21,
            "win_pct": "69.7%", "loss_pct": "21.0%",
            "margin": "+12.7%", "status": "Solid", "highlight": ""
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design B",
            "type": "Standard multiple-choice",
            "wins": 63, "draws": 9, "losses": 28,
            "win_pct": "63.0%", "loss_pct": "28.0%",
            "margin": "+6.0%", "status": "Baseline Choice", "highlight": ""
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design EK",
            "type": "Compact shortlist",
            "wins": 62, "draws": 10, "losses": 28,
            "win_pct": "62.3%", "loss_pct": "27.7%",
            "margin": "+5.3%", "status": "Solid", "highlight": ""
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "random-control",
            "type": "Random move baseline",
            "wins": 57, "draws": 9, "losses": 34,
            "win_pct": "57.0%", "loss_pct": "34.0%",
            "margin": "0.0%", "status": "Baseline", "highlight": "neutral"
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design I",
            "type": "Raw lines-only description",
            "wins": 42, "draws": 12, "losses": 46,
            "win_pct": "42.0%", "loss_pct": "46.0%",
            "margin": "-15.0%", "status": "Sub-baseline", "highlight": "red"
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design J",
            "type": "Verbose prose threats (450 tokens)",
            "wins": 35, "draws": 20, "losses": 45,
            "win_pct": "35.0%", "loss_pct": "45.0%",
            "margin": "-22.0%", "status": "Diluted", "highlight": "red"
        },
        # Connect Four
        {
            "game": "Connect Four",
            "setting": "Design B",
            "type": "Choice with drop physics",
            "wins": 259, "draws": 0, "losses": 41,
            "win_pct": "86.3%", "loss_pct": "13.7%",
            "margin": "+40.0%", "status": "Winner", "highlight": "gold"
        },
        {
            "game": "Connect Four",
            "setting": "Design K",
            "type": "Compact 7-col threat flags",
            "wins": 250, "draws": 0, "losses": 50,
            "win_pct": "83.3%", "loss_pct": "16.7%",
            "margin": "+37.0%", "status": "Token Winner", "highlight": "green"
        },
        {
            "game": "Connect Four",
            "setting": "Design A",
            "type": "Noul column feasibility",
            "wins": 234, "draws": 0, "losses": 66,
            "win_pct": "78.0%", "loss_pct": "22.0%",
            "margin": "+31.7%", "status": "Solid", "highlight": ""
        },
        {
            "game": "Connect Four",
            "setting": "Design KF",
            "type": "Full rules + priority order",
            "wins": 222, "draws": 0, "losses": 78,
            "win_pct": "74.0%", "loss_pct": "26.0%",
            "margin": "+27.7%", "status": "Solid", "highlight": ""
        },
        {
            "game": "Connect Four",
            "setting": "random-control",
            "type": "Random legal column baseline",
            "wins": 139, "draws": 0, "losses": 161,
            "win_pct": "46.3%", "loss_pct": "53.7%",
            "margin": "0.0%", "status": "Baseline", "highlight": "neutral"
        },
        # 8-Puzzle (Sliding Tile)
        {
            "game": "8-Puzzle",
            "setting": "Design A",
            "type": "Independent Noul per slide",
            "wins": 5, "draws": 0, "losses": 15,
            "win_pct": "25.0%", "loss_pct": "75.0%",
            "margin": "3.0 Steps (1.00x Optimal A*)", "status": "Winner", "highlight": "gold"
        },
        {
            "game": "8-Puzzle",
            "setting": "random-walker",
            "type": "Non-reversing random baseline",
            "wins": 4, "draws": 0, "losses": 16,
            "win_pct": "20.0%", "loss_pct": "80.0%",
            "margin": "3.0 Steps (1.00x Optimal A*)", "status": "Baseline", "highlight": "neutral"
        },
        {
            "game": "8-Puzzle",
            "setting": "Design B / K / KF",
            "type": "Choice with heuristic delta",
            "wins": 0, "draws": 0, "losses": 20,
            "win_pct": "0.0%", "loss_pct": "100.0%",
            "margin": "20.0 Steps (Timeout)", "status": "Oscillated", "highlight": "red"
        },
        # 2048 (Single Player)
        {
            "game": "2048",
            "setting": "Design A",
            "type": "Independent Noul per direction",
            "wins": "Score: 1166.4", "draws": "Max: 2536", "losses": "Tile: 256",
            "win_pct": "123.6 Turns", "loss_pct": "+53.5%",
            "margin": "1.53x vs Random", "status": "Score Winner", "highlight": "gold"
        },
        {
            "game": "2048",
            "setting": "random-baseline",
            "type": "Uniform random legal slides",
            "wins": "Score: 760.0", "draws": "Max: 1556", "losses": "Tile: 128",
            "win_pct": "93.8 Turns", "loss_pct": "Base",
            "margin": "1.00x (Base)", "status": "Baseline", "highlight": "neutral"
        },
        {
            "game": "2048",
            "setting": "Design KF",
            "type": "Full rules + corner priority",
            "wins": "Score: 664.0", "draws": "Max: 1472", "losses": "Tile: 128",
            "win_pct": "87.2 Turns", "loss_pct": "-12.6%",
            "margin": "0.87x vs Random", "status": "Sub-baseline", "highlight": ""
        },
        {
            "game": "2048",
            "setting": "Design B",
            "type": "Factual choice over moves",
            "wins": "Score: 456.0", "draws": "Max: 1040", "losses": "Tile: 64",
            "win_pct": "70.6 Turns", "loss_pct": "-40.0%",
            "margin": "0.60x vs Random", "status": "Sub-baseline", "highlight": "red"
        },
    ]

    table_smart = [
        # Tic-Tac-Toe vs Smart Random
        {
            "game": "Tic-Tac-Toe",
            "setting": "smart_random (Baseline)",
            "type": "1-ply immediate win & block engine",
            "wins": 93, "draws": 36, "losses": 171,
            "win_pct": "31.0%", "loss_pct": "57.0%",
            "margin": "0.0%", "status": "Opponent Baseline", "highlight": "neutral"
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design KF",
            "type": "Full rules + priority ordering",
            "wins": 48, "draws": 29, "losses": 223,
            "win_pct": "16.0%", "loss_pct": "74.3%",
            "margin": "-15.0%", "status": "Best Against Smart", "highlight": "green"
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design K",
            "type": "Compact threat flags",
            "wins": 35, "draws": 29, "losses": 236,
            "win_pct": "11.7%", "loss_pct": "78.7%",
            "margin": "-19.3%", "status": "Tactical Ceiling", "highlight": ""
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design B",
            "type": "Standard choice",
            "wins": 32, "draws": 22, "losses": 246,
            "win_pct": "10.7%", "loss_pct": "82.0%",
            "margin": "-20.3%", "status": "Tactical Ceiling", "highlight": ""
        },
        {
            "game": "Tic-Tac-Toe",
            "setting": "Design KP",
            "type": "Compressed priority text",
            "wins": 13, "draws": 29, "losses": 258,
            "win_pct": "4.3%", "loss_pct": "86.0%",
            "margin": "-26.7%", "status": "Tactical Ceiling", "highlight": "red"
        },
        # Connect Four vs Smart Random
        {
            "game": "Connect Four",
            "setting": "smart_random (Baseline)",
            "type": "Mechanical 1-ply win/block bot",
            "wins": 157, "draws": 6, "losses": 137,
            "win_pct": "52.3%", "loss_pct": "45.7%",
            "margin": "0.0%", "status": "Opponent Baseline", "highlight": "neutral"
        },
        {
            "game": "Connect Four",
            "setting": "Design B",
            "type": "Choice with drop physics",
            "wins": 6, "draws": 0, "losses": 294,
            "win_pct": "2.0%", "loss_pct": "98.0%",
            "margin": "-50.3%", "status": "Tactical Ceiling", "highlight": "red"
        },
        {
            "game": "Connect Four",
            "setting": "Design K",
            "type": "Compact 7-col threat flags",
            "wins": 3, "draws": 0, "losses": 297,
            "win_pct": "1.0%", "loss_pct": "99.0%",
            "margin": "-51.3%", "status": "Tactical Ceiling", "highlight": "red"
        },
        {
            "game": "Connect Four",
            "setting": "Design KF",
            "type": "Full rules + priority order",
            "wins": 0, "draws": 0, "losses": 300,
            "win_pct": "0.0%", "loss_pct": "100.0%",
            "margin": "-52.3%", "status": "Tactical Ceiling", "highlight": "red"
        },
        # 8-Puzzle & 2048 notes for smart random
        {
            "game": "8-Puzzle",
            "setting": "All Designs",
            "type": "Single-player deterministic puzzle",
            "wins": "N/A", "draws": "N/A", "losses": "N/A",
            "win_pct": "No Opponent", "loss_pct": "N/A",
            "margin": "Evaluated vs A* Shortest Path", "status": "Single Player", "highlight": "neutral"
        },
        {
            "game": "2048",
            "setting": "All Designs",
            "type": "Single-player stochastic puzzle",
            "wins": "N/A", "draws": "N/A", "losses": "N/A",
            "win_pct": "No Opponent", "loss_pct": "N/A",
            "margin": "Evaluated for Score Maximization", "status": "Single Player", "highlight": "neutral"
        },
    ]

    return {
        "table_random": table_random,
        "table_smart": table_smart,
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        ui_dir = os.path.join(PROJECT_ROOT, "ui")
        super().__init__(*args, directory=ui_dir, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        if parsed.path == "/api/state":
            game_name = qs.get("game", ["tictactoe"])[0]
            self._send_json(get_game_state_payload(game_name))
        elif parsed.path == "/api/logs":
            self._send_json({"logs": get_latest_log_lines(35)})
        elif parsed.path == "/api/benchmarks":
            self._send_json(get_benchmarks_data())
        elif parsed.path == "/api/audit":
            self._handle_get_audit()
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            body = json.loads(post_body)
        except Exception:
            body = {}

        if parsed.path == "/api/step":
            self._handle_post_step(body)
        elif parsed.path == "/api/auto_game":
            self._handle_post_auto_game(body)
        elif parsed.path == "/api/reset":
            self._handle_post_reset(body)
        else:
            self.send_response(404)
            self.end_headers()

    def _send_json(self, data, status=200):
        response_bytes = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

    def _handle_get_audit(self):
        log_files = glob.glob(os.path.join(LOG_DIR, "*.jsonl"))
        if not log_files:
            self._send_json({"status": "no_logs", "message": "No logs recorded yet."})
            return
        latest = max(log_files, key=os.path.getmtime)
        try:
            passed = audit_log_file(latest)
            self._send_json({"status": "passed", "file": os.path.basename(latest)})
        except Exception as e:
            self._send_json({"status": "failed", "error": str(e), "file": os.path.basename(latest)})

    def _handle_post_reset(self, body):
        game_name = body.get("game", "tictactoe")
        game = GAMES.get(game_name, GAMES["tictactoe"])
        state = game.reset()
        LAST_DECISIONS[game_name] = None
        ACTIVE_LOGGER.log_game_start(game_index=1, player="X" if game_name != "2048" else "Player")
        self._send_json(get_game_state_payload(game_name))

    def _handle_post_step(self, body):
        game_name = body.get("game", "tictactoe")
        game = GAMES.get(game_name, GAMES["tictactoe"])
        design = body.get("design", "A" if game_name in ("eight_puzzle", "2048") else "E")

        state = game.get_state()
        if state.get("is_game_over"):
            self._send_json({"error": "Game is already over. Please reset."}, status=400)
            return

        legal = game.get_legal_moves()
        if not legal:
            self._send_json({"error": "No legal moves remaining."}, status=400)
            return

        # Log state
        ACTIVE_LOGGER.log_state(state, legal)

        # Query Laya
        chosen_move, decision = choose_move(state, legal, design=design)
        LAST_DECISIONS[game_name] = decision

        # Log decision before acting
        ACTIVE_LOGGER.log_laya_call(
            state_text=decision.get("state_text", ""),
            questions=decision.get("questions", {}),
            raw_answer=decision.get("raw_response", {}),
            probabilities=decision.get("probabilities", {}),
        )
        ACTIVE_LOGGER.log_decision(chosen_move=chosen_move)

        # Submit move to game
        ACTIVE_LOGGER.log_move_sent(move=chosen_move)
        new_state = game.submit_move(chosen_move)
        ACTIVE_LOGGER.log_move_result(updated_state=new_state)

        if new_state.get("is_game_over"):
            ACTIVE_LOGGER.log_game_end(
                result=str(new_state.get("result", "over")),
                total_turns=new_state.get("turn_number", new_state.get("steps_taken", 0)),
            )

        payload = get_game_state_payload(game_name)
        payload["chosen_move"] = chosen_move
        payload["probabilities"] = decision.get("probabilities", {})
        payload["questions"] = decision.get("questions", {})
        payload["state_text"] = decision.get("state_text", "")
        payload["design"] = design

        self._send_json(payload)

    def _handle_post_auto_game(self, body):
        game_name = body.get("game", "tictactoe")
        game = GAMES.get(game_name, GAMES["tictactoe"])
        design = body.get("design", "A" if game_name in ("eight_puzzle", "2048") else "E")
        max_steps = 25 if game_name != "2048" else 40

        game.reset()
        ACTIVE_LOGGER.log_game_start(game_index=1, player="X" if game_name != "2048" else "Player")
        turns = []

        steps = 0
        while not game.get_state().get("is_game_over") and steps < max_steps:
            state = game.get_state()
            legal = game.get_legal_moves()
            if not legal:
                break
            chosen_move, decision = choose_move(state, legal, design=design)
            LAST_DECISIONS[game_name] = decision

            ACTIVE_LOGGER.log_decision(chosen_move)
            ACTIVE_LOGGER.log_move_sent(chosen_move)
            new_state = game.submit_move(chosen_move)
            ACTIVE_LOGGER.log_move_result(new_state)

            turns.append({
                "chosen_move": chosen_move,
                "probabilities": decision.get("probabilities", {}),
            })
            steps += 1

        final_state = game.get_state()
        ACTIVE_LOGGER.log_game_end(
            result=str(final_state.get("result", "over")),
            total_turns=steps,
        )

        payload = get_game_state_payload(game_name)
        payload["turns"] = turns
        payload["total_turns"] = len(turns)
        payload["design"] = design
        self._send_json(payload)


def run_server(port=8080):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, DashboardHandler)
    print(f"Laya Multi-Game Dashboard Server running on http://127.0.0.1:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
