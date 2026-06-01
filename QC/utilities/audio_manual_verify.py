"""audio_manual_verify.py — interactive CLI for triaging the suspect worklist.

Port of Jacob Ye's `manual_verify.py` from
`Formosan-ILRDF_Dicts/data_validation/`.

For each row in `suspect_audio.csv`, plays the audio, prints the
transcript + ASR hypothesis, and prompts for a verdict. Verdicts are
written to `{Lang}_verdicts.csv` (or whatever path the operator passes
to `--verdicts`). Re-running resumes from the first unverified row.

Single-keypress controls (no Enter required if `readchar` is installed):
    p   play audio again
    c   mark CORRECT
    w   mark WRONG
    u   mark UNCLEAR
    s   skip (no verdict recorded, advance)
    n   add a free-text note to the current row, then re-prompt
    b   back one entry
    q   quit and save

Usage:
    python QC/utilities/audio_manual_verify.py \\
        --suspicious Corpora/ePark/results/suspect_audio.csv \\
        --verdicts   Corpora/ePark/results/Amis_verdicts.csv \\
        [--player afplay]
"""
import argparse
import csv
import shutil
import subprocess
import sys
from pathlib import Path


VERDICT_HEADER_EXTRA = ["verdict", "notes"]


def get_player(name: str | None) -> list[str]:
    if name:
        return [name]
    for cand, args in [
        ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
        ("afplay", []),
        ("aplay", []),
        ("mpg123", ["-q"]),
        ("mpv", ["--really-quiet"]),
    ]:
        if shutil.which(cand):
            return [cand] + args
    raise SystemExit(
        "No audio player found. Install ffmpeg (provides ffplay) or pass --player <cmd>."
    )


def play(player_cmd: list[str], audio_path: str) -> None:
    if not Path(audio_path).is_file():
        print(f"  [audio missing: {audio_path}]")
        return
    try:
        subprocess.run(player_cmd + [audio_path], check=False)
    except KeyboardInterrupt:
        pass


def get_keypress(prompt: str) -> str:
    """Single-char input where possible, fallback to line input."""
    try:
        import readchar
        sys.stdout.write(prompt)
        sys.stdout.flush()
        ch = readchar.readkey()
        print(ch)
        return ch.lower().strip()
    except ImportError:
        return input(prompt).lower().strip()


def load_verdicts(path: Path) -> tuple[dict, list[dict]]:
    if not path.exists():
        return {}, []
    out: dict = {}
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            sid = row.get("sentence_id")
            if sid and row.get("verdict"):
                out[sid] = row
    return out, rows


def write_verdicts(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def fmt_score(s) -> str:
    if s is None or s == "":
        return "—"
    try:
        return f"{float(s):.3f}"
    except (TypeError, ValueError):
        return str(s)


def display(idx: int, total: int, row: dict) -> None:
    sid = row.get("sentence_id", "?")
    lang = row.get("lang", "")
    print()
    print("=" * 72)
    print(f"[{idx + 1} / {total}]  {lang}  {sid}")
    if row.get("word"):
        print(f"  word     : {row['word']}")
    print(f"  triggers : {row.get('triggers','')}  "
          f"(n={row.get('n_triggers','')}, suspicion={row.get('suspicion','')})")
    print(f"  ctc={fmt_score(row.get('ctc_score'))}  "
          f"pdm={fmt_score(row.get('pdm_score'))}  "
          f"wer={fmt_score(row.get('wer'))}  "
          f"cer={fmt_score(row.get('cer'))}")
    print(f"  audio    : {row.get('audio_path','')}")
    print(f"  TRANSCRIPT : {row.get('transcript','')}")
    if row.get("asr_hypothesis"):
        print(f"  ASR HYPOTH : {row['asr_hypothesis']}")
    print()


def prepare_working_list(susp_rows: list[dict], susp_fields: list[str],
                         existing_by_id: dict) -> tuple[list[dict], list[str]]:
    """Build the working list, merging in any prior verdicts."""
    fieldnames = list(susp_fields) + [c for c in VERDICT_HEADER_EXTRA if c not in susp_fields]
    working: list[dict] = []
    for r in susp_rows:
        sid = r.get("sentence_id")
        prev = existing_by_id.get(sid)
        merged = {k: r.get(k, "") for k in fieldnames}
        if prev:
            merged["verdict"] = prev.get("verdict", "")
            merged["notes"] = prev.get("notes", "")
        working.append(merged)
    return working, fieldnames


def first_unverified_index(working: list[dict]) -> int:
    return next((i for i, r in enumerate(working) if not r.get("verdict")), 0)


def apply_decision(row: dict, ch: str) -> str | None:
    """Apply a single-key decision to `row` in place. Returns one of:
    'advance', 'reprompt', 'back', 'quit', or None on unrecognized.
    """
    if ch == "p":
        return "reprompt"  # caller replays audio + reprompts
    if ch == "n":
        return "note"      # caller takes a note then reprompts
    if ch == "c":
        row["verdict"] = "correct"
        return "advance"
    if ch == "w":
        row["verdict"] = "wrong"
        return "advance"
    if ch == "u":
        row["verdict"] = "unclear"
        return "advance"
    if ch == "s":
        return "advance"   # skip — leave verdict blank, advance
    if ch == "b":
        return "back"
    if ch == "q":
        return "quit"
    return None


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--suspicious", required=True, type=Path,
                   help="suspect_audio.csv from flag_audio_suspicious.py")
    p.add_argument("--verdicts", type=Path, default=None,
                   help="output CSV (default: <suspicious stem>_verdicts.csv)")
    p.add_argument("--player", default=None,
                   help="override audio player command (ffplay / afplay / mpv / …)")
    p.add_argument("--auto-play", default="yes", choices=["yes", "no"],
                   help="play audio automatically when an entry is shown (default: yes)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    susp_path: Path = args.suspicious
    if not susp_path.is_file():
        print(f"suspicious file not found: {susp_path}", file=sys.stderr)
        return 2
    verdicts_path = args.verdicts if args.verdicts is not None else susp_path.with_name(
        susp_path.stem.replace("_suspicious", "") + "_verdicts.csv"
    )

    with susp_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        susp_rows = list(reader)
        susp_fields = reader.fieldnames or []
    if not susp_rows:
        print(f"{susp_path} has no rows.", file=sys.stderr)
        return 0

    existing_by_id, _ = load_verdicts(verdicts_path)
    working, fieldnames = prepare_working_list(susp_rows, susp_fields, existing_by_id)
    player_cmd = get_player(args.player)
    auto_play = (args.auto_play == "yes")
    idx = first_unverified_index(working)
    if idx > 0:
        print(f"Resuming at row {idx + 1} (skipped {idx} already-verified entries).")

    try:
        while idx < len(working):
            row = working[idx]
            display(idx, len(working), row)
            if auto_play:
                play(player_cmd, row.get("audio_path", ""))

            ch = get_keypress(
                "verdict? [c]orrect [w]rong [u]nclear [p]lay [n]ote [s]kip [b]ack [q]uit > "
            )
            action = apply_decision(row, ch)
            if action is None:
                print("  (unrecognized — try one of c / w / u / p / n / s / b / q)")
                continue
            if action == "reprompt":
                play(player_cmd, row.get("audio_path", ""))
                continue
            if action == "note":
                row["notes"] = input("note: ").strip()
                continue
            if action == "back":
                idx = max(0, idx - 1)
                continue
            if action == "quit":
                break
            # 'advance'
            write_verdicts(verdicts_path, working, fieldnames)
            idx += 1
    finally:
        write_verdicts(verdicts_path, working, fieldnames)
        decided = sum(1 for r in working if r.get("verdict"))
        correct = sum(1 for r in working if r.get("verdict") == "correct")
        wrong = sum(1 for r in working if r.get("verdict") == "wrong")
        unclear = sum(1 for r in working if r.get("verdict") == "unclear")
        print()
        print(f"Saved {decided} / {len(working)} verdicts to {verdicts_path}")
        print(f"  correct={correct}  wrong={wrong}  unclear={unclear}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
