import json
import sys
from collections import defaultdict

def load_json(path):
    with open(path) as f:
        return json.load(f)

def compute_deltas(old, new):
    deltas = {}
    for lang in new:
        old_total, old_dialects = old.get(lang, [0, {}])
        new_total, new_dialects = new.get(lang, [0, {}])
        
        total_delta = new_total - old_total

        dialect_delta = defaultdict(int)
        all_dialects = set(new_dialects) | set(old_dialects)
        for dialect in all_dialects:
            delta = new_dialects.get(dialect, 0) - old_dialects.get(dialect, 0)
            dialect_delta[dialect] = delta

        deltas[lang] = [total_delta, dict(dialect_delta)]

    return deltas

if __name__ == "__main__":
    old_path = sys.argv[1]
    new_path = sys.argv[2]
    out_path = sys.argv[3]

    old = load_json(old_path)
    new = load_json(new_path)

    deltas = compute_deltas(old, new)

    with open(out_path, "w") as f:
        json.dump(deltas, f, indent=2)
