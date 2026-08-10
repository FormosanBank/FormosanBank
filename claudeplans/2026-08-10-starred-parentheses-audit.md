# Repo-wide audit: `*(X)` / `(*X)` starred-parenthesis conventions

**Date:** 2026-08-10
**Branch:** `worktree-audit-starred-parens` (off `main`)
**Trigger:** The Shih-Rukai-Adverbial dev-repo audit surfaced that `*(X)` in
linguistics sources means X is **obligatory** (the sentence is ungrammatical
*without* X), while `(*X)` means X is **forbidden** (ungrammatical *with* X) —
neither is the ordinary "optional" `(X)`. A pipeline that treats all
parentheticals alike corrupts data in two ways:

- stripping the parenthesized content of `*(X)` **deletes obligatory material**,
  publishing an ungrammatical string as if attested;
- stripping only the parens of `(*X)` **injects forbidden material** as plain
  text.

## Method

Swept every corpus under `Corpora/` for `*(`, `(*<letter>`, fullwidth `＊` and
`*（`, in (a) the raw/intermediate post-scrape data under each
`CodeAndDocs/` (all text formats; PDFs via `pdftotext`; `.docx` via unzip) and
(b) the published `XML/`. Every hit was traced from raw record → processing
script → published `<S>` element. Limits: only raw data actually committed to
this repo was checkable — corpora whose scrape intermediates live only in dev
repos or upstream (ILRDF_Dicts, ePark, Glosbe caches, …) could be checked on
the XML side only (all clean there).

## Findings, ranked

### 1. HARD — NTUFormosanCorpus deleted an obligatory word (`*(malra)`), publishing an ungrammatical sentence

- **Raw:** `CodeAndDocs/sentence/Rukai_Vedai/20200529-FW-Lixing-2.json`,
  sentence 2: ori = `kay tatulru muavaevaeva *(malra) kay karadrare.`, gloss
  `*(malra)` = `*(take)` / `*(拿)`, free translation "Three people went and
  took one basket." / 「三個人合拿一個籃子。」 The source marks *malra* 'take'
  as obligatory.
- **Published XML:** `Corpora/NTUFormosanCorpus/XML/Sentences/Rukai/Rukai.xml`
  S `20200529-FW-Lixing-2_S_2` (line ~70744):
  `<FORM kindOf="original">kay tatulru muavaevaeva kay karadrare.</FORM>`
  — *malra* is gone from both FORM tiers, both PHON tiers, and the W tier.
  The published sentence is ungrammatical by the source's own judgment and no
  longer matches its retained translation ("…took one basket" with no 'take'
  verb). Contrast the neighboring grammatical sentence (line ~72369)
  `kay lalasu muavaevaeva malra kay karadrare.`, which keeps *malra*.
- **Cause:** `CodeAndDocs/scripts/utils.py:244`
  `UNGRAMMATICAL_PAREN_RE = re.compile(r'\*\([^)]*\)|\(\*[^)]*\)')` treats
  `*(X)` and `(*X)` **identically**, and `parse_sentences.py:176–181` (and the
  analogous filters in `parse_grammar.py:260, 263, 301`) drop any matching
  token from ori and gloss before FORM reconstruction. Dropping is correct for
  `(*X)` (forbidden) but exactly wrong for `*(X)` (obligatory), where the
  attested surface form *includes* X.
- **Scope:** this is the only `*(X)`-in-FORM instance in NTU raw data (the
  other `*(…)` hits are in dropped story notes, see finding 4), so exactly
  **one published sentence** is corrupted.
- **Fix (script, not hand-edit):** in the NTU parsers, split the regex: for
  `*(X)` keep X in ori/FORM (unstarred) and record the obligatoriness
  machine-readably (e.g. FORM/W `notes`); for `(*X)` keep the current drop,
  ideally also recording it. Regenerate the Rukai Sentences XML.

### 2. SOFT — NTUFormosanCorpus `(*X)` forbidden-type tokens dropped without a trace (7 sentences, output grammatical)

- `CodeAndDocs/sentence/Kanakanavu_Kanakanavu/3.json`: sentences 27
  (`(na)(*sua)`), 69 (`(*sua)`), 75 (`(*na)`), 106 (`(*sua)`), 190
  (`arivuree(*=cu/ci)=maku`) — forbidden case-markers/clitics dropped by the
  same filter. The published sentences are the grammatical variants (correct
  outcome), but nothing records the source's negative-evidence judgment, and
  in sentence 27 the *optional* `(na)` was collateral damage of dropping the
  whole token.
- `CodeAndDocs/grammar/Kanakanavu_Kanakanavu/11.json`: two `(*kara)` question
  sentences. Handled **well** in
  `XML/Grammar/Kanakanavu/Kanakanavu.xml` (lines ~29369, ~29440): grammatical
  FORM published, and the second even preserves the optional-`(kara)` variant
  in `FORM/@notes` — a good model for what finding 1's fix should do.

### 3. SOFT — NTUFormosanCorpus nested-paren strip bug leaves `.)` remnant in a TRANSL

English translation-level judgments like
`All the children took fish. (*Children took all the fish.)` (7 sentences in
`XML/Sentences/Kanakanavu/Kanakanavu.xml`) are correctly preserved verbatim in
`TRANSL/@notes` with the starred part stripped from the TRANSL text. But at
line ~15315 the note `Teacher(s) hit all students. (*All teachers hit
student(s).)` was stripped with a non-nesting regex that stopped at the first
`)` inside `student(s)`, yielding
`<TRANSL …>Teacher hit all students. .)</TRANSL>` — a stray ` .)` and a lost
`(s)`. One-line fix: nesting-aware (or greedy-to-final-`)`) strip; regenerate.

### 4. INFO — NTU story `#n` linguist notes containing starred forms are dropped wholesale (no FORM impact)

- `story/Kanakanavu_Kanakanavu/kkvNr_sowing_Kuatu.json`: note
  `mucUmcUm=kia (*’inia); mucUmcUm=kia *(mokusa) ‘inia。` (appears twice).
- `story/Seediq_Tgdaya/sdqNr-childhood_micang 2020s.json`: note
  `asi=ku (*m-)osa` (m- prefix forbidden after *asi*).
- Neither note reaches the story XML; the actual story sentences are
  unaffected. Annotation loss only — acceptable, but worth remembering that
  `#n` notes carry grammaticality judgments if notes are ever ingested.

### 5. CLEAN — Nowbucyang-Truku-Thesis handles the conventions correctly and documents it

The only corpus whose pipeline explicitly distinguishes the cases.
`(*saman/shiga)`, `(*ge-idas)`, `(*ge-idaw)` in `examples_{raw,clean}.jsonl`
are stripped from FORM by `scripts/pipeline.py:1569–1572` with a comment
("explicitly ungrammatical alternatives, not corpus text"); starred slash
alternatives are omitted with generated notes
(`_preserve_slash_options()`, ~1945–1992); whole star-initial sentences are
rejected with reason `ungrammatical_starred_form` (~1383); and a validator
fails if a `*` marker ever reaches FORM (~2605). All instances are logged in
`manual_qc_parentheses.txt` / `manual_qc_slash_options.txt` with the emitted
S ids. No `*(X)` obligatory instances exist in this corpus. **No action.**

### 6. CLEAN outcome / latent hazard — Song-Kanakanavu-Grammar strips all parens blindly

`raw_data/official_text.jsonl` p.134 has the same two Kanakanavu `(*kara)`
examples as NTU's grammar section (both derive from Song 2018): 11-2c
`nikʉmʉʉn kara Pani (*kara) mamíriki?` and 11-2d
`'esi kara marivura'ʉ(kara)'uva (*kara) nguain tamna manu?`. Published as
S0228/S0229 with the grammatical *kara* placement only, and the `source=`
attribute documents the omission — correct result. But the mechanism,
`build_xml.py` `xml_word_form()` (`re.sub(r"\([^)]*\)", "", text)`, likewise
`extract_interlinear.py:530`), strips **every** parenthetical
indiscriminately: it produced the right answer here only because both
instances are the forbidden type. An `*(X)` obligatory instance would be
silently deleted, malra-style. Worth a guard (assert no `*(` in input, or
handle explicitly) if the pipeline is ever re-run or reused. The optional
`(kara)` variant of 11-2d was also dropped without a note (NTU kept it —
finding 2).

### 7. NOT the convention — asterisks in SEALS33, Presidential_Apologies, Wikipedias XML

Classified to rule them out:

- **SEALS33** (e.g. `saisiyat_seals.xml` S 9: FORM `(Uri TADMOR)` → PHON
  `(*ri ta*mor)`): PHON-tier `*` placeholders for characters the phonology
  mapping couldn't handle (here, uppercase letters of a proper name); FORM is
  faithful. Not grammaticality notation.
- **Presidential_Apologies** (`Kavalan.xml`, e.g. FORM
  `"taywan tungse"( 台 灣 通 史 )` → PHON `"tajwan tuŋsə"( * * * * )`): one
  PHON `*` per unmapped Chinese character. Expected `add_phonology` behavior.
- **Wikipedias**: mostly the same PHON-placeholder pattern (100+ files,
  expected), **but** ~34 files have `*` in **FORM** tiers that are leftover
  wiki markup (e.g. `Seediq/Angola.xml` `*為預測值 *` footnote marker;
  `Seediq/Kari_mstrung_lupung_ka_Truku_sbiyaw.xml` and `Amis/Paraguay.xml`
  fullwidth `＊` list markers). A source-fidelity cleanup item for the
  Wikipedias cleaning scripts — unrelated to `*(X)`, tracked here so it isn't
  lost.

### 8. No hits anywhere else

All other corpora's greppable raw data, the Montgomery/Wakelin source PDFs,
the HundredPaiwanStories `.docx`, and all other published XML contain no
`*(`/`(*X` patterns. `.py` matches in Glosbe, YeddaPalemeqBlog, NTU_Paiwan_ASR,
Safolu, Wikipedias scripts are code (regexes/globs), not data.

## Recommended remediation (scripts, not hand-edits)

1. **NTUFormosanCorpus** (the only real corruption): split
   `UNGRAMMATICAL_PAREN_RE` handling — `*(X)` ⇒ keep X in FORM + machine-readable
   note; `(*X)` ⇒ drop + note. Fix the nested-paren TRANSL strip. Regenerate
   Rukai Sentences, Kanakanavu Sentences (+ ideally record finding-2 drops).
   NTU is scrape-reproducible in-repo, so this is a `CodeAndDocs/scripts`
   change + re-run.

   **DONE (this branch, 2026-08-10):** `UNGRAMMATICAL_PAREN_RE` replaced by
   `resolve_ungrammatical_parens()` in `utils.py` (`*(X)` → `X`, `(*X)` → ``),
   applied in `parse_sentences.py` and `parse_grammar.py` (including the
   whole-sentence `startswith('*')` skip, so `*(X)` no longer risks dropping
   the sentence in grammar files); `extract_notes()` made nesting-aware
   (fixes finding 3's stray `.)`). Covered by
   `tests/corpora/test_ntu_starred_parens.py` (TDD; 12 tests) and verified
   end-to-end: rerunning `parse_sentences.py`/`parse_grammar.py` on the real
   corpus restores `malra` (S FORM + W element) in Rukai
   `20200529-FW-Lixing-2_S_2`, leaves zero `*(`/`(*` in any regenerated FORM,
   and reproduces the existing correct `(*kara)`/TRANSL-notes behavior.
   Published `XML/` intentionally NOT regenerated here — the maintainer's
   upcoming full pipeline rerun will pick the fix up.
2. **Song-Kanakanavu-Grammar**: add a `*(`-guard to `xml_word_form()` /
   `morpheme_form()` so a future obligatory-type instance fails loudly instead
   of being deleted.
3. **Wikipedias**: separate ticket to strip wiki `*`/`＊` markup remnants from
   ~34 FORM tiers.
4. Consider a project-level QC rule (validate_text) flagging `*(` / `(*` in any
   raw-vs-XML diff or in published FORM, so future scrapes can't silently eat
   grammaticality notation (same family as the Shih-Rukai-Adverbial `*(=aku)`
   dev-repo finding).
