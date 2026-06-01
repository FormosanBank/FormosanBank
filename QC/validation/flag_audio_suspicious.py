"""flag_audio_suspicious.py — turn scores CSV into a worklist of suspect entries.

Port of Jacob Ye's `flag_suspicious.py` from
`Formosan-ILRDF_Dicts/data_validation/`. Input is the scores CSV
produced by `validate_audio_quality.py`. Output is `suspect_audio.csv`
(standardized name per B9.2 plan, not Jacob's per-language
`{Lang}_scores_suspicious.csv`).

For each metric (`ctc_score`, `pdm_score`, `wer`, `cer`), the per-language
distribution is independently rank-normalized; an entry is flagged if
it falls in the worst K%% of that metric. The suspicion score is

    suspicion = (100 - worst_pct_rank) + 10 * (n_triggers - 1)

Each suspicious row also emits a SOFT Finding so the rest of the QC
suite has visibility (and CI can surface counts).

Usage:
    python QC/validation/flag_audio_suspicious.py \\
        --scores Corpora/ePark/results/Amis_scores.csv \\
        --out    Corpora/ePark/results/suspect_audio.csv
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from statistics import median

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.validation._finding import Finding, Severity  # noqa: E402


RULE_SUSPECT = "V140"


# (column_name, higher_is_better, default_pct)
METRICS = [
    ("ctc_score",  True,  5.0),
    ("pdm_score",  True,  5.0),
    ("wer",        False, 5.0),
    ("cer",        False, 5.0),
]


def to_float(s):
    if s is None or s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def percentile_rank(values, value, higher_is_better) -> float | None:
    """Return percentile 0-100 of `value` in `values`; 0 = worst.

    Skips Nones. If higher_is_better is True, "worst" = smallest value.
    """
    if value is None:
        return None
    sorted_vals = sorted(v for v in values if v is not None)
    if not sorted_vals:
        return None
    if higher_is_better:
        idx = next((i for i, v in enumerate(sorted_vals) if v >= value),
                   len(sorted_vals) - 1)
    else:
        idx = next((i for i, v in enumerate(sorted_vals[::-1]) if v <= value),
                   len(sorted_vals) - 1)
    return 100.0 * idx / max(1, len(sorted_vals) - 1)


def load_scores(scores_path: Path) -> list[dict]:
    rows: list[dict] = []
    with scores_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for col, *_ in METRICS:
                if col in row:
                    row[col] = to_float(row[col])
            rows.append(row)
    return rows


def flag(rows: list[dict], worst_pct: float = 5.0, min_agreement: int = 1,
         abs_cutoffs: dict | None = None, limit: int = 0) -> list[dict]:
    """Rank-normalize per-language, return suspicious rows sorted worst-first."""
    abs_cutoffs = abs_cutoffs or {}

    # Group by language (each language gets its own percentile distribution).
    by_lang: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_lang[r.get("lang", "")].append(r)

    flagged_all: list[dict] = []
    for lang, lang_rows in by_lang.items():
        distributions = {col: [r.get(col) for r in lang_rows if r.get(col) is not None]
                         for col, *_ in METRICS}
        pct_cutoffs = {}
        for col, higher_is_better, _ in METRICS:
            vals = sorted(distributions[col])
            if not vals:
                pct_cutoffs[col] = None
                continue
            k = max(1, int(len(vals) * worst_pct / 100.0))
            pct_cutoffs[col] = vals[k - 1] if higher_is_better else vals[-k]

        for r in lang_rows:
            triggers = []
            for col, higher_is_better, _ in METRICS:
                v = r.get(col)
                if v is None:
                    continue
                cutoff = abs_cutoffs.get(col)
                if cutoff is not None:
                    hit = (v < cutoff) if higher_is_better else (v > cutoff)
                else:
                    pc = pct_cutoffs[col]
                    if pc is None:
                        hit = False
                    else:
                        hit = (v <= pc) if higher_is_better else (v >= pc)
                if hit:
                    triggers.append(col)
            if len(triggers) < min_agreement:
                continue
            ranks = []
            for col, higher_is_better, _ in METRICS:
                if r.get(col) is None:
                    continue
                ranks.append(percentile_rank(distributions[col], r[col], higher_is_better))
            worst_rank = min(ranks) if ranks else 100.0
            agreement_bonus = 10.0 * (len(triggers) - 1)
            out_row = {**{k: r[k] for k in r if k not in {c for c, *_ in METRICS}}}
            for col, *_ in METRICS:
                v = r.get(col)
                out_row[col] = v if v is not None else ""
            out_row["triggers"] = ",".join(triggers)
            out_row["n_triggers"] = len(triggers)
            out_row["worst_pct_rank"] = round(worst_rank, 2)
            out_row["suspicion"] = round((100.0 - worst_rank) + agreement_bonus, 2)
            flagged_all.append(out_row)

    flagged_all.sort(key=lambda r: (-r["suspicion"], r["worst_pct_rank"]))
    if limit:
        flagged_all = flagged_all[:limit]
    return flagged_all


def write_suspects(out_path: Path, flagged: list[dict]) -> None:
    if not flagged:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("", encoding="utf-8")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(flagged[0].keys()))
        writer.writeheader()
        writer.writerows(flagged)


def as_findings(flagged: list[dict]) -> list[Finding]:
    """One SOFT Finding per suspicious row, for downstream visibility."""
    out: list[Finding] = []
    for row in flagged:
        path_str = row.get("audio_path") or row.get("sentence_id") or ""
        out.append(Finding(
            rule_id=RULE_SUSPECT,
            severity=Severity.SOFT,
            message=(f"suspect audio (triggers={row.get('triggers','')}, "
                     f"suspicion={row.get('suspicion','')})"),
            path=Path(path_str) if path_str else Path("."),
            location=row.get("sentence_id"),
            language=row.get("lang"),
        ))
    return out


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--scores", required=True, type=Path,
                   help="scores CSV from validate_audio_quality.py")
    p.add_argument("--out", type=Path, default=None,
                   help="output CSV (default: suspect_audio.csv next to scores)")
    p.add_argument("--worst-pct", type=float, default=5.0,
                   help="flag entries in the worst K%% of any single metric (default: 5)")
    p.add_argument("--min-agreement", type=int, default=1,
                   help="require this many metrics to agree (default: 1)")
    p.add_argument("--ctc-max", type=float, default=None,
                   help="absolute cutoff: flag if ctc_score < this")
    p.add_argument("--pdm-max", type=float, default=None,
                   help="absolute cutoff: flag if pdm_score < this")
    p.add_argument("--wer-min", type=float, default=None,
                   help="absolute cutoff: flag if wer > this")
    p.add_argument("--cer-min", type=float, default=None,
                   help="absolute cutoff: flag if cer > this")
    p.add_argument("--limit", type=int, default=0,
                   help="cap the worklist size (0 = no cap)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    if not args.scores.is_file():
        print(f"scores file not found: {args.scores}", file=sys.stderr)
        return 2
    out_path = args.out if args.out is not None else (args.scores.parent / "suspect_audio.csv")
    rows = load_scores(args.scores)
    if not rows:
        print(f"{args.scores} has no rows", file=sys.stderr)
        return 0
    abs_cutoffs = {
        "ctc_score": args.ctc_max,
        "pdm_score": args.pdm_max,
        "wer":       args.wer_min,
        "cer":       args.cer_min,
    }
    flagged = flag(rows, worst_pct=args.worst_pct, min_agreement=args.min_agreement,
                   abs_cutoffs=abs_cutoffs, limit=args.limit)
    write_suspects(out_path, flagged)

    if flagged:
        print(f"Flagged {len(flagged)} / {len(rows)} entries → {out_path}", file=sys.stderr)
        # Median per metric for diagnostics
        for col, *_ in METRICS:
            vals = [r.get(col) for r in rows if r.get(col) is not None]
            if vals:
                print(f"  {col:<10} median={median(vals):.4f}  n={len(vals)}",
                      file=sys.stderr)
    else:
        print("No suspicious entries under the current thresholds.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
