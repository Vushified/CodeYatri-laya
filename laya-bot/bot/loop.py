"""
loop.py - The main game play loop.

Loop cycle:
1. get_state() & get_legal_moves()
2. log state
3. describe facts & build questions
4. call Laya to predict move (Design A)
5. validate chosen move is legal
6. log laya_call & decision (FLUSH & FSYNC BEFORE ACTING - Rule 7)
7. submit_move()
8. log move_sent & move_result
9. check if game over, repeat until done.
"""

from typing import Any, Dict, Optional
from bot.decide import decide_move_design_a
from bot.game_api import GameAdapter
from bot.logger import GameLogger


def play_one_game(
    game: GameAdapter,
    logger: GameLogger,
    game_index: int = 1,
    max_turns: int = 20,
) -> Dict[str, Any]:
    """
    Play a single full game of tic-tac-toe using Laya for all decisions.

    Args:
        game: An instance conforming to GameAdapter.
        logger: An active GameLogger instance.
        game_index: Index of the current game in the batch.
        max_turns: Safety guard to prevent infinite loops.

    Returns:
        dict: The final game state.
    """
    logger.log_game_start(game_index=game_index, player="X")
    state = game.reset()
    turn_count = 0

    try:
        while not state["is_game_over"]:
            turn_count += 1
            if turn_count > max_turns:
                err_msg = f"Max turns guard ({max_turns}) exceeded. Terminating game."
                logger.log_error(err_msg, {"turn_count": turn_count})
                raise RuntimeError(err_msg)

            legal_moves = game.get_legal_moves()
            if not legal_moves:
                break

            # 1. Log current state and legal moves
            logger.log_state(state, legal_moves)

            # 2. Query Laya for decision
            decision = decide_move_design_a(state, legal_moves)
            chosen_move = decision["chosen_move"]

            # 3. CRITICAL (Rule 7): Log before acting!
            # Must log laya_call and decision BEFORE submitting the move.
            logger.log_laya_call(
                state_text=decision["state_text"],
                questions=decision["questions"],
                raw_answer=decision["raw_response"],
                probabilities=decision["probabilities"],
            )
            logger.log_decision(chosen_move=chosen_move)

            # 4. Submit move to game
            logger.log_move_sent(move=chosen_move)
            state = game.submit_move(chosen_move)

            # 5. Log move result
            logger.log_move_result(updated_state=state)

        # Game finished normally
        logger.log_game_end(result=state["result"], total_turns=turn_count)
        return state

    except Exception as e:
        logger.log_error(f"Game aborted due to exception: {str(e)}", {"turn_count": turn_count})
        raise
