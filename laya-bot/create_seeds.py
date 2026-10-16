"""
create_seeds.py - Generates 300 tune seeds and 300 test seeds with strictly 0 overlap.
"""

import json
import os
import random

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(data_dir, exist_ok=True)

r_tune = random.Random(1337)
tune_seeds = [r_tune.randint(1000, 999999) for _ in range(300)]

r_test = random.Random(9999)
test_seeds = []
tune_set = set(tune_seeds)
while len(test_seeds) < 300:
    s = r_test.randint(1000, 999999)
    if s not in tune_set and s not in test_seeds:
        test_seeds.append(s)

tune_path = os.path.join(data_dir, "tune_seeds.json")
test_path = os.path.join(data_dir, "test_seeds.json")

with open(tune_path, "w", encoding="utf-8") as f:
    json.dump(tune_seeds, f, indent=2)

with open(test_path, "w", encoding="utf-8") as f:
    json.dump(test_seeds, f, indent=2)

print(f"Created {tune_path} with {len(tune_seeds)} seeds.")
print(f"Created {test_path} with {len(test_seeds)} seeds.")
print(f"Overlap: {len(set(tune_seeds) & set(test_seeds))}")
assert len(set(tune_seeds) & set(test_seeds)) == 0, "Seeds overlap!"
