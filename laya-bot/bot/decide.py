"""
decide.py - Unified decision engine supporting Designs A, B, C, D, E, F, I, and J.

Hard Rules Enforced:
1. Laya chooses the move. Python only extracts probabilities/scores to find the highest.
2. NO fallback move. If anything fails or probabilities cannot be retrieved, raise an error.
3. No game strategy in Python.
4. Export unified function:
   choose_move(state, legal_moves, design: str, input_mode: str = "board",
               wording: str = "good", history = None) -> (move, laya_call_details)
"""

from typing import Any, Dict, List, Optional, Tuple
from bot.describe import (
    build_state_text,
    describe_move,
    describe_lines_only,
    describe_threat_facts,
)
from bot.laya_client import ask

WORDING_PROMPTS_A = {
    "good": "Is playing cell {m} a good move for X?",
    "safe": "Is playing cell {m} a safe move for X?",
    "wins": "Does playing cell {m} win the game for X?",
    "hurts_opponent": "Does playing cell {m} hurt the opponent O?",
}

WORDING_PROMPTS_D = {
    "good": "Rate how good playing cell {m} is for X",
    "safe": "Rate how safe playing cell {m} is for X",
    "wins": "Rate how likely playing cell {m} wins the game for X",
    "hurts_opponent": "Rate how much playing cell {m} hurts the opponent O",
}

WORDING_PROMPTS_F = {
    "good": "Marking cell {m} is consistent with a good strategy for X.",
    "safe": "Marking cell {m} is consistent with a safe strategy for X.",
    "wins": "Marking cell {m} is consistent with a winning strategy for X.",
    "hurts_opponent": "Marking cell {m} is consistent with a strategy that hurts the opponent O.",
}

SCORE_CRITERIA = ["Very bad", "Bad", "Neutral", "Good", "Very good"]


def _decide_design_a(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
    wording: str = "good",
) -> Tuple[int, Dict[str, Any]]:
    """Design A: noul (one yes/no question per move)."""
    template = WORDING_PROMPTS_A.get(wording, WORDING_PROMPTS_A["good"])
    questions = {
        f"move_{m}": {"type": "noul", "instructions": template.format(m=m)}
        for m in legal_moves
    }
    raw = ask(state_text, questions)
    probs = {}
    for m in legal_moves:
        qid = f"move_{m}"
        p = raw["answers"][qid].get("noul")
        if p is None:
            raise RuntimeError(f"Missing noul probability for {qid}")
        probs[m] = float(p)

    chosen = max(probs, key=probs.get)
    return chosen, {
        "design": "A",
        "wording": wording,
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": probs,
        "chosen_move": chosen,
    }


def _decide_design_b(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
) -> Tuple[int, Dict[str, Any]]:
    """Design B: choice (one question with all moves as options, fact descriptions)."""
    criteria = {f"cell_{m}": describe_move(state, m) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move is best for X?",
            "criteria": criteria,
        }
    }
    raw = ask(state_text, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection: {ans}")

    chosen = int(chosen_key.replace("cell_", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("cell_", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "B",
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_design_c(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
) -> Tuple[int, Dict[str, Any]]:
    """Design C: neutral-label choice ('Which cell should be marked next?')."""
    criteria = {f"cell_{m}": f"Cell {m}" for m in legal_moves}
    questions = {
        "next_cell": {
            "type": "choice",
            "instructions": "Which cell should be marked next?",
            "criteria": criteria,
        }
    }
    raw = ask(state_text, questions)
    ans = raw["answers"]["next_cell"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection: {ans}")

    chosen = int(chosen_key.replace("cell_", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("cell_", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "C",
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_design_d(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
    wording: str = "good",
) -> Tuple[int, Dict[str, Any]]:
    """Design D: score per move ('Rate how good this move is for X' with 5 levels)."""
    template = WORDING_PROMPTS_D.get(wording, WORDING_PROMPTS_D["good"])
    questions = {
        f"score_{m}": {
            "type": "score",
            "instructions": template.format(m=m),
            "criteria": SCORE_CRITERIA,
        }
        for m in legal_moves
    }
    raw = ask(state_text, questions)
    scores = {}
    probs = {}

    for m in legal_moves:
        qid = f"score_{m}"
        ans = raw["answers"][qid]
        expected_score = ans.get("score")
        if expected_score is None:
            p_dist = ans.get("probabilities", {})
            expected_score = sum(int(lvl) * float(p) for lvl, p in p_dist.items())
        scores[m] = float(expected_score)
        probs[m] = float(expected_score) / 4.0

    chosen = max(scores, key=scores.get)
    return chosen, {
        "design": "D",
        "wording": wording,
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "scores": scores,
        "probabilities": probs,
        "chosen_move": chosen,
    }


def _decide_design_e(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
) -> Tuple[int, Dict[str, Any]]:
    """Design E: two-round shortlist (Round 1: choice top 3, Round 2: noul final)."""
    k = min(3, len(legal_moves))
    if len(legal_moves) <= 2:
        shortlist = list(legal_moves)
        r1_details = {"skipped": True, "shortlist": shortlist}
    else:
        criteria = {f"cell_{m}": describe_move(state, m) for m in legal_moves}
        q_r1 = {
            "shortlist_choice": {
                "type": "choice",
                "instructions": "Which move is best for X?",
                "criteria": criteria,
            }
        }
        raw_r1 = ask(state_text, q_r1)
        probs_r1 = raw_r1["answers"]["shortlist_choice"].get("probabilities", {})
        sorted_candidates = sorted(
            probs_r1.items(), key=lambda item: float(item[1]), reverse=True
        )
        shortlist = [int(k.replace("cell_", "")) for k, _ in sorted_candidates[:k]]
        r1_details = {
            "questions": q_r1,
            "raw_response": raw_r1,
            "shortlist": shortlist,
            "probabilities": probs_r1,
        }

    q_r2 = {
        f"move_{m}": {"type": "noul", "instructions": f"Is playing cell {m} a good move for X?"}
        for m in shortlist
    }
    raw_r2 = ask(state_text, q_r2)
    probs_r2 = {}
    for m in shortlist:
        qid = f"move_{m}"
        p = raw_r2["answers"][qid].get("noul")
        probs_r2[m] = float(p)

    chosen = max(probs_r2, key=probs_r2.get)
    return chosen, {
        "design": "E",
        "state_text": state_text,
        "round_1": r1_details,
        "round_2": {
            "questions": q_r2,
            "raw_response": raw_r2,
            "probabilities": probs_r2,
        },
        "probabilities": probs_r2,
        "chosen_move": chosen,
    }


def _decide_design_f(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
    wording: str = "good",
) -> Tuple[int, Dict[str, Any]]:
    """Design F: neutral-label noul ('Marking cell N is consistent with a strategy for X.')."""
    template = WORDING_PROMPTS_F.get(wording, WORDING_PROMPTS_F["good"])
    questions = {
        f"move_{m}": {"type": "noul", "instructions": template.format(m=m)}
        for m in legal_moves
    }
    raw = ask(state_text, questions)
    probs = {}
    for m in legal_moves:
        qid = f"move_{m}"
        p = raw["answers"][qid].get("noul")
        if p is None:
            raise RuntimeError(f"Missing noul probability for {qid}")
        probs[m] = float(p)

    chosen = max(probs, key=probs.get)
    return chosen, {
        "design": "F",
        "wording": wording,
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": probs,
        "chosen_move": chosen,
    }


def _decide_design_i(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
) -> Tuple[int, Dict[str, Any]]:
    """Design I: Only actual line descriptions through each candidate cell."""
    criteria = {f"cell_{m}": describe_lines_only(state, m) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move is best for X based on line counts?",
            "criteria": criteria,
        }
    }
    raw = ask(state_text, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection: {ans}")

    chosen = int(chosen_key.replace("cell_", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("cell_", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "I",
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_design_j(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
) -> Tuple[int, Dict[str, Any]]:
    """
    Design J: Threat facts specifically.
    Evaluates:
    - Does X win immediately with this move?
    - Does O win immediately if X doesn't play this cell?
    - Does this move create a fork for X (two ways to win)?
    - Does this move block a fork for O?
    """
    criteria = {f"cell_{m}": describe_threat_facts(state, m) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move is best for X considering winning lines, immediate blocks, and forks?",
            "criteria": criteria,
        }
    }
    raw = ask(state_text, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection: {ans}")

    chosen = int(chosen_key.replace("cell_", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("cell_", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "J",
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_design_k(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
) -> Tuple[int, Dict[str, Any]]:
    """
    Design K: Ultra-compact token-minimized threat design.
    Combines:
    - Compact rules (context)
    - Compact board state
    - High-density threat/fork flags
    Consumes ~60-80 tokens total, leaving 400+ tokens for model attention.
    """
    from bot.describe import build_compact_threat_state, compact_threat_facts
    compact_state = build_compact_threat_state(state, legal_moves)
    criteria = {f"c{m}": compact_threat_facts(state, m) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Best move for X?",
            "criteria": criteria,
        }
    }
    raw = ask(compact_state, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection: {ans}")

    chosen = int(chosen_key.replace("c", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("c", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "K",
        "state_text": compact_state,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_design_kp(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
) -> Tuple[int, Dict[str, Any]]:
    """
    Design KP: Design K with explicit priority ordering added to rules:
    'Tic-tac-toe 3x3. X wins with 3 in a line. Turn: X.
    Priority: 1.win:Y 2.block:Y 3.fork:Y 4.block_fork:Y 5.strongest cell.'
    Same compact board format, same flag format, same single choice question.
    """
    from bot.describe import build_compact_priority_threat_state, compact_threat_facts
    compact_state = build_compact_priority_threat_state(state, legal_moves)
    criteria = {f"c{m}": compact_threat_facts(state, m) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Best move for X?",
            "criteria": criteria,
        }
    }
    raw = ask(compact_state, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection: {ans}")

    chosen = int(chosen_key.replace("c", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("c", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "KP",
        "state_text": compact_state,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_design_ek(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
) -> Tuple[int, Dict[str, Any]]:
    """
    Design EK: Two-round shortlist architecture with Design K's compact prompt format in both rounds.
    Round 1: compact rules (no priority line) + compact board + flags for all legal moves + choice question 'Best move for X?'
    Round 2: same compact format but only for the 3 shortlisted moves from round 1 + one noul question per shortlisted move: 'Is cell N the best move for X given these flags?'
    Both rounds are logged separately. The move comes from round 2's top noul answer. Python never overrides either round.
    """
    from bot.describe import (
        build_compact_threat_state,
        compact_rules_text,
        compact_board_text,
        compact_threat_facts,
    )

    k = min(3, len(legal_moves))
    state_text_r1 = build_compact_threat_state(state, legal_moves)

    if len(legal_moves) <= 2:
        shortlist = list(legal_moves)
        r1_details = {
            "skipped": True,
            "shortlist": shortlist,
            "state_text": state_text_r1,
            "probabilities": {m: 1.0 / len(legal_moves) for m in legal_moves},
        }
    else:
        criteria_r1 = {f"c{m}": compact_threat_facts(state, m) for m in legal_moves}
        q_r1 = {
            "shortlist_choice": {
                "type": "choice",
                "instructions": "Best move for X?",
                "criteria": criteria_r1,
            }
        }
        raw_r1 = ask(state_text_r1, q_r1)
        ans_r1 = raw_r1["answers"]["shortlist_choice"]
        probs_r1_raw = ans_r1.get("probabilities", {})
        sorted_candidates = sorted(
            probs_r1_raw.items(), key=lambda item: float(item[1]), reverse=True
        )
        shortlist = [int(key.replace("c", "")) for key, _ in sorted_candidates[:k]]
        mapped_probs_r1 = {int(k.replace("c", "")): float(v) for k, v in probs_r1_raw.items()}
        r1_details = {
            "state_text": state_text_r1,
            "questions": q_r1,
            "raw_response": raw_r1,
            "shortlist": shortlist,
            "probabilities": mapped_probs_r1,
        }

    # Round 2: same compact format but only for the 3 shortlisted moves
    rules = compact_rules_text()
    board = compact_board_text(state)
    shortlist_threats = "Moves: " + " ".join([compact_threat_facts(state, m) for m in shortlist])
    state_text_r2 = f"{rules} {board} {shortlist_threats}"

    q_r2 = {
        f"move_{m}": {
            "type": "noul",
            "instructions": f"Is cell {m} the best move for X given these flags?",
        }
        for m in shortlist
    }
    raw_r2 = ask(state_text_r2, q_r2)
    probs_r2 = {}
    for m in shortlist:
        qid = f"move_{m}"
        p = raw_r2["answers"][qid].get("noul")
        if p is None:
            raise RuntimeError(f"Missing noul probability for {qid} in Design EK Round 2")
        probs_r2[m] = float(p)

    chosen = max(probs_r2, key=probs_r2.get)
    return chosen, {
        "design": "EK",
        "state_text": state_text_r2,
        "round_1": r1_details,
        "round_2": {
            "state_text": state_text_r2,
            "questions": q_r2,
            "raw_response": raw_r2,
            "probabilities": probs_r2,
        },
        "probabilities": probs_r2,
        "chosen_move": chosen,
    }


def _decide_design_kf(
    state: Dict[str, Any],
    legal_moves: List[int],
    state_text: str,
) -> Tuple[int, Dict[str, Any]]:
    """
    Design KF:
    - Fuller rules block with explicit win & lose conditions + priority ordering (<200 tokens)
    - Compact board and threat flags
    - Single choice question: 'Which cell should X play?'
    """
    from bot.describe import build_kf_state, compact_threat_facts
    kf_state = build_kf_state(state, legal_moves)
    criteria = {f"c{m}": compact_threat_facts(state, m) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which cell should X play?",
            "criteria": criteria,
        }
    }
    raw = ask(kf_state, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in Design KF: {ans}")

    chosen = int(chosen_key.replace("c", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("c", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "KF",
        "state_text": kf_state,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _is_connect4(state: Dict[str, Any]) -> bool:
    if state.get("game") == "connect4":
        return True
    if state.get("game") == "eight_puzzle":
        return False
    board = state.get("board")
    if isinstance(board, list) and len(board) == 6 and isinstance(board[0], list):
        return True
    return False


def _is_eight_puzzle(state: Dict[str, Any]) -> bool:
    if state.get("game") == "eight_puzzle":
        return True
    board = state.get("board")
    if isinstance(board, list) and len(board) == 3 and isinstance(board[0], list) and len(board[0]) == 3:
        if isinstance(board[0][0], int):
            return True
    return False


def _decide_eight_puzzle_k(
    state: Dict[str, Any],
    legal_moves: List[int],
    history: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Design K for 8-Puzzle: Compact board + distance + compact move facts."""
    from bot.eight_puzzle_describe import describe_puzzle_state, compact_move_facts
    last_move = history[-1]["move"] if history else None
    compact_state = describe_puzzle_state(state, history=history)
    criteria = {f"m{m}": compact_move_facts(state["board"], m, last_move=last_move) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move brings the puzzle closest to the goal?",
            "criteria": criteria,
        }
    }
    raw = ask(compact_state, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in 8-Puzzle Design K: {ans}")

    chosen = int(chosen_key.replace("m", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("m", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "K",
        "state_text": compact_state,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_eight_puzzle_kf(
    state: Dict[str, Any],
    legal_moves: List[int],
    history: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Design KF for 8-Puzzle: Fuller rules + priority order + compact moves."""
    from bot.eight_puzzle_describe import describe_kf_puzzle_state, compact_move_facts
    last_move = history[-1]["move"] if history else None
    kf_state = describe_kf_puzzle_state(state, history=history)
    criteria = {f"m{m}": compact_move_facts(state["board"], m, last_move=last_move) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move is best to reach the goal?",
            "criteria": criteria,
        }
    }
    raw = ask(kf_state, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in 8-Puzzle Design KF: {ans}")

    chosen = int(chosen_key.replace("m", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("m", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "KF",
        "state_text": kf_state,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_eight_puzzle_b(
    state: Dict[str, Any],
    legal_moves: List[int],
    history: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """Design B for 8-Puzzle: Choice with factual move metrics (goal distance delta)."""
    from bot.eight_puzzle_describe import format_board_compact, describe_move_plain
    last_move = history[-1]["move"] if history else None
    board_str = format_board_compact(state["board"])
    state_text = f"8-Puzzle sliding tile game on a 3x3 grid. Current board: {board_str}. Goal: 123/456/780."
    criteria = {f"m{m}": describe_move_plain(state["board"], m, last_move=last_move) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move is best to solve the puzzle in minimum steps?",
            "criteria": criteria,
        }
    }
    raw = ask(state_text, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in 8-Puzzle Design B: {ans}")

    chosen = int(chosen_key.replace("m", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("m", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "B",
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_eight_puzzle_a(
    state: Dict[str, Any],
    legal_moves: List[int],
    wording: str = "good",
) -> Tuple[int, Dict[str, Any]]:
    """Design A for 8-Puzzle: Noul question per legal move."""
    from bot.eight_puzzle_describe import format_board_compact
    from bot.eight_puzzle_game import MOVE_NAMES
    board_str = format_board_compact(state["board"])
    state_text = f"8-Puzzle sliding tile game on a 3x3 grid. Current board: {board_str}. Goal: 123/456/780."

    template = "Is moving the blank {name} the best move to solve the puzzle in minimum steps?"
    questions = {
        f"move_{m}": {"type": "noul", "instructions": template.format(name=MOVE_NAMES[m])}
        for m in legal_moves
    }
    raw = ask(state_text, questions)
    probs = {}
    for m in legal_moves:
        qid = f"move_{m}"
        p = raw["answers"][qid].get("noul")
        if p is None:
            raise RuntimeError(f"Missing noul probability for {qid} in 8-Puzzle Design A")
        probs[m] = float(p)

    chosen = max(probs, key=probs.get)
    return chosen, {
        "design": "A",
        "wording": wording,
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": probs,
        "chosen_move": chosen,
    }


def _is_2048(state: Dict[str, Any]) -> bool:
    if state.get("game") == "2048":
        return True
    board = state.get("board")
    if isinstance(board, list) and len(board) == 4 and isinstance(board[0], list) and len(board[0]) == 4:
        return True
    return False


def _decide_2048_a(
    state: Dict[str, Any],
    legal_moves: List[int],
    wording: str = "good",
) -> Tuple[int, Dict[str, Any]]:
    """Design A for 2048: Independent Noul question per legal slide direction."""
    from bot.game_2048 import MOVE_NAMES
    from bot.game_2048_describe import format_board_compact
    score = state.get("score", 0)
    max_tile = state.get("max_tile", 0)
    b_str = format_board_compact(state["board"])
    state_text = f"2048 puzzle on a 4x4 grid. Score: {score}, Max Tile: {max_tile}.\nBoard: {b_str}"

    template = "Is sliding {name} a good move to maximize score and keep empty space?"
    questions = {
        f"move_{m}": {"type": "noul", "instructions": template.format(name=MOVE_NAMES[m])}
        for m in legal_moves
    }
    raw = ask(state_text, questions)
    probs = {}
    for m in legal_moves:
        qid = f"move_{m}"
        p = raw["answers"][qid].get("noul")
        probs[m] = float(p)

    chosen = max(probs, key=probs.get)
    return chosen, {
        "design": "A",
        "wording": wording,
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": probs,
        "chosen_move": chosen,
    }


def _decide_2048_b(
    state: Dict[str, Any],
    legal_moves: List[int],
) -> Tuple[int, Dict[str, Any]]:
    """Design B for 2048: Choice over legal moves with factual metrics."""
    from bot.game_2048_describe import format_board_compact, describe_move_plain_2048
    score = state.get("score", 0)
    max_tile = state.get("max_tile", 0)
    b_str = format_board_compact(state["board"])
    state_text = (
        f"2048 sliding puzzle on a 4x4 grid. Current Score: {score}, Max Tile: {max_tile}.\n"
        f"Board: {b_str}."
    )
    criteria = {f"m{m}": describe_move_plain_2048(state["board"], m) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which slide move is best to maximize score and keep the board open?",
            "criteria": criteria,
        }
    }
    raw = ask(state_text, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in 2048 Design B: {ans}")

    chosen = int(chosen_key.replace("m", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("m", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "B",
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_2048_k(
    state: Dict[str, Any],
    legal_moves: List[int],
) -> Tuple[int, Dict[str, Any]]:
    """Design K for 2048: Compact state + compact move flags."""
    from bot.game_2048_describe import describe_2048_state_k, compact_move_facts_2048
    compact_state = describe_2048_state_k(state)
    criteria = {f"m{m}": compact_move_facts_2048(state["board"], m) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move is best according to the priority rules?",
            "criteria": criteria,
        }
    }
    raw = ask(compact_state, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in 2048 Design K: {ans}")

    chosen = int(chosen_key.replace("m", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("m", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "K",
        "state_text": compact_state,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_2048_kf(
    state: Dict[str, Any],
    legal_moves: List[int],
) -> Tuple[int, Dict[str, Any]]:
    """Design KF for 2048: Fuller rules + priority order + compact move flags."""
    from bot.game_2048_describe import describe_2048_state_kf, compact_move_facts_2048
    kf_state = describe_2048_state_kf(state)
    criteria = {f"m{m}": compact_move_facts_2048(state["board"], m) for m in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move is best to maximize score and survive?",
            "criteria": criteria,
        }
    }
    raw = ask(kf_state, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in 2048 Design KF: {ans}")

    chosen = int(chosen_key.replace("m", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("m", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "KF",
        "state_text": kf_state,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_connect4_k(
    state: Dict[str, Any],
    legal_moves: List[int],
) -> Tuple[int, Dict[str, Any]]:
    """Design K for Connect Four: Compact rules + board + high-density threat flags."""
    from bot.connect4_describe import describe_state, compact_threat_facts
    compact_state = describe_state(state)
    criteria = {f"c{col}": compact_threat_facts(state["board"], col) for col in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Best move for X?",
            "criteria": criteria,
        }
    }
    raw = ask(compact_state, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in Connect4 Design K: {ans}")

    chosen = int(chosen_key.replace("c", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("c", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "K",
        "state_text": compact_state,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_connect4_kf(
    state: Dict[str, Any],
    legal_moves: List[int],
) -> Tuple[int, Dict[str, Any]]:
    """Design KF for Connect Four: Fuller rules + lose condition + priority ordering + compact board + flags."""
    from bot.connect4_describe import describe_kf_state, compact_threat_facts
    kf_state = describe_kf_state(state)
    criteria = {f"c{col}": compact_threat_facts(state["board"], col) for col in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which column should X play?",
            "criteria": criteria,
        }
    }
    raw = ask(kf_state, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in Connect4 Design KF: {ans}")

    chosen = int(chosen_key.replace("c", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("c", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "KF",
        "state_text": kf_state,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_connect4_a(
    state: Dict[str, Any],
    legal_moves: List[int],
    wording: str = "good",
) -> Tuple[int, Dict[str, Any]]:
    """Design A for Connect Four: noul question per legal column."""
    from bot.connect4_describe import describe_board_plain
    board_text = describe_board_plain(state)
    state_text = f"Connect Four 7x6. Drop discs into columns 0-6. X wins with 4 in a row. Turn: X.\n{board_text}"
    template = "Is playing column {c} a good move for X?"
    if wording == "safe":
        template = "Is playing column {c} a safe move for X?"
    elif wording == "wins":
        template = "Does playing column {c} win the game for X?"
    elif wording == "hurts_opponent":
        template = "Does playing column {c} hurt the opponent O?"

    questions = {
        f"move_{c}": {"type": "noul", "instructions": template.format(c=c)}
        for c in legal_moves
    }
    raw = ask(state_text, questions)
    probs = {}
    for c in legal_moves:
        qid = f"move_{c}"
        p = raw["answers"][qid].get("noul")
        if p is None:
            raise RuntimeError(f"Missing noul probability for {qid} in Connect4 Design A")
        probs[c] = float(p)

    chosen = max(probs, key=probs.get)
    return chosen, {
        "design": "A",
        "wording": wording,
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": probs,
        "chosen_move": chosen,
    }


def _decide_connect4_b(
    state: Dict[str, Any],
    legal_moves: List[int],
) -> Tuple[int, Dict[str, Any]]:
    """Design B for Connect Four: choice over legal columns with factual descriptions."""
    from bot.connect4_describe import describe_board_plain, describe_col_move
    board_text = describe_board_plain(state)
    state_text = f"Connect Four 7x6. Drop discs into columns 0-6. X wins with 4 in a row. Turn: X.\n{board_text}"
    criteria = {f"col_{c}": describe_col_move(state, c) for c in legal_moves}
    questions = {
        "best_move": {
            "type": "choice",
            "instructions": "Which move is best for X?",
            "criteria": criteria,
        }
    }
    raw = ask(state_text, questions)
    ans = raw["answers"]["best_move"]
    chosen_key = ans.get("choice")
    if not chosen_key:
        raise RuntimeError(f"Laya choice question returned no selection in Connect4 Design B: {ans}")

    chosen = int(chosen_key.replace("col_", "").replace("c", ""))
    probs_dict = ans.get("probabilities", {})
    mapped_probs = {int(k.replace("col_", "").replace("c", "")): float(v) for k, v in probs_dict.items()}

    return chosen, {
        "design": "B",
        "state_text": state_text,
        "questions": questions,
        "raw_response": raw,
        "probabilities": mapped_probs,
        "chosen_move": chosen,
    }


def _decide_connect4_e(
    state: Dict[str, Any],
    legal_moves: List[int],
) -> Tuple[int, Dict[str, Any]]:
    """Design E for Connect Four: Two-round shortlist (Round 1 choice top 3, Round 2 noul)."""
    from bot.connect4_describe import describe_board_plain, describe_col_move
    k = min(3, len(legal_moves))
    board_text = describe_board_plain(state)
    state_text = f"Connect Four 7x6. Drop discs into columns 0-6. X wins with 4 in a row. Turn: X.\n{board_text}"

    if len(legal_moves) <= 2:
        shortlist = list(legal_moves)
        r1_details = {"skipped": True, "shortlist": shortlist}
    else:
        criteria = {f"col_{c}": describe_col_move(state, c) for c in legal_moves}
        q_r1 = {
            "shortlist_choice": {
                "type": "choice",
                "instructions": "Which move is best for X?",
                "criteria": criteria,
            }
        }
        raw_r1 = ask(state_text, q_r1)
        probs_r1 = raw_r1["answers"]["shortlist_choice"].get("probabilities", {})
        sorted_candidates = sorted(
            probs_r1.items(), key=lambda item: float(item[1]), reverse=True
        )
        shortlist = [int(k.replace("col_", "").replace("c", "")) for k, _ in sorted_candidates[:k]]
        r1_details = {
            "questions": q_r1,
            "raw_response": raw_r1,
            "shortlist": shortlist,
            "probabilities": probs_r1,
        }

    q_r2 = {
        f"move_{c}": {"type": "noul", "instructions": f"Is playing column {c} a good move for X?"}
        for c in shortlist
    }
    raw_r2 = ask(state_text, q_r2)
    probs_r2 = {}
    for c in shortlist:
        qid = f"move_{c}"
        p = raw_r2["answers"][qid].get("noul")
        probs_r2[c] = float(p)

    chosen = max(probs_r2, key=probs_r2.get)
    return chosen, {
        "design": "E",
        "state_text": state_text,
        "questions": q_r2 if len(legal_moves) > 2 else q_r1,
        "raw_response": raw_r2 if len(legal_moves) > 2 else raw_r1,
        "round_1": r1_details,
        "round_2": {
            "questions": q_r2,
            "raw_response": raw_r2,
            "probabilities": probs_r2,
        },
        "probabilities": probs_r2,
        "chosen_move": chosen,
    }


def choose_move(
    state: Dict[str, Any],
    legal_moves: List[int],
    design: str = "A",
    input_mode: str = "board",
    wording: str = "good",
    history: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """
    Unified entry point for choosing a move.
    Supported designs: A, B, C, D, E, F, I, J, K, KP, EK, KF.
    Supports both Tic-Tac-Toe and Connect Four.
    """
    if not legal_moves:
        raise ValueError("Cannot choose move: legal_moves is empty.")

    design_upper = design.upper().strip()

    # Route Connect Four states
    if _is_connect4(state):
        if design_upper == "K":
            chosen, details = _decide_connect4_k(state, legal_moves)
        elif design_upper == "KF":
            chosen, details = _decide_connect4_kf(state, legal_moves)
        elif design_upper == "A":
            chosen, details = _decide_connect4_a(state, legal_moves, wording=wording)
        elif design_upper == "B":
            chosen, details = _decide_connect4_b(state, legal_moves)
        elif design_upper == "E":
            chosen, details = _decide_connect4_e(state, legal_moves)
        elif design_upper in ("KP", "EK"):
            chosen, details = _decide_connect4_k(state, legal_moves)
        else:
            raise ValueError(f"Design '{design}' is not supported for Connect Four. Supported: A, B, E, K, KF.")

        if chosen not in legal_moves:
            raise ValueError(f"Chosen move {chosen} is not in legal_moves {legal_moves}!")
        return chosen, details

    # Route Eight Puzzle states
    if _is_eight_puzzle(state):
        if design_upper == "K":
            chosen, details = _decide_eight_puzzle_k(state, legal_moves, history=history)
        elif design_upper == "KF":
            chosen, details = _decide_eight_puzzle_kf(state, legal_moves, history=history)
        elif design_upper == "B":
            chosen, details = _decide_eight_puzzle_b(state, legal_moves, history=history)
        elif design_upper == "A":
            chosen, details = _decide_eight_puzzle_a(state, legal_moves, wording=wording)
        else:
            chosen, details = _decide_eight_puzzle_k(state, legal_moves, history=history)

        if chosen not in legal_moves:
            raise ValueError(f"Chosen move {chosen} is not in legal_moves {legal_moves}!")
        return chosen, details

    # Route 2048 states
    if _is_2048(state):
        if design_upper == "A":
            chosen, details = _decide_2048_a(state, legal_moves, wording=wording)
        elif design_upper == "B":
            chosen, details = _decide_2048_b(state, legal_moves)
        elif design_upper == "KF":
            chosen, details = _decide_2048_kf(state, legal_moves)
        elif design_upper == "K":
            chosen, details = _decide_2048_k(state, legal_moves)
        else:
            chosen, details = _decide_2048_b(state, legal_moves)

        if chosen not in legal_moves:
            raise ValueError(f"Chosen move {chosen} is not in legal_moves {legal_moves}!")
        return chosen, details

    # Tic-tac-toe path
    # Automatically set appropriate input mode if using Design I or J
    if design_upper == "I" and input_mode == "board":
        input_mode = "lines"
    elif design_upper == "J" and input_mode == "board":
        input_mode = "threats"

    state_text = build_state_text(
        state=state,
        legal_moves=legal_moves,
        input_mode=input_mode,
        history=history,
    )

    if design_upper == "A":
        chosen, details = _decide_design_a(state, legal_moves, state_text, wording)
    elif design_upper == "B":
        chosen, details = _decide_design_b(state, legal_moves, state_text)
    elif design_upper == "C":
        chosen, details = _decide_design_c(state, legal_moves, state_text)
    elif design_upper == "D":
        chosen, details = _decide_design_d(state, legal_moves, state_text, wording)
    elif design_upper == "E":
        chosen, details = _decide_design_e(state, legal_moves, state_text)
    elif design_upper == "F":
        chosen, details = _decide_design_f(state, legal_moves, state_text, wording)
    elif design_upper == "I":
        chosen, details = _decide_design_i(state, legal_moves, state_text)
    elif design_upper == "J":
        chosen, details = _decide_design_j(state, legal_moves, state_text)
    elif design_upper == "K":
        chosen, details = _decide_design_k(state, legal_moves, state_text)
    elif design_upper == "KP":
        chosen, details = _decide_design_kp(state, legal_moves, state_text)
    elif design_upper == "EK":
        chosen, details = _decide_design_ek(state, legal_moves, state_text)
    elif design_upper == "KF":
        chosen, details = _decide_design_kf(state, legal_moves, state_text)
    else:
        raise ValueError(f"Unknown design '{design}'. Supported: A, B, C, D, E, F, I, J, K, KP, EK, KF.")


    if chosen not in legal_moves:
        raise ValueError(f"Chosen move {chosen} is not in legal_moves {legal_moves}!")

    return chosen, details


def decide_move_design_a(state: Dict[str, Any], legal_moves: List[int]) -> Dict[str, Any]:
    chosen, details = choose_move(
        state=state,
        legal_moves=legal_moves,
        design="A",
        input_mode="facts",
        wording="good",
    )
    return details
