"""
connect4_describe.py - Objective factual board descriptions and flag computation for Connect Four.

Hard Rules Enforced:
1. Facts only, no strategy or advice in code.
2. Token limit: compact state text must stay under 200 tokens.
3. Flags computed per legal column:
   - win: playing this column wins immediately for X
   - block: playing this column blocks O from winning immediately
   - fork: playing this column creates >= 2 threats for X
   - block_fork: playing this column reduces O's threat count from >= 2 down to <= 1
   - height: how many discs are currently in this column (0 to 5)
   - top_row: row index where disc would land (0=bottom, 5=top)
"""

from typing import Any, Dict, List, Optional, Set, Tuple

ROWS = 6
COLS = 7

DIRECTIONS = [
    (0, 1),   # Horizontal
    (1, 0),   # Vertical
    (1, 1),   # Diagonal-up (/)
    (-1, 1),  # Diagonal-down (\)
]


def _get_lowest_empty_row(board: List[List[str]], col: int) -> Optional[int]:
    """Return lowest empty row index in col (0=bottom, 5=top), or None if full."""
    for r in range(ROWS):
        if board[r][col] == "":
            return r
    return None


def _check_win_at(board: List[List[str]], row: int, col: int, player: str) -> bool:
    """Check if placing player at (row, col) forms a 4-in-a-row."""
    for dr, dc in DIRECTIONS:
        count = 1
        # Forward
        r, c = row + dr, col + dc
        while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == player:
            count += 1
            r += dr
            c += dc
        # Backward
        r, c = row - dr, col - dc
        while 0 <= r < ROWS and 0 <= c < COLS and board[r][c] == player:
            count += 1
            r -= dr
            c -= dc
        if count >= 4:
            return True
    return False


def count_threats(board: List[List[str]], player: str) -> int:
    """
    Counts the number of positions where player needs exactly one more disc
    to complete four in a row.
    Used for fork and block_fork detection.
    """
    threat_positions: Set[Tuple[int, int]] = set()
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == "":
                if _check_win_at(board, r, c, player):
                    threat_positions.add((r, c))
    return len(threat_positions)


def compute_col_flags(board: List[List[str]], col: int) -> Dict[str, Any]:
    """
    Compute objective tactical flags for playing in `col`.
    Flags:
      win: playing this column wins immediately for X
      block: playing this column blocks O from winning immediately
      fork: playing this column creates >= 2 separate threats of four-in-a-row for X
      block_fork: playing this column reduces O's threat count from >= 2 down to <= 1
      height: discs already in column (0 to 5)
      top_row: row index disc would land on (0 to 5)
    """
    r = _get_lowest_empty_row(board, col)
    if r is None:
        raise ValueError(f"Column {col} is full, cannot compute move flags.")

    # 1. Height and top_row
    height = r
    top_row = r

    # 2. Immediate win for X
    board[r][col] = "X"
    win = _check_win_at(board, r, col, "X")

    # 3. Fork for X
    # fork: playing this column creates two or more separate threats for X
    threats_after_x = count_threats(board, "X")
    fork = threats_after_x >= 2
    board[r][col] = ""

    # 4. Immediate block for X (blocks O's immediate win)
    board[r][col] = "O"
    block = _check_win_at(board, r, col, "O")
    board[r][col] = ""

    # 5. Block fork (reduces O's threat count from >= 2 down to <= 1)
    o_threats_before = count_threats(board, "O")
    if o_threats_before >= 2:
        board[r][col] = "X"
        o_threats_after = count_threats(board, "O")
        board[r][col] = ""
        block_fork = o_threats_after <= 1
    else:
        block_fork = False

    return {
        "win": win,
        "block": block,
        "fork": fork,
        "block_fork": block_fork,
        "height": height,
        "top_row": top_row,
    }


def compact_threat_facts(board: List[List[str]], col: int) -> str:
    """Format single move flags compactly: c0:[win:N,block:N,fork:N,block_fork:N,h:0]"""
    flags = compute_col_flags(board, col)
    w = "Y" if flags["win"] else "N"
    b = "Y" if flags["block"] else "N"
    f = "Y" if flags["fork"] else "N"
    bf = "Y" if flags["block_fork"] else "N"
    h = flags["height"]
    return f"c{col}:[win:{w},block:{b},fork:{f},block_fork:{bf},h:{h}]"


def format_compact_board(board: List[List[str]]) -> str:
    """
    Compact board representation showing only non-empty cells.
    Format: X:[col,row pairs] O:[col,row pairs]. E.g. X:[3r0,3r1] O:[4r0].
    If empty: Board: empty.
    """
    x_cells = []
    o_cells = []
    for c in range(COLS):
        for r in range(ROWS):
            val = board[r][c]
            if val == "X":
                x_cells.append(f"{c}r{r}")
            elif val == "O":
                o_cells.append(f"{c}r{r}")

    if not x_cells and not o_cells:
        return "Board: empty."

    x_part = f"X:[{','.join(x_cells)}]" if x_cells else "X:none"
    o_part = f"O:[{','.join(o_cells)}]" if o_cells else "O:none"
    return f"Board: {x_part} {o_part}."


def describe_state(state: Dict[str, Any]) -> str:
    """
    Compact state text format (<200 tokens total) for Design K:
    Connect Four 7x6. Drop discs into columns 0-6.
    X wins with 4 in a row (horiz/vert/diag). X loses if O does first.
    Turn: X. Priority: 1.win:Y 2.block:Y 3.fork:Y 4.block_fork:Y 5.lowest height.
    Board: X:[3r0,3r1] O:[4r0].
    Moves: c0:[win:N,block:N,fork:N,block_fork:N,h:0] ...
    """
    board = state["board"]
    legal_moves = state.get("legal_moves")
    if legal_moves is None:
        legal_moves = [c for c in range(COLS) if board[ROWS - 1][c] == ""]

    board_text = format_compact_board(board)
    moves_text = "Moves: " + " ".join([compact_threat_facts(board, c) for c in legal_moves])

    return (
        "Connect Four 7x6. Drop discs into columns 0-6.\n"
        "X wins with 4 in a row (horiz/vert/diag). X loses if O does first.\n"
        "Turn: X. Priority: 1.win:Y 2.block:Y 3.fork:Y 4.block_fork:Y 5.lowest height.\n"
        f"{board_text}\n"
        f"{moves_text}"
    )


def describe_kf_state(state: Dict[str, Any]) -> str:
    """
    Design KF state text: Fuller rules block + lose condition + priority ordering + compact board + flags.
    Guaranteed under 200 tokens.
    """
    board = state["board"]
    legal_moves = state.get("legal_moves")
    if legal_moves is None:
        legal_moves = [c for c in range(COLS) if board[ROWS - 1][c] == ""]

    board_text = format_compact_board(board)
    moves_text = "Moves: " + " ".join([compact_threat_facts(board, c) for c in legal_moves])

    return (
        "Connect Four 7 columns (0-6) by 6 rows. Discs drop to lowest empty row.\n"
        "X wins by placing 4 discs in a line horizontally, vertically, or diagonally.\n"
        "X loses if O does this first.\n"
        "Turn: X. Priority: 1.win:Y 2.block:Y 3.fork:Y 4.block_fork:Y 5.lowest height.\n"
        f"{board_text}\n"
        f"{moves_text}"
    )


def describe_board_plain(state: Dict[str, Any]) -> str:
    """Plain-text description of the board for baseline designs (A, B, E)."""
    board = state["board"]
    x_cells = []
    o_cells = []
    for c in range(COLS):
        for r in range(ROWS):
            val = board[r][c]
            if val == "X":
                x_cells.append(f"c{c}r{r}")
            elif val == "O":
                o_cells.append(f"c{c}r{r}")
    x_str = ", ".join(x_cells) if x_cells else "none"
    o_str = ", ".join(o_cells) if o_cells else "none"
    return f"Connect Four board (7 cols, 6 rows). Player X has discs at [{x_str}]. Player O has discs at [{o_str}]."


def describe_col_move(state: Dict[str, Any], col: int) -> str:
    """Factual description of dropping a disc into column `col`."""
    board = state["board"]
    r = _get_lowest_empty_row(board, col)
    if r is None:
        return f"Column {col} is full."
    flags = compute_col_flags(board, col)
    win_str = "Yes" if flags["win"] else "No"
    block_str = "Yes" if flags["block"] else "No"
    return f"Column {col}: lands on row {r}. Immediate win: {win_str}; Blocks opponent win: {block_str}."
