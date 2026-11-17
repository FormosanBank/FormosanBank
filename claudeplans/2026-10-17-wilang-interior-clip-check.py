#!/usr/bin/env python3
"""Length of the 4 Wilang mid-video sentence clips on Hugging Face (read-only; reads ~4 KB per file).

Run on the Mac from the FormosanBank folder:  python3 claudeplans/2026-10-17-wilang-interior-clip-check.py
Reuses duration() from 2026-10-17-wilang-tail-clip-check.py (same folder).
"""
import runpy
from pathlib import Path

duration = runpy.run_path(str(Path(__file__).with_name("2026-10-17-wilang-tail-clip-check.py")), run_name="lib")["duration"]
# file, start, end in the first version (source caption track), end now
CLIPS = [
    ("20190209_YutasWilang_ki_Yagu_03_disanduan_Atayal_2.wav", 2.4, 6.4, 15.0),
    ("20190209_YutasWilang_ki_Yagu_05_diwuduan_Atayal_137.wav", 615.04, 619.34, 641.68),
    ("20190209_YutasWilang_ki_Yagu_07_diqiduan_yakidege_Atayal_4.wav", 13.28, 19.14, 46.5),
    ("muqianxianzuozhepian_20160525_binkafeifangtan_Yutas_Wilang_muqianxianzuozhepian_Atayal_196.wav", 858.6, 862.22, 862.72),
]
print("clip\tpublished seconds\tif cut to first-version end\tif cut to current end")
for name, start, old_end, new_end in CLIPS:
    print(name, duration(name), f"{old_end - start:.2f}", f"{new_end - start:.2f}", sep="\t", flush=True)
