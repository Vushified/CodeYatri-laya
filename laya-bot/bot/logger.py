"""
logger.py - Append-only JSONL event logger with immediate flush and fsync.

Hard Rule 7: Log before acting!
Every decision must be written and flushed to disk before the move is submitted to the game.
Events tracked:
- game_start
- state
- laya_call
- decision
- move_sent
- move_result
- error
- game_end
"""

import json
import os
import time
from typing import Any, Dict, Optional


class GameLogger:
    """
    Writes append-only JSONL logs for game sessions.
    Guarantees every line is flushed and fsynced to disk immediately.
    """

    def __init__(self, session_id: str, log_dir: str = "data/logs"):
        self.session_id = session_id
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.filepath = os.path.join(self.log_dir, f"{session_id}.jsonl")
        # Open in append mode with UTF-8 encoding
        self._file = open(self.filepath, "a", encoding="utf-8")

    def log(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """
        Write a single JSON event to disk, then flush and fsync.
        """
        payload = {
            "session_id": self.session_id,
            "timestamp": time.time(),
            "event": event_type,
            "data": data or {},
        }
        line = json.dumps(payload) + "\n"
        self._file.write(line)
        self._file.flush()
        try:
            os.fsync(self._file.fileno())
        except (AttributeError, OSError):
            # In some environments or virtual filesystems fsync may be unsupported
            pass

    def log_game_start(self, game_index: int, player: str = "X") -> None:
        self.log("game_start", {"game_index": game_index, "bot_player": player})

    def log_state(self, state: Dict[str, Any], legal_moves: list) -> None:
        self.log("state", {"state": state, "legal_moves": legal_moves})

    def log_laya_call(
        self,
        state_text: str,
        questions: Dict[str, Any],
        raw_answer: Dict[str, Any],
        probabilities: Dict[int, float],
    ) -> None:
        self.log(
            "laya_call",
            {
                "state_text": state_text,
                "questions": questions,
                "raw_answer": raw_answer,
                "probabilities": {str(k): v for k, v in probabilities.items()},
            },
        )

    def log_decision(self, chosen_move: int) -> None:
        self.log("decision", {"chosen_move": chosen_move})

    def log_move_sent(self, move: int) -> None:
        self.log("move_sent", {"move": move})

    def log_move_result(self, updated_state: Dict[str, Any]) -> None:
        self.log("move_result", {"updated_state": updated_state})

    def log_error(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.log("error", {"message": message, "details": details or {}})

    def log_game_end(self, result: Optional[str], total_turns: int) -> None:
        self.log("game_end", {"result": result, "total_turns": total_turns})

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
