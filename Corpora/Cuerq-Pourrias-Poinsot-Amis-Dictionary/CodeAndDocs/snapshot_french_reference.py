#!/usr/bin/env python3
"""Write data/french_reference_pages_1_4.json: every French S from pages 1-4 of the old French-volume build.

The corpus test FrenchCarriedOver checks that each of these French translations appears in the new XML (maintainer,
round 3: "Please confirm that the French translations from those 4 pages are getting incorporated into the new
XMLs."). The old build exists only in the private dev repo's history (Formosan-Poinsot commit 30140ba, files
XML/Amis/Poinsot/amis_poinsot_{lexicon,examples}.xml), so this script ran once there and the result is committed;
the test reads the JSON and needs no git history.
"""
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

CODE = Path(__file__).resolve().parent
FRENCH_COMMIT = "30140ba"

records = []
for name in ("amis_poinsot_lexicon.xml", "amis_poinsot_examples.xml"):
    xml = subprocess.run(["git", "-C", str(CODE.parent), "show", f"{FRENCH_COMMIT}:XML/Amis/Poinsot/{name}"],
                         check=True, capture_output=True).stdout
    for s in ET.fromstring(xml).iter("S"):
        if int(s.get("id")[1:4]) <= 4:
            records.append({"id": s.get("id"), "form": s.find("FORM[@kindOf='original']").text or "",
                            "transl": [t.text or "" for t in s.findall("TRANSL")]})
out = {"_note": f"French pages 1-4 of the old French-volume build (Formosan-Poinsot {FRENCH_COMMIT}); "
                "written by snapshot_french_reference.py", "records": records}
(CODE / "data" / "french_reference_pages_1_4.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                                                              encoding="utf-8")
print(len(records), "records")
