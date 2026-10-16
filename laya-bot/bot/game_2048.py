"""
game_2048.py - Standard 2048 game engine conforming to GameAdapter interface.

Single-player tile-sliding game on a 4x4 grid.
Moves:
0: UP
1: DOWN
2: LEFT
3: RIGHT

Physics:
- Tiles slide as far as they can in chosen direction.
- Colliding equal tiles merge into one with double the value and add that value to score.
- Each tile can merge at most once per move.
- Random tile (90% 2, 10% 4) spawns in an empty cell after each legal move.
- Game ends when no legal moves remain.
"""

import random
from typing import Any, Dict, List, Optional, Tuple
from bot.game_api import GameAdapter

MOVE_NAMES = {
    0: "UP",
    1: "DOWN",
    2: "LEFT",
    3: "RIGHT",
}

MOVE_BY_NAME = {v: k for k, v in MOVE_NAMES.items()}


def slide_and_merge_line(line: List[int]) -> Tuple[List[int], int]:
    """Applies 2048 slide and merge rules to a single 4-element line."""
    non_zero = [x for x in line if x != 0]
    merged = []
    points = 0
    skip = False
    for i in range(len(non_zero)):
        if skip:
            skip = False
            continue
        if i + 1 < len(non_zero) and non_zero[i] == non_zero[i + 1]:
            val = non_zero[i] * 2
            merged.append(val)
            points += val
            skip = True
        else:
            merged.append(non_zero[i])

    merged += [0] * (len(line) - len(merged))
    return merged, points


def simulate_move(board: List[List[int]], move: int) -> Tuple[List[List[int]], int, bool]:
    """
    Simulates a move on a 4x4 board.
    Returns (new_board, points_gained, is_legal).
    A move is legal if and only if new_board != board.
    """
    new_board = [list(row) for row in board]
    total_points = 0

    if move == 2:  # LEFT
        for r in range(4):
            new_board[r], pts = slide_and_merge_line(new_board[r])
            total_points += pts

    elif move == 3:  # RIGHT
        for r in range(4):
            rev = new_board[r][::-1]
            merged, pts = slide_and_merge_line(rev)
            new_board[r] = merged[::-1]
            total_points += pts

    elif move == 0:  # UP
        for c in range(4):
            col = [new_board[r][c] for r in range(4)]
            merged, pts = slide_and_merge_line(col)
            total_points += pts
            for r in range(4):
                new_board[r][c] = merged[r]

    elif move == 1:  # DOWN
        for c in range(4):
            col = [new_board[r][c] for r in range(4)][::-1]
            merged, pts = slide_and_merge_line(col)
            total_points += pts
            merged_rev = merged[::-1]
            for r in range(4):
                new_board[r][c] = merged_rev[r]
    else:
        raise ValueError(f"Invalid move {move}. Must be 0 (UP), 1 (DOWN), 2 (LEFT), 3 (RIGHT).")

    is_legal = (new_board != board)
    return new_board, total_points, is_legal


def get_legal_moves_for_board(board: List[List[int]]) -> List[int]:
    """Returns list of legal move directions [0..3] that change the board."""
    legal = []
    for m in (0, 1, 2, 3):
        _, _, is_legal = simulate_move(board, m)
        if is_legal:
            legal.append(m)
    return legal


class Game2048(GameAdapter):
    """2048 game implementation implementing GameAdapter."""

    def __init__(self, seed: Optional[int] = None, max_steps: int = 1000):
        self.seed = seed
        self.rng = random.Random(seed)
        self.max_steps = max_steps
        self.board: List[List[int]] = [[0] * 4 for _ in range(4)]
        self.score: int = 0
        self.steps_taken: int = 0
        self.game_over: bool = False
        self.reset()

    def _spawn_tile(self) -> None:
        """Spawns a 2 (90% prob) or 4 (10% prob) in an empty cell."""
        empty_cells = [(r, c) for r in range(4) for c in range(4) if self.board[r][c] == 0]
        if not empty_cells:
            return
        r, c = self.rng.choice(empty_cells)
        val = 2 if self.rng.random() < 0.9 else 4
        self.board[r][c] = val

    def reset(self) -> Dict[str, Any]:
        """Resets the board, spawns 2 initial tiles, and resets score."""
        self.rng = random.Random(self.seed)
        self.board = [[0] * 4 for _ in range(4)]
        self.score = 0
        self.steps_taken = 0
        self.game_over = False
        self._spawn_tile()
        self._spawn_tile()
        return self.get_state()

    def get_legal_moves(self) -> List[int]:
        """Returns list of legal moves (0: UP, 1: DOWN, 2: LEFT, 3: RIGHT)."""
        if self.game_over:
            return []
        return get_legal_moves_for_board(self.board)

    def get_max_tile(self) -> int:
        return max(max(row) for row in self.board)

    def get_state(self) -> Dict[str, Any]:
        """Returns state dictionary adhering to GameAdapter."""
        legal = self.get_legal_moves()
        is_over = len(legal) == 0 or self.steps_taken >= self.max_steps
        max_tile = self.get_max_tile()

        return {
            "game": "2048",
            "board": [list(row) for row in self.board],
            "score": self.score,
            "max_tile": max_tile,
            "steps_taken": self.steps_taken,
            "current_player": "Player",
            "legal_moves": legal,
            "game_over": is_over,
            "is_game_over": is_over,
            "result": "game_over" if is_over else None,
        }

    def submit_move(self, move: int) -> Dict[str, Any]:
        """Executes a move, merges tiles, adds score, spawns a tile, and returns updated state."""
        if self.game_over:
            raise ValueError("Cannot submit move: game is already over.")

        new_board, points, is_legal = simulate_move(self.board, move)
        if not is_legal:
            raise ValueError(f"Move {move} ({MOVE_NAMES.get(move, 'UNKNOWN')}) is not legal for current board.")

        self.board = new_board
        self.score += points
        self.steps_taken += 1
        self._spawn_tile()

        legal_after = self.get_legal_moves()
        if not legal_after or self.steps_taken >= self.max_steps:
            self.game_over = True

        return self.get_state()
