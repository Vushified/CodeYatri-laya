"""
eight_puzzle_game.py - 8-Puzzle (Sliding Tile) Game conforming to GameAdapter.

Grid: 3x3 with tiles 1 to 8 and 0 representing the empty space.
Goal State:
  1 2 3
  4 5 6
  7 8 0

Moves are actions applied to the blank space (0):
  0: UP    (blank swaps with tile above)
  1: DOWN  (blank swaps with tile below)
  2: LEFT  (blank swaps with tile to the left)
  3: RIGHT (blank swaps with tile to the right)
"""

import copy
import heapq
import random
from typing import Any, Dict, List, Optional, Set, Tuple
from bot.game_api import GameAdapter

GOAL_BOARD: List[List[int]] = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 0],
]

MOVE_NAMES: Dict[int, str] = {
    0: "UP",
    1: "DOWN",
    2: "LEFT",
    3: "RIGHT",
}

MOVE_DELTAS: Dict[int, Tuple[int, int]] = {
    0: (-1, 0),  # UP
    1: (1, 0),   # DOWN
    2: (0, -1),  # LEFT
    3: (0, 1),   # RIGHT
}

# Precomputed target coordinates for Manhattan distance
# tile 1 -> (0, 0), tile 2 -> (0, 1), ..., tile 8 -> (2, 1), tile 0 -> (2, 2)
GOAL_POSITIONS: Dict[int, Tuple[int, int]] = {
    1: (0, 0), 2: (0, 1), 3: (0, 2),
    4: (1, 0), 5: (1, 1), 6: (1, 2),
    7: (2, 0), 8: (2, 1), 0: (2, 2),
}


def compute_manhattan_distance(board: List[List[int]]) -> int:
    """Sum of Manhattan distances of tiles 1-8 to their goal positions."""
    total = 0
    for r in range(3):
        for c in range(3):
            val = board[r][c]
            if val != 0:
                target_r, target_c = GOAL_POSITIONS[val]
                total += abs(r - target_r) + abs(c - target_c)
    return total


def compute_misplaced_tiles(board: List[List[int]]) -> int:
    """Number of tiles 1-8 not currently in their goal position."""
    misplaced = 0
    for r in range(3):
        for c in range(3):
            val = board[r][c]
            if val != 0 and val != GOAL_BOARD[r][c]:
                misplaced += 1
    return misplaced


def solve_a_star(board: List[List[int]]) -> Optional[int]:
    """
    Solves the 8-puzzle using A* search with Manhattan distance heuristic.
    Returns the minimum number of steps to reach the goal state.
    """
    def board_to_tuple(b: List[List[int]]) -> Tuple[int, ...]:
        return tuple(b[r][c] for r in range(3) for c in range(3))

    goal_tuple = board_to_tuple(GOAL_BOARD)
    start_tuple = board_to_tuple(board)
    if start_tuple == goal_tuple:
        return 0

    open_heap = []
    # (f_score, g_score, board_tuple, blank_idx)
    start_blank = start_tuple.index(0)
    h0 = compute_manhattan_distance(board)
    heapq.heappush(open_heap, (h0, 0, start_tuple, start_blank))
    g_scores: Dict[Tuple[int, ...], int] = {start_tuple: 0}

    while open_heap:
        _, g, current, b_idx = heapq.heappop(open_heap)
        if current == goal_tuple:
            return g
        if g > g_scores.get(current, float("inf")):
            continue

        b_r, b_c = divmod(b_idx, 3)
        for move_id, (dr, dc) in MOVE_DELTAS.items():
            nr, nc = b_r + dr, b_c + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                next_b_idx = nr * 3 + nc
                cur_list = list(current)
                # Swap blank with target
                cur_list[b_idx], cur_list[next_b_idx] = cur_list[next_b_idx], cur_list[b_idx]
                nxt = tuple(cur_list)
                new_g = g + 1
                if new_g < g_scores.get(nxt, float("inf")):
                    g_scores[nxt] = new_g
                    # 2D list for manhattan
                    b_2d = [cur_list[i*3:(i+1)*3] for i in range(3)]
                    h = compute_manhattan_distance(b_2d)
                    heapq.heappush(open_heap, (new_g + h, new_g, nxt, next_b_idx))

    return None


class EightPuzzleGame(GameAdapter):
    """8-Puzzle environment adhering to GameAdapter."""

    def __init__(
        self,
        seed: Optional[int] = None,
        scramble_depth: int = 10,
        max_steps: int = 50,
    ):
        self.rng = random.Random(seed)
        self.seed = seed
        self.scramble_depth = scramble_depth
        self.max_steps = max_steps
        self.board: List[List[int]] = [list(row) for row in GOAL_BOARD]
        self.current_player: str = "Player"
        self.is_game_over: bool = False
        self.result: Optional[str] = None  # "win", "timeout"
        self.steps_taken: int = 0
        self.initial_board: List[List[int]] = [list(row) for row in GOAL_BOARD]
        self.optimal_steps: Optional[int] = 0

        self.reset()

    def _find_blank(self) -> Tuple[int, int]:
        """Locate the (row, col) of the empty space (0)."""
        for r in range(3):
            for c in range(3):
                if self.board[r][c] == 0:
                    return r, c
        raise ValueError("Blank tile (0) not found on board!")

    def reset(self) -> Dict[str, Any]:
        """
        Reset board by scrambling from the goal state using scramble_depth valid random moves.
        Guarantees solvability and deterministic reproducibility from seed.
        """
        self.board = [list(row) for row in GOAL_BOARD]
        self.steps_taken = 0
        self.is_game_over = False
        self.result = None

        # Re-initialize rng from seed if provided for reproducible reset
        if self.seed is not None:
            self.rng = random.Random(self.seed)

        # Scramble
        prev_move = None
        for _ in range(self.scramble_depth):
            legal = self.get_legal_moves()
            # Try to avoid immediately undoing the previous move
            if prev_move is not None:
                opposite = {0: 1, 1: 0, 2: 3, 3: 2}[prev_move]
                non_undo = [m for m in legal if m != opposite]
                candidates = non_undo if non_undo else legal
            else:
                candidates = legal
            chosen = self.rng.choice(candidates)
            self._apply_move_internal(chosen)
            prev_move = chosen

        self.initial_board = [list(row) for row in self.board]
        self.optimal_steps = solve_a_star(self.board)
        return self.get_state()

    def get_state(self) -> Dict[str, Any]:
        """Return raw game state dictionary."""
        legal = self.get_legal_moves()
        return {
            "game": "eight_puzzle",
            "board": [list(row) for row in self.board],
            "current_player": self.current_player,
            "legal_moves": legal,
            "is_game_over": self.is_game_over,
            "game_over": self.is_game_over,
            "result": self.result,
            "steps_taken": self.steps_taken,
            "max_steps": self.max_steps,
            "manhattan": compute_manhattan_distance(self.board),
            "misplaced": compute_misplaced_tiles(self.board),
            "optimal_steps": self.optimal_steps,
        }

    def get_legal_moves(self) -> List[int]:
        """Return list of legal moves (0:UP, 1:DOWN, 2:LEFT, 3:RIGHT)."""
        if self.is_game_over:
            return []
        br, bc = self._find_blank()
        legal = []
        for m_id, (dr, dc) in MOVE_DELTAS.items():
            nr, nc = br + dr, bc + dc
            if 0 <= nr < 3 and 0 <= nc < 3:
                legal.append(m_id)
        return legal

    def _apply_move_internal(self, move: int) -> None:
        """Internal tile swap without game-over or step counting."""
        br, bc = self._find_blank()
        dr, dc = MOVE_DELTAS[move]
        nr, nc = br + dr, bc + dc
        if not (0 <= nr < 3 and 0 <= nc < 3):
            raise ValueError(f"Illegal move {move} ({MOVE_NAMES.get(move)}) from blank at ({br}, {bc})")
        # Swap
        self.board[br][bc], self.board[nr][nc] = self.board[nr][nc], self.board[br][bc]

    def submit_move(self, move: int) -> Dict[str, Any]:
        """Execute a move, update step count, and check for win or step limit."""
        if self.is_game_over:
            raise ValueError("Game is already over. Reset before playing.")

        legal = self.get_legal_moves()
        if move not in legal:
            raise ValueError(f"Move {move} ({MOVE_NAMES.get(move)}) is illegal. Legal moves: {legal}")

        self._apply_move_internal(move)
        self.steps_taken += 1

        # Check win condition
        if self.board == GOAL_BOARD:
            self.is_game_over = True
            self.result = "win"
        elif self.steps_taken >= self.max_steps:
            self.is_game_over = True
            self.result = "timeout"

        return self.get_state()
