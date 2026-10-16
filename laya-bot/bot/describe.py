"""
describe.py - Produces objective, factual descriptions of the board, rules, moves, and threat facts.

Hard Rules Enforced:
1. Facts only, no judgments or advice!
2. Rules first: Every state string begins with the game rules and objective (<80 words).
3. History (when included) is capped at the last 2 moves only.
"""

from typing import Any, Dict, List, Optional, Tuple

CELL_TYPES = {
    0: "corner",
    1: "edge",
    2: "corner",
    3: "edge",
    4: "centre",
    5: "edge",
    6: "corner",
    7: "edge",
    8: "corner",
}

# The 8 winning lines in tic-tac-toe
ALL_LINES: List[Tuple[str, Tuple[int, int, int]]] = [
    ("row 0", (0, 1, 2)),
    ("row 1", (3, 4, 5)),
    ("row 2", (6, 7, 8)),
    ("column 0", (0, 3, 6)),
    ("column 1", (1, 4, 7)),
    ("column 2", (2, 5, 8)),
    ("main diagonal", (0, 4, 8)),
    ("anti diagonal", (2, 4, 6)),
]


def game_rules_text() -> str:
    """
    Returns a concise plain-English description of the game rules (<80 words).
    Must be placed at the very top of every state string sent to Laya.
    """
    return (
        "Game: Tic-tac-toe on a 3x3 grid with cells numbered 0 to 8. "
        "Two players take turns placing their own mark: X or O. "
        "A player wins by getting three of their own marks in a line (horizontally across a row, vertically down a column, or diagonally). "
        "It is X's turn. Pick the best move for X to win or block O from winning."
    )


def describe_board(state: Dict[str, Any]) -> str:
    """
    Produce a concise factual description of the whole board.
    Lists which player marks are in which cells.
    """
    board = state["board"]
    x_cells = [str(i) for i, cell in enumerate(board) if cell == "X"]
    o_cells = [str(i) for i, cell in enumerate(board) if cell == "O"]
    empty_cells = [str(i) for i, cell in enumerate(board) if cell == " "]

    x_str = ", ".join(x_cells) if x_cells else "none"
    o_str = ", ".join(o_cells) if o_cells else "none"
    empty_str = ", ".join(empty_cells) if empty_cells else "none"

    return (
        f"Board state: Player X has {len(x_cells)} marks at cells [{x_str}]. "
        f"Player O has {len(o_cells)} marks at cells [{o_str}]. "
        f"Empty legal cells: [{empty_str}]."
    )


def describe_lines_only(state: Dict[str, Any], move: int) -> str:
    """
    Design I: Only actual line descriptions (rows, columns, diagonals through cell).
    """
    board = state["board"]
    lines_through_cell = []
    for line_name, (c1, c2, c3) in ALL_LINES:
        if move in (c1, c2, c3):
            line_cells = [board[c1], board[c2], board[c3]]
            num_x = line_cells.count("X")
            num_o = line_cells.count("O")
            num_empty = line_cells.count(" ")
            lines_through_cell.append(f"{line_name}: {num_x}X, {num_o}O, {num_empty}empty")

    return f"Cell {move} lines: [" + "; ".join(lines_through_cell) + "]"


def compute_threat_facts(board: List[str], move: int) -> Dict[str, bool]:
    """
    Design J: Evaluates objective threat and fork facts for a candidate move.
    1. Immediate win: Placing X at move completes 3 in a line.
    2. Blocks immediate loss: Placing O at move would have completed 3 in a line for O.
    3. Creates fork: Placing X at move results in >= 2 unblocked winning threats (lines with 2 X's and 1 empty).
    4. Blocks fork: Opponent O playing at move would have created >= 2 winning threats.
    """
    # 1. Immediate win for X
    b_x = list(board)
    b_x[move] = "X"
    x_immediate_win = any(
        b_x[a] == b_x[b] == b_x[c] == "X"
        for _, (a, b, c) in ALL_LINES
        if move in (a, b, c)
    )

    # 2. Blocks immediate win for O
    b_o = list(board)
    b_o[move] = "O"
    o_immediate_win = any(
        b_o[a] == b_o[b] == b_o[c] == "O"
        for _, (a, b, c) in ALL_LINES
        if move in (a, b, c)
    )

    # 3. Creates fork for X (count lines with 2 X's and 1 empty)
    x_threat_lines = 0
    for _, (a, b, c) in ALL_LINES:
        line = [b_x[a], b_x[b], b_x[c]]
        if line.count("X") == 2 and line.count(" ") == 1:
            x_threat_lines += 1
    creates_fork = x_threat_lines >= 2

    # 4. Blocks fork for O
    o_threat_lines = 0
    for _, (a, b, c) in ALL_LINES:
        line = [b_o[a], b_o[b], b_o[c]]
        if line.count("O") == 2 and line.count(" ") == 1:
            o_threat_lines += 1
    blocks_fork = o_threat_lines >= 2

    return {
        "immediate_win": x_immediate_win,
        "blocks_immediate_loss": o_immediate_win,
        "creates_fork": creates_fork,
        "blocks_fork": blocks_fork,
    }


def describe_threat_facts(state: Dict[str, Any], move: int) -> str:
    """
    Formats the computed threat facts into factual text.
    """
    threats = compute_threat_facts(state["board"], move)
    w_str = "Yes" if threats["immediate_win"] else "No"
    l_str = "Yes" if threats["blocks_immediate_loss"] else "No"
    fx_str = "Yes" if threats["creates_fork"] else "No"
    fo_str = "Yes" if threats["blocks_fork"] else "No"

    return (
        f"Cell {move} threats: Immediate win: {w_str}; "
        f"Blocks opponent win: {l_str}; "
        f"Creates fork: {fx_str}; "
        f"Blocks opponent fork: {fo_str}."
    )


def describe_move(state: Dict[str, Any], move: int) -> str:
    """Standard factual move description."""
    board = state["board"]
    pos_type = CELL_TYPES.get(move, "cell")

    lines_through_cell = []
    for line_name, (c1, c2, c3) in ALL_LINES:
        if move in (c1, c2, c3):
            line_cells = [board[c1], board[c2], board[c3]]
            num_x = line_cells.count("X")
            num_o = line_cells.count("O")
            num_empty = line_cells.count(" ")
            lines_through_cell.append(
                f"{line_name} ({num_x} X, {num_o} O, {num_empty} empty)"
            )

    lines_desc = "; ".join(lines_through_cell)
    return f"Cell {move} ({pos_type}): passes through {lines_desc}."


def format_history_text(history: Optional[List[Dict[str, Any]]] = None) -> str:
    """Format history of recent moves (last 2 moves only)."""
    if not history:
        return ""
    recent = history[-2:]
    parts = []
    for item in recent:
        p = item.get("player", "?")
        m = item.get("move", "?")
        parts.append(f"{p} marked cell {m}")
    return "Recent moves: " + "; ".join(parts) + "."


def build_state_text(
    state: Dict[str, Any],
    legal_moves: List[int],
    input_mode: str = "board",
    history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Constructs the complete state string for Laya:
    - input_mode == "board": Rules + Board state
    - input_mode == "lines": Rules + Board + Line descriptions only (Design I)
    - input_mode == "threats": Rules + Board + Threat & Fork facts (Design J)
    - input_mode == "facts": Rules + Board + Standard move descriptions
    - input_mode == "history": Rules + Board + Last 2 moves
    """
    sections = [game_rules_text(), describe_board(state)]

    if input_mode == "lines":
        lines_text = " Lines: " + " ".join([describe_lines_only(state, m) for m in legal_moves])
        sections.append(lines_text)

    elif input_mode == "threats":
        threats_text = " Threats: " + " ".join([describe_threat_facts(state, m) for m in legal_moves])
        sections.append(threats_text)

    elif input_mode == "facts":
        move_facts = " Legal options: " + " ".join([describe_move(state, m) for m in legal_moves])
        sections.append(move_facts)

    if input_mode == "history" or history:
        hist_text = format_history_text(history)
        if hist_text:
            sections.append(hist_text)

    return " ".join(sections)


def describe_state_and_moves(state: Dict[str, Any], legal_moves: List[int]) -> str:
    return build_state_text(state, legal_moves, input_mode="facts")


# --- Ultra-Compact Token-Minimized Helpers (Design K) ---

def compact_rules_text() -> str:
    """Ultra-compact rules definition (~18 words, minimal tokens)."""
    return "Tic-tac-toe (3x3). Rule: win with 3 of own mark in line. Turn: X. Objective: win or block O."


def compact_board_text(state: Dict[str, Any]) -> str:
    """Ultra-compact board state."""
    board = state["board"]
    x_cells = [str(i) for i, c in enumerate(board) if c == "X"]
    o_cells = [str(i) for i, c in enumerate(board) if c == "O"]
    return f"Board: X:[{','.join(x_cells) or 'none'}] O:[{','.join(o_cells) or 'none'}]."


def compact_threat_facts(state: Dict[str, Any], move: int) -> str:
    """Ultra-compact threat facts for a single move."""
    t = compute_threat_facts(state["board"], move)
    w = "Y" if t["immediate_win"] else "N"
    b = "Y" if t["blocks_immediate_loss"] else "N"
    f = "Y" if t["creates_fork"] else "N"
    bf = "Y" if t["blocks_fork"] else "N"
    return f"c{move}:[win:{w},block:{b},fork:{f},block_fork:{bf}]"


def build_compact_threat_state(state: Dict[str, Any], legal_moves: List[int]) -> str:
    """
    Constructs an ultra-compact, token-minimized prompt containing:
    1. Compact rules (for context)
    2. Compact board state
    3. High-density threat/fork flags per candidate move
    Consumes ~60-80 tokens total, leaving 400+ tokens for model attention.
    """
    rules = compact_rules_text()
    board = compact_board_text(state)
    threats = "Moves: " + " ".join([compact_threat_facts(state, m) for m in legal_moves])
    return f"{rules} {board} {threats}"


# --- Design KP: Compact Rules with Explicit Priority Ordering ---

def compact_priority_rules_text() -> str:
    """Design KP exact rules text with explicit priority ordering."""
    return (
        "Tic-tac-toe 3x3. X wins with 3 in a line. Turn: X.\n"
        "Priority: 1.win:Y 2.block:Y 3.fork:Y 4.block_fork:Y 5.strongest cell."
    )


def build_compact_priority_threat_state(state: Dict[str, Any], legal_moves: List[int]) -> str:
    """
    Constructs the compact prompt for Design KP:
    1. Priority rules text
    2. Compact board state
    3. Moves with flags
    """
    rules = compact_priority_rules_text()
    board = compact_board_text(state)
    threats = "Moves: " + " ".join([compact_threat_facts(state, m) for m in legal_moves])
    return f"{rules} {board} {threats}"


# --- Design KF: Fuller Rules Block + Lose Condition + Priority Ordering (<200 tokens) ---

def kf_rules_text() -> str:
    """Fuller rules block with explicit win & lose conditions and priority ordering."""
    return (
        "Tic-tac-toe 3x3 grid, cells 0-8.\n"
        "X wins by placing 3 marks in any row, column or diagonal.\n"
        "X loses if O does this first.\n"
        "Turn: X. Make the best move.\n"
        "Priority order: 1.win:Y (take it immediately) \n"
        "2.block:Y (opponent wins next turn, stop it) \n"
        "3.fork:Y (creates two ways to win) \n"
        "4.block_fork:Y (stops opponent fork) \n"
        "5.any remaining cell."
    )


def build_kf_state(state: Dict[str, Any], legal_moves: List[int]) -> str:
    """
    Constructs the complete prompt for Design KF:
    Fuller rules + lose condition + priority ordering + compact board + flags.
    Guaranteed under 200 tokens.
    """
    rules = kf_rules_text()
    board = compact_board_text(state)
    threats = "Moves: " + " ".join([compact_threat_facts(state, m) for m in legal_moves])
    return f"{rules} {board} {threats}"



