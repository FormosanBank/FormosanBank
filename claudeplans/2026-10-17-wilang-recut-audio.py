#!/usr/bin/env python3
"""Re-cut the Wilang Yutas audio for the 22 source end times (maintainer 2026-10-17: "Go with B - fix all 22").

Run on the Mac (Hugging Face is not reachable from the container), from the FormosanBank folder, with the
Wilang branch's two tables available (pass the folder that holds them):

    python3 claudeplans/2026-10-17-wilang-recut-audio.py

(the two tables are copied in claudeplans/2026-10-17-wilang-recut-tables/; or pass a CodeAndDocs folder)

Reads CodeAndDocs/caption_end_times.tsv (22 sentences) and CodeAndDocs/untranscribed_clips.tsv (7 new clips).
Downloads each of the 22 published sentence clips from FormosanBank/YutasWilang at the pinned revision, then
writes into ../WilangYutas_recut/Atayal/ (next to the FormosanBank folder):
  * each sentence clip trimmed to (end - start) seconds, under its published name;
  * each new untranscribed clip = the part of a sentence clip after the sentence's new end.
Nothing is uploaded and nothing in the repository changes. Standard library only (PCM WAV via `wave`).
Prints every output with its duration and SHA-256, and checks each against the expected length.
"""
import csv, hashlib, sys, urllib.request, wave
from pathlib import Path

REV = "84f9ff90ad4d92b136c14f143e5184549cdb1cdb"
BASE = f"https://huggingface.co/datasets/FormosanBank/YutasWilang/resolve/{REV}/Atayal/"
OUT = Path(__file__).resolve().parent.parent.parent / "WilangYutas_recut" / "Atayal"
CACHE = OUT.parent / "_downloaded"


def fetch(name: str) -> Path:
    dest = CACHE / name
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"  downloading {name} ...", flush=True)
        with urllib.request.urlopen(BASE + name, timeout=300) as r, open(dest, "wb") as f:
            while chunk := r.read(1 << 20):
                f.write(chunk)
    return dest


def cut(src: Path, dest: Path, from_s: float, to_s: float | None) -> float:
    with wave.open(str(src), "rb") as w:
        params, rate, total = w.getparams(), w.getframerate(), w.getnframes()
        a = round(from_s * rate)
        b = total if to_s is None else min(total, round(to_s * rate))
        w.setpos(a)
        frames = w.readframes(b - a)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dest), "wb") as o:
        o.setparams(params)
        o.writeframes(frames)
    return (b - a) / rate


def report(path: Path, seconds: float, expected: float | None) -> None:
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    flag = "" if expected is None or abs(seconds - expected) < 0.1 else f"  <-- expected {expected:.2f}"
    print(f"{path.name}\t{seconds:.2f}\t{sha}{flag}", flush=True)


def main() -> None:
    codedocs = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("2026-10-17-wilang-recut-tables")
    ends = list(csv.DictReader(open(codedocs / "caption_end_times.tsv", encoding="utf-8"), delimiter="\t"))
    clips = list(csv.DictReader(open(codedocs / "untranscribed_clips.tsv", encoding="utf-8"), delimiter="\t"))
    assert len(ends) == 22 and len(clips) == 7, (len(ends), len(clips))
    print("file\tseconds\tsha256")
    by_new_end = {}
    for row in ends:
        name = f"{row['output_stem']}_{row['sentence_id']}.wav"
        start, end = float(row["start"]), float(row["end"])
        src = fetch(name)
        report(OUT / name, cut(src, OUT / name, 0.0, end - start), end - start)
        by_new_end[(row["output_stem"], row["end"])] = (src, start)
    for clip in clips:
        stem = Path(clip["companion_output"]).stem.removesuffix("_untranscribed")
        src, start = by_new_end[(stem, clip["start"])]
        offset = float(clip["start"]) - start
        seconds = cut(src, OUT / clip["file"], offset, None)
        report(OUT / clip["file"], seconds, float(clip["end"]) - float(clip["start"]))
    print(f"\nWrote {len(ends) + len(clips)} files to {OUT}. Upload after review with:")
    print(f"  hf upload FormosanBank/YutasWilang {OUT} Atayal --repo-type dataset "
          f"--commit-message \"Wilang: source end times for 22 sentences; 7 untranscribed clips\"")


if __name__ == "__main__":
    main()
