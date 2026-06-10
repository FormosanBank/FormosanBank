"""Per-corpus statistics CSVs for FormosanBank (consumed by the Gitbook).

Counting rules live in QC/corpus_counts.py (shared with corpus_metrics.py
and count_tokens.py). Writes statistics/<CorpusName>_corpora_stats.csv.

Audio durations are NOT computed here (CI has no audio files): the
seconds columns are carried forward from the existing CSV and refreshed
only by the manual QC/utilities/update_audio_stats.py. Audio *counts*
are recomputed from XML on every run.

Column names through `file_count` are a published interface: the Gitbook's
update_corpus_stats.py reads them by name. Only append columns, never
rename or remove.
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import corpus_counts

FIELDNAMES = [
    "language", "dialect", "segmented_words", "glossed_words",
    "transcribed_audio_count", "transcribed_audio_seconds",
    "untranscribed_audio_count", "untranscribed_audio_seconds",
    "eng_transl_count", "zho_transl_count", "word_count", "file_count",
    # Appended 2026-06 (pipeline unification); safe for DictReader consumers.
    "sentences", "word_elements", "morpheme_elements",
    "translation_elements", "audio_elements", "parse_errors",
]

SUM_FIELDS = [f for f in FIELDNAMES if f not in
              ("language", "dialect",
               "transcribed_audio_seconds", "untranscribed_audio_seconds",
               "parse_errors")]


def load_carry_seconds(csv_path: Path) -> dict:
    """Read seconds columns from an existing CSV, keyed (language, dialect).

    Missing CSV is normal for a brand-new corpus: seconds start at 0 and
    get filled in by a manual update_audio_stats.py run."""
    carried = {}
    if not csv_path.is_file():
        return carried
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row.get("language", ""), row.get("dialect", ""))
            carried[key] = (
                float(row.get("transcribed_audio_seconds") or 0),
                float(row.get("untranscribed_audio_seconds") or 0),
            )
    return carried


def stats_paths(corpus_path: Path) -> tuple[Path, str]:
    """Derive (repo_root/statistics dir, corpus name) from the corpus path."""
    parts = corpus_path.resolve().parts
    corpora_idx = next((i for i, p in enumerate(parts) if p == "Corpora"), None)
    if corpora_idx is not None:
        repo_root = Path(*parts[:corpora_idx])
        name = parts[corpora_idx + 1] if corpora_idx + 1 < len(parts) else "unknown"
    else:
        repo_root = corpus_path.resolve()
        name = repo_root.name
    return repo_root / "statistics", name


def process_corpus(corpus_path: Path, strict: bool) -> int:
    """Analyze one corpus directory and write its CSV. Returns exit code."""
    corpus_path = Path(corpus_path)
    xml_dir = corpus_path / "XML" if (corpus_path / "XML").is_dir() else corpus_path
    stats_dir, corpus_name = stats_paths(corpus_path)
    csv_path = stats_dir / f"{corpus_name}_corpora_stats.csv"

    carried = load_carry_seconds(csv_path)

    buckets = defaultdict(lambda: {f: 0 for f in FIELDNAMES if f not in ("language", "dialect")})
    n_warnings = 0
    records, parse_errors = corpus_counts.collect_records(xml_dir)

    for record in records:
        key = (record["language"], record["dialect"])
        bucket = buckets[key]
        for field in SUM_FIELDS:
            bucket[field] += record[field]
        for warning in record["warnings"]:
            n_warnings += 1
            print(f"[get_corpus_stats] WARNING {record['path']}: {warning}", file=sys.stderr)

    for key, (t_sec, u_sec) in carried.items():
        if key in buckets:
            buckets[key]["transcribed_audio_seconds"] = t_sec
            buckets[key]["untranscribed_audio_seconds"] = u_sec

    for item in parse_errors:
        print(f"[get_corpus_stats] PARSE ERROR {item['path']}: {item['error']}", file=sys.stderr)
    if parse_errors:
        buckets[("", "")]["parse_errors"] = len(parse_errors)

    stats_dir.mkdir(exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for (language, dialect), values in sorted(buckets.items()):
            values["transcribed_audio_seconds"] = round(values["transcribed_audio_seconds"], 1)
            values["untranscribed_audio_seconds"] = round(values["untranscribed_audio_seconds"], 1)
            writer.writerow({"language": language, "dialect": dialect, **values})

    print(f"Corpus statistics saved to {csv_path} "
          f"({len(records)} files, {len(parse_errors)} parse errors, {n_warnings} warnings)")
    return 1 if (strict and parse_errors) else 0


def main() -> int:
    default_corpora = Path(__file__).resolve().parents[2] / "Corpora"
    parser = argparse.ArgumentParser(description="Per-corpus statistics CSVs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("corpora_path", nargs="?",
                       help="Path to a single corpus directory (e.g. Corpora/ePark).")
    group.add_argument("--all", action="store_true",
                       help="Run on every corpus under --corpora_root.")
    parser.add_argument("--corpora_root", default=str(default_corpora),
                        help="Collection root used with --all (default: repo Corpora/).")
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero if any XML file fails to parse.")
    args = parser.parse_args()

    if args.all:
        corpora_root = Path(args.corpora_root).resolve()
        corpus_dirs = sorted(d for d in corpora_root.iterdir()
                             if d.is_dir() and (d / "XML").is_dir())
        if not corpus_dirs:
            print(f"No corpus directories with XML/ in {corpora_root}", file=sys.stderr)
            return 1
        worst = 0
        for corpus_dir in corpus_dirs:
            print(f"Processing {corpus_dir.name} …")
            worst = max(worst, process_corpus(corpus_dir, args.strict))
        return worst
    return process_corpus(Path(args.corpora_path), args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
