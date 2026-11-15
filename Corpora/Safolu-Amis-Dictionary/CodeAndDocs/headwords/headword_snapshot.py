#!/usr/bin/env python3
"""Capture the headword fields of the Safolu dictionary from g0v/amis-moedict checkouts.

The headword generator (generate_headwords.py) reads only the snapshot this writes, never a checkout.
Run explicitly, never during XML generation:

    python3 CodeAndDocs/headwords/headword_snapshot.py BASE_DOCS_S PIN_DOCS_S

BASE_DOCS_S: docs/s at the examples' snapshot (e7c6976a0766e9b0aeb7083e2c06db60f5485252); it fixes the headword
             order, so the S ids (H00001, ...) follow the same order as the examples file's source.
PIN_DOCS_S:  docs/s at the editors' version (4cb82539d7e51e7211e262d4dbaecaa41a772b2f), whose text is published
             (maintainer, s-version: "Editors' version (4cb82539d)"). Files only in the pin are appended.
Writes headword_source.jsonl.gz (one row per headword file: ordinal, file, t, stem, tag, h = [{name, d: [{f}]}])
and headword_manifest.json (commits, counts, sha256).
"""
import gzip, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPECIAL = {"=.json", "ch-mapping.json", "index.json", "lenToRegex.json", "precomputed.json", "stem-words.json"}
BASE_COMMIT = "e7c6976a0766e9b0aeb7083e2c06db60f5485252"
PIN_COMMIT = "4cb82539d7e51e7211e262d4dbaecaa41a772b2f"


def main():
    base, pin = Path(sys.argv[1]), Path(sys.argv[2])
    base_names = sorted(p.name for p in base.glob("*.json") if p.name not in SPECIAL)
    pin_names = sorted(p.name for p in pin.glob("*.json") if p.name not in SPECIAL)
    order = base_names + [n for n in pin_names if n not in set(base_names)]
    rows = []
    for ordinal, name in enumerate(order, 1):
        path = pin / name
        if not path.exists():
            continue
        e = json.loads(path.read_text(encoding="utf-8"))
        row = {"ordinal": ordinal, "file": name, "t": e["t"]}
        for k in ("stem", "tag"):
            if e.get(k):
                row[k] = e[k]
        row["h"] = [dict(({"name": h["name"]} if h.get("name") else {}), d=[{"f": d.get("f", "")} for d in h.get("d", [])]) for h in e.get("h", [])]
        rows.append(row)
    out = HERE / "headword_source.jsonl.gz"
    data = "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows).encode("utf-8")
    with gzip.GzipFile(out, "wb", mtime=0) as f:
        f.write(data)
    manifest = {"source": "https://github.com/g0v/amis-moedict", "path": "docs/s", "order_commit": BASE_COMMIT,
                "text_commit": PIN_COMMIT, "headword_files": len(rows), "base_files": len(base_names),
                "files_only_in_text_commit": len(order) - len(base_names),
                "senses": sum(len(h["d"]) for r in rows for h in r["h"]),
                "snapshot_sha256": hashlib.sha256(data).hexdigest()}
    (HERE / "headword_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
