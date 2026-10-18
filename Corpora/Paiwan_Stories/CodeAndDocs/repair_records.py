#!/usr/bin/env python3
"""Record the reviewed ID, locator and quotation repairs to the old transcription.

This one-off migration is not a build step. Source words and translations stay
unchanged; the S4 spacing follows Hartshorne's published 4e1a510df correction.
"""

import csv
from pathlib import Path


def repair(path: Path) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = [name for name in reader.fieldnames if name not in {"review_status", "audio_filename", "notes"}]
        fields.insert(fields.index("original"), "notes")
        records = list(reader)
    for row in records:
        if not row["legacy_id"] and (row["story"], row["sequence"]) != ("maljialjian", "7"):
            raise ValueError("unreviewed new source unit")
        row["s_id"] = row["legacy_id"] or "S6a"
        if row["story"] == "maljialjian":
            sequence = int(row["sequence"])
            physical_row = sequence if sequence <= 4 else sequence - 1
            part = ", first unit" if sequence == 4 else ", second unit" if sequence == 5 else ""
            locator = f"Word table row {physical_row}{part}"
            row["original_locator"] = row["translation_locator"] = locator
            if sequence == 4:
                row["original"] = row["original"].replace("sikudakuda ?", "sikudakuda?")
                row["notes"] = "Published quotation typography retained (Hartshorne, 2026-06-08, 4e1a510df)."
            elif sequence == 12:
                row["notes"] = "Published comma spacing and quotation typography retained."
            elif sequence == 13:
                row["notes"] = "Published quotation typography retained."
        if row["story"] == "dingding" and row["s_id"] == "S15":
            row["notes"] = "Published ASCII exclamation mark retained; the PDF uses a full-width mark."
        if row["notes"] == "Paiwan and Chinese text visually verified against the rendered source":
            row["notes"] = ""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    repair(Path(__file__).resolve().parent / "data/reviewed_records.tsv")
