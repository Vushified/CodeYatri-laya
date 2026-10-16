"""
check_step1.py - Verification script for Step 1.
Asks Laya: "Does this text mention a refund?" about a sample sentence,
and prints the raw answer received.
"""

import json
import sys
import os

# Add project directory to python path so we can import bot.laya_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.laya_client import ask


def main():
    sample_sentence = "The customer requested a refund for the delayed parcel."
    questions = {
        "refund_query": {
            "type": "noul",
            "instructions": "Does this text mention a refund?",
        }
    }

    print("--- Asking Laya ---")
    print(f"State text: '{sample_sentence}'")
    print(f"Question: {questions['refund_query']['instructions']}")
    
    raw_answer = ask(sample_sentence, questions)
    
    print("\n--- Raw Laya Answer ---")
    print(json.dumps(raw_answer, indent=2))
    
    # Simple sanity check
    assert "answers" in raw_answer, "Missing 'answers' in Laya response"
    assert "refund_query" in raw_answer["answers"], "Missing 'refund_query' in answers"
    print("\nStep 1 check PASSED successfully!")


if __name__ == "__main__":
    main()
