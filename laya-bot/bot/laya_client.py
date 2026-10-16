"""
laya_client.py - The ONLY file in the project that communicates directly with Laya.

This module loads the Laya model once and provides a single helper function, `ask`,
which takes a state text and a dictionary of questions, passes them to Laya,
and returns the raw dictionary response.

Features persistent disk-backed memoization (data/cache_laya.json) so no evaluation
is ever repeated, surviving restarts and dramatically accelerating paired-seed comparisons.
"""

import json
import os
from typing import Any, Dict, Tuple
import laya

_CACHED_AGENT = None
_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cache_laya.json"
)
_INFERENCE_CACHE: Dict[str, Dict[str, Any]] = {}
_DIRTY_COUNT = 0

# Load persistent cache if it exists on disk
if os.path.exists(_CACHE_FILE):
    try:
        with open(_CACHE_FILE, "r", encoding="utf-8") as f:
            _INFERENCE_CACHE = json.load(f)
    except Exception:
        _INFERENCE_CACHE = {}


def _save_cache_to_disk():
    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
    temp_file = _CACHE_FILE + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(_INFERENCE_CACHE, f)
    os.replace(temp_file, _CACHE_FILE)


def get_agent():
    """
    Load the Laya agent if it is not already loaded.
    Plain English: Loads the model weights into memory the first time it is called.
    """
    global _CACHED_AGENT
    if _CACHED_AGENT is None:
        _CACHED_AGENT = laya.load()
    return _CACHED_AGENT


def ask(state_text: str, questions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send state_text and questions to Laya, returning the raw dictionary response.
    Checks disk-backed cache first.
    """
    global _DIRTY_COUNT
    cache_key = state_text + " || " + json.dumps(questions, sort_keys=True)
    if cache_key in _INFERENCE_CACHE:
        return _INFERENCE_CACHE[cache_key]

    agent = get_agent()
    response = agent.predict(state=state_text, questions=questions)
    _INFERENCE_CACHE[cache_key] = response
    _DIRTY_COUNT += 1

    # Save to disk every 10 new evaluations or on first evaluation
    if _DIRTY_COUNT % 10 == 0 or _DIRTY_COUNT == 1:
        try:
            _save_cache_to_disk()
        except Exception:
            pass

    return response
