# Laya Bot - Tic-Tac-Toe Decision Harness

A clean, beginner-friendly Python harness for playing games using **Laya**, an open-weight, non-autoregressive decision model developed for calibrated system-1 evaluations.

Built for a hackathon practice workflow by a 3rd-year IT student.

---

## 1. What This Bot Is

Laya is **not** a chatbot. It does not converse, have long-term memory, or play games on its own. Instead, it takes a piece of text (the *state*) and a dictionary of typed questions (e.g., binary probability questions or multiple-choice questions) and returns calibrated probabilities.

The **harness** is all the code around Laya:
1. It reads the game state from the environment (`bot/game_api.py`).
2. It lists legal moves strictly provided by the game.
3. It describes the state factually (`bot/describe.py`).
4. It poses questions to Laya (`bot/decide.py` and `bot/laya_client.py`).
5. It reads Laya's probabilities, selects the highest probability move, and checks legality.
6. It logs the decision with immediate `fsync` before acting (`bot/logger.py`).
7. It submits the move to the game environment and repeats until the game ends (`bot/loop.py`).

### Hard Rules Strictly Followed
- **Laya chooses every move:** Python never picks moves or injects rules like "take the centre first".
- **No fallbacks:** If Laya fails, the bot halts and logs the error. It never guesses or plays a random move.
- **Facts, not verdicts:** Move descriptions only state geometry and cell counts (e.g. `2 X, 0 O, 1 empty`), never whether a move is good or bad.
- **Log before acting:** Every move decision is written and synced to disk before sending it to the game.
- **Minimax is a referee only:** Minimax exists only in `tools/minimax.py` for evaluation; it is never imported by the bot.

---

## 2. Project Layout & What Each File Does

```text
laya-bot/
  README.md                 # Plain-language explanation, walkthrough, and how to run
  requirements.txt          # Pinned dependencies (laya==0.4.6, torch, etc.)
  NOTES.md                  # Detailed notes on Laya's API and evaluation results
  bot/
    game_api.py             # Abstract GameAdapter interface (reset, get_state, get_legal_moves, submit_move)
    tictactoe_game.py       # Tic-tac-toe game implementation with random O opponent
    describe.py             # Turns board state and legal moves into objective facts
    laya_client.py          # The ONLY file that calls laya.predict()
    decide.py               # Builds questions, queries Laya, maps probabilities to legal moves
    logger.py               # Append-only JSONL logger with immediate flush and fsync
    loop.py                 # Core game loop with max-turn guardrails
  tools/
    viewer.py               # Terminal live viewer displaying turns, top 3 probabilities, and outcomes
    audit.py                # Verifies that every move_sent has a preceding laya_call and decision
    evaluate.py             # Benchmarks question designs on TUNE and TEST sets using minimax
    minimax.py              # Perfect tic-tac-toe solver (referee only)
  data/
    logs/                   # Append-only JSONL log files
    positions_tune.json     # 50 tuning positions where it is X's turn
    positions_test.json     # 50 fresh test positions (0 overlap with tune set)
    evaluation_summary.json # Saved metrics from evaluate.py
```

---

## 3. How to Run

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Play 10 Games with Full Logging & Audit
```bash
python check_step5.py
```

### Run the Terminal Live Viewer
Tails the newest game log and displays turns with top probabilities:
```bash
python tools/viewer.py
```
Or view a specific log:
```bash
python tools/viewer.py data/logs/<session_id>.jsonl
```

### Audit a Log File
Checks that every move sent was decided by Laya:
```bash
python tools/audit.py data/logs/<session_id>.jsonl
```

### Run the Evaluation Experiments
Runs minimax referee benchmarks on the TUNE (50) and TEST (50) sets and simulates 100 games:
```bash
python tools/evaluate.py
```

---

## 4. Benchmark Results Table

We benchmarked 4 distinct question prompt designs across 50 non-overlapping TUNE positions, picked the winner, and ran it once on 50 fresh TEST positions:

| Question Design | Description | TUNE Score (50 pos) | TEST Score (50 pos) | Chance Baseline |
|---|---|---|---|---|
| **Design A** | `noul` per move + facts | 25/50 (**50.0%**) | N/A | 56.8% (Tune) |
| **Design B** | `choice` best move + facts | 27/50 (**54.0%**) | N/A | 56.8% (Tune) |
| **Design C** *(Winner)* | `noul` per move, board only | 29/50 (**58.0%**) | 21/50 (**42.0%**) | 56.8% (Tune) / 50.4% (Test) |
| **Design D** | `noul` + facts + move history | 26/50 (**52.0%**) | N/A | 56.8% (Tune) |

### 100-Game Record (Design C vs Random Opponent)
- **X (Laya) Wins:** 67 (67.0%)
- **Draws:** 20 (20.0%)
- **O (Opponent) Wins:** 13 (13.0%)
- **Undefeated Rate:** **87.0%**

---

## 5. Walk Through One Real Move

Here is an actual move taken directly from log `session_step5_1791923908.jsonl` (Game 1, Turn 3):

### 1. Game State Before the Move
- **Board Grid:**
  ```text
   O |   |   
  ---+---+---
   O |   |   
  ---+---+---
     | X | X 
  ```
- **Player X marks:** cells `[7, 8]`
- **Player O marks:** cells `[0, 3]`
- **Legal moves available for X:** `[1, 2, 4, 5, 6]`

### 2. Facts Generated by `describe.py`
```text
Tic-tac-toe 3x3 board. Player X has 2 marks at cells [7, 8]. Player O has 2 marks at cells [0, 3]. Empty cells: [1, 2, 4, 5, 6].
Legal moves:
- Move 1 (edge): passes through row 0 (0 X, 1 O, 2 empty); column 1 (1 X, 0 O, 2 empty).
- Move 2 (corner): passes through row 0 (0 X, 1 O, 2 empty); column 2 (1 X, 0 O, 2 empty); anti diagonal (0 X, 0 O, 3 empty).
- Move 4 (centre): passes through row 1 (0 X, 1 O, 2 empty); column 1 (1 X, 0 O, 2 empty); main diagonal (1 X, 1 O, 1 empty); anti diagonal (0 X, 0 O, 3 empty).
- Move 5 (edge): passes through row 1 (0 X, 1 O, 2 empty); column 2 (1 X, 0 O, 2 empty).
- Move 6 (corner): passes through row 2 (2 X, 0 O, 1 empty); column 0 (0 X, 2 O, 1 empty); anti diagonal (0 X, 0 O, 3 empty).
```

### 3. Questions Asked to Laya
Five parallel `noul` questions:
- `move_1`: *"Is playing cell 1 a good move for X?"*
- `move_2`: *"Is playing cell 2 a good move for X?"*
- `move_4`: *"Is playing cell 4 a good move for X?"*
- `move_5`: *"Is playing cell 5 a good move for X?"*
- `move_6`: *"Is playing cell 6 a good move for X?"*

### 4. Laya's Calibrated Probabilities $P(\text{true})$
- Cell 1: `0.3470` (34.70%)
- Cell 2: `0.5399` (53.99%)
- Cell 4: `0.5375` (53.75%)
- Cell 5: `0.5928` (59.28%)
- **Cell 6:** **`0.6555` (65.55%)** $\leftarrow$ **HIGHEST**

### 5. Decision & Execution
1. Python identified **Cell 6** as having the maximum probability (`0.6555`).
2. Validated that Cell 6 is in `[1, 2, 4, 5, 6]`.
3. Flushed and synced the decision event to disk.
4. Sent move `6` to the game. Cell 6 completed row 2 (`[6, 7, 8]`), securing an immediate **X Victory**!

---

## 6. What We Do Not Know Yet

1. **How Laya will perform on the hackathon game:** On the actual hackathon day, the game might not be tic-tac-toe. It could be Connect Four, Nim, Battleship, or an imperfect-information game. We do not yet know how well Laya's zero-shot priors generalize to larger or novel game boards.
2. **Optimal phrasing for non-grid games:** We observed that verbose text degraded accuracy compared to concise representations. We do not yet know the optimal text compression format for larger state spaces.
3. **Choice vs Noul in multi-action games:** While `choice` (Design B) is faster because it requires only 1 forward pass, its performance on games with 20+ actions remains uncharacterized.
