#!/usr/bin/env python3
"""Protect source-proven corrections and remove the obsolete standard tier."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE = ROOT / "data" / "verses.jsonl"
REPLACEMENTS = {
    ("John/chapter5.xml", "verse28"): {"Ynn4": "Ynnâ", "ynn4": "ynnâ"},
    ("John/chapter6.xml", "verse20"): {"Ynn4": "Ynnâ", "ynn4": "ynnâ"},
    ("John/chapter6.xml", "verse27"): {"Ynn4": "Ynnâ", "ynn4": "ynnâ"},
    ("John/chapter7.xml", "verse3"): {
        "tæ'i3-papara": "tæ'iä-papara",
        "tæ'i3papara": "tæ'iäpapara",
    },
}
FULL_ORIGINAL_FORMS = {
    ("John/chapter5.xml", "verse42"): "Ra k'alang-en-nau-kamou, ka aoussi-[kamou] ymoumi-æn ki kavæangö-an ki Alid.",
    ("John/chapter7.xml", "verse39"): (
        ".. ( Ka pa-sousou-en tyn ta atta mattæi-mymmia ki Joep-pan ka "
        "â-balei-au nein ka tna-msing tyni-æn. Ka a'cu-siappa ta Joep-pan "
        "ka dilligh matiktik, alei ka assi-appa ni-pou-keirang-en ki kidi "
        "ta ti Jesus.)"
    ),
    ("John/chapter12.xml", "verse12"): (
        "Tou sasat ki wæ'i ka tou ææugh makoi-lalaulau ka maba-toung ka "
        "ierrou-'ato tou Ou-vava-toug-han, dou millingigh ka sah-ka kouan "
        "ti Jesus mou-Jerusalem,"
    ),
    ("John/chapter12.xml", "verse28"): (
        "Rama pou-vavau-ei ki kidi ta Nanang oho. Annata ni-ieroua ta yngau "
        "makka toun-noun ki vullum, [koun], Ni-pou-vavau-en-nau ki kidi ka "
        "mi-la-ah-koh pou-vavau ki kidi [ty-ni-æn."
    ),
    ("John/chapter12.xml", "verse29"): (
        "Annata makoilalaulau ka mi-touhko hynna millingigh [ki atta,] "
        "ni-k'ma, akoume-âto ki 'ltæh. Ni-k'ma ta rarouma, ka yngau-en ta "
        "teni ki Tama-Gnau."
    ),
    ("John/chapter12.xml", "verse33"): (
        "Ni-pasousou-en tyn ta atta ka pou-ki di-eih kapatei-an ka mama ki "
        "mang ka kapatei-eih tyn.)"
    ),
    ("Matthew/chapter16.xml", "verse9"): (
        "Assi-appa moumi oum-han, assi-moumi pæh-balei-en pæh-dim-dim ta "
        "ryrymma ki paoul, ki rym-ma katounnoun-nan [ka papæ-ræh] ka "
        "pyppynna ka læ'i-an ka ni-a-likough-noumi illud?"
    ),
    ("Matthew/chapter16.xml", "verse10"): (
        "Ta pyppytto-appa ki paoul, ki hpat katounnoun-nan [ki papæ-ræh], "
        "ka pyppynna ka læ'i-æn ta ni-a-likough-noumi illud?"
    ),
    ("Matthew/chapter22.xml", "verse2"): (
        "Mæmyhkaulaula ta Peifa-fou-an ki tounnoun ki vullum ki voual ka "
        "Si-bavau Mei-fafou, ka ni-papæhtatanang ki Alak tyn [ka paræh] ki "
        "vatouh-an ki pakakyt-tyl-an."
    ),
    ("Matthew/chapter23.xml", "verse14"): (
        "Ænnæi ymoumi ka Mako-sasoulat ki Fariséen appa, ka pa-ninien ki "
        "rÿh [ki sou:] Alei ka ka-nin-noumi ta tatalagh ki jnæjna ka "
        "ni-kapatei-æn ki tbung, tou hau-at-en ki hawei ki "
        "pako-dalliadalli-en makou Alilid. Alei ki anna pa-ki-valei-ei "
        "moumi ta siouro niak-dung ka ding-ding-en."
    ),
    ("Matthew/chapter24.xml", "verse2"): (
        "Ka ni-k'ma ta ti Jesus neini-æn, Assi-moumi kaua ararau-en "
        "tamamang katta? Missing koun-nau-kamou, Assi pæ-itoukoua-eih hia "
        "ta [sasasat ka] vahto pæ-itou-halap ki vahto [ka rouma,] ka assi "
        "taktak-auh."
    ),
    ("Matthew/chapter24.xml", "verse19"): (
        "Ennai ymoumi [ka jnæ-jna] ka mavoë ka pa-ouho tou wæ'i k'anna."
    ),
    ("Matthew/chapter26.xml", "verse71"): (
        "Jrou ka mou-mala ta teni tou tangagh, ni-kmytta-appa ty-ni-æn ta "
        "pani [ka jna ka pæiroung-in] ka k'ma neini-æn ka æ'ia-koua hynna, "
        "Teni-appa ta na lam ti Jesus ka tæ'i-Nazareth."
    ),
    ("Matthew/chapter27.xml", "verse53"): (
        "Ka rou ni-'tpæpænæh-hen nein makka-rbo ki ravaravak si-äugh ki "
        "ni-patimææ'-æn [pææh-pit] tyni-æn, ni-ierroua ta neni tou 'æuma "
        "ka ni-pa-itou-nni tou tatamd-den ki Alid, ka ni-moupæ-næh tou "
        "æmæh ki mabatoung [ki voual.]"
    ),
    ("Matthew/chapter27.xml", "verse64"): (
        "Padingi-au hnyn papææu-saoun kmading ta ravak tou kidi ki "
        "katatouro ki wæ'i, alei ka assi lava ierrou-'ah ta "
        "Pahtatæutæuug-han tyn dou euvanan haouzoung tyni-æn, ka "
        "mattæ'i-k'ma-ah-hynna ki ta'u, Ni-patimææ'-æn [pæ-æhpit] ki "
        "ni-kapateian: ka komma-hynna masaoun-al-ato mat'e ta taurahei-en "
        "ka siæugh ki ni-siouro-ato."
    ),
}


def main() -> None:
    rows = [json.loads(line) for line in INTERMEDIATE.read_text(encoding="utf-8").splitlines()]
    changed = 0
    for row in rows:
        replacements = REPLACEMENTS.get((row["path"], row["sentence_id"]), {})
        original_field = next(
            field
            for field in row["fields"]
            if field["tag"] == "FORM" and field["kindOf"] == "original"
        )
        before = original_field["text"]
        # The canonical input has completed rendered-scan review. Keep these
        # earlier full-form adjudications explicit so their focused regression
        # checks remain independent of the corpus-wide review manifest.
        explicit = FULL_ORIGINAL_FORMS.get((row["path"], row["sentence_id"]))
        if explicit is not None:
            original_field["text"] = explicit
        for old, new in replacements.items():
            original_field["text"] = original_field["text"].replace(old, new)
        changed += before != original_field["text"]

        before_count = len(row["fields"])
        row["fields"] = [
            field
            for field in row["fields"]
            if not (field["tag"] == "FORM" and field["kindOf"] == "standard")
        ]
        changed += before_count != len(row["fields"])

    with INTERMEDIATE.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(
        f"Applied {changed} source-tier updates; no standard FORM is emitted "
        "because current authority designates no Siraya standard."
    )


if __name__ == "__main__":
    main()
