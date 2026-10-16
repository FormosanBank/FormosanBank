#!/usr/bin/env python3
"""Score a rebuilt NTU XML tree and compare it against the recorded baseline.

The point is not to assert that any particular number is *good*. It is to make
a change's effect on the corpus legible: rebuild the XML, run this, and every
test that moved is printed with its direction. A score that drops below the
baseline is a regression and exits non-zero; a score that rises is reported so
the baseline can be refreshed deliberately.

    python check_regressions.py --subcorpus stories --xml <dir> --json <dir>
    python check_regressions.py --subcorpus stories --xml <dir> --json <dir> --update

`--update` rewrites baseline.tsv. It is never automatic: a baseline that moves
on its own cannot catch anything.

Exit codes: 0 no regression, 1 at least one test regressed, 2 bad invocation.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

BASELINE = HERE / "baseline.tsv"
# A test may drift by this much without being called a regression: the counting
# is integer-exact, so anything larger is a real change, not float noise.
TOLERANCE = 0.05


def load_baseline(path: Path = BASELINE) -> dict:
    out: dict = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        sub, test, score = parts
        out[(sub.strip(), test.strip())] = float(score)
    return out


def write_baseline(rows: dict, path: Path = BASELINE) -> None:
    lines = [
        "# NTU corpus QA baseline: the score each test achieved on the corpus as",
        "# published. Regenerate ONLY with check_regressions.py --update, and only",
        "# when the change that moved a number is understood and intended.",
        "#",
        "# subcorpus\ttest\tpercent",
    ]
    for (sub, test), score in sorted(rows.items()):
        lines.append(f"{sub}\t{test}\t{score:.1f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def score(subcorpus: str, xml: Path, json_dir: Path) -> dict:
    """Run the right suite and return {test name: percent passing}."""
    if subcorpus == "grammar":
        import grammar_xml_tests as suite
    else:
        import sentence_xml_tests as suite
    # The two suites return different-length tuples (the sentence suite also
    # reports a sentence count); only the first two matter here.
    result = suite.run(xml, json_dir)
    ok, bad = result[0], result[1]
    out = {}
    for test in sorted(set(ok) | set(bad)):
        passed, failed = ok.get(test, 0), bad.get(test, 0)
        if passed + failed:
            out[test] = 100.0 * passed / (passed + failed)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--subcorpus", required=True,
                    choices=("grammar", "sentences", "stories"))
    ap.add_argument("--xml", required=True, type=Path, help="the rebuilt XML tree")
    ap.add_argument("--json", required=True, type=Path, help="the source JSON dir")
    ap.add_argument("--update", action="store_true",
                    help="rewrite baseline.tsv from this run (deliberate act)")
    args = ap.parse_args()
    if not args.xml.exists() or not args.json.exists():
        print(f"missing path: {args.xml if not args.xml.exists() else args.json}",
              file=sys.stderr)
        return 2

    current = score(args.subcorpus, args.xml, args.json)
    baseline = load_baseline()
    mine = {k: v for (s, k), v in baseline.items() if s == args.subcorpus}

    if args.update:
        merged = dict(baseline)
        for test, value in current.items():
            merged[(args.subcorpus, test)] = value
        write_baseline(merged)
        print(f"baseline.tsv updated for {args.subcorpus} ({len(current)} tests)")
        return 0

    if not mine:
        print(f"no baseline recorded for {args.subcorpus}; run with --update first",
              file=sys.stderr)
        return 2

    worse, better, new = [], [], []
    for test, value in sorted(current.items()):
        if test not in mine:
            new.append((test, value))
        elif value < mine[test] - TOLERANCE:
            worse.append((test, mine[test], value))
        elif value > mine[test] + TOLERANCE:
            better.append((test, mine[test], value))
    missing = sorted(t for t in mine if t not in current)

    print(f"=== {args.subcorpus}: {len(current)} tests scored against baseline")
    for test, was, now in worse:
        print(f"  REGRESSED  {test:46}{was:8.1f} -> {now:8.1f}")
    for test, was, now in better:
        print(f"  improved   {test:46}{was:8.1f} -> {now:8.1f}")
    for test, value in new:
        print(f"  new test   {test:46}{'':8} -> {value:8.1f}")
    for test in missing:
        print(f"  NOT SCORED {test:46}(in the baseline, absent from this run)")
    if not (worse or better or new or missing):
        print("  no test moved.")
    if worse:
        print(f"\n{len(worse)} regression(s). If intended, re-record with --update.")
    return 1 if worse else 0


if __name__ == "__main__":
    raise SystemExit(main())
