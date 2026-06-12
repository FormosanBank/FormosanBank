from __future__ import annotations

# Alias -> canonical Official dialect name. Seeded from Ortho113.pdf renaming
# notes (appendix p.74) and dialects.csv OtherNames. Extend as needed.
DIALECT_ALIASES: dict[str, str] = {
    "Chulu": "Xiqun",        # 初鹿 -> 西群 (Puyuma)
    "Northern Amis": "Southern",  # 北部阿美 -> 南勢 (note: 'Southern' is 南勢)
    "Central Amis": "Xiuguluan",  # 中部阿美 -> 秀姑巒
    "Toda": "Duda",          # dialects.csv OtherNames (Seediq)
    "Tgdaya": "Tegudaya",
}
