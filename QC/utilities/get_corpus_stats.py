"""Per-corpus statistics CSVs for FormosanBank (read by the documentation site).

Counting rules live in QC/corpus_counts.py (shared with corpus_metrics.py
and count_tokens.py). Writes statistics/<CorpusName>_corpora_stats.csv.

Audio durations are NOT computed here (CI has no audio files): the
seconds columns are read from statistics/audio_durations.csv (the
source of truth written by update_audio_stats.py / refresh_audio_stats.py).
Staleness is flagged when XML audio-element counts differ from those stored
in that file. Audio *counts* are recomputed from XML on every run.

Column names are a published interface: the documentation site
(docs/tools/site_stats.py) and anyone downloading the CSVs read them by name.
Only append columns, never rename or remove.
"""
import argparse
import csv
import hashlib
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import audio_durations
import corpus_counts

FIELDNAMES = [
    "language", "dialect", "segmented_words", "glossed_words",
    "transcribed_audio_count", "transcribed_audio_seconds",
    "untranscribed_audio_count", "untranscribed_audio_seconds",
    "eng_transl_count", "zho_transl_count", "word_count", "file_count",
    # Appended 2026-06 (pipeline unification); safe for DictReader consumers.
    "sentences", "word_elements", "morpheme_elements",
    "translation_elements", "audio_elements", "parse_errors",
    # Appended 2026-09-10; safe for DictReader consumers, same as the 2026-06 batch.
    "jpn_transl_count",
    "nld_transl_count",
    # Appended 2026-10-18 (documentation site growth figures).
    "transcribed_words",
]

SUM_FIELDS = [f for f in FIELDNAMES if f not in
              ("language", "dialect",
               "transcribed_audio_seconds", "untranscribed_audio_seconds",
               "parse_errors")]


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


# Discovery is shared with every other counting consumer via corpus_counts
# (maintainer ruling 2026-08-11: counting scripts must be physically unable
# to disagree on the file set).
corpus_xml_dirs = corpus_counts.corpus_xml_dirs
_collect_corpus_records = corpus_counts.collect_corpus_records


# What a corpus's CSV depends on besides its own files. If any of these changes,
# every corpus is regenerated (their git ids are part of each fingerprint).
_CODE_INPUTS = (
    "QC/utilities/get_corpus_stats.py", "QC/utilities/audio_durations.py",
    "QC/corpus_counts.py", "QC/xml_forms.py", "languages.csv",
)
SOURCES_FILE = "corpora_stats_sources.csv"  # beside the CSVs; not *_corpora_stats.csv


def _git(repo_root: Path, *args: str) -> str | None:
    proc = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else None


def fingerprint(corpus_dir: Path) -> str | None:
    """The inputs a corpus's CSV is computed from, as one hash; None if unknowable.

    None (always regenerate) when the corpus folder or a code input has
    uncommitted edits, or git is unavailable: the committed ids would not
    describe the files actually read.
    """
    stats_dir, name = stats_paths(corpus_dir)
    repo_root = stats_dir.parent
    if _git(repo_root, "status", "--porcelain", "--", f"Corpora/{name}", *_CODE_INPUTS) != "":
        return None
    parts = [f"corpus {_git(repo_root, 'rev-parse', f'HEAD:Corpora/{name}')}"]
    for rel in _CODE_INPUTS:
        parts.append(f"{rel} {_git(repo_root, 'rev-parse', f'HEAD:{rel}')}")
    durations = audio_durations.load_for_corpus(stats_dir, name)
    parts.append("audio " + repr(sorted(durations.items())))
    if any(p.split(" ", 1)[1] in ("None", "") for p in parts[:-1]):
        return None
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def load_sources(stats_dir: Path) -> dict[str, str]:
    path = stats_dir / SOURCES_FILE
    if not path.is_file():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {row["corpus"]: row["fingerprint"] for row in csv.DictReader(f)}


def save_sources(stats_dir: Path, sources: dict[str, str]) -> None:
    with open(stats_dir / SOURCES_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["corpus", "fingerprint"])
        writer.writeheader()
        for corpus in sorted(sources):
            writer.writerow({"corpus": corpus, "fingerprint": sources[corpus]})


def process_corpus(corpus_path: Path, strict: bool) -> int:
    """Analyze one corpus directory and write its CSV. Returns exit code."""
    corpus_path = Path(corpus_path)
    stats_dir, corpus_name = stats_paths(corpus_path)
    csv_path = stats_dir / f"{corpus_name}_corpora_stats.csv"

    durations = audio_durations.load_for_corpus(stats_dir, corpus_name)

    buckets: defaultdict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {f: 0 for f in FIELDNAMES if f not in ("language", "dialect")}
    )
    n_warnings = 0
    records, parse_errors = _collect_corpus_records(corpus_path)

    for record in records:
        key = (record["language"], record["dialect"])
        bucket = buckets[key]
        for field in SUM_FIELDS:
            bucket[field] += record[field]
        for warning in record["warnings"]:
            n_warnings += 1
            print(f"[get_corpus_stats] WARNING {record['path']}: {warning}", file=sys.stderr)

    # Fill seconds from the audio-durations source of truth and flag staleness.
    for key, bucket in buckets.items():
        entry = durations.get(key)
        if entry is not None:
            bucket["transcribed_audio_seconds"] = entry["transcribed_audio_seconds"]
            bucket["untranscribed_audio_seconds"] = entry["untranscribed_audio_seconds"]
        current_audio = bucket["transcribed_audio_count"] + bucket["untranscribed_audio_count"]
        if current_audio and audio_durations.is_stale(
                bucket["transcribed_audio_count"], bucket["untranscribed_audio_count"], entry):
            language, dialect = key
            anchor = (
                "never" if entry is None
                else "unknown" if (entry["transcribed_audio_count"] is None
                                   or entry["untranscribed_audio_count"] is None)
                else f"{entry['transcribed_audio_count']}+{entry['untranscribed_audio_count']}")
            print(f"[get_corpus_stats] STALE AUDIO {corpus_name} {language}/{dialect}: "
                  f"XML has {bucket['transcribed_audio_count']}+"
                  f"{bucket['untranscribed_audio_count']} audio elements; seconds "
                  f"computed against {anchor} (run refresh_audio_stats.py).",
                  file=sys.stderr)

    for item in parse_errors:
        print(f"[get_corpus_stats] PARSE ERROR {item['path']}: {item['error']}", file=sys.stderr)
    if parse_errors:
        buckets[("", "")]["parse_errors"] = len(parse_errors)

    stats_dir.mkdir(exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for (language, dialect), values in sorted(buckets.items()):
            values["transcribed_audio_seconds"] = round(float(values["transcribed_audio_seconds"]), 1)
            values["untranscribed_audio_seconds"] = round(float(values["untranscribed_audio_seconds"]), 1)
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
    group.add_argument("--report-stale-audio", action="store_true",
                       help="Scan corpora under --corpora_root and list every "
                            "stale (corpus, language, dialect) audio bucket; "
                            "write nothing. Exit 1 if any are stale.")
    parser.add_argument("--corpora_root", default=str(default_corpora),
                        help="Collection root used with --all (default: repo Corpora/).")
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero if any XML file fails to parse.")
    parser.add_argument("--changed-only", action="store_true",
                        help=f"With --all: regenerate only corpora whose inputs differ from those "
                             f"recorded in statistics/{SOURCES_FILE} (or whose CSV is missing), "
                             "and record the new ones.")
    args = parser.parse_args()

    if args.report_stale_audio:
        corpora_root = Path(args.corpora_root).resolve()
        any_stale = False
        for corpus_dir in sorted(d for d in corpora_root.iterdir()
                                 if d.is_dir() and corpus_xml_dirs(d)):
            stats_dir, corpus_name = stats_paths(corpus_dir)
            durations = audio_durations.load_for_corpus(stats_dir, corpus_name)
            records, _ = _collect_corpus_records(corpus_dir)
            counts: dict = {}
            for r in records:
                cur = counts.setdefault((r["language"], r["dialect"]), [0, 0])
                cur[0] += r["transcribed_audio_count"]
                cur[1] += r["untranscribed_audio_count"]
            for key, (t, u) in sorted(counts.items()):
                if (t + u) and audio_durations.is_stale(t, u, durations.get(key)):
                    any_stale = True
                    print(f"STALE {corpus_name} {key[0]}/{key[1]}: XML {t}+{u}")
        return 1 if any_stale else 0

    if args.all:
        corpora_root = Path(args.corpora_root).resolve()
        corpus_dirs = sorted(d for d in corpora_root.iterdir()
                             if d.is_dir() and corpus_xml_dirs(d))
        if not corpus_dirs:
            print(f"No corpus directories with XML/ in {corpora_root}", file=sys.stderr)
            return 1
        worst = 0
        stats_dir = stats_paths(corpus_dirs[0])[0]
        sources = load_sources(stats_dir) if args.changed_only else {}
        skipped = 0
        for corpus_dir in corpus_dirs:
            fp = fingerprint(corpus_dir) if args.changed_only else None
            csv_path = stats_dir / f"{corpus_dir.name}_corpora_stats.csv"
            if fp is not None and sources.get(corpus_dir.name) == fp and csv_path.is_file():
                skipped += 1
                continue
            print(f"Processing {corpus_dir.name} …")
            code = process_corpus(corpus_dir, args.strict)
            worst = max(worst, code)
            if args.changed_only:
                if fp is not None and code == 0:
                    sources[corpus_dir.name] = fp
                else:
                    sources.pop(corpus_dir.name, None)
        if args.changed_only:
            names = {d.name for d in corpus_dirs}
            save_sources(stats_dir, {c: v for c, v in sources.items() if c in names})
            print(f"Unchanged inputs, skipped: {skipped} of {len(corpus_dirs)} corpora")
        return worst
    return process_corpus(Path(args.corpora_path), args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
