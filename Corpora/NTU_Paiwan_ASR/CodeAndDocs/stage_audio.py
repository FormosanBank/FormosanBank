"""
Stage all NTU Paiwan FULL recordings under PUBLIC pseudonymised names, ready for
HuggingFace upload. Mirrors the published layout: Audio/Paiwan/<Pseudonym>/<name>.wav,
where <name> matches each XML's TEXT/@audio. Per-sentence clips are NOT staged here --
they are generated client-side by extract_audio_clips.py at download time.

Sources (real names / NTU codes -> pseudonyms via the same resolver as the converter):
  - Y1 audio:  Temp/NTU_Y1*/<realname>/*.wav  and  Temp/MissingWavs/*.wav
  - Y2 audio:  NTU_NewDownload/NTU_Y2/<code>/*.wav

Usage:  python CodeAndDocs/stage_audio.py [--out Audio]
"""
import argparse
import glob
import os
import re
import shutil

from build_y2_and_spontaneous import resolve_speaker, load_dialects


def stem_of(path):
    s = os.path.splitext(os.path.basename(path))[0].strip()
    return re.sub(r"\s*1\s*min$", "", s).strip()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(repo, "Audio"))
    ap.add_argument("--sources", nargs="*", default=[
        os.path.join(repo, "Temp"),
        os.path.join(repo, "NTU_NewDownload", "NTU_Y2"),
    ])
    args = ap.parse_args()

    staged = {}        # target_relpath -> source path (first wins; dedup)
    unresolved = []
    for root in args.sources:
        for wav in glob.glob(root + "/**/*.wav", recursive=True):
            pseud, pseud_stem = resolve_speaker(stem_of(wav))
            if pseud is None:
                unresolved.append(os.path.relpath(wav, repo))
                continue
            target = f"{pseud_stem.replace(' ', '_')}.wav"
            rel = os.path.join("Paiwan", pseud, target)
            staged.setdefault(rel, wav)

    for rel, src in staged.items():
        dst = os.path.join(args.out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.copy2(src, dst)

    by_pseud = {}
    for rel in staged:
        by_pseud.setdefault(rel.split(os.sep)[1], 0)
        by_pseud[rel.split(os.sep)[1]] += 1
    print(f"Staged {len(staged)} full recordings into {args.out}/Paiwan/<Pseudonym>/")
    for p in sorted(by_pseud):
        print(f"  {p:10} {by_pseud[p]}")
    if unresolved:
        print(f"\nUNRESOLVED sources ({len(unresolved)}):")
        for u in unresolved[:40]:
            print("  ", u)


if __name__ == "__main__":
    main()
