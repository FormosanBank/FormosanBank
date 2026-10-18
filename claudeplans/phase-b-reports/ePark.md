# ePark regeneration: full diff vs `main` (Phase B, Group 2)

Sweep turn executed 2026-08-12 on `work/epark` (branched off `work/classifier`
at `59a4212ab`, so it carries the quote-classifier fixes that lifted the
Saisiyat process guard). ePark is the largest corpus in the bank: 436 XML
files, 285,346 sentences, 126,149 words, 409,078 `<AUDIO>` elements, 16
languages, 11 sub-corpora, 218 MB.

Every FORM/PHON/TRANSL/AUDIO of every S/W was matched by element id against the
`main` state and each difference classified by character-level edit operations.
**2,571,534 edit operations, 0 unclassified (100.0000%).**

## Run facts

- **Single entry point**: new `CodeAndDocs/make_xml.sh` (Phase 2 — the offline,
  reproducible rebuild of the derived tiers). ePark had no wrapper script
  before; the README's pipeline was ~40 loose commands including a corrupted
  one (see "README corrections").
- **Idempotent, and reproducible from `main`**: four full runs. Run 3 is
  **byte-identical** to run 2 across all 436 files (`diff -rq` → 0
  differences); run 2 differed from run 1 only by the intended V073 fix below.
  The committed state was then produced by a **from-scratch run**: `XML/` was
  restored to the pristine `main` state and `make_xml.sh` run once with the
  final scripts — output **byte-identical** to runs 2 and 3 (0 differences).
  So the committed XML is exactly what one command produces from `main`.
- **`quote_corrections.csv` records repo-relative paths.** `make_xml.sh` `cd`s
  to the repo root and addresses the corpus as `Corpora/ePark/XML`, because the
  path handed to `clean_xml.py` is what lands in the `file` column of this
  durable, committed log — an absolute build path there would differ between
  checkouts. Worth copying in other corpora's entry points.
- **POL-035: no snapshot.** ePark's *text* is regenerable from committed
  inputs: `CodeAndDocs/ePark_{1,2,3}/` hold the original source CSVs for all
  eleven sub-corpora (3,974 tracked files). Spot-checked by reading the source
  CSVs directly and comparing to the published original FORMs — e.g.
  `ePark_2/族語短文/03 海岸阿美語.csv` → `zu_yu_duan_wen/Amis/Coastal_Amis.xml`
  matches 163/163 rows once the documented cleaning rules (curly quotes,
  dashes, entities) are applied; `文化篇` and `生活會話篇` reproduce 98–99% by the
  same test, the remainder being other clean_xml rules. The pipeline is the
  baseline. (Phase 1's *audio* is not reproducible offline — see below — but
  quote correction touches only the sentence-level original FORM.)
- **Quote correction**: 8 `c031` + 1 `c032` across 4 sentences, all verified
  correct (see below). `CodeAndDocs/quote_corrections.csv` is committed. A
  second run appends nothing.
- **Sidecars (POL-033)**: reviewed then deleted by step 7 of `make_xml.sh` —
  `cleaner_warnings.csv` (16,823 rows: 14,800 `c030` apostrophe-ambiguity
  flags, 2,021 `c002` single-quote variants in Chinese TRANSL, 1 `c022`
  asterisk) and a **tracked** `XML/html_entities.log` (1,564 lines, a stale run
  log from the original build, still naming the pre-port `Final_XML/ep3_文化篇/`
  paths). The log is now deleted from the tree and from the pipeline's output —
  `XML/` holds XML only.
- **AUDIO untouched**: 409,078 `<AUDIO>` elements before and after, and the
  SHA-256 of every element's full attribute set in document order is identical
  (`ea73bd84…e6993`). No audio was downloaded at any point.

## Standing ruling: the second `clean_xml` pass is removed

ePark's README documented a second `clean_xml` after `standardize.py`, claimed
to strip `-` from the standard tier and normalize `’`→`'`. **Removed.** It is
not merely redundant — under the current `clean_xml` it is inert, and what it
historically did was wrong for this corpus:

- **A second pass is now a verified no-op.** Running `clean_xml` again over the
  finished corpus rewrote **0 of 436 files**, produced no transformations and no
  new quote corrections; the output is byte-identical.
- **Why**: today's `clean_xml` explicitly excludes `FORM[@kindOf="standard"]`
  ("standardize.py owns all cleaning of the standard tier (C012 et al.)"), so a
  post-standardize pass cannot touch the standard tier at all. The `’`→`'` job
  is covered by the *first* pass, which cleans the original tier that
  `standardize --copy` then duplicates.
- **What used to survive it, and now does not.** C012 (`standardize.py`'s
  `_apply_standard_hyphens`) only fires on morpheme-segmented sentences
  (`element.find(".//M") is not None`). **ePark has zero `<M>` elements**, so
  C012 correctly never applies. The old pass, by contrast, stripped hyphens
  unconditionally, and the strings it produced were malformed:
  `ceng-fo` (政府) → `cengfo`, `Yin-cu-min` (原住民) → `Yincumin`, `gak-ku` (學校)
  → `gakku`, `U-ke-lan` (烏克蘭) → `Ukelan`, `tala-Taypak` → `talaTaypak`,
  `Kacaw-Vutul` → `KacawVutul`, `ping-syang` → `pingsyang`.
- **Counts and shapes of what now remains in standard FORMs** (reported, not
  re-stripped, per the ruling): hyphens in standard S-FORMs go **9,016 →
  13,196** occurrences, in **5,482 → 7,425** sentences (V133 SOFT, same
  numbers). 2,243 distinct hyphenated tokens are newly present, 3,204
  occurrences. The shapes are: Chinese/Japanese loanword syllabification
  (`ceng-vu` ×41, `ceng-fo` ×29, `tin-se` ×22, `gak-ku` ×14, `Yin-cu-min` ×9),
  transliterated place names (`U-ke-lan`, `O-ke-lan`, `E-lo-se`), hyphenated
  personal names (`Kacaw-Vutul`, `Siyaw-kay`), and prefix boundaries
  (`tala-Taypak`, `si-tjing`). None are morpheme segmentation. Also restored: 6
  `=` characters in 2 sentences (`ni^ra=nira=niira=ningra`, a paradigm listing
  in Xiuguluan Amis) — V126 SOFT ×2, new.
- Since ePark has no `<M>` tier, C012 does **not** cover this corpus the way it
  covered Nowbucyang's segmented case; the correct outcome here is that nothing
  strips these hyphens, because they are orthography, not segmentation.

Invariant re-checked after the removal: in every `--copy` sub-corpus the
standard FORM is now **exactly** the original FORM — **0 mismatches** across all
285,346 sentences and 126,149 words. Differences between the tiers occur only in
the four blocks that use a conversion table.

## The four quote rewrites — every one, with a verdict

All four are direct speech. In all four the Chinese translation renders the same
material inside fullwidth double quotes `＂…＂`, which is decisive independent
evidence that the `'…'` pair is quotation and not the glottal letter.

**1. `hui_ben_ping_tai/Rukai/Wutai_Rukai.xml` S 50551 — CORRECT** (2 × c031)

> `kay Cangale si agiini ka ababay yacengecenge ka kadrua ku kaupungulini si kanekane ku akaneane. 'ama, ama, lrimuinusu la iya?'`
> → `… "ama, ama, lrimuinusu la iya?"`
> zho: `小凱正在和妹妹悠閒地吃點心。＂爸爸、爸爸，要去哪？＂`

Vocative direct speech ("father, father, where are you going?"). The **same
picture book in Amis** renders the identical line with ASCII double quotes
already: `hui_ben_ping_tai/Amis/Coastal_Amis.xml` has `… ci siyaw-kay ato kaka
fafahiyan. "mama, mama tatalacowa kiso?"`. Same book, same line, same
punctuation intent.

**2. `hui_ben_ping_tai/Rukai/Wutai_Rukai.xml` S 146942 — CORRECT** (1 × c031 +
1 × c032 stranded repair)

> `'aneanenumi? watumatumanenumi ikay kikay? ' kay sakaumanemane ka umaumase la kalisi si akuadrau giringi.`
> → `"aneanenumi? watumatumanenumi ikay kikay?" kay …`
> zho: `＂你們是誰？ 在這裡幹什麼？＂巨人生氣地大吼。`

Quoted speech closed by the quotative `kay` ("thus said"). The **next sentence
in the same file** (S 146943) already writes exactly this construction with
ASCII double quotes: `"kikay babengelradhaneli!" kay sakaumanemane ka umaumase
la iya kay: "kainaku paubangalre …"`. The `c032` repair removed the stray space
the source left before the closing mark (`kikay? '` → `kikay?"`), which is the
right normalization.

**3. `hui_ben_ping_tai/Bunun/Junqun_Bunun.xml` S 205909 — CORRECT** (2 × c031;
this was the one flagged *uncertain* going in)

> `kulung hai kusia sasaduan ahil cia tu ilav 'tupatu' maiskava matua mas ilav tan, …`
> → `… ilav "tupatu" maiskava …`
> zho: `kulung去圖書館的門口，說：＂快開門，讓我進去看書。＂`

Three independent lines of evidence resolve the uncertainty:
- The Chinese renders the quoted material as direct speech in `＂…＂` ("Open the
  door quickly, let me in to read"); `ilav` is "door" and `tupatu` the
  imperative.
- **`tupatu` occurs 160 times bare in ePark** (plus `anatupatu` ×40,
  `intupatu` ×14, `sintupatu` ×12); `'tupatu'` occurs exactly once. The
  apostrophes are not part of the word.
- Phonotactics: the old PHON rendered it `ʔtupatuʔ` — a glottal stop before a
  word-initial stop is not a possible Bunun word. Bunun's 8,880 apostrophes in
  ePark are overwhelmingly word-internal (`tas'a`, `mas'an`, `uvaz'az`); only 27
  tokens begin with one at all.

**Verdict: acceptable — I am not committing anything I judge wrong.**

**4. `wen_hua_pian/Amis/Hengchun_Amis.xml` S 266 — CORRECT** (2 × c031)

> `sacaciyaw sa cingra 'o cima kona mamalitemoh no mako hokiya?' sa a mi sacaciyaw, so'elin sa malitemoh ningra ko widang ningra."`
> → `sacaciyaw sa cingra "o cima kona mamalitemoh no mako hokiya?" sa a mi …`
> zho: `他會喃喃自語：＂我會遇到誰呢？＂還真的遇見了他的朋友。＂`

"He mutters *'who will I meet?'*", framed by `sacaciyaw sa cingra` ("he says")
and closed by the quotative `sa`. Note the sentence carries a stray unmatched
`"` at the very end in **both** the Formosan text and the Chinese; that
imbalance is in the source and is untouched here.

Residual, not acted on: 14,800 `c030` ambiguity flags were raised and left
alone, and 26 Bunun tokens besides `'tupatu'` begin with an unpaired apostrophe
(`'bunun`, `'maaz`, `'hala`, …). Those are a review worklist, not rewrites.

## Diff classification — 2,571,534 operations, 100% classified

| class | ops | share | where |
|---|---:|---:|---|
| PHON: variant notation `x~y` → `[x\|y]` | 1,824,634 | 70.96% | S orig 850,451 / S std 863,817 / W orig 48,595 / W std 61,771 |
| PHON: unmapped punctuation & marks dropped | 688,060 | 26.76% | S orig 343,091 / S std 343,332 / W 1,637 |
| PHON: IPA recode (profile change) | 53,504 | 2.08% | `ʦ`→`c` before front vowels (Paiwan), `ə`→`e` next to `q`/`ħ` (Truku), syllabic `m̩`→`m` |
| FORM: source hyphen restored to standard tier | 4,132 | 0.16% | S std — second-`clean_xml` removal |
| FORM: standard-tier accent strip / TSV letter map | 822 | 0.03% | S std 411 / W std 411 — all `jiu_jie_jiao_cai` Rukai (`nusipéléya`→`nusipeleya`) |
| FORM: dash look-alike → ASCII `-` | 94 | 0.00% | U+2014 ×21, U+2013 ×17, U+FF0D ×8, U+2015 ×1, mirrored in both tiers |
| structural: `<W>` removed (`cleanup_empty_words`) | 90 | 0.00% | punctuation-only `<W>` with no audio, all `jiu_jie_jiao_cai` |
| structural: empty `W/PHON` removed | 174 | 0.00% | 87 W × 2 tiers — the V073 fix below |
| FORM: POL-018 quote correction `'`→`"` | 16 | 0.00% | 8 original + 8 mirrored standard |
| FORM: source `=` restored to standard tier | 6 | 0.00% | S std — second-`clean_xml` removal |
| FORM: whitespace normalization | 2 | 0.00% | one space before a comma, both tiers |

Structure: **S unchanged at 285,346**; W 126,239 → **126,149** (−90); files 436 →
436; **no TEXT attribute changed anywhere**; no `<S>` added or removed.

## V073 regression, found and fixed in committed code

Run 1 introduced **174 HARD `V073 phon_non_empty`** findings in 16 files
(`validate_xml` had been clean on `main`). Cause: 87 `<W>` in `jiu_jie_jiao_cai`
have a bare punctuation mark as their FORM (`,` ×57, `!` ×13, `.` ×12, `"` ×5)
because the source CSVs list punctuation as its own word row. Punctuation is not
sound, so `add_phonology` gave each an **empty** PHON on both tiers.
`cleanup_empty_words.py` spares these `<W>` because they carry an audio file.

Fixed by extending `drop_unmapped_phon.py` (POL-038 — committed code, no hand
edits) from "drop original-tier all-`*` placeholder PHON" to "drop PHON with no
phonemic content", which now also covers empty PHON on either tier. Its
docstring and the README document both cases. `validate_xml` is back to clean.
The general fix belongs upstream — `add_phonology` should not emit an empty PHON
element at all — and is left as a repo-wide follow-up.

## Validators, before → after

| check | `main` | this branch | delta |
|---|---|---|---|
| `validate_xml` | clean | clean | — (V073 ×174 appeared mid-run, fixed) |
| `validate_text` HARD | 931 (V121 928, V129 2, V131 1) | 931 (identical) | — |
| `validate_text` SOFT | 265,667 | 61,553 | **−204,114** |
| ├ V147 phon_legacy_tilde_variant | 205,994 | **0** | −205,994 |
| ├ V146 phon_variant_group_malformed | 2 | **0** | −2 |
| ├ V133 dash_in_S_standard_FORM | 5,482 | 7,425 | +1,943 (hyphens restored — expected) |
| ├ V126 equal_sign_in_S_standard | 0 | 2 | +2 (same cause) |
| ├ V116 non_ascii_in_form | 1,304 | 1,257 | −47 (dash canonicalization) |
| ├ V137 trailing_decimal_footnote | 181 | 165 | −16 |
| └ V111 / V136 / V141 / V142 | 8 / 22 / 2 / 4 | unchanged | — |
| `validate_glosses` | SOFT 269,456 (V060 269,281, V061 175) | SOFT 269,430 (V060 269,255, V061 175) | −26 (the 90 removed `<W>`) |
| duplicate QC | **HARD** 2,513 within + 29,595 cross, 100,137 occ. | **SOFT** 2,514 within + 29,587 cross, 100,082 occ. | severity flip; −55 occurrences |
| token count | 1,782,446 | 1,782,446 | **0** |

**HARD reduction**: `validate_text` HARD is unchanged at 931, but the 100,137
duplicate occurrences flip from HARD to SOFT (see below), and the 174 V073 that
the rerun would otherwise have introduced were eliminated. The rule changes the
brief anticipated (V144 per sentence, V062/V064 → SOFT) move nothing here:
ePark has **no `<M>` tier at all**, so V144/V145 never fire, and
`validate_glosses` produces no HARD findings on this corpus in either state.

## Token delta

**Zero, in every language and every dialect.** Total 1,782,446 → 1,782,446.
Amis 204,855, Atayal 244,555, Bunun 171,371, Kanakanavu 49,011, Kavalan 55,429,
Paiwan 167,980, Puyuma 176,974, Rukai 195,041, Saaroa 42,787, Saisiyat 50,629,
Sakizaya 53,657, Seediq 138,523, Thao 55,072, Truku 56,323, Tsou 56,555,
Yami 63,684 — all unchanged.

This is not a coincidence worth glossing over: the hyphen restorations
(`cengfo` → `ceng-fo`) keep one token; the 33 cases that gain a free-standing
`-` (`Panay Tutuy` → `Panay - Tutuy`) add a chunk with no letter or digit, which
the counting rules do not count; and the 90 removed `<W>` are word-tier, while
tokens come from sentence-level FORM only. **There is no counting discontinuity
to announce for ePark.**

## Issue #62 dispositions

| claim | verdict |
|---|---|
| "928 V121, 2 V129, 1 V131" | **Confirmed exactly**, and unchanged after regen. All three are source-inherited content, not regeneration defects. V121: 464 `<W>` × 2 tiers in `jiu_jie_jiao_cai` where the source puts an alternate form in parentheses inside a word token — POL-026/POL-027 worklist. V129: one Dona Rukai sentence (S 243) with `*ka` mid-sentence, mirrored into the standard tier by `--copy` — POL-016 worklist. V131: a U+FEFF inside a **W-level** TRANSL in `Tanqun_Bunun.xml` (W 399-402); `clean_xml` cleans S-level TRANSL only, so **POL-041 blocks cleaning it here** — needs a source-side fix in Phase 1 or a maintainer call, not a cleaner change. |
| "Duplicates are HARD because the pipeline declares deduplication under POL-022" | **Confirmed count, refuted cause — now resolved.** ePark has **no** duplicate-removal step. `validate_duplicate_sentences.dedup_in_pipeline()` greps `CodeAndDocs/` for the literal tokens `remove_duplicate_sentences|dedup`, and the *only* match in the whole corpus was a **prose comment** in `ePark3.py` ("duplicates that a later dedup step removed"). The comment was also factually wrong — nothing removes duplicates here; the ePark_3 copies of topics 4–8 are simply not generated. Comment corrected (no data change); the detector now returns `False` and all 100,082 occurrences are SOFT, i.e. the maintainer's call per POL-022, which is right for graded teaching material that repeats sentences by design. **Repo-level follow-up**: a bare-substring grep over every `.py/.md/.txt` in `CodeAndDocs/` is a fragile way to detect a declared pipeline step — any corpus that merely *discusses* duplicates gets 100k findings upgraded to HARD. |
| "2 V141, 4 V142, 2 V146, 205,994 V147" | **All four confirmed exactly.** V146 → **0** and V147 → **0** after regeneration. V141 (2 sentences where the W tier reconstructs only 56% of the S FORM) and V142 (4, an inline `? ` in Luanqun Bunun) are unchanged content worklist items. |
| "Audio statistics are stale for Amis/Xiuguluan, Bunun/Junqun, Sakizaya, Yami" | **Confirmed** — `get_corpus_stats.py --report-stale-audio` reports exactly those four buckets (and no others for ePark). **Unchanged and unchangeable here**: `<AUDIO>` is byte-identical, and refreshing the seconds requires pulling the corpus's audio from Hugging Face (`refresh_audio_stats.py`), which this turn is explicitly forbidden to do. Out of scope, still open. |
| "Hosted-audio parity passes" | **Not verified** — `validate_hf_audio` needs network access to Hugging Face. Since no `<AUDIO>` element changed, whatever parity held on `main` still holds. |
| "Repair each source-specific generator path, then regenerate standard FORM and PHON" | **Half done.** Standard FORM and PHON are fully regenerated. The generator paths (`ePark1and2.py` / `ePark3.py`) are *not* repaired: their remaining findings (V121, V129, V141) are faithful renderings of what the source CSVs contain, so "repairing" them means content decisions (splitting POL-026 parenthetical variants into two `<S>`), not parser fixes. Recommend re-scoping that half of the issue as a linguistic worklist. |

## README corrections

The README was rewritten (current pipeline + data-user facts). Beyond the
second-`clean_xml` removal and the new entry point, three factual repairs:

- The documented `qing_jing_zu_yu` Amis command was **corrupted** — two commands
  run together on one line, with `standardize.py` left without its `--tsv_path`:
  `standardize.py --corpora_path …/Amis python …/add_phonology.py --corpora_path
  …/Amis --orthography Ortho113Liberal`. The published data proves what actually
  ran: qing_jing Amis shows the full `Amis_113lib_113` mapping including the
  Southern column's `o`→`u` (Southern_Amis `o` 26 → 0, `u` 3,038 → 3,064).
  Reconstructed and verified.
- The orthography mapping is now a table, per sub-corpus × language, and was
  verified empirically before being written down (`u`/`o` counts per dialect
  file confirm the Amis TSV ran in exactly `hui_ben`, `jiu_jie` and `qing_jing`
  and nowhere else). Two of the six table-driven blocks —
  `jiu_jie_jiao_cai` Atayal and Puyuma — produce **zero** changes on this data;
  they are kept and run for correctness, and documented as inert.
- The README referenced a `Final_XML/` directory that does not exist in the
  published corpus, and described the corpus as if it were still the dev repo.

Recorded, not changed: `jiu_jie_jiao_cai` Amis is standardized *from*
Ortho113Liberal but phonologized with `Ortho113` (the other two Amis blocks use
`Ortho113Liberal`). The two profiles have an identical `letter` column and
differ only by Ortho113's extra `default` fallback, so the asymmetry is inert.
Flagged in the README rather than silently normalized.

## Script changes

| file | change |
|---|---|
| `CodeAndDocs/make_xml.sh` | **new** — single documented entry point, 7 steps, sidecar cleanup, `SIDECAR_KEEP_DIR` review hook |
| `CodeAndDocs/drop_unmapped_phon.py` | extended to drop empty PHON on both tiers (V073 fix) |
| `CodeAndDocs/cleanup_empty_words.py` | `--final_xml_dir` argument replacing a hardcoded `./Final_XML/...` path |
| `CodeAndDocs/ePark3.py` | comment corrected (no data change); removes the false dedup declaration |
| `CodeAndDocs/quote_corrections.csv` | **new**, committed (POL-035) — 9 rows |
| `XML/html_entities.log` | **deleted** — stale run log tracked inside `XML/` |
| `README.md` | rewritten |

`fix_parenthetical_spacing.py` was **retired from the Phase 2 pipeline** per the
standing ruling: verified no-op, 0 edits across 436 files, because its
correction is already baked into the committed original tier. The script is
kept and re-documented as a Phase 1 step, where it does real work when building
from the source CSVs. `drop_unmapped_phon.py` was verified to still do real
work (3,891 PHON removed per run) and stays.

## UNEXPLAINED

**None.** 2,571,534 / 2,571,534 edit operations classified (100.0000%), across
12 classes, with zero changes to `<AUDIO>`, zero changes to any `TEXT`
attribute, and zero token movement.
