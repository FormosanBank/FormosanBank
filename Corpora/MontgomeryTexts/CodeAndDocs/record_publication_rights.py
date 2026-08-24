#!/usr/bin/env python3
"""Record the maintainer-confirmed publication rights decision."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CORPUS_ROOT = Path(__file__).resolve().parents[1]
SOURCE_RECORDS = CORPUS_ROOT / "CodeAndDocs/source_records.json"
SOURCE_MANIFEST = CORPUS_ROOT / "CodeAndDocs/source_manifest.json"
OLD_NOTICE = "CC-BY-NC-ND"
PUBLICATION_NOTICE = "All rights reserved; FormosanBank has permission to publish."
RIGHTS_RECORD = (
    "Publication rights confirmed by the FormosanBank maintainer on 2026-08-23; "
    "no open license is asserted."
)
PRIVATE_SOURCE_REPO = "FormosanBank/Formosan-Old_Texts"
PRIVATE_SOURCE_COMMIT = "e1f52f43ab9e17b1d9a99329964b2ab64fbe864a"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def update_source_records() -> int:
    data = load_json(SOURCE_RECORDS)
    texts = data.get("texts", [])
    if len(texts) != 3:
        raise ValueError(f"Expected 3 Montgomery texts, found {len(texts)}")

    changed = 0
    for text in texts:
        notice = text.get("copyright")
        if notice not in {OLD_NOTICE, PUBLICATION_NOTICE}:
            raise ValueError(
                f"Unexpected copyright notice for {text['text_id']}: {notice!r}"
            )
        if notice != PUBLICATION_NOTICE:
            text["copyright"] = PUBLICATION_NOTICE
            changed += 1
    write_json(SOURCE_RECORDS, data)
    return changed


def update_source_manifest() -> None:
    data = load_json(SOURCE_MANIFEST)
    source = data.get("source", {})
    if source.get("key") != "montgomery_1962_amis_text.pdf":
        raise ValueError("Unexpected Montgomery source manifest")
    source["rights"] = RIGHTS_RECORD
    source["private_source_repo"] = PRIVATE_SOURCE_REPO
    source["private_source_commit"] = PRIVATE_SOURCE_COMMIT
    write_json(SOURCE_MANIFEST, data)


def main() -> int:
    changed = update_source_records()
    update_source_manifest()
    print(f"Recorded publication rights; updated {changed} source-text notices")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
