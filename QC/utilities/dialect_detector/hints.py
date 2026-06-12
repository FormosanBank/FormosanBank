from __future__ import annotations

# Ortho113.pdf as a dialect-detection signal — investigation outcome (2026-06-12).
#
# We evaluated whether the PDF could supply *grapheme-level* hints to separate the
# dialect pairs the held-out cross-validation actually confuses (Amis's four
# "common-orthography" dialects, and Paiwan). It cannot, and the reason is in the
# TSVs themselves:
#   - Paiwan: all four dialects share an IDENTICAL letter inventory in
#     Orthographies/Ortho113/Paiwan.tsv (no NA cells); they differ only in IPA
#     realization (e.g. Southern r->R, l->ɣ), not in graphemes.
#   - Amis: the four common dialects (Xiuguluan/Coastal/Malan/Hengchun) share one
#     writing system (通用版); only Southern (南勢) is orthographically distinct,
#     and that distinction is already in Amis.tsv (b/v/u vs f/o).
# So the languages that are orthographically separable are already at ~1.0
# held-out, and the hard cases have NO orthographic signal to encode — their
# dialects are written identically and can only be told apart lexically (which
# the word feature already does). Hand-authored grapheme hints would encode
# rules that do not exist. The PDF's usable contribution is therefore the
# naming/alias reconciliation below, not orthography rules.

# Alias -> canonical Official dialect name. Seeded from Ortho113.pdf renaming
# notes (appendix p.74) and dialects.csv OtherNames. Extend as needed.
DIALECT_ALIASES: dict[str, str] = {
    "Chulu": "Xiqun",        # 初鹿 -> 西群 (Puyuma)
    "Northern Amis": "Southern",  # 北部阿美 -> 南勢 (note: 'Southern' is 南勢)
    "Central Amis": "Xiuguluan",  # 中部阿美 -> 秀姑巒
    "Toda": "Duda",          # dialects.csv OtherNames (Seediq)
    "Tgdaya": "Tegudaya",
}
