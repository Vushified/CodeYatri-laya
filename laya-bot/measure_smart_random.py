"""
measure_smart_random.py - Measure smart_random opponent's win rate against random X
over 300 games on tune seeds for Connect Four.
"""

import json
from tools.runner import play_random_control_game

with open("data/tune_seeds.json", "r", encoding="utf-8") as f:
    seeds = json.load(f)[:300]

print(f"Measuring smart_random opponent strength on {len(seeds)} tune seeds...")
x_wins = 0
o_wins = 0
draws = 0

for s in seeds:
    # X plays random, O plays smart_random
    res = play_random_control_game(seed=s, opponent="smart_random", x_player="random", game_name="connect4")
    if res == "X":
        x_wins += 1
    elif res == "O":
        o_wins += 1
    else:
        draws += 1

total = len(seeds)
o_win_pct = (o_wins / total) * 100
x_win_pct = (x_wins / total) * 100
draw_pct = (draws / total) * 100

print(f"Games: {total}")
print(f"smart_random (O) Wins: {o_wins} ({o_win_pct:.1f}%)")
print(f"random (X) Wins: {x_wins} ({x_win_pct:.1f}%)")
print(f"Draws: {draws} ({draw_pct:.1f}%)")
