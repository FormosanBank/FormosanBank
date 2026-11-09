"""Read or recapture the examples the dictionary editors added upstream after our snapshot.

The snapshot (source_examples.jsonl.gz) holds the example fields at the commit in
source_manifest.json. The editors have since added examples in g0v/amis-moedict
docs/s. `capture` compares a clean checkout at UPSTREAM_COMMIT with the snapshot,
entry file by entry file:

* an example present in both (same cleaned Amis and Chinese) is unchanged;
* an example only in the snapshot is paired with the most similar example only in
  the checkout (difflib ratio of Amis + Chinese above 0.6): that pair is an edit
  (handled by safolu_source_overrides.json), not an addition;
* every remaining example only in the checkout is an addition.

Additions identical to an entry of printed_additions.json are already published
there and are left out. The rest are written to upstream_additions.json with
source ordinals after the printed additions, in (file, heteronym, definition,
example) order. Run explicitly, never during XML generation:

    python3 CodeAndDocs/upstream_additions.py /path/to/clean/amis-moedict
"""

from __future__ import annotations

import argparse
import collections
import difflib
import json
import subprocess
from pathlib import Path

from moedict_formosanbank import clean_moedict_link_markup, iter_moedict_json_files, parse_marked_example
from source_snapshot import load_rows

HERE = Path(__file__).resolve().parent
ADDITIONS = HERE / "upstream_additions.json"
PRINTED = HERE / "printed_additions.json"
UPSTREAM_COMMIT = "4cb82539d7e51e7211e262d4dbaecaa41a772b2f"
FIRST_ORDINAL = 49424  # after the snapshot (1-49419) and the printed additions (S49420-S49423)
EDIT_SIMILARITY = 0.6


def load_additions(path: Path = ADDITIONS) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["additions"]
    ordinals = [row["source_ordinal"] for row in rows]
    if ordinals != list(range(FIRST_ORDINAL, FIRST_ORDINAL + len(rows))):
        raise ValueError("upstream_additions.json ordinals are not consecutive from %d" % FIRST_ORDINAL)
    return rows


def _key(raw_example: str) -> tuple[str, str]:
    form, _, translation = parse_marked_example(raw_example)
    return clean_moedict_link_markup(form), clean_moedict_link_markup(translation)


def _checkout_rows(checkout: Path) -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = collections.defaultdict(list)
    for source_file in iter_moedict_json_files(checkout / "docs" / "s"):
        entry = json.loads(source_file.read_text(encoding="utf-8"))
        name = "docs/s/" + source_file.name
        for h_index, heteronym in enumerate(entry.get("h", []), 1):
            for d_index, definition in enumerate(heteronym.get("d", []), 1):
                for e_index, example in enumerate(definition.get("e", []) or [], 1):
                    rows[name].append({
                        "source_file": name,
                        "entry_title": entry.get("t", ""),
                        "heteronym_index": h_index,
                        "definition_index": d_index,
                        "example_index": e_index,
                        "definition": definition.get("f", ""),
                        "raw_example": example,
                    })
    return rows


def _unmatched(rows: list[dict], keys: list[tuple[str, str]], surplus: collections.Counter) -> list[tuple[dict, tuple[str, str]]]:
    want = collections.Counter(surplus)
    out = []
    for row, key in zip(rows, keys):
        if want[key] > 0:
            out.append((row, key))
            want[key] -= 1
    return out


def find_additions(checkout: Path) -> list[dict]:
    old: dict[str, list[dict]] = collections.defaultdict(list)
    for row in load_rows():
        old[row["source_file"]].append(row)
    new = _checkout_rows(checkout)
    additions = []
    for name in sorted(new):
        old_rows, new_rows = old.get(name, []), new[name]
        old_keys = [_key(row["raw_example"]) for row in old_rows]
        new_keys = [_key(row["raw_example"]) for row in new_rows]
        removed = _unmatched(old_rows, old_keys, collections.Counter(old_keys) - collections.Counter(new_keys))
        added = _unmatched(new_rows, new_keys, collections.Counter(new_keys) - collections.Counter(old_keys))
        paired: set[int] = set()
        for _, removed_key in removed:
            best, best_ratio = None, 0.0
            for index, (_, added_key) in enumerate(added):
                if index in paired:
                    continue
                ratio = difflib.SequenceMatcher(None, "".join(removed_key), "".join(added_key)).ratio()
                if ratio > best_ratio:
                    best, best_ratio = index, ratio
            if best is not None and best_ratio > EDIT_SIMILARITY:
                paired.add(best)
        additions += [row for index, (row, _) in enumerate(added) if index not in paired]
    return additions


def capture(checkout: Path) -> None:
    commit = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
    if commit != UPSTREAM_COMMIT:
        raise ValueError(f"Checkout is at {commit}, expected {UPSTREAM_COMMIT}")
    if subprocess.check_output(["git", "-C", str(checkout), "status", "--porcelain", "--", "docs/s"]):
        raise ValueError("Source checkout has local changes")
    printed = {(item["form"], item["translation"]) for item in json.loads(PRINTED.read_text(encoding="utf-8"))["additions"]}
    found = find_additions(checkout)
    kept = [row for row in found if _key(row["raw_example"]) not in printed]
    for ordinal, row in enumerate(kept, FIRST_ORDINAL):
        row["source_ordinal"] = ordinal
    payload = {
        "description": (
            "Examples the dictionary editors added to g0v/amis-moedict docs/s after the snapshot in "
            "source_manifest.json, captured by upstream_additions.py at upstream_commit. "
            f"{len(found)} additions found; {len(found) - len(kept)} are already published from printed_additions.json "
            "and are left out."
        ),
        "upstream_commit": commit,
        "additions": [{"source_ordinal": row.pop("source_ordinal"), **row} for row in kept],
    }
    ADDITIONS.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(found)} additions found; {len(kept)} written to {ADDITIONS.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("checkout", type=Path, help=f"Clean g0v/amis-moedict checkout at {UPSTREAM_COMMIT}")
    capture(parser.parse_args().checkout.resolve())
