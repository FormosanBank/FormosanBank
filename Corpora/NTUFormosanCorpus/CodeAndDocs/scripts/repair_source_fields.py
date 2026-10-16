#!/usr/bin/env python3
"""Repair reviewed NTU source-field extraction defects.

The three legacy parsers intentionally remain general-purpose.  This pass
handles the small set of source records that need record-level judgement:
mislabelled free-translation languages, repeated translation fields whose
second value is an alternative or annotation, explicit missing-translation
placeholders, and source annotations embedded in FORM text.

Every translation case pins a SHA-256 digest of the complete source ``free``
array.  Every FORM case pins the exact parser output.  A source or parser drift
therefore stops the build instead of applying a repair to a merely similar
record.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from xml.dom import minidom

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SOURCE_ROOT = HERE.parent
sys.path.insert(0, str(HERE))

from utils import (  # noqa: E402
    clean_punctuation,
    merge_notes,
    strip_speaker_labels_from_translation,
)

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")


@dataclass(frozen=True)
class Case:
    xml: str
    sentence_id: str
    source: str
    source_id: int | str
    free_digest: str
    mode: str = ""


@dataclass(frozen=True)
class FormRepair:
    xml: str
    sentence_id: str
    expected: str
    replacement: str
    note: str


@dataclass(frozen=True)
class SourceWordDeletion:
    xml: str
    sentence_id: str
    source: str
    source_id: int | str
    source_digest: str
    expected_forms: tuple[str, ...]
    remove_from_index: int
    note: str


@dataclass(frozen=True)
class MalformedTranslation:
    xml: str
    sentence_id: str
    source: str
    source_indices: tuple[int, ...]
    source_digest: str
    lang: str
    expected: str
    replacement: str | None


@dataclass(frozen=True)
class TranslSpec:
    lang: str
    text: str
    ver: str | None = None
    notes: str | None = None


SWAPS = (
    Case("Sentences/Kanakanavu/Kanakanavu.xml", "5_S_32", "sentence/Kanakanavu_Kanakanavu/5.json", 32, "bda0ddd82ffff0a31446b896d6631fabc103c3b5efdeee07f007d6fb018dd012"),
    Case("Sentences/Rukai/Rukai.xml", "20200530-FW-Lixing-1_S_13", "sentence/Rukai_Vedai/20200530-FW-Lixing-1.json", 13, "174b1267a60e90d31d0e955d20054b92ce4e566941d04526303349811dcd5580"),
    Case("Sentences/Rukai/Rukai.xml", "20200530-FW-Lixing-1_S_14", "sentence/Rukai_Vedai/20200530-FW-Lixing-1.json", 14, "174b1267a60e90d31d0e955d20054b92ce4e566941d04526303349811dcd5580"),
    Case("Sentences/Rukai/Rukai.xml", "20200530-FW-Lixing-1_S_18", "sentence/Rukai_Vedai/20200530-FW-Lixing-1.json", 18, "47ec2388505f610a2c49619ee79c0f19e1433cd1ab6337c010a7fcfedcbdcd22"),
    Case("Sentences/Rukai/Rukai.xml", "20200529-FW-Ryan_S_1", "sentence/Rukai_Vedai/20200529-FW-Ryan.json", 1, "5fba0b078cda8518b960994635f147d40d8372ca19eeebf8b582c458a8eaa555"),
    Case("Sentences/Rukai/Rukai.xml", "20200529-FW-Ryan_S_2", "sentence/Rukai_Vedai/20200529-FW-Ryan.json", 2, "a4de2e59899dc5dff22a8a3ffa8efbe255dc5c392c777213bb8c288bab6b00e3"),
    Case("Sentences/Rukai/Rukai.xml", "20200528-FW-Ryan_S_1", "sentence/Rukai_Vedai/20200528-FW-Ryan.json", 1, "dcf00c4290c8bc1f7f7d29adf9723f0673c60d382b9d3e728346073b3eee29ab"),
    Case("Sentences/Rukai/Rukai.xml", "20200528-FW-Ryan_S_2", "sentence/Rukai_Vedai/20200528-FW-Ryan.json", 2, "98b96b786c0b61b0e12aaab361aae0bce573225fd403e3b0dfdd1a1ce3ade898"),
    Case("Sentences/Rukai/Rukai.xml", "20200529-FW-Lixing-1_S_10", "sentence/Rukai_Vedai/20200529-FW-Lixing-1.json", 10, "b0753c74c0a3b054aba23ccb23c3b8e3a6b979423c311a533eeb2ee55bafa03a"),
    Case("Stories/Kanakanavu/Kanakanavu_kkvNr-puratu_Muu.xml", "kkvNr-puratu_Muu_S_21", "story/Kanakanavu_Kanakanavu/kkvNr-puratu_Muu.json", 21, "e6be69f73d1e482087d9d594c75c5c1c45de8156e26a8b21e25591840e6ac03e"),
    Case("Stories/Kanakanavu/Kanakanavu_kkvNr-puratu_Muu.xml", "kkvNr-puratu_Muu_S_139", "story/Kanakanavu_Kanakanavu/kkvNr-puratu_Muu.json", 139, "a61488fca867f968952169be96716200432ddfe55c8cad82fa916b696dc414d3"),
    Case("Stories/Kanakanavu/Kanakanavu_kkvNr_frog_Uva.xml", "kkvNr_frog_Uva_S_34", "story/Kanakanavu_Kanakanavu/kkvNr_frog_Uva.json", 34, "e5c8477515abecd2e9761956fdc92a6e1240a28473af32c20b6525e8000b1536"),
    Case("Stories/Rukai/Rukai_RukaiNr-frog_salrabu.xml", "RukaiNr-frog_salrabu_S_37", "story/Rukai_Vedai/RukaiNr-frog_salrabu.json", 37, "8dfb3c2c8ae7eda99ca3303ed94c2c184cf8ff1b922a2e088d1b59b5d7c77fcb"),
    Case("Stories/Sakizaya/Sakizaya_skzyNr-tribalhistory_sinay.xml", "skzyNr-tribalhistory_sinay_S_196", "story/Sakizaya_Sakizaya/skzyNr-tribalhistory_sinay.json", 196, "d3f77a259c1729bfde2cbf0e2458e5be9242668dac714280555f3585bac47e70"),
    Case("Stories/Tsou/Tsou_TsouConv-typhoon.xml", "TsouConv-typhoon_S_116", "story/Tsou_Tsou/TsouConv-typhoon.json", 116, "d19dc29bdd64e28eb1eb4ad25f6ff6ef3098aeafe5f6c8b535e87ef6de5b71f0"),
)


DUPLICATES = (
    Case("Sentences/Bunun/Bunun.xml", "01-3_S_2", "sentence/Bunun_Isbukun/01-3.json", 2, "fad107a6cc21140b04e58cb7609ba741ebfacc52f9a8d916f0341771a38b6fdd", "zho_alt"),
    Case("Sentences/Bunun/Bunun.xml", "11_S_7", "sentence/Bunun_Isbukun/11.json", 7, "d61212e5bc14d2c8d98e2b28eb85b58308addca69bdadbd97869806eaa916917", "eng_alt"),
    Case("Stories/Amis/Amis_Amis_Nr-frog_ofad.xml", "Amis_Nr-frog_ofad_S_7", "story/Amis_Ciwkangan/Amis_Nr-frog_ofad.json", 7, "7d143eb2f68c81949a1f90de716915c0ba5096abbb2bbf67c88eec211dd06228", "zho_annotation"),
    Case("Stories/Atayal/Atayal_AtaNr-weaving_Kagaw.xml", "AtaNr-weaving_Kagaw_S_14", "story/Atayal_Mayrinax/AtaNr-weaving_Kagaw.json", 14, "5418c1dbc20e5525067629ea72bd69dd81c54850aed7f526a0652f67e9dee583", "eng_concat"),
    Case("Stories/Atayal/Atayal_AtaNr-weaving_Kagaw.xml", "AtaNr-weaving_Kagaw_S_23", "story/Atayal_Mayrinax/AtaNr-weaving_Kagaw.json", 23, "7c99d319953f1dc6ad000b52ea32b5abe5cb800cbc90bb1f5a3d0784a624b943", "eng_concat"),
    Case("Stories/Atayal/Atayal_AtaNr-weaving_Kagaw.xml", "AtaNr-weaving_Kagaw_S_42", "story/Atayal_Mayrinax/AtaNr-weaving_Kagaw.json", 42, "47073a5a2fb6a85992b54550e2634275cc67b84b6177a9930c573e8b39c1ab7f", "eng_concat"),
    Case("Stories/Atayal/Atayal_AtaNr-weaving_Kagaw.xml", "AtaNr-weaving_Kagaw_S_64", "story/Atayal_Mayrinax/AtaNr-weaving_Kagaw.json", 64, "ddef4eda7163de50c43080a63bc74900c7e8267afde7b6995b04e32bcd2b0263", "eng_alt"),
    Case("Stories/Atayal/Atayal_AtaNr-weaving_Kagaw.xml", "AtaNr-weaving_Kagaw_S_77", "story/Atayal_Mayrinax/AtaNr-weaving_Kagaw.json", 77, "441fcda6fb9aef54db47290bc0f319610fe27ce6c5e5f11d918a606978f19508", "eng_concat"),
    Case("Stories/Atayal/Atayal_AtaNr-weaving_Kagaw.xml", "AtaNr-weaving_Kagaw_S_78", "story/Atayal_Mayrinax/AtaNr-weaving_Kagaw.json", 78, "cc08e0a8d208195a49cbfcf76c74fb29eaf28ce29c5eeda48935be7b48a302b6", "eng_concat"),
    Case("Stories/Atayal/Atayal_AtaNr-weaving_Kagaw.xml", "AtaNr-weaving_Kagaw_S_79", "story/Atayal_Mayrinax/AtaNr-weaving_Kagaw.json", 79, "da3caec2050154e533ebfffcee24d09a90143005c5adc8af5d83f0933e39cc1a", "eng_concat"),
    Case("Stories/Atayal/Atayal_AtaNr-weaving_Kagaw.xml", "AtaNr-weaving_Kagaw_S_80", "story/Atayal_Mayrinax/AtaNr-weaving_Kagaw.json", 80, "aef2e9d322d3620c03c4432a72b2d14de14b151099d5521cdb488b7b5eb6117b", "eng_concat"),
    Case("Stories/Atayal/Atayal_AtaNr-weaving_Kagaw.xml", "AtaNr-weaving_Kagaw_S_96", "story/Atayal_Mayrinax/AtaNr-weaving_Kagaw.json", 96, "26caa400472badce0717a62558934cf0db1aab47f29941282a304a6f3d26415d", "eng_concat"),
    Case("Stories/Bunun/Bunun_bnNr-frog_Laniahu.xml", "bnNr-frog_Laniahu_S_21", "story/Bunun_Isbukun/bnNr-frog_Laniahu.json", 21, "2ca5d55195200469518b7bf7e52cc9fc2a4de22fefc737ab166d4f101ef62a69", "zho_annotation"),
    Case("Stories/Kavalan/Kavalan_KavCon-weaving_abas_ipay3.xml", "KavCon-weaving_abas_ipay3_S_53", "story/Kavalan_Xinshe/KavCon-weaving_abas_ipay3.json", 53, "a3492d753fe8a51ab8a5aee8b73e79712c0558fa841c42a2e21be2f516ab9209", "eng_annotation"),
    Case("Stories/Rukai/Rukai_RukaiNr-frog_Tuku.xml", "RukaiNr-frog_Tuku_S_63", "story/Rukai_Vedai/RukaiNr-frog_Tuku.json", 63, "aa2cb81875edd47b5776ae41eadd881449e140933b297dee1f48cd671ccd52ef", "two_c_languages"),
    Case("Stories/Sakizaya/Sakizaya_skzyNr-frog_sinay.xml", "skzyNr-frog_sinay_S_16", "story/Sakizaya_Sakizaya/skzyNr-frog_sinay.json", 16, "40a7377898d5de3f76e87c1122f07b3f71480a9d8a173ba9c074172a60687242", "zho_annotation"),
    Case("Stories/Sakizaya/Sakizaya_skzyNr-frog_sinay.xml", "skzyNr-frog_sinay_S_23", "story/Sakizaya_Sakizaya/skzyNr-frog_sinay.json", 23, "7284893c098fd9f4cfa66e8901226a14a799fb1c5b6cbac161534d34fe3b05fe", "zho_annotation"),
    Case("Stories/Sakizaya/Sakizaya_skzyNr-frog_sinay.xml", "skzyNr-frog_sinay_S_38", "story/Sakizaya_Sakizaya/skzyNr-frog_sinay.json", 38, "3ac51e1851f1631f315667d38b3b2a6ccdca6e32324da9e1b127e55ec1829f2b", "zho_annotation"),
    Case("Stories/Seediq/Seediq_sdqCon-dialog2_ciwas_tiwas 2021s.xml", "sdqCon-dialog2_ciwas_tiwas 2021s_S_128", "story/Seediq_Tgdaya/sdqCon-dialog2_ciwas_tiwas 2021s.json", 128, "845bc7be1b9b745ef80392f6586e6531bb47388dde37d0571a967c8d548988b0", "bilingual_alt"),
    Case("Stories/Rukai/Rukai_RukaiNr-childhood_balenge.xml", "RukaiNr-childhood_balenge_S_8", "story/Rukai_Vedai/RukaiNr-childhood_balenge.json", 8, "56999a5e2e89340c5abc0582736aa45314455f1dd354d30261e72d404aa474c2", "mislabelled_zho_annotation"),
)


MISSING_MARKERS = (
    Case("Stories/Kavalan/Kavalan_KacCon-Teaching Weaving_abas_ipay.xml", "KacCon-Teaching Weaving_abas_ipay_S_9", "story/Kavalan_Xinshe/KacCon-Teaching Weaving_abas_ipay.json", 9, "e663647de3a5bc713cb1c281351ce52d5597e59aa40e42149fca743c98b4a0b7"),
    Case("Stories/Kavalan/Kavalan_KacCon-Teaching Weaving_abas_ipay.xml", "KacCon-Teaching Weaving_abas_ipay_S_44", "story/Kavalan_Xinshe/KacCon-Teaching Weaving_abas_ipay.json", 44, "199f157dfb063b4ed709c3d2fca29c1fc68556373530b4b635b1afc167ac9a7b"),
    Case("Stories/Kavalan/Kavalan_KavCon-marriage_abas_pilaw.xml", "KavCon-marriage_abas_pilaw_S_44", "story/Kavalan_Xinshe/KavCon-marriage_abas_pilaw.json", 44, "273785e05507f0cb0e1056b2b602e03ee0d7f1e6ccc7546703a2730a7a4486bf"),
    Case("Stories/Kavalan/Kavalan_KavCon-marriage_abas_pilaw.xml", "KavCon-marriage_abas_pilaw_S_62", "story/Kavalan_Xinshe/KavCon-marriage_abas_pilaw.json", 62, "b713c8b52c1177d5e7c91380fe44c72aa958d87622e0f549a2ece10fa690e3b5"),
    Case("Stories/Kavalan/Kavalan_KavCon-marriage_abas_pilaw.xml", "KavCon-marriage_abas_pilaw_S_94", "story/Kavalan_Xinshe/KavCon-marriage_abas_pilaw.json", 94, "7a11e3634754176172445751c1e9d2c5fde8cde4b5d3b203340cc8a0c7ec8ffe"),
    Case("Stories/Kavalan/Kavalan_KavCon-marriage_abas_pilaw.xml", "KavCon-marriage_abas_pilaw_S_111", "story/Kavalan_Xinshe/KavCon-marriage_abas_pilaw.json", 111, "96af1fe8eb5e16761aac7eae3b594db66b575d43f0a2c3000ba186e6b27c4eaf"),
    Case("Stories/Kavalan/Kavalan_KavCon-marriage_abas_pilaw.xml", "KavCon-marriage_abas_pilaw_S_169", "story/Kavalan_Xinshe/KavCon-marriage_abas_pilaw.json", 169, "74b93e52360bff1e89d7600c0b5d7f77bc1410fe58f34aef98af120df1337dff"),
)


PLACEHOLDERS = (
    Case("Stories/Amis/Amis_Amis_Nr-pear_lungi.xml", "Amis_Nr-pear_lungi_S_10", "story/Amis_Ciwkangan/Amis_Nr-pear_lungi.json", 10, "bc697b917e836b4f9c1b7679356626dc82bf9a6bc0da79edd02c94e30f6c6d73"),
    Case("Stories/Amis/Amis_Amis_Nr-pear_lungi.xml", "Amis_Nr-pear_lungi_S_23", "story/Amis_Ciwkangan/Amis_Nr-pear_lungi.json", 23, "bc697b917e836b4f9c1b7679356626dc82bf9a6bc0da79edd02c94e30f6c6d73"),
    Case("Stories/Kanakanavu/Kanakanavu_kkvNr-fishing_Muu.xml", "kkvNr-fishing_Muu_S_13", "story/Kanakanavu_Kanakanavu/kkvNr-fishing_Muu.json", 13, "f56ad37df5b24233e6de4d6ffaa0da5d98237d1687d79a817e9ba4519c20b336"),
    Case("Stories/Kanakanavu/Kanakanavu_kkvNr-puratu_Muu.xml", "kkvNr-puratu_Muu_S_78", "story/Kanakanavu_Kanakanavu/kkvNr-puratu_Muu.json", 78, "9ca05403ada0b107502a2fa5e446c2d2b3b570f35414ee258fa25b2a4a02002d"),
    Case("Stories/Kanakanavu/Kanakanavu_kkvNr_domestic_troubles_Muu.xml", "kkvNr_domestic_troubles_Muu_S_7", "story/Kanakanavu_Kanakanavu/kkvNr_domestic_troubles_Muu.json", 7, "64ee0d3e0361a457315b5a19c7b13a75c1fa7770c86838e7a90c1388fab8f748"),
    Case("Stories/Kanakanavu/Kanakanavu_kkvNr_domestic_troubles_Muu.xml", "kkvNr_domestic_troubles_Muu_S_51", "story/Kanakanavu_Kanakanavu/kkvNr_domestic_troubles_Muu.json", 51, "1b50e3279732c99c285cefb895973814eb1a5cd942757f00204c69ed0c61c660"),
    Case("Stories/Kanakanavu/Kanakanavu_kkvNr_life_Kuatu.xml", "kkvNr_life_Kuatu_S_18", "story/Kanakanavu_Kanakanavu/kkvNr_life_Kuatu.json", 18, "51f895d16be4e6a2262a3a307db249ea5bdd5350c09cab36f2cf62349a67c755"),
    Case("Stories/Kavalan/Kavalan_KacCon-Teaching Weaving_abas_ipay.xml", "KacCon-Teaching Weaving_abas_ipay_S_34", "story/Kavalan_Xinshe/KacCon-Teaching Weaving_abas_ipay.json", 34, "77170cda82af2cc0549c84a55316035886e096d4324d947665a47f5ca94e4fb4"),
    Case("Stories/Saisiyat/Saisiyat_SaiNr-holiday_kalaeh a _oemaw.xml", "SaiNr-holiday_kalaeh a _oemaw_S_107", "story/Saisiyat_Tong-he/SaiNr-holiday_kalaeh a _oemaw.json", 107, "c37e5375d609de047f5046a0efbf31d5a7774c6b5d506ff241204884cf209ca4"),
    Case("Stories/Seediq/Seediq_sdqCon-dialog3_robo_bakan 2021s.xml", "sdqCon-dialog3_robo_bakan 2021s_S_27", "story/Seediq_Tgdaya/sdqCon-dialog3_robo_bakan 2021s.json", 27, "7ad912ee7e3319958eed015f38e443cccfa0691a182c197fb11d6d8b058c5295"),
    Case("Stories/Seediq/Seediq_sdqCon-dialog4_robo_bakan_ape 2020s.xml", "sdqCon-dialog4_robo_bakan_ape 2020s_S_52", "story/Seediq_Tgdaya/sdqCon-dialog4_robo_bakan_ape 2020s.json", 52, "ce3ad1f569573272b1c47c9b6e3955abb255a84ac3e53e4306a428b7c2976486"),
    Case("Stories/Saisiyat/Saisiyat_SaiNr-election_lahi_ a taro_ babay.xml", "SaiNr-election_lahi_ a taro_ babay_S_48", "story/Saisiyat_Tong-he/SaiNr-election_lahi_ a taro_ babay.json", 48, "d4bd0d1635c50eebd53c5a21185396af5f521eb9837a9e6847f2543bf8c62f54"),
)


GLOSS_LABEL_TRANSLATIONS = (
    Case("Stories/Saisiyat/Saisiyat_SaiNr-pear3_kalaeh a taro_.xml", "SaiNr-pear3_kalaeh a taro__S_21", "story/Saisiyat_Tong-he/SaiNr-pear3_kalaeh a taro_.json", 21, "595eb25d2af26f0e24864ed41726101d811274b43edd7d2fcc07415918d8aa3b", "DM"),
)


from source_repair_registry import (
    load_compact_translation_alternatives,
    load_malformed_translations,
)


MALFORMED_TRANSLATIONS = tuple(
    MalformedTranslation(**case) for case in load_malformed_translations()
)

COMPACT_TRANSLATION_ALTERNATIVES = (
    load_compact_translation_alternatives()
)

COMPLETE_TRANSLATION_SEPARATOR = re.compile(
    r"(?<=[.!?。！？])\s*/\s*|\s+/\s+"
)


FORM_REPAIRS = (
    FormRepair("Sentences/Kanakanavu/Kanakanavu.xml", "3_S_458", "Temusu sekarapeen tanuku mima pai'ici?(少用).", "Temusu sekarapeen tanuku mima pai'ici?", "source FORM annotation removed: 少用 (rarely used)"),
    FormRepair("Sentences/Kanakanavu/Kanakanavu.xml", "3_S_459", "temusu 'urupenin tanuku mima pai'ici (較好).", "temusu 'urupenin tanuku mima pai'ici.", "source FORM annotation removed: 較好 (preferred form)"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_141", "kasa(日語)", "kasa", "source FORM: kasa（日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_178", "kunga'a (借詞)", "kunga'a", "source FORM: kunga'a （借詞）; 借詞 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_182", "kuruma (日語)", "kuruma", "source FORM: kuruma （日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_482", "minmana(已發生)", "minmana", "source FORM: minmana（已發生）; 已發生 is an aspect annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_511", "pangka(日語)", "pangka", "source FORM: pangka（日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_595", "'aviki(日語)", "'aviki", "source FORM: ’aviki（日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_597", "seto(日語)", "seto", "source FORM: seto（日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_601", "hasami(日語)", "hasami", "source FORM: hasami（日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_607", "siking (日語)", "siking", "source FORM: siking （日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_656", "puraku(日語)", "puraku", "source FORM: puraku（日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_665", "tangria(借詞)", "tangria", "source FORM: tangria（借詞）; 借詞 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_719", "tingami(日語)", "tingami", "source FORM: tingami（日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_730", "tomi(日語)", "tomi", "source FORM: tomi（日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_883", "'utori (日語)", "'utori", "source FORM: ’utori （日語）; 日語 is an etymological annotation"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "A2_S_891", "'ʉngaa(借詞)", "'ʉngaa", "source FORM: ’ʉngaa（借詞）; 借詞 is an etymological annotation"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "10_S_24", "問:tayza i taypey kisu haw?", "tayza i taypey kisu haw?", "source FORM prefix removed: 問："),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "10_S_28", "問:i luma' ci ina?", "i luma' ci ina?", "source FORM prefix removed: 問："),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "11_S_31", "問:cimanan kisu micaliw tu paysu?", "cimanan kisu micaliw tu paysu?", "source FORM prefix removed: 問："),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_1", "mapatay tu kya mikalatay ci Akian a wacu中心語.", "mapatay tu kya mikalatay ci Akian a wacu.", "source FORM annotation removed: 中心語"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_2", "u daecusay tu kya nikanan ni Aki a tali中心語.", "u daecusay tu kya nikanan ni Aki a tali.", "source FORM annotation removed: 中心語"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_3", "iniw tu kya mamiculu' tu tipus a tulaku中心語.", "iniw tu kya mamiculu' tu tipus a tulaku.", "source FORM annotation removed: 中心語"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_4", "makazih ci Sawmahan kya tatusaay ya mitiikay ci Mayawan a tatama a saydan中心語.", "makazih ci Sawmahan kya tatusaay ya mitiikay ci Mayawan a tatama a saydan.", "source FORM annotation removed: 中心語"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_5", "makazih ci Sawmahan kya mitiikay ci Mayawan a tatusaay a tatama a saydan中心語.", "makazih ci Sawmahan kya mitiikay ci Mayawan a tatusaay a tatama a saydan.", "source FORM annotation removed: 中心語"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_6", "iniw tu kya mialaay tu cudad aku a tademaw主事者.", "iniw tu kya mialaay tu cudad aku a tademaw.", "source FORM annotation removed: 主事者"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_7", "mazih aku kya matiikay ni Aki a wawa受事者.", "mazih aku kya matiikay ni Aki a wawa.", "source FORM annotation removed: 受事者"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_8", "matai'35 tu ku sapiletek ni Ofad tu kilang a pulung工具.", "matai' tu ku sapiletek ni Ofad tu kilang a pulung.", "source FORM annotations removed: footnote 35 and 工具"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_9", "midadum ci Panay i pinanuman ni Aki a tebun處所.", "midadum ci Panay i pinanuman ni Aki a tebun.", "source FORM annotation removed: 處所"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_10", "manaumh ci Aki ci Panayan中心語, ya i belaway.", "manaumh ci Aki ci Panayan, ya i belaway.", "source FORM annotation removed: 中心語"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "14_S_11", "u saba ni Aki中心語, ya nitiikan aku, manamuh ci Panayan.", "u saba ni Aki, ya nitiikan aku, manamuh ci Panayan.", "source FORM annotation removed: 中心語"),
    FormRepair("Grammar/Kanakanavu/Kanakanavu.xml", "11_S_2", "macangcangarʉ kara kasu↘?", "macangcangarʉ kara kasu?", "source FORM prosodic fall marker removed: ↘"),
    FormRepair("Grammar/Sakizaya/Sakizaya.xml", "09_S_24", "papicakayen ni Panay ci Kuli tu lami´.", "papicakayen ni Panay ci Kuli tu lami'.", "source FORM acute mark normalized to the apostrophe in the aligned source word"),
    FormRepair("Sentences/Rukai/Rukai.xml", "20200529-FW-Ludwig_S_15", "apiapakisaalraku musuane kay hungu 想要實現使役借第一人稱單數附著主格 第二人稱單數自由斜格.", "apiapakisaalraku musuane kay hungu.", "source gloss-only rows excluded from FORM: 想要-實現-使役-借=第一人稱單數.附著主格; 第二人稱單數.自由斜格"),
    FormRepair("Stories/Saisiyat/Saisiyat_SaiNr-kathethel_parain a _oemaw.xml", "SaiNr-kathethel_parain a _oemaw_S_66", "koSa'en e ka tatnon 日wa日 inoka ka SaiSiyat a ka ino inoka biwa' minkoringan mwai' toertoeroe' ma' isaza.", "koSa'en e ka tatnon wa inoka ka SaiSiyat a ka ino inoka biwa' minkoringan mwai' toertoeroe' ma' isaza.", "source code-switch wrapper <日wa日> removed; embedded Formosan wa retained"),
)


SOURCE_WORD_DELETIONS = (
    SourceWordDeletion(
        "Sentences/Rukai/Rukai.xml",
        "20200529-FW-Ludwig_S_15",
        "sentence/Rukai_Vedai/20200529-FW-Ludwig.json",
        15,
        "8b65a33e7bfce27a4eeee5bc6b0115da2d83aaf22cac1ec6cbef7b04f70b2d31",
        (
            "apiapakisaalraku",
            "musuane",
            "kay",
            "hungu.",
            "想要-實現-使役-借=第一人稱單數.附著主格",
            "第二人稱單數.自由斜格",
        ),
        4,
        "source gloss-only analysis rows omitted from W tiers",
    ),
)


PUNCTUATION_CASES = (
    Case("Stories/Rukai/Rukai_RukaiNr-princess balenge_balenge.xml", "RukaiNr-princess balenge_balenge_S_48", "story/Rukai_Vedai/RukaiNr-princess balenge_balenge.json", 48, "6559c8bbb99df4f68b7d04bacaacf63170179e4dea3c1e4af7aec55a68116266", "nested_quotes"),
    Case("Stories/Saisiyat/Saisiyat_SaiNr-election_lahi_ a taro_ babay.xml", "SaiNr-election_lahi_ a taro_ babay_S_3", "story/Saisiyat_Tong-he/SaiNr-election_lahi_ a taro_ babay.json", 3, "dd08e83632e9b4532be7c346dcb5827eed95e24192a308b3b9327273da06eb12", "editorial_equals"),
    Case("Stories/Bunun/Bunun_bnNr-frog_Adus.xml", "bnNr-frog_Adus_S_21", "story/Bunun_Isbukun/bnNr-frog_Adus.json", 21, "ba425c9ff089cbfaf25370475e93e76b42617d2e8e62905acd60a886927229b7", "translation_asides"),
    Case("Stories/Seediq/Seediq_sdqCon-dialog2_ciwas_tiwas 2021s.xml", "sdqCon-dialog2_ciwas_tiwas 2021s_S_24", "story/Seediq_Tgdaya/sdqCon-dialog2_ciwas_tiwas 2021s.json", 24, "a03e3f9ba6e3079a516e62b191c4b9d267aed3e0f59e37b9b087d99b0d18d239", "pause_before_numeral"),
)


def _digest(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _source_free(case: Case) -> list[str]:
    path = SOURCE_ROOT / case.source
    data = json.loads(path.read_text(encoding="utf-8"))["glosses"]
    if case.source.startswith("story/"):
        index = 0
        offset = 0
        while offset < len(data):
            rows = []
            while True:
                rows.append(data[offset])
                if rows[-1][1].get("s_end") or offset + 1 >= len(data):
                    break
                offset += 1
            if index == case.source_id:
                free = rows[-1][1].get("free", []) or []
                break
            index += 1
            offset += 1
        else:
            raise AssertionError(f"source story group not found: {case}")
    else:
        matches = [
            row for row in data if str(row[0]) == str(case.source_id)
        ]
        if len(matches) != 1:
            raise AssertionError(
                f"expected one source record for {case.source}:{case.source_id}; "
                f"found {len(matches)}"
            )
        free = matches[0][1].get("free", []) or []

    actual = _digest(free)
    if actual != case.free_digest:
        raise AssertionError(
            f"source free array drifted for {case.source}:{case.source_id}; "
            f"expected {case.free_digest}, found {actual}"
        )
    return list(free)


def _source_record(case: SourceWordDeletion) -> dict:
    path = SOURCE_ROOT / case.source
    data = json.loads(path.read_text(encoding="utf-8"))["glosses"]
    matches = [row for row in data if str(row[0]) == str(case.source_id)]
    if len(matches) != 1:
        raise AssertionError(
            f"expected one source record for {case.source}:{case.source_id}; "
            f"found {len(matches)}"
        )
    record = matches[0][1]
    actual = _digest(record)
    if actual != case.source_digest:
        raise AssertionError(
            f"source record drifted for {case.source}:{case.source_id}; "
            f"expected {case.source_digest}, found {actual}"
        )
    return record


def _source_rows(case: MalformedTranslation) -> list[object]:
    path = SOURCE_ROOT / case.source
    data = json.loads(path.read_text(encoding="utf-8"))["glosses"]
    try:
        rows = [data[index] for index in case.source_indices]
    except IndexError as exc:
        raise AssertionError(
            f"source row indices drifted for {case.source}:"
            f"{case.source_indices}"
        ) from exc
    actual = _digest(rows)
    if actual != case.source_digest:
        raise AssertionError(
            f"source rows drifted for {case.source}:{case.source_indices}; "
            f"expected {case.source_digest}, found {actual}"
        )
    return rows


def _normalized(raw: str, lang: str, *, ver: str | None = None,
                notes: str | None = None) -> TranslSpec:
    content = clean_punctuation(raw[2:])
    content = strip_speaker_labels_from_translation(content)
    return TranslSpec(lang, content, ver, notes)


def _joined(raws: list[str], lang: str) -> TranslSpec:
    fragments = [raw[2:].strip() for raw in raws]
    text = " ".join(fragments)
    text = re.sub(r"(?<=[.!?])(?=[A-Z])", " ", text)
    spec = _normalized(f"#e {text}", lang)
    evidence = "source translation fragments: " + " | ".join(fragments)
    return TranslSpec(spec.lang, spec.text, spec.ver,
                      merge_notes(spec.notes, evidence))


class Corpus:
    def __init__(self, xml_dir: Path):
        self.xml_dir = xml_dir
        self.trees: dict[str, ET.ElementTree] = {}
        self.modified: set[str] = set()

    def tree(self, relative: str) -> ET.ElementTree:
        if relative not in self.trees:
            path = self.xml_dir / relative
            if not path.is_file():
                raise AssertionError(f"expected XML file missing: {path}")
            self.trees[relative] = ET.parse(path)
        return self.trees[relative]

    def sentence(self, relative: str, sentence_id: str) -> ET.Element:
        matches = [
            s for s in self.tree(relative).getroot().findall("S")
            if s.get("id") == sentence_id
        ]
        if len(matches) != 1:
            raise AssertionError(
                f"expected one {sentence_id!r} in {relative}; "
                f"found {len(matches)}"
            )
        return matches[0]

    def mark(self, relative: str) -> None:
        self.modified.add(relative)

    def write(self) -> None:
        for relative in sorted(self.modified):
            root = self.trees[relative].getroot()
            _strip_whitespace(root)
            raw = ET.tostring(root, encoding="utf-8")
            rendered = minidom.parseString(raw).toprettyxml(indent="    ")
            (self.xml_dir / relative).write_text(rendered, encoding="utf-8")


def _strip_whitespace(element: ET.Element) -> None:
    if element.text and not element.text.strip():
        element.text = None
    if element.tail and not element.tail.strip():
        element.tail = None
    for child in element:
        _strip_whitespace(child)


def _translation_elements(sentence: ET.Element) -> list[ET.Element]:
    return list(sentence.findall("TRANSL"))


def _parser_text(raw: str, lang: str, xml_path: str) -> str:
    """Model the legacy parser's pre-repair S-level translation text."""
    if xml_path.startswith("Sentences/") and lang == "zho":
        content = raw[2:].replace("「這是真的中文翻譯」", "").strip()
        content = strip_speaker_labels_from_translation(content)
        return content
    return _normalized(raw, lang).text


def _assert_parser_translations(sentence: ET.Element, free: list[str],
                                case: Case) -> None:
    expected = {}
    for raw in free:
        if not isinstance(raw, str) or raw[:2] not in {"#e", "#c"}:
            continue
        lang = "en" if raw[:2] == "#e" else "zho"
        expected[lang] = _parser_text(raw, lang, case.xml)
    actual = {
        element.get(XML_LANG): (element.text or "")
        for element in _translation_elements(sentence)
    }
    if set(actual) != set(expected):
        raise AssertionError(
            f"parser translation languages drifted for {case.sentence_id}: "
            f"expected {sorted(expected)}, found {sorted(actual)}"
        )
    for lang, expected_text in expected.items():
        if actual[lang] != expected_text:
            raise AssertionError(
                f"parser translation drifted for {case.sentence_id} {lang}: "
                f"expected {expected_text!r}, found {actual[lang]!r}"
            )


def _replace_translations(sentence: ET.Element,
                          specs: list[TranslSpec]) -> None:
    for element in _translation_elements(sentence):
        sentence.remove(element)
    children = list(sentence)
    insertion = 0
    while insertion < len(children) and children[insertion].tag in {
        "FORM", "PHON"
    }:
        insertion += 1
    for offset, spec in enumerate(specs):
        element = ET.Element("TRANSL")
        element.set(XML_LANG, spec.lang)
        if spec.ver:
            element.set("ver", spec.ver)
        if spec.notes:
            element.set("notes", spec.notes)
        element.text = spec.text
        sentence.insert(insertion + offset, element)


def _add_form_note(sentence: ET.Element, note: str) -> None:
    form = sentence.find("FORM[@kindOf='original']")
    if form is None:
        raise AssertionError(f"original FORM missing in {sentence.get('id')}")
    form.set("notes", merge_notes(form.get("notes"), note))


def repair_swaps(corpus: Corpus) -> int:
    for case in SWAPS:
        free = _source_free(case)
        sentence = corpus.sentence(case.xml, case.sentence_id)
        _assert_parser_translations(sentence, free, case)
        eng = [raw for raw in free if raw[:2] == "#c"]
        zho = [raw for raw in free if raw[:2] == "#e"]
        if len(eng) != 1 or len(zho) != 1:
            raise AssertionError(f"swap shape drifted for {case.sentence_id}")
        _replace_translations(
            sentence,
            [_normalized(zho[0], "zho"), _normalized(eng[0], "en")],
        )
        corpus.mark(case.xml)
    return len(SWAPS)


def repair_duplicates(corpus: Corpus) -> int:
    for case in DUPLICATES:
        free = _source_free(case)
        sentence = corpus.sentence(case.xml, case.sentence_id)
        _assert_parser_translations(sentence, free, case)
        eng = [raw for raw in free if raw[:2] == "#e"]
        zho = [raw for raw in free if raw[:2] == "#c"]

        if case.mode == "zho_alt":
            specs = [_normalized(zho[0], "zho"), _normalized(eng[0], "en"),
                     _normalized(zho[1], "zho", ver="alt")]
        elif case.mode == "eng_alt":
            specs = [_normalized(zho[0], "zho"), _normalized(eng[0], "en"),
                     _normalized(eng[1], "en", ver="alt")]
        elif case.mode == "zho_annotation":
            specs = [_normalized(zho[0], "zho"), _normalized(eng[0], "en")]
            _add_form_note(sentence, f"source annotation: {zho[1][2:].strip()}")
        elif case.mode == "eng_annotation":
            specs = [_normalized(zho[0], "zho"), _normalized(eng[0], "en")]
            _add_form_note(sentence, f"source annotation: {eng[1][2:].strip()}")
        elif case.mode == "eng_concat":
            specs = [_normalized(zho[0], "zho"), _joined(eng, "en")]
        elif case.mode == "two_c_languages":
            specs = [_normalized(zho[1], "zho"), _normalized(zho[0], "en")]
        elif case.mode == "bilingual_alt":
            specs = [_normalized(zho[0], "zho"), _normalized(eng[0], "en"),
                     _normalized(eng[1], "en", ver="alt"),
                     _normalized(zho[1], "zho", ver="alt")]
        elif case.mode == "mislabelled_zho_annotation":
            specs = [_normalized(eng[0], "zho")]
            _add_form_note(sentence, f"source annotation: {zho[0][2:].strip()}")
        else:
            raise AssertionError(f"unknown duplicate mode: {case.mode}")

        _replace_translations(sentence, specs)
        corpus.mark(case.xml)
    return len(DUPLICATES)


def repair_missing_markers(corpus: Corpus) -> int:
    marker = re.compile(r"\[translation missing\]|\[翻譯漏失\]", re.I)
    for case in MISSING_MARKERS:
        free = _source_free(case)
        sentence = corpus.sentence(case.xml, case.sentence_id)
        _assert_parser_translations(sentence, free, case)
        specs = []
        for lang, prefix in (("zho", "#c"), ("en", "#e")):
            raw_values = [raw for raw in free if raw[:2] == prefix]
            if len(raw_values) != 1:
                raise AssertionError(
                    f"missing-marker shape drifted for {case.sentence_id} {lang}"
                )
            raw = raw_values[0]
            content = strip_speaker_labels_from_translation(raw[2:])
            content, count = marker.subn(" ", content)
            if count != 1:
                raise AssertionError(
                    f"expected one missing marker for {case.sentence_id} {lang}; "
                    f"found {count}"
                )
            content = re.sub(r"(^|\s)--?(?=\s|$)", " ", content)
            content = re.sub(r"\s+", " ", content).strip()
            spec = _normalized(f"{prefix} {content}", lang,
                               notes=raw[2:].strip())
            specs.append(spec)
        _replace_translations(sentence, specs)
        corpus.mark(case.xml)
    return len(MISSING_MARKERS) * 2


def remove_placeholders(corpus: Corpus) -> int:
    placeholder = re.compile(
        r"^(?:[?!.…。@\-]+|aaa|\(目前缺漏\)|"
        r"\(It is missing presently\))$",
        re.I,
    )
    removed = 0
    for case in PLACEHOLDERS:
        free = _source_free(case)
        sentence = corpus.sentence(case.xml, case.sentence_id)
        _assert_parser_translations(sentence, free, case)
        by_lang = {
            element.get(XML_LANG): element
            for element in _translation_elements(sentence)
        }
        source_placeholders = []
        for raw in free:
            if raw[:2] not in {"#e", "#c"}:
                continue
            value = raw[2:].strip()
            if not placeholder.fullmatch(value):
                continue
            lang = "en" if raw[:2] == "#e" else "zho"
            element = by_lang.get(lang)
            if element is None:
                raise AssertionError(
                    f"placeholder translation missing for {case.sentence_id} {lang}"
                )
            sentence.remove(element)
            source_placeholders.append(f"{lang}={value}")
            removed += 1
        if not source_placeholders:
            raise AssertionError(f"no placeholder found for {case.sentence_id}")
        _add_form_note(
            sentence,
            "source translation placeholder omitted: "
            + "; ".join(source_placeholders),
        )
        corpus.mark(case.xml)
    return removed


def remove_gloss_label_translations(corpus: Corpus) -> int:
    for case in GLOSS_LABEL_TRANSLATIONS:
        free = _source_free(case)
        sentence = corpus.sentence(case.xml, case.sentence_id)
        _assert_parser_translations(sentence, free, case)
        expected = [f"#e {case.mode}", f"#c {case.mode}"]
        if free != expected:
            raise AssertionError(
                f"gloss-label translation shape drifted for {case.sentence_id}: "
                f"expected {expected!r}, found {free!r}"
            )
        _replace_translations(sentence, [])
        _add_form_note(
            sentence,
            "source free-translation fields omitted as gloss labels: "
            + "; ".join(free),
        )
        corpus.mark(case.xml)
    return len(GLOSS_LABEL_TRANSLATIONS)


def repair_malformed_translations(corpus: Corpus) -> int:
    for case in MALFORMED_TRANSLATIONS:
        _source_rows(case)
        sentence = corpus.sentence(case.xml, case.sentence_id)
        matches = [
            element for element in _translation_elements(sentence)
            if element.get(XML_LANG) == case.lang
        ]
        if len(matches) != 1:
            raise AssertionError(
                f"expected one {case.lang} translation for "
                f"{case.xml}:{case.sentence_id}; found {len(matches)}"
            )
        element = matches[0]
        if element.text != case.expected:
            raise AssertionError(
                f"parser translation drifted for {case.xml}:"
                f"{case.sentence_id} {case.lang}; expected "
                f"{case.expected!r}, found {element.text!r}"
            )

        evidence = "source malformed translation: " + case.expected
        if case.replacement is None:
            sentence.remove(element)
            _add_form_note(sentence, evidence + "; translation omitted")
        else:
            element.text = case.replacement
            element.set("notes", merge_notes(element.get("notes"), evidence))
        corpus.mark(case.xml)
    return len(MALFORMED_TRANSLATIONS)


def _translation_readings(relative: str, sentence_id: str, lang: str,
                          text: str) -> list[str] | None:
    key = (relative, sentence_id, lang)
    compact = COMPACT_TRANSLATION_ALTERNATIVES.get(key)
    if compact is not None:
        if text != compact:
            raise AssertionError(
                f"compact translation alternatives drifted for "
                f"{relative}:{sentence_id} {lang}; expected {compact!r}, "
                f"found {text!r}"
            )
        return [part.strip() for part in text.split("/")]

    parts = COMPLETE_TRANSLATION_SEPARATOR.split(text)
    if len(parts) == 1:
        return None
    if any(not part.strip() for part in parts):
        raise AssertionError(
            f"empty complete translation reading in {relative}:"
            f"{sentence_id} {lang}: {text!r}"
        )
    return [part.strip() for part in parts]


def split_complete_translation_alternatives(
    corpus: Corpus,
) -> tuple[int, int, int]:
    expanded = 0
    alternates = 0
    unacceptable = 0
    seen_compact: set[tuple[str, str, str]] = set()

    for path in sorted(corpus.xml_dir.rglob("*.xml")):
        relative = str(path.relative_to(corpus.xml_dir))
        tree = corpus.tree(relative)
        for sentence in tree.getroot().findall("S"):
            sentence_id = sentence.get("id") or ""
            for element in list(_translation_elements(sentence)):
                lang = element.get(XML_LANG) or ""
                text = element.text or ""
                key = (relative, sentence_id, lang)
                if key in COMPACT_TRANSLATION_ALTERNATIVES:
                    seen_compact.add(key)
                readings = _translation_readings(
                    relative, sentence_id, lang, text
                )
                if readings is None:
                    continue

                accepted = [
                    reading for reading in readings
                    if not reading.lstrip().startswith("*")
                ]
                rejected = [
                    reading for reading in readings
                    if reading.lstrip().startswith("*")
                ]
                if not accepted:
                    raise AssertionError(
                        f"all complete translation readings are unacceptable "
                        f"in {relative}:{sentence_id} {lang}"
                    )

                source_note = "source translation alternatives: " + text
                rejected_note = None
                if rejected:
                    rejected_note = (
                        "source unacceptable translation readings omitted: "
                        + " | ".join(rejected)
                    )
                element.text = accepted[0]
                element.attrib.pop("ver", None)
                element.set(
                    "notes",
                    merge_notes(
                        element.get("notes"), source_note, rejected_note
                    ),
                )
                insertion = list(sentence).index(element) + 1
                for offset, reading in enumerate(accepted[1:]):
                    alternative = ET.Element("TRANSL")
                    alternative.set(XML_LANG, lang)
                    alternative.set("ver", "alt")
                    alternative.set("notes", source_note)
                    alternative.text = reading
                    sentence.insert(insertion + offset, alternative)

                expanded += 1
                alternates += len(accepted) - 1
                unacceptable += len(rejected)
                corpus.mark(relative)

    missing = set(COMPACT_TRANSLATION_ALTERNATIVES) - seen_compact
    if missing:
        rendered = ", ".join(
            f"{relative}:{sentence_id} {lang}"
            for relative, sentence_id, lang in sorted(missing)
        )
        raise AssertionError(
            "compact translation alternative cases missing: " + rendered
        )
    return expanded, alternates, unacceptable


def repair_forms(corpus: Corpus) -> int:
    for repair in FORM_REPAIRS:
        sentence = corpus.sentence(repair.xml, repair.sentence_id)
        form = sentence.find("FORM[@kindOf='original']")
        if form is None:
            raise AssertionError(f"original FORM missing: {repair}")
        if form.text != repair.expected:
            raise AssertionError(
                f"parser FORM drifted for {repair.xml}:{repair.sentence_id}; "
                f"expected {repair.expected!r}, found {form.text!r}"
            )
        form.text = repair.replacement
        form.set("notes", merge_notes(form.get("notes"), repair.note))
        corpus.mark(repair.xml)
    return len(FORM_REPAIRS)


def remove_source_analysis_words(corpus: Corpus) -> int:
    removed = 0
    for case in SOURCE_WORD_DELETIONS:
        _source_record(case)
        sentence = corpus.sentence(case.xml, case.sentence_id)
        words = sentence.findall("W")
        actual_forms = tuple(
            (word.find("FORM[@kindOf='original']").text or "")
            for word in words
        )
        if actual_forms != case.expected_forms:
            raise AssertionError(
                f"parser W tiers drifted for {case.xml}:{case.sentence_id}; "
                f"expected {case.expected_forms!r}, found {actual_forms!r}"
            )
        if not 0 <= case.remove_from_index < len(words):
            raise AssertionError(f"invalid W removal index: {case}")
        for word in words[case.remove_from_index:]:
            sentence.remove(word)
            removed += 1
        _add_form_note(sentence, case.note)
        corpus.mark(case.xml)
    return removed


def repair_punctuation(corpus: Corpus) -> int:
    for case in PUNCTUATION_CASES:
        free = _source_free(case)
        sentence = corpus.sentence(case.xml, case.sentence_id)
        _assert_parser_translations(sentence, free, case)
        eng = next(raw for raw in free if raw[:2] == "#e")
        zho = next(raw for raw in free if raw[:2] == "#c")
        if case.mode == "nested_quotes":
            specs = [
                TranslSpec(
                    "zho",
                    "「對Balenge說『我要嫁給百步蛇』這件事我們該怎麼辦呢？」",
                    notes=zho[2:].strip(),
                ),
                TranslSpec(
                    "en",
                    "“What should we do that Balenge said ‘I will go to the hundred pacer?’”",
                    notes=eng[2:].strip(),
                ),
            ]
        elif case.mode == "editorial_equals":
            zho_spec = _normalized(zho.replace("=", "", 1), "zho",
                                   notes=zho[2:].strip())
            specs = [zho_spec, _normalized(eng, "en")]
        elif case.mode == "translation_asides":
            if eng != "#e Are there two of them? [boy and dog]" or zho != (
                "#c 是不是會有兩個？ [孩子跟狗]"
            ):
                raise AssertionError(
                    f"translation-aside shape drifted for {case.sentence_id}"
                )
            specs = [
                TranslSpec(
                    "zho",
                    "是不是會有兩個?",
                    notes=zho[2:].strip(),
                ),
                TranslSpec(
                    "en",
                    "Are there two of them?",
                    notes=eng[2:].strip(),
                ),
            ]
        elif case.mode == "pause_before_numeral":
            if eng != (
                "#e How was it possible? Eleven years old is too small to go hunting."
            ) or zho != "#c 你不可能會（打獵）..11（歲）太小了，":
                raise AssertionError(
                    f"pause-before-numeral shape drifted for {case.sentence_id}"
                )
            specs = [
                TranslSpec(
                    "zho",
                    "你不可能會 11 太小了,",
                    notes=zho[2:].strip(),
                ),
                _normalized(eng, "en"),
            ]
        else:
            raise AssertionError(f"unknown punctuation mode: {case.mode}")
        _replace_translations(sentence, specs)
        corpus.mark(case.xml)
    return len(PUNCTUATION_CASES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--xml_dir", type=Path,
        default=REPO / "CodeAndDocs" / "Final_XML",
    )
    args = parser.parse_args()
    corpus = Corpus(args.xml_dir.resolve())

    stats = {
        "language swaps": repair_swaps(corpus),
        "duplicate-field records": repair_duplicates(corpus),
        "missing markers removed": repair_missing_markers(corpus),
        "placeholder translations omitted": remove_placeholders(corpus),
        "gloss-label translation records omitted": remove_gloss_label_translations(corpus),
        "malformed translations repaired or omitted": repair_malformed_translations(corpus),
        "FORM annotation repairs": repair_forms(corpus),
        "source analysis-only W tiers omitted": remove_source_analysis_words(corpus),
        "punctuation/editorial repairs": repair_punctuation(corpus),
    }
    translation_stats = split_complete_translation_alternatives(corpus)
    stats.update({
        "complete translation fields expanded": translation_stats[0],
        "acceptable alternative translations emitted": translation_stats[1],
        "unacceptable translation readings omitted": translation_stats[2],
    })
    corpus.write()
    print("Source-field repairs passed")
    for label, count in stats.items():
        print(f"  {label}: {count}")
    print(f"  XML files rewritten: {len(corpus.modified)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
