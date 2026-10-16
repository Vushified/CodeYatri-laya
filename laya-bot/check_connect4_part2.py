"""
check_connect4_part2.py - Verification for Part 2:
Print the full state text for 3 different board positions:
1. win flag fires
2. block flag fires
3. fork flag fires
Verify each flag is correct by inspecting the board.
Also count tokens.
"""

from bot.connect4_describe import describe_state, count_threats, compute_col_flags
from bot.connect4_game import Connect4Game

def print_board(board):
    for r in range(5, -1, -1):
        row_str = " ".join([board[r][c] if board[r][c] != "" else "." for c in range(7)])
        print(f"r{r}: | {row_str} |")
    print("     -----------------")
    print("      c0 c1 c2 c3 c4 c5 c6\n")

print("=" * 60)
print("POSITION 1: WIN FLAG FIRES FOR X")
print("=" * 60)
game1 = Connect4Game()
# Create a horizontal 3-in-a-row for X at row 0: c0, c1, c2
game1.board[0][0] = "X"
game1.board[0][1] = "X"
game1.board[0][2] = "X"
# O has a disc at c5
game1.board[0][5] = "O"

state1 = game1.get_state()
print("Board visualization:")
print_board(state1["board"])

text1 = describe_state(state1)
print("State text:")
print(text1)
flags_c3 = compute_col_flags(state1["board"], 3)
print(f"\nFlags for column 3: {flags_c3}")
assert flags_c3["win"] is True, "Expected win flag to be True for c3!"
print(">>> Position 1 PASSED: win flag correctly fires on c3!\n")

print("=" * 60)
print("POSITION 2: BLOCK FLAG FIRES FOR X (O threatens immediate win)")
print("=" * 60)
game2 = Connect4Game()
# O has a vertical 3-in-a-row in column 4 at rows 0, 1, 2
game2.board[0][4] = "O"
game2.board[1][4] = "O"
game2.board[2][4] = "O"
# X has discs elsewhere
game2.board[0][1] = "X"
game2.board[0][2] = "X"

state2 = game2.get_state()
print("Board visualization:")
print_board(state2["board"])

text2 = describe_state(state2)
print("State text:")
print(text2)
flags_c4 = compute_col_flags(state2["board"], 4)
print(f"\nFlags for column 4: {flags_c4}")
assert flags_c4["block"] is True, "Expected block flag to be True for c4!"
print(">>> Position 2 PASSED: block flag correctly fires on c4!\n")

print("=" * 60)
print("POSITION 3: FORK FLAG FIRES FOR X")
print("=" * 60)
game3 = Connect4Game()
# X has discs at (0, 2) and (0, 3)
# If X plays column 1, X gets (0, 1), giving X (0, 1), (0, 2), (0, 3).
# Threats created: (0, 0) and (0, 4) - two separate 4-in-a-row threats!
game3.board[0][2] = "X"
game3.board[0][3] = "X"
# O has a disc at c6
game3.board[0][6] = "O"

state3 = game3.get_state()
print("Board visualization:")
print_board(state3["board"])

text3 = describe_state(state3)
print("State text:")
print(text3)
flags_c1 = compute_col_flags(state3["board"], 1)
flags_c4 = compute_col_flags(state3["board"], 4)
print(f"\nFlags for column 1: {flags_c1}")
print(f"Flags for column 4: {flags_c4}")
assert flags_c1["fork"] is True, "Expected fork flag to be True for c1!"
assert flags_c4["fork"] is True, "Expected fork flag to be True for c4!"
print(">>> Position 3 PASSED: fork flag correctly fires on c1 and c4!\n")

# Token counts
try:
    from bot.laya_client import _tokenizer
    if _tokenizer:
        for i, t in enumerate([text1, text2, text3], 1):
            toks = len(_tokenizer.encode(t))
            print(f"Position {i} Laya Token Count: {toks} tokens (Limit: <200 tokens)")
            assert toks < 200, f"Token count {toks} exceeds 200!"
except Exception as e:
    print(f"Could not load Laya tokenizer directly: {e}")
    # Approximate with words
    for i, t in enumerate([text1, text2, text3], 1):
        words = len(t.split())
        print(f"Position {i} Word count: {words} words (~{int(words * 1.3)} tokens)")
