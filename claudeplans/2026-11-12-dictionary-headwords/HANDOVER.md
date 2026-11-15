# Dictionary headwords (Safolu + Virginia Fey): handover

Status on 2026-11-15: **waiting for the maintainer's answers on the round 1 decision page.**
No corpus has been changed. Nothing is built or published. Everything in this folder is
draft analysis to resume from.

- Decision page (18 cards): https://claude.ai/artifact/1N7xc3PCVuYYsmyynos5S4 (v2)
- Answers when this was written: **none**. Both db collections, `answers` and `meta`, were empty
  (checked with ArtifactData `list` on 2026-11-15).
- Base used for all counts: `origin/main` at `525ad4932`.

## 1. What the maintainer asked (verbatim)

> "Apparently when we processed Safolu, we pulled just the example sentences and didn't pull
> headword entries (which would be a separate XML). Please do. Also check Virginia_Fey_Dictionary
> and Blust-Thao-Dictionary and Glosbe and Cuerq-Pourrias, for the same purposes."

> ""Layout follows POL-025. " <-- see if you can distinguish between one word with multiple senses
> and actual homophones, based on structure of the source."

The second message objected to the first version of the page, which presented
"all same-spelled entries become one S" as settled. It is now an open question, asked on
the cards `s-homophones` and `f-homophones`.

Neither message approves executing anything. Per the project rule "plan → discuss → execute",
build only after the cards are answered **and** the answers are quoted back.

## 2. Findings

### Which of the five corpora are missing headwords

| Corpus | Headwords published? | Evidence |
|---|---|---|
| Safolu-Amis-Dictionary | **No** | Only `amis_safolu_examples.xml` (50,322 example S). Upstream g0v/amis-moedict `docs/s` at the examples' snapshot (e7c6976) has 42,273 headwords with 57,361 definitions. The committed snapshot keeps only the 45,740 definitions that have an example (36,268 headwords). |
| Virginia_Fey_Dictionary | **No** | Only `Amis.xml` (2,042 S from the sheet's example cells). The sheet's 詞條 (headword) column holds 4,848 headwords with 6,115 English+Chinese senses, none published. |
| Blust-Thao-Dictionary | Yes | 7,248 entry S in 8 `blust_2003_thao_entries_*.xml`. The builder emits 11,485, and the corpus-wide dedup (build step 8) removes the rest. I did **not** re-run Blust's build to confirm the exact count removed. |
| Glosbe | Yes | 1,156 lexical S in 4 `*_lexical.xml`. The crawl found 0 →zh headword candidates. The live site can't be reached from the container, so that could not be checked. |
| Cuerq-Pourrias | Yes | 23,316 headword entries. |

### Safolu draft (`draft/safolu_headwords.py`)

| Item | Value |
|---|---|
| Output S | 42,363, then 42,354 after `remove_duplicate_sentences.py` |
| Headwords removed by dedup (9) | 'acefolay a fu'is, kacudu, katacumuli, mapulusi, pusi, pusian, safun, ucyaya, unsing |
| Validators | 0 HARD. SOFT: V122 984, V133 24, V116 27 |
| Tokens added | +42,637, on a current 249,176 |
| Upstream version difference (e7c6976 vs 4cb82539d) | 72 headwords added; 383 headwords with changed definitions (213 lost senses, 54 gained, 106 edited text, 10 changed only in a parenthetical) |
| Removed senses | 216 removed senses appear nowhere in the later dictionary (e.g. kalatawan) |

That version difference is card `s-version`.

### Fey draft (`draft/fey_headwords.py`)

| Item | Value |
|---|---|
| Output S | 4,704 (144 headwords whose only sense is a cross-reference are dropped) |
| Validators | 0 HARD. SOFT: V122 2,248, V133 8 |
| Tokens added | +4,709, on a current 9,199 |
| Senses marked (FIXME) | 6 |

### Homophones vs one word with several senses

**Safolu.** The source is the printed dictionary text at miaoski/amis-safolu `dict/*.txt`, commit f512d5b.

- **①②③ inside one printed entry reliably marks one word.**
  - Example: `'aca ① 只有 ② 即使…也… ③ 又，再`
- **Separately printed entries with the same spelling are not reliable.** They can be:
  - real homophones:
    - deko 袖手 / 泥蟹
    - ngangiw 蛔蟲 / 月桃芯
    - pakayakayay 造橋 / 做媒
    - ama 祖母 / 爸爸
  - reprints in section 23 (the `'` section) and section 24 (the loanwords appendix);
  - the same word printed twice in one section:
    - maamootay, twice in section 10
    - 36 groups word for word identical;
  - senses split into entries: 'adingo is ①影子②靈魂 in section 01 but two entries in section 23.
- **The upstream converter does not preserve the distinction.**
  - It makes one `h` per printed paragraph and merges all same-spelled entries into one file.
  - Its parse produces fragments (micekos has 7 `h`).
- **Counts:**
  - 882 headwords are printed as 2+ differing entries in one section.
  - 326 align cleanly with upstream `h`; 556 need a check.
  - One S per upstream `h` would give 43,626 S (1,087 headwords split).
- **Shared wording does not separate the cases**, in either direction:
  - pinawnawan: shared wording, different words;
  - macerar: no shared wording, one word.

**Fey.** There is no structural signal. No numbering, no homograph mark, and no repeated headwords; `ha` mixes three meanings in one entry. Capitalised names are already separate headwords. 1,024 headwords have 2+ senses.

## 3. The 18 open cards

Recommended option in **bold**. Answers go to db collection `answers`, one doc per card id:
`{choice, note, at}`. The "round done" flag is doc `meta/round1`: `{done, note, at}`.

| Card id | Question (short) | Options (recommended in bold) | Items shown |
|---|---|---|---|
| s-homophones | Words spelled alike but printed as separate entries: separate S? | **Follow the book's entries, check the rest** / One S per spelling / One S per upstream entry (h) | 26 |
| s-version | Which version of the definitions | Base snapshot (e7c6976) / Editors' version (4cb82539d) / **Keep both** | 377 |
| s-xref | Definition that is only 同 X / 參見 X | **Leave it out** / Put it in FORM notes / Publish as a translation | 34 |
| s-label | Definition that is only a bracketed label | **Put it in FORM notes** / Leave it out / Publish as a translation | 164 |
| s-nochinese | Definition with no Chinese in it | **Put it in FORM notes** / Leave it out / Publish as a translation | 136 |
| s-embedded | Example sentence sitting in the definition field | **Move to the examples file** / Leave it out / Keep as a translation | 104 |
| s-heading | Senses that are a heading ending in a colon | **Leave them out** / Keep them | 23 |
| s-affix | Affix and circumfix entries | **Leave them out** / Publish them | 41 |
| s-nosense | Headwords with no definition | **Leave them out** / Publish with no translation | 12 |
| s-stemtag | Stem and reduplication tag | **Put them in FORM notes** / Don't publish them | 10 |
| s-synrel | Synonym and related-word links | **Don't publish them** / Put them in FORM notes | 13 |
| s-borrow | Borrowing labels inside definitions | **Keep it in the translation** / Move it to TRANSL notes | 20 |
| f-homophones | Fey: keep one S per headword? | **One S per headword** / Review the 1,024 multi-sense headwords | 8 |
| f-split | Senses that list several glosses | **Split, keep the original in notes** / Keep each sense whole | 30 |
| f-xref | Headwords whose only sense is a cross-reference | **Leave them out** / Publish, cross-reference in notes / Publish the cross-reference as the translation | 144 |
| f-fixme | Chinese senses marked (FIXME) | **Remove the marker, say so in notes** / Drop those Chinese senses / Keep (FIXME) in the text | 6 |
| f-affix | Prefix entries | **Leave them out** / Publish them | 8 |
| f-see | The see-also column (參見) | **Don't publish them** / Put them in FORM notes | 15 |

**Choices that create a follow-up round before building:**

- `s-homophones` = "Follow the book's entries" needs a review page for the 556 Safolu headwords, grouped by kind (reprint, repeat, split senses, real homophones).
- `f-homophones` = "Review" needs a review page for the 1,024 Fey headwords.
- `s-embedded` = "Move to the examples file" changes `amis_safolu_examples.xml`, which is published, so the change must be shown before it is made.

## 4. How to resume

1. **Read the answers.** Use ArtifactData `list` on collection `answers`, then on `meta`, for the URL above. Quote each answer back to the maintainer, and log it in `claudeplans/sweep-qa-decision-log.md` with the maintainer's own words (a choice on a button is the answer to that card only).
2. **Recreate the working directory.** The draft scripts expect one directory `WORK` laid out like the original session scratchpad:

```bash
WORK=/path/to/scratch            # any empty directory
FB=/workspace/FormosanBank       # the shared checkout (used only to add worktrees)
# This folder lives only on branch plans/dictionary-headwords-handover, which is not meant to be merged
# (maintainer, 2026-11-11: "Let's delete old Claude plans and other detritus of interacting with agents.").
git -C $FB fetch origin plans/dictionary-headwords-handover
git -C $FB worktree add --detach $WORK/handover origin/plans/dictionary-headwords-handover
D=$WORK/handover/claudeplans/2026-11-12-dictionary-headwords

# FormosanBank at the commit the counts were made on (read-only)
git -C $FB worktree add --detach $WORK/main-ro 525ad4932

# Upstream Safolu JSON at the two commits
git clone --filter=blob:none https://github.com/g0v/amis-moedict.git $WORK/moedict
mkdir -p $WORK/src/e7c6976 $WORK/src/4cb8
git -C $WORK/moedict archive e7c6976a0766e9b0aeb7083e2c06db60f5485252 docs/s | tar x -C $WORK/src/e7c6976
git -C $WORK/moedict archive 4cb82539d7e51e7211e262d4dbaecaa41a772b2f docs/s | tar x -C $WORK/src/4cb8
# expect 42,278 and 42,350 files
ls $WORK/src/e7c6976/docs/s | wc -l; ls $WORK/src/4cb8/docs/s | wc -l

# "Keep both" pin: 4cb8 overlaid with e7c6976 (42,350 files + any only in e7c6976)
mkdir -p $WORK/src/optA/docs && cp -r $WORK/src/4cb8/docs/s $WORK/src/optA/docs/ && cp -r $WORK/src/e7c6976/docs/s/. $WORK/src/optA/docs/s/

# The printed dictionary text (for the homophone analysis)
git clone https://github.com/miaoski/amis-safolu.git $WORK/src/printed/amis-safolu
git -C $WORK/src/printed/amis-safolu checkout f512d5ba0d08f81b26093a9b7b4a85acac760a30

# The drafts
cp -r $D/draft $WORK/draft
cp $D/survey/*.py $WORK/
```

3. **Commands as run in the original session.** `$WORK` stands for the session scratchpad. Run them from `$WORK/draft`, with `-I` because the inputs are downloaded data.

```bash
# Safolu headword drafts, one per version (log_*.json are their summaries)
python3 -I safolu_headwords.py --base $WORK/src/e7c6976/docs/s --pin $WORK/src/e7c6976/docs/s \
  --pin-commit e7c6976a0766e9b0aeb7083e2c06db60f5485252 \
  --out $WORK/draft/out_e7c6976/XML/Amis/Safolu/amis_safolu_headwords.xml --log $WORK/draft/log_e7c6976.json
#   (the same with 4cb8 / 4cb82539d7e51e7211e262d4dbaecaa41a772b2f in place of e7c6976 gives out_4cb8 + log_4cb8.json)
python3 -I safolu_headwords.py --base $WORK/src/e7c6976/docs/s --pin $WORK/src/optA/docs/s \
  --pin-commit "e7c6976a0766e9b0aeb7083e2c06db60f5485252 (definitions) with the 72 headwords added by 4cb82539d7e51e7211e262d4dbaecaa41a772b2f" \
  --out $WORK/draft/out_optA/XML/Amis/Safolu/amis_safolu_headwords.xml
#   switches for the card options: --xref --label --nochinese {drop,notes,translation}; --affix {keep,drop};
#   --stem-tag {none,notes}; --syn-rel {none,notes}; --keep-senseless

# Fey headword drafts
python3 -I fey_headwords.py --sheet $WORK/main-ro/Corpora/Virginia_Fey_Dictionary/CodeAndDocs/source/virginia_fey_source.csv \
  --split keep --out $WORK/draft/fey_keep/XML/Amis/Amis_headwords.xml
#   switches: --split {keep,split}; --xref {drop,translation}; --affix {keep,drop}; --see-also {none,notes}

# Survey scripts (one argument: a docs/s directory; pindiff takes two)
python3 -I $WORK/inventory.py $WORK/src/e7c6976/docs/s
python3 -I $WORK/fsurvey.py $WORK/src/e7c6976/docs/s
python3 -I $WORK/pindiff.py $WORK/src/e7c6976/docs/s $WORK/src/4cb8/docs/s
python3 -I $WORK/safolu_cases.py $WORK/src/e7c6976/docs/s

# Card data and the decision page (each takes WORK as its only argument)
python3 -I cards_data.py $WORK          # -> draft/cards.json (not committed: 3.3 MB, regenerable)
python3 -I build_page_data.py $WORK     # -> draft/page_cards.json
python3 -I homophones.py $WORK          # -> draft/homophone_examples.json
python3 -I homophones2.py $WORK         # -> draft/homophone_groups.json
python3 -I homophone_cards.py $WORK     # -> draft/homophone_cards.json
python3 -I assemble_page.py $WORK       # -> draft/dictionary-headwords-round1.html
```

`assemble_page.py` was written at handover time from the inline commands that built v2. On the committed inputs it reproduces the published page byte for byte: SHA-256 `0f836a8bf88165d19d096f2a55008a49b5eed2a21c1755449b130ad334bec1d4` for both. Everything else listed above was re-run only in the original session, not after copying here.

Known draft defects to fix in the real build:

- `fey_headwords.py` writes FORM notes `"source sheet line N"`. Drop them.
- The Fey TEXT has **no glottocode** because the Fey examples TEXT has none. Don't add one.

## 5. Build plan after the answers (not approved yet)

One branch and one PR for both corpora, touching **only** `Corpora/Safolu-Amis-Dictionary/` and `Corpora/Virginia_Fey_Dictionary/`.

**Safolu**

- Commit a headword snapshot as jsonl.gz plus a manifest naming the upstream commits.
- Move the headword generator into `CodeAndDocs/`.
- Extend `generate_xml.sh`.
- Update the README.
- Output: `XML/Amis/Safolu/amis_safolu_headwords.xml`.
  - TEXT `id="amis_safolu_headwords"`.
  - Citation, BibTeX, copyright (CC BY-NC-SA 3.0 TW), xml:lang `ami`, glottocode `amis1246` and dialect `Coastal` are the same as the examples file.
- If `s-homophones` is "follow the book", also commit the printed text it was aligned against, or an alignment ledger.

**Fey**

- Move the headword generator, which reads the committed sheet, into `CodeAndDocs/`.
- Extend `generate_xml.sh`.
- Update the README.
- TEXT `id="VirginiaFeyDictionary_headwords"`, dialect `Xiuguluan`, CC BY-NC 3.0.

**Shared pipeline**, as used by both corpora's existing builds:

- `clean_xml.py`
- `standardize.py` with `Amis_Church_113.tsv`: column `Coastal` for Safolu, `Xiuguluan` for Fey.
- `add_phonology.py`: `--orthography Church` for Safolu, `Ortho113` for Fey.
- `remove_duplicate_sentences.py by_path --apply`
- Validators: `validate_xml`, `validate_text`, `validate_glosses`, each with `--csv` and `--no-exit-on-hard`.

Then one build each, `tests/corpora`, and push and PR commands for the maintainer. The maintainer pushes; `gh` does not run in the container.

## 6. Files in this folder

| Path | What it is |
|---|---|
| `draft/safolu_headwords.py` | Safolu headword generator (draft); each open card is a switch |
| `draft/fey_headwords.py` | Fey headword generator (draft) |
| `draft/cards_data.py`, `draft/build_page_data.py` | Build the per-card example rows and per-option renderings |
| `draft/homophones.py`, `draft/homophones2.py` | Printed-text vs upstream `h` comparison; per-section grouping |
| `draft/homophone_cards.py` | Builds the two homophone cards |
| `draft/assemble_page.py` | Assembles the decision page from template + card data |
| `draft/page_template.html` | Page template (db: `answers/<card id>`, `meta/round1`) |
| `draft/dictionary-headwords-round1.html` | The page exactly as published (v2) |
| `draft/page_cards.json`, `draft/homophone_cards.json` | Card data embedded in the page |
| `draft/homophone_groups.json`, `draft/homophone_examples.json` | The 882 printed groups and the examples drawn from them |
| `draft/log_e7c6976.json`, `draft/log_4cb8.json` | Counts from the two draft Safolu builds |
| `survey/*.py` | First-pass survey scripts (inventory, field survey, version diff, edge cases) |
| `decision-log-entry.md` | Copy of this item's entry in `claudeplans/sweep-qa-decision-log.md` as of 2026-11-15 |

When the corpora are built and merged, the real build scripts belong in each corpus's `CodeAndDocs/`. This branch can then be deleted.

Not committed, because they're regenerable or large: the upstream JSON exports (178 MB each), the printed-text clone (262 MB), the draft XML outputs, and `cards.json`.
