"""Shared, source-verified configuration for the Nanpo Dozoku Pazeh songs."""

from __future__ import annotations

import os
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SOURCE_PATH = Path(
    os.environ.get(
        "SOURCE_PDF",
        ROOT / "Private" / "source" / "nanpo_dozoku_v3n1_taisha_songs_1931.pdf",
    )
)
SOURCE_SHA256 = "094658186d845c0fd1fae2da6a8c41870734742a08e86fcfa97815710e1f485e"
SOURCE_BYTES = 16_508_391
SOURCE_PAGES = 14

CITATION = (
    'Sato, B. 1931. "Native Songs from Taisha-sho, Pazeh Tribe, Formosa" '
    "(大社庄の蕃歌). Nanpo Dozoku 3(1): 116–126."
)
BIBTEX = (
    "@article{sato1931taisha, author={Sato, B.}, "
    "title={Native Songs from Taisha-sho, Pazeh Tribe, Formosa}, "
    "journal={Nanpo Dozoku}, year={1931}, volume={3}, number={1}, "
    "pages={116--126}}"
)
# POL-042: exactly one value from FormosanBank's rights_vocabulary.csv.
# Project-director determination, 2026-09-10 — see the Rights section of
# ../README.md for the reasoning, which is not a grant.
COPYRIGHT = "CC BY-NC 4.0"

SOURCE_ATTRIBUTE = (
    "Basecamp card 8538287698; NTU Library item 812667; "
    "NLPI catalog https://das.nlpi.edu.tw/handle/a678g"
)

TEXTS = {
    "kaiki": {
        "title": "I 開基之歌 (Song of Origins)",
        "text_id": "Nanpo1931_Pazeh_Kaiki_no_Uta",
        "id_prefix": "nanpo1931_kaiki",
        "filename": "Nanpo_Dozoku_1931_Kaiki_no_Uta.xml",
        "expected_count": 21,
    },
    "flood": {
        "title": "II 大水氾濫之歌 (Song of the Great Flood)",
        "text_id": "Nanpo1931_Pazeh_Daisui_Hanran_no_Uta",
        "id_prefix": "nanpo1931_flood",
        "filename": "Nanpo_Dozoku_1931_Daisui_Hanran_no_Uta.xml",
        "expected_count": 39,
    },
    "dispersion": {
        "title": "III 氾濫後人民分居之歌 (Song of Post-Flood Dispersion)",
        "text_id": "Nanpo1931_Pazeh_Hanran_go_Jinmin_Bunkyo_no_Uta",
        "id_prefix": "nanpo1931_dispersion",
        "filename": "Nanpo_Dozoku_1931_Hanran_go_Jinmin_Bunkyo_no_Uta.xml",
        "expected_count": 23,
    },
}

FINAL_DIR = ROOT / "XML" / "Pazeh"
REVIEWED_CSV = HERE / "intermediate" / "reviewed_sentences.csv"
BLOCKS_CSV = HERE / "intermediate" / "source_blocks.csv"
LEDGER_CSV = HERE / "intermediate" / "source_ledger.csv"


def final_path(text_key: str) -> Path:
    return FINAL_DIR / TEXTS[text_key]["filename"]


def sentence_id(text_key: str, sequence: int) -> str:
    if text_key == "dispersion" and sequence == 22:
        return "nanpo1931_dispersion_s021b"
    if text_key == "dispersion" and sequence == 23:
        return "nanpo1931_dispersion_s022"
    return f"{TEXTS[text_key]['id_prefix']}_s{sequence:03d}"


def relative_final_path(text_key: str) -> str:
    return final_path(text_key).relative_to(ROOT).as_posix()


def source_locator(row: dict[str, str]) -> str:
    pdf_page = int(row["page"]) - 115
    return f"attachment PDF p. {pdf_page}; printed p. {row['page']}, {row['source_line']}"
