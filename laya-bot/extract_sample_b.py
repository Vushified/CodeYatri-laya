"""
extract_sample_b.py - Extract a mid-game state (>= 8 discs played) for Design B from logs
and compute exact token count.
"""

import json
from transformers import AutoTokenizer

sample_entry = None

with open("data/logs/c4_run2.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        entry = json.loads(line)
        if entry.get("event") == "laya_call":
            data = entry["data"]
            # Check if this is Design B (instructions: Which move is best for X?)
            q = data.get("questions", {}).get("best_move", {})
            if q.get("instructions") == "Which move is best for X?":
                # Check how many discs are on the board
                state_text = data.get("state_text", "")
                if "c" in state_text and "r" in state_text:
                    # Count discs
                    import re
                    discs = re.findall(r"c\dr\d", state_text)
                    if len(discs) >= 8:
                        sample_entry = data
                        break

if sample_entry:
    print("Found mid-game sample for Design B:")
    print("State Text:")
    print(sample_entry["state_text"])
    print("\nQuestions (Options/Criteria):")
    print(json.dumps(sample_entry["questions"], indent=2))
    
    # Let's count words and tokens
    words = len(sample_entry["state_text"].split())
    print(f"\nWord count of state text: {words} words")
    
    # Try tokenizer
    try:
        from bot.laya_client import get_agent
        agent = get_agent()
        tok = agent.tokenizer
        tokens = len(tok.encode(sample_entry["state_text"]))
        print(f"Exact Laya Token count: {tokens} tokens")
    except Exception as e:
        print(f"Approximated tokens: ~{int(words * 1.3)} tokens ({e})")
else:
    print("No sample found matching criteria.")
