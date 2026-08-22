# Phase B regeneration report — YeddaPalemeqBlog

**Date:** 2026-08-12 · **Branch:** `work/b3-yedda` (off `main` @ `3ce8e7dac`) · **Group:** 2
**Corpus:** `Corpora/YeddaPalemeqBlog` — Paiwan (`pwn`, dialect `Southern`), one file,
671 S / 5,643 W / 7,654 M / 666 AUDIO. Declared original-tier orthography: Ortho113.

This is the corpus the sweep tracking doc flagged as the bank's only **unrecorded** hand
edits (README §5 prose, no id list, no script). The capture succeeded, so the corpus is now
regenerable end-to-end and `apply_manual_edits.py` is a real pipeline step here.

## 1. POL-030 capture — 6 sentences, recovered by rebuild-and-diff

**Method.** `CodeAndDocs/analyze_blog_structure.py --generate-xml` was re-run over the
existing local `html_cache/` in the dev repo (`../Formosan-Yeddas-Blog/`, 730 files) — **no
re-download**. That rebuild was then put through `clean_xml.py` and diffed against the
published `XML/` element by element, on the `manual_edits` strip basis (all standard FORM
and all PHON removed, so standardize/add_phonology drift cannot masquerade as a hand edit).

The first pass showed 552 differing sentences — too many to be hand edits — and every one of
them turned out to be a **defect in the committed parser**, not an edit (§2). After fixing
those two defects the diff collapsed to exactly **3 changed + 3 new sentences**, which are
exactly the `/`-and-`()` corrections README §5 described:

| id | what was done | AUDIO |
|---|---|---|
| `S24_1` | `mareka qali/drava` → `mareka qali` | removed |
| `S24_1b` | **new**: same sentence with `drava` | none |
| `S483_1` | `ni kama a abar (yasi).` → `ni kama a abar.`; the parenthetical second reading split into a `TRANSL ver="alt"` | removed |
| `S483_1b` | **new**: same sentence with `yasi` | none |
| `S535_1` | `/ siyak` removed from the **W tier only** | **kept** |
| `S535_1b` | **new**: `tjangtjang,` variant | none |

Captured with `QC/utilities/capture_manual_edits.py` against a throwaway commit holding the
rebuild, giving `CodeAndDocs/manual_edits.xml` (6 records, 3 of them with `after=` placement
hints) and, at apply time, `CodeAndDocs/manual_edits.md`. `apply_manual_edits.py` reports
`6 edit(s) across 1 file(s); 0 no-op(s)`.

**Unattributed published-vs-rebuild differences: none.** Every difference is accounted for
by the two parser defects, by `clean_xml`, or by the six records above.

**Finding (left for review):** the post-535 correction is **incomplete and inconsistent with
the other two**. `S535_1`'s sentence-level FORM still reads `tjangtjang / siyak` while its W
tier was resolved, and it kept its `AUDIO` where the other two split sentences lost theirs.
Resolving it means choosing which alternate `S535_1` should carry — a content call, so it is
recorded in the README's "Manual edits" section rather than guessed at here.

## 2. Two defects in the committed generator (fixed; POL-038)

Both were found by the capture diff and are fixed in `CodeAndDocs/analyze_blog_structure.py`.
Each fix makes the rebuild reproduce the published values; neither invents data.

1. **Double XML escaping.** `escape_xml_content()` hand-escaped `& < > " '` and then
   ElementTree escaped again at serialization, so every value was stored double-encoded
   (`k&lt;em&gt;acu`, `&apos;`). The published corpus is *not* double-encoded because the
   pipeline of the day decoded it; **today's `clean_xml.py` decodes FORM tiers only
   (`sentence.findall('TRANSL')` is S-level), so a naive rerun would have regressed 552
   sentences' word- and morpheme-level glosses to `&apos;` residue.** Replaced by a
   pass-through `xml_text()` with the reasoning in its docstring.
2. **Duplicate M ids.** `all_morphemes.index(morph) + 1` returns the *first* index, so a word
   with a repeated morpheme (`ki-pa-pa-rangez`) gave two `M` elements the same id — 68 such
   ids. Replaced with positional `enumerate`, which reproduces the published ids exactly
   (verified: 68/68 W elements, all M id lists identical to published). This retires README
   §6, which told the reader to run `validate_xml.py` to "fix" the ids; the current
   `validate_xml.py` is a pure validator and fixes nothing.

## 3. Reproducibility: committed intermediate instead of a POL-035 snapshot

The scrape input (`html_cache/`, 730 files, 68 MB) is **not committed anywhere** — it is
gitignored in the dev repo and absent from FormosanBank. Committing it is not proportionate.
Instead the parser's output is committed as **`CodeAndDocs/raw_xml/Paiwan/Paiwan_Yedda_Blog.xml`**
(1.7 MB) and the pipeline starts from it. Per POL-035 this makes the corpus a *regenerable*
one — the pipeline is the baseline, self-correcting from a committed input on every run — so
no `pre_correction_snapshot/` was taken. Re-scraping is documented in the README and in the
`make_xml.sh` header as the (network- and `beautifulsoup4`-dependent) way to refresh
`raw_xml/`; it is deliberately **not** a step of `make_xml.sh`.

## 4. Pipeline: new `CodeAndDocs/make_xml.sh` (executable, committed)

Single entry point, FormosanBank root parameterized (arg / `FORMOSANBANK_ROOT`, default = the
checkout the corpus lives in; `PYTHON` overrides the interpreter):

0. restore `XML/` from `CodeAndDocs/raw_xml/`
1. `QC/cleaning/clean_xml.py`
2. `QC/cleaning/apply_manual_edits.py` — **not a no-op**: 6 edits
3. `QC/utilities/standardize.py --remove_accents` (standing ruling; README's `--copy` superseded)
4. `QC/utilities/add_phonology.py --orthography Ortho113` (README-declared profile)

Verified **idempotent**: a second full run is byte-identical (md5).

## 5. Quote correction — Paiwan dictionary armed, **zero rows**

`QC/validation/reference/Paiwan/attestation.txt` is armed (131 edge-apostrophe entries after
`b80bef60c`). The cleaning run produced **no `quote_corrections.csv` anywhere and 0 c031/c032
rows**. `cleaner_warnings.csv` carried 2 `c030` ambiguity flags only, both in `S217_1`
(`na'ivu'ivu`, word-internal glottal inside a quoted clause) — no correction attempted,
matching the Phase A Paiwan prediction of 0 rewrites.

## 6. Sidecars (POL-033: reviewed, then deleted)

- `XML/cleaner_warnings.csv` — 2 rows, both `c030` (above). Reviewed, deleted, not committed.
- No `standardize_warnings.csv` produced.
- No `html_entities.log` produced (defect 1's residue is gone at source).
- **Deleted from the repo:** `Corpora/YeddaPalemeqBlog/html_entities.log`, a committed
  cleaner sidecar (POL-033 violation) that the new pipeline no longer even generates.

## 7. Diff audit vs git HEAD — 100% classified

Scripted element-by-element comparison of every FORM / PHON / TRANSL / AUDIO / id-list /
attribute value at S, W and M level: **76,825 keys compared, 0 keys added, 0 removed,
6,244 changed.** TEXT attributes identical; S/W/M id sets identical.

| class | count | notes |
|---|---|---|
| PHON regenerated | 6,190 | current shared-source generator; sub-effects below |
| manual-edit sentences (the 6 records) | 49 | 48 of them PHON; 1 standard FORM (below) |
| standard FORM rederived — accent removal | 5 | `S303_1` + its W/M: `yípó`→`yipo`, `āyí`→`āyi` (only the acute is stripped; the macron is source spelling and survives) |
| **UNEXPLAINED** | **0** | 100.0000% ≥ 99.9% |

The single non-PHON change inside the manual-edit set is `S535_1b`'s standard FORM,
`tjangtjang , asaw` → `tjangtjang, asaw`: the standard tier is now *derived* from the
original rather than being a separately typed string, so the stray space before the comma is
gone.

PHON sub-effects, over all 6,238 changed PHON values (scripted per-value reconciliation):

| sub-effect | values | verification |
|---|---|---|
| punctuation / angle-bracket / hyphen removal only | 4,203 | new value == old value with `. , ; : ! ? ( ) " ' / - < >` removed and whitespace collapsed; e.g. `k<əm>aʦu` → `kəmaʦu` |
| the same, **plus** `tj` now realized `c` (was `ʦ`) | 2,022 | 2,412 `ʦ`→`c` character replacements, each backed by a `tj` in the FORM. `Orthographies/Ortho113/Paiwan.tsv` maps `tj`→`c` and `c`→`ʦ`; the old values rendered `tj` as `ʦ`, i.e. **the regeneration is a correction** |
| downstream of accent removal | 5 | `S303_1` standard tier: the old generator emitted `*` for the accented vowels it could not map (`j*p*`, `*j*`); with the accents gone the bare vowels map (`jipu`, `*ji`) |
| whitespace artifact of punctuation removal | 6 | `S155_1`/`S189_1`/`S535_1`: dropping a trailing `.`/`!` or an interior `/` leaves a trailing or doubled space in the PHON value (see §10) |
| entity-residue PHON repaired | 2 | `S477_1W37`: published PHON was the corrupt `ʔ&ɣt;əm>umaʎ` (the old generator transliterated a literal `&lt;` residue, `l`→`ɣ`); now `ʔəmumaʎ` |

## 8. Token counts and validators

| metric | before (HEAD) | after | Δ |
|---|---|---|---|
| tokens Paiwan / Southern | 5,878 | 5,878 | **0** |
| `validate_xml` | 0 issues | 0 issues | — |
| `validate_text` HARD | 0 | 0 | 0 |
| `validate_text` SOFT | 2,403 | 2,394 | **−9** |
| `validate_glosses` HARD | 7,928 | 7,928 | 0 |
| `validate_glosses` SOFT | 800 | 800 | 0 |
| duplicate sentences | 2 SOFT within-file groups | 2 | 0 |

SOFT movement is entirely V116 `non_ascii_in_form` 30 → 21: the nine acute-accented
characters that `--remove_accents` took out of the standard tier. V122
`parens_slashes_anywhere` is unchanged at 2,373 (POL-026 worklist — the blog writes optional
material and roots in parentheses throughout the word glosses). V147 was 0 before and after
(this corpus never carried legacy `~` PHON notation).

## 9. Issue #82 dispositions — every claim verified, none acted on

Reproduced exactly on `main`: V062 = 271, V064 = 7,654, V067 = 3 (incl. `S584_1W7M1`
= `d-<in>udu`), V065 = 778, V061 = 3, 2 SOFT within-file duplicate groups. All unchanged by
this turn.

- **V064 (7,654 M with no TRANSL) — linguistic worklist, not mechanical.** The blog glosses
  *words*, not morphemes; the parser attaches each gloss to the W. Splitting a word gloss
  across its morphemes is a segmentation judgment per word, and under POL-036 any such gloss
  would be a *new* `kindOf="standard"` TRANSL, never a rewrite of the source's. Needs a
  linguist. **Not attempted.**
- **V062 (271 infix M without an angle-bracket gloss on the parent W) — same.** The rule wants
  the parent W's *TRANSL* to use `<X>` notation; the blog's prose glosses mostly do not. This
  is a gloss-notation decision, not a data repair. **Not attempted.**
- **V067 (3) + V061 (3) — one root cause, diagnosed, fix deliberately withheld.** Three words
  carry *two* infixes: `d<em><in>udu` (`S584_1W7`), `s<em><in>amalji` (`S322_1W1`),
  `g<em><in>agalj` (`S288_1W3`). The parser's extraction regex
  (`^(.*?)<([^<>]+)>(.*?)$`) is single-shot, so the second infix stays inside the M FORM,
  producing `d-<in>udu`. Looping the extraction would be mechanical, but it would **not**
  clear the gate — those W elements would still fail V062 — and it changes M content/count in
  the gloss tier. Recommend folding it into the one coordinated gloss-tier pass that V062/V064
  need anyway. **Not applied**; recorded in the corpus README's "Known limitations".
- **V065 (778 W with no TRANSL)** — words the gloss matcher could not align to a gloss entry.
  SOFT; part of the same worklist.
- **2 duplicate groups** — `S194_1`/`S511_1` and `S463_1`/`S531_1`, genuine re-posts of the
  same sentence on different days. No dedup step is declared for this corpus, so POL-022
  keeps them SOFT; maintainer's call.

**Issue #82 stays open.**

## 10. Observations for the maintainer (non-blocking)

- **`clean_xml.py` cleans S-level TRANSL only.** W/M-level TRANSL gets no `clean_trans` pass
  (and, since C028 lives in the FORM loop, no entity decode either). Here that is now moot,
  but it is a repo-wide asymmetry worth a ruling — the published W glosses keep `[...]` where
  S-level translations had theirs converted to `(...)`.
- **`add_phonology` leaves whitespace artifacts** where it drops punctuation: a trailing space
  when the FORM ended in `.`/`!`, a double space where an interior `/` was removed. Cosmetic,
  repo-wide, six values here.
- **`beautifulsoup4` is not in `requirements.txt`**, so the documented re-scrape step cannot
  run in the repo `.venv`. Left alone (repo-wide pinned file, and the scrape is not part of
  `make_xml.sh`); add it if the re-scrape path should be first-class.
  *(Retired in correction round 2: it is now pinned in `requirements.txt`.)*
- **Deleted stale dev-repo test harness** from `CodeAndDocs/Scripts/`: `README.md`,
  `baseline_metrics.json`, `test_runner.py`, `test_xml_baseline.py`. Its "baseline" was
  `Final_XML/Paiwan_Yedda_Blog.xml` at 640 S / 4,526 W — a superseded file that is not in this
  repo, so the harness could only ever report failure. `download_html.py` and
  `download_audio.py` were kept (reproduction infrastructure).
- `S305_1` quotes Japanese; its Paiwan FORM contains kana (7 V116 rows). Faithful to source.
- The corpus README file is `readme.md` (lowercase) where the rest of the bank uses
  `README.md`; left as-is to avoid breaking external references.
  *(Retired in correction round 2: renamed with `git mv`; nothing in the repo referenced it.)*
- GitBook corpus-page update (per-corpus procedure step 9) deferred to post-merge.

**UNEXPLAINED items: none.**

## Correction round (maintainer review, 2026-08-12)

The maintainer rejected the first pass at two of the three alternate splits
and supplied the correct analysis; both are now fixed in
`CodeAndDocs/manual_edits.xml` and re-applied through `make_xml.sh`.

**S535 (post 535).** The first pass left `tjangtjang / siyak` in the
sentence-level FORM of `S535_1`, kept its AUDIO, and — worse — gave
*both* variants `siyak` in the W tier, so `S535_1b`'s sentence text and
word tier disagreed. Per the source (`tjangtjang or siyak : pumkin`,
i.e. one gloss for a synonym pair) the two sentences are now identical
except at `W5`: `tjangtjang` in `S535_1`, `siyak` in `S535_1b`. Both
carry the shared gloss `pumkin`, the `/` is gone from both sentence
FORMs, and AUDIO is dropped from both (the recording speaks both
options), matching the post-24 precedent.

**S483 (post 483).** `(yasi)` is not optional material — it is an
alternative to `abar`; the blog post is titled "abar / yasi" and glosses
the pair as one entry. The two sentences now differ only at `W7`
(`abar` / `yasi`), both carrying the shared gloss ("coconut trees. abar
is in RF's dictionary (1982); however … replaced by the loanword from
Japanese やし.").

Also recovered from the source in passing: `'ata` (`' ata or kata : and`)
was unglossed in both S535 sentences and now carries `and`.

**Identifier change, announced per POL-037**: making each pair parallel
renumbered W/M ids inside these four sentences (contiguous `W1…Wn`, the
alternate at the same index in both). S ids unchanged; no other sentence
affected. Recorded in the corpus README.

Post-correction: validate_xml clean; validate_text SOFT 2,396
(V116 21, V122 2,375); tokens 5,878 → **5,877** (the `/` that had been
left in S535_1's sentence FORM was being counted as a token).

**Audio on alternate blocks (maintainer ruling, 2026-08-12).** Where a
sentence was split into alternates, the audio is unusable — the recording
speaks both options — so it is removed from the XML entirely: the `AUDIO`
element *and* the sentence's `audio_url` attribute. Applied to all six
split sentences (S24_1/1b, S483_1/1b, S535_1/1b); the AUDIO elements were
already gone, the `audio_url` attributes were still advertising a
recording that matches neither variant. The remaining 665 of 671
sentences keep their audio untouched. validate_xml clean.

## Correction round 2 (maintainer review, 2026-08-12)

Six rulings from the maintainer, all applied through committed code (POL-038):
`manual_edits.xml`, the committed parser, or the new `CodeAndDocs/fix_m_tier.py`
wired in as `make_xml.sh` step 3. No file was hand-edited.

### 1. Renumbering reverted — original ids with gaps (POL-037 as clarified)

Round 1 renumbered the four alternate-split sentences to run `W1…Wn`
contiguously. Under the clarified POL-037 (**preserving published ids beats
tidiness; gaps are fine**) that churn is reverted, leaving exactly **one**
changed public id in the whole corpus:

| sentence | ids now | vs published on `main` |
|---|---|---|
| `S535_1` | `W1 W2 W3 W4 W5 W8 W9 W10 W11 W12` | `W7`(`siyak`) → `W5`(`tjangtjang`) — the only change; `W5` is the id the raw parse gives `tjangtjang`, and the word at that slot is what the correction changes |
| `S535_1b` | `W1…W4 W7…W12` | unchanged |
| `S483_1` | `W1…W7` | unchanged |
| `S483_1b` | `W1…W6 W8` | unchanged |
| `S24_1`, `S24_1b` | `W1…W13` | unchanged (already contiguous in the raw parse) |

M ids follow their W (`S535_1W5M1`). `apply_manual_edits.py` still reports
`6 edit(s) across 1 file(s); 0 no-op(s)` — no record was orphaned. Everything
else from round 1 is kept: no `/` in any sentence FORM, the shared `pumkin` and
`abar or yasi : coconut trees…` glosses, `'ata` = `and`, and no audio at all
(neither `AUDIO` elements nor `audio_url`) on the six split sentences.

### 2. V067 double infixes fixed in the parser → 0

Three words carry two infixes; the single-shot regex
`^(.*?)<([^<>]+)>(.*?)$` extracted only the first and left the second inside the
root M FORM (`d-<in>udu`), a V067 HARD finding. Replaced by
`split_infix_morphs()`, which extracts **every** bracketed group. Maintainer's
ruling: two infixes at the **same site** still take a single `-` in the root, so
the empty segment between adjacent brackets is dropped before rejoining:

| W | M FORMs before | after |
|---|---|---|
| `S584_1W7` `d<em><in>udu` | `d-<in>udu`, `-em-` | `d-udu`, `-em-`, `-in-` |
| `S322_1W1` `na-s<em><in>amalji` | `na`, `s-<in>amalji`, `-em-` | `na`, `s-amalji`, `-em-`, `-in-` |
| `S288_1W3` `na-g<em><in>agalj` | `na`, `g-<in>agalj`, `-em-` | `na`, `g-agalj`, `-em-`, `-in-` |

Real material between two *separate* sites would keep its hyphen
(`a<em>b<in>c` → `a-b-c`); no such word occurs here.

`raw_xml/` was regenerated from the committed `html_cache/`
(`../Formosan-Yeddas-Blog/html_cache`, 730 files, **no re-download**).
**Single-infix behavior is provably unchanged**: the pre-fix parser reproduced
the committed `raw_xml/` byte-for-byte (md5 `7a148dca…`), and the post-fix diff
against it is exactly the 9 lines above — 3 M FORMs rewritten, 3 M elements
added, nothing else. V067 3 → **0** and V061 3 → **0** (same root cause: the M
count now matches the FORM's segmentation). V062 rises 271 → 274, because the
three recovered `-in-` morphemes are themselves infix M under a prose gloss (§6).

### 3. `M`-tier presence, per sentence — `CodeAndDocs/fix_m_tier.py`

The parser emitted one M per W unconditionally, so unparsed sentences carried a
tier of bare M mirrors — an analysis Yedda never made. Applying POL-023 **per
sentence** (maintainer's ruling):

**Criterion for "this sentence carries some morphological parsing"** — either
(a) some W in the sentence has ≥2 M children, or (b) some M's FORM differs from
its parent W's FORM. On this data the clauses agree: **0 sentences qualify by
(b) alone**, so the split is unambiguous.

| | sentences | M |
|---|---|---|
| carried parsing, every W already had an M → untouched | **494** | 6,492 kept |
| carried no parsing → M tier removed | **161** | **1,165 removed** |
| gained an M element (parsing sentence with an M-less W) | **0** | 0 added |
| no W tier at all (nothing to do) | 16 | — |

Totals: 671 S, 5,643 W, 6,492 M (was 7,654), 665 AUDIO.

**Consequence to escalate:** `validate_xml`'s **V144 is per *file***, so it now
reports **1,165 SOFT** M-less W — every one of them the intended state under the
per-sentence ruling. Either V144 learns the per-sentence reading or this corpus
carries a permanent 1,165-row SOFT baseline. Not changed here (repo-wide
validator, and POLICIES.md was off-limits this turn).

### 4. Duplicates — neither group is literally identical; **nothing removed**

Both groups were compared element by element (S attributes, FORM, TRANSL, W/M
ids, W FORMs, glosses, M splits, AUDIO).

- `S194_1` / `S511_1` — same Paiwan FORM, but different English translation,
  different glosses throughout, different segmentation (`aicu` vs `a-icu`,
  `mamaw` vs `ma-maw`, `kinamasanpazangalan` unparsed vs
  `k<in>a-masan-pa-zangal-an`), and different audio (different posts/recordings).
- `S463_1` / `S531_1` — same Paiwan FORM, different translation, different
  glosses on all five W, different audio.

In both, the later post revisits the sentence with a **new analysis**: the
second block is content, not a copy. **Both pairs kept; 0 S removed; token delta
0 from dedup.** Documented in the README. They remain 2 SOFT within-file groups
under POL-022.

### 5. `readme.md` → `README.md`

Renamed with `git mv`. No script, workflow, test or doc in the repo referenced
the lowercase path (only historical `claudeplans/` prose, left as the record it
is), so nothing needed rewiring. This retires the round-1 observation in §10.

### 6. Two findings recorded, deliberately not acted on

- **V062 (274).** The corpus *does* gloss infix function — in prose, not Leipzig
  notation: `k<em>acu` is glossed "bring, actor focus" or "bring, AV. The root is
  kacu 'bring'." rather than `<AV>`. Distribution: `-em-` 155, `-in-` 90
  (87 + the 3 recovered in §2), `-en-` 27, `-ema-` 1, `-ar-` 1. Under POL-036 the
  repair is **additive** — a standardized `<AV>` gloss is added as a separate
  `TRANSL[@kindOf="standard"]`, never by rewriting Yedda's prose — and it is a
  per-word linguistic judgment. **Needs a linguist; not acted on.**
- **V065 (772) / V064 (6,492).** This is a **partly-glossed corpus**: some W
  simply have no gloss and the blog glosses words rather than morphemes. That is
  a property of the source, not a defect (maintainer's ruling). Stated plainly in
  the README's "Known limitations" as well.

### 7. Numbers after correction round 2

| metric | before (`main`) | after | Δ |
|---|---|---|---|
| tokens Paiwan / Southern | 5,878 | **5,877** | **−1** (the `/` left in `S535_1`'s sentence FORM had been counted) |
| S / W / M / AUDIO | 671 / 5,643 / 7,654 / 666 | 671 / 5,643 / **6,492** / **665** | M −1,162, AUDIO −1 |
| `validate_xml` HARD | 0 | **0** | 0 |
| `validate_xml` SOFT | 0 | **1,165** (V144, all expected — §3) | +1,165 |
| `validate_text` HARD | 0 | 0 | 0 |
| `validate_text` SOFT | 2,403 | **2,396** | −7 (V116 30→21 accent removal; V122 2,373→2,375, the two shared `abar or yasi` glosses carry `(1982)`) |
| `validate_glosses` HARD | 7,928 | **6,766** | −1,162 (V062 271→274; V064 7,654→6,492; **V067 3→0**) |
| `validate_glosses` SOFT | 800 | **790** | −10 (V060 19→18, the `/` gone from `S535_1`; **V061 3→0**; V065 778→772, the six W that gained the shared glosses) |
| duplicate sentence groups | 2 SOFT | 2 SOFT | 0 (§4) |

Every delta above is accounted for; the counts reconcile exactly
(7,654 + 3 new `-in-` M − 1,165 pruned = 6,492).

`make_xml.sh` re-verified **idempotent** after the new step: two consecutive full
runs give the same md5 (`bea3bbae…`). `XML/cleaner_warnings.csv` (2 `c030` rows,
`S217_1`, unchanged from round 1) reviewed and deleted, not committed (POL-033).

**UNEXPLAINED items: none.**
