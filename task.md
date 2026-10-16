# TASK: Build a small bot that plays a game by asking Laya, and test it

## Who this is for
The owner is a 3rd-year IT student who is still learning how this works. The goal
is a **working first version** and **understanding**, not a perfect score.
So: keep code simple, add plain-language comments, and explain what you did after each step.

## Background (read this first)
- Laya is a small open-weight model. It takes some text (the "state") and a few typed
  questions, and returns probabilities. It is NOT a chatbot. It cannot browse, remember
  earlier calls, or play by itself.
- We are practising for a hackathon. On the day, a hosted game is revealed. Our bot reads
  the game state through an API, asks Laya, and sends a move.
- The "harness" is all the code around Laya: read state, list legal moves, build the
  questions, call Laya, pick the move, check it is legal, log it, send it, repeat.
- Today we build the harness and test it on ONE local game (tic-tac-toe).

## Hard rules (do not break these)
1. **Laya chooses every move.** Python code may list legal moves, describe them, ask
   Laya, check the answer is legal, log it, and send it. Python must NEVER choose a move.
2. **No fallback.** If Laya fails or its answer cannot be mapped to a legal move, log the
   error and STOP. Do not pick a random or "default" move.
3. **No game strategy in the bot.** No "take the centre first", no "block if opponent has
   two in a row" rules in the bot code.
4. **Facts, not verdicts.** Move descriptions may state what a move IS ("cell 4, the
   centre; row has 1 of my marks and 0 of opponent's"). They must not say whether a move
   is good or bad ("this blocks a loss", "best move").
5. **Minimax is allowed ONLY in the evaluation script** as a referee to score Laya's
   choices. It must never be imported by the bot.
6. Do not guess Laya's API. Read the installed package / README first (see Step 1).
7. Log before acting: write the decision to the log file and flush it to disk BEFORE
   sending the move.

## Project layout
```
laya-bot/
  README.md                 # plain-language explanation + how to run
  requirements.txt
  bot/
    game_api.py             # GameAdapter interface (abstract)
    tictactoe_game.py       # local tic-tac-toe game exposing the same interface
    describe.py             # turns state + legal moves into facts (text)
    laya_client.py          # the ONLY file that calls Laya
    decide.py               # builds questions, calls Laya, maps answer to a legal move
    logger.py               # append-only JSONL log, flush + fsync
    loop.py                 # the main play loop
  tools/
    viewer.py               # terminal live viewer (tails the log)
    audit.py                # checks every sent move has a logged Laya call
    evaluate.py             # experiments (uses minimax as referee)
    minimax.py              # referee only, never imported by bot/
  data/
    logs/                   # JSONL logs
    positions_tune.json     # positions used to choose the question design
    positions_test.json     # fresh positions, never used while tuning
  NOTES.md                  # what we tried and what happened (fill as you go)
```

## Steps
Do one step at a time. After each step, run the check, then STOP and tell the owner in
3-6 plain sentences what you built and what the check showed. Do not jump ahead.

### Step 1: Setup and learn Laya's real API
- Create the project and a virtual environment. Python 3.10+.
- Install Laya: `pip install laya` (the team's slides say v0.4.6; pin whatever version
  installs and write it in requirements.txt).
- Read the installed package's README/docstrings (and `help()` on its main classes).
  Write what you learn in NOTES.md: how to load the model, how to send a state plus
  questions, what comes back (field names), question types (choice / score / noul),
  limits (max questions per call, how many tokens of state are read).
- Write `bot/laya_client.py` with ONE function, for example
  `ask(state_text, questions) -> dict`, that returns the raw Laya answer.
- **Check:** a tiny script asks Laya "Does this text mention a refund?" about a sample
  sentence and prints the raw answer. Show the output to the owner.
- If Laya cannot run locally, say so and explain the options. Do not silently switch to
  another model.

### Step 2: The local game
- `bot/game_api.py`: define an interface the bot uses for ANY game:
  - `reset() -> state`
  - `get_state() -> dict` (raw state: board, whose turn, game over, result)
  - `get_legal_moves() -> list` (moves come from the game, not from the bot)
  - `submit_move(move) -> dict` (new state, result)
- `bot/tictactoe_game.py`: implement tic-tac-toe behind that interface. The bot plays X.
  The opponent (O) plays a random legal move after each bot move.
- Keep it a plain Python class first. (Later, optionally wrap it in a tiny HTTP server so
  it feels like a hosted game. Not needed now.)
- **Check:** a script plays 3 full games with random moves for X and prints the boards.
  Confirm legal moves are correct and the winner is detected.

### Step 3: Describe the moves (facts only)
- `bot/describe.py`: given the state and one legal move, produce a short factual text.
  Example for tic-tac-toe, per move: the cell number and position name (corner, edge,
  centre), and for each line (row, column, diagonal) through that cell: how many X, how
  many O, how many empty.
- Also produce a short text of the whole board.
- Follow hard rule 4. No judgments.
- **Check:** print the description for 3 different states. The owner reads them and
  confirms they are true and contain no advice.

### Step 4: Ask Laya, pick the move (Design A: one yes/no per legal move)
- `bot/decide.py`:
  - Put the board and the whole move description in the state text. Put the most important
    text FIRST (Laya only reads the first ~512 tokens per question).
  - For each legal move, create one yes/no (noul-type) question such as
    "Is playing cell 4 a good move for X?". Respect the max questions per request.
  - Call Laya once, read P(true) for each move, pick the highest, map it to the legal
    move, and verify it is in the legal list.
  - Return the move plus all the probabilities and the raw answer.
- If anything fails, raise an error. No fallback move.
- **Check:** run it on 5 different states and print the question, the probabilities and
  the chosen move.

### Step 5: Logging, the loop, the viewer, the audit
- `bot/logger.py`: append one JSON object per line to `data/logs/<session_id>.jsonl`.
  Flush and fsync after every write. Events: `game_start`, `state`, `laya_call`
  (state text, questions, raw answer, probabilities), `decision` (chosen move),
  `move_sent`, `move_result`, `error`, `game_end` (result).
- `bot/loop.py`: the loop is state -> legal moves -> describe -> Laya -> validate ->
  LOG -> submit -> result -> repeat until game over. Add a max-turns guard.
- `tools/viewer.py`: tails the newest log and prints each decision as it happens
  (turn number, the top 3 moves with probabilities, the chosen move).
- `tools/audit.py`: reads a log and fails loudly if any `move_sent` has no matching
  earlier `laya_call` + `decision`.
- **Check:** play 10 full games. Show one full game's log lines, the viewer output and the
  audit result.

### Step 6: Measure (the important step)
Goal: find out whether Laya is actually choosing good moves, and which question style is best.

- `tools/minimax.py`: a perfect tic-tac-toe solver. Used only by `tools/evaluate.py`.
- Create two files of positions where it is X's turn, with NO overlap:
  `positions_tune.json` (about 50) and `positions_test.json` (about 50, fresh).
  Include a mix: early, middle and late positions, and some with a win or a forced
  block available.
- For each position, minimax gives the set of optimal moves. A Laya choice is "good" if
  it is in that set.
- Metrics to print:
  - good-move rate (fraction of positions where Laya picked an optimal move)
  - chance level (average of optimal moves / legal moves), so we know what random gets
  - win / draw / loss over 100 games against the random opponent
- Compare these designs, **choosing on the TUNE set only**:
  - **A:** one yes/no question per legal move, with facts (Step 4)
  - **B:** one multiple-choice (choice-type) question: "which move is best?"
    with all legal moves as options
  - **C:** Design A without the facts (board only)
  - **D:** Design A plus the last 3 moves and outcomes as history in the state
- Pick the best design on the TUNE set. Then run ONLY that design once on the TEST set.
  Report both numbers. Do not tune on the test set.
- Write everything honestly in NOTES.md, including bad results. If Laya is close to chance,
  say so. That is useful information, not a failure.
- **Check:** a results table in NOTES.md (design vs tune score vs test score vs chance).

### Step 7: README
- Plain-language README: what the bot is, what each file does, how to run a game, the
  viewer, the audit and the evaluation, and the results table.
- Add a section "Walk through one move": one real example from a log (state, the facts,
  the questions, Laya's probabilities, the chosen move).
- Add a section "What we do not know yet".

## Style rules for code and writing
- Simple code. Small functions. Type hints. No clever tricks, no frameworks the task does
  not need.
- Comments in plain English that explain WHY, written for a beginner.
- Do not claim anything works unless you ran it. Report real output.
- If something in this file is unclear or Laya behaves differently than expected, stop and
  ask the owner instead of guessing.

## Definition of done
- 10 full games played by the bot with every move logged; audit passes.
- The viewer shows decisions live.
- NOTES.md has the comparison table with honest TUNE and TEST numbers.
- README has the one-move walkthrough.
- The owner has been told, in plain words, what each step did.
