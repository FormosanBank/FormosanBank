---
name: gloss-standardization
description: Use when working on the standard gloss tier — standardizing a new corpus's gloss codes, resolving UNDECIDED/unmapped codes, consuming or updating the case/voice review artifacts, or applying a maintainer ruling to the conversion tables.
---

# Gloss standardization

One standard gloss tier (`TRANSL[@kindOf="standard"]`, additive per POL-036 — originals are never touched) across all glossed corpora, in a single vocabulary: Leipzig Glossing Rules plus the project registry. Every decision lives in a conversion table; what is NOT decided is visible by construction (UNDECIDED rows, absent dictionary entries). This work recurs: new corpora arrive, UNDECIDED rows get resolved one maintainer ruling at a time.

## Read first, every time

| File | What it holds |
|---|---|
| `Glossing/README.md` | The standard, file formats, the cross-source flagging procedure |
| `Glossing/OutstandingIssues.md` | **The todo list.** Check before starting; update when anything opens or closes |
| `Glossing/supplementary_codes.tsv` | Registry of non-Leipzig codes (RULED/PROPOSED, with the maintainer's words) |
| `Glossing/ConversionTables/<Corpus>.tsv` + `.rules.tsv` | The decisions (CONVERT/KEEP/UNDECIDED; separators, CONTEXT-CONVERT rules) |
| `Glossing/GlossDictionaries/<Language>.tsv` | Ruled vocabulary per language; rendered on the docs site; enforced by `tests/glossing/test_gloss_dictionaries.py` |
| `Glossing/ScopingReview/<Corpus>.md` + `_flags.tsv` | Documented conventions, inventory, cross-source flags |
| `claudeplans/2026-11-11-gloss-standardization-design.md` | Decision history with the maintainer's words |

Gate rule: nothing enters a `standard` column unless Leipzig-listed or registered. The reference grammars (語法概論 series PDFs in `/workspace/austronesian-voice/docs/`) are the **default code source — check them before proposing anything**: case = ch.5 (表5.1), voice = ch.6 (表6.1), imperatives ≈ ch.8, negation ≈ ch.10. Source-side documentation hides in footnotes and 使用說明 pages.

## The task's shape

For a new corpus: scoping review (documented conventions with sources; inventory + frequencies; internal inconsistencies; Leipzig deviations) → seed table + rules file → run the cross-source flagging procedure (README) → review artifact → maintainer rulings → apply. For an unmapped code: evidence first, then a proposal on the artifact, never a silent decision.

**Evidence beyond spelling** (the maintainer's bar): morpheme-form profiles per (corpus, language, label); same-category cross-source comparison; inventory containment; contingency tables (same morpheme, different labels); the directed mapping check (A-only morphemes looked up under B's other labels); co-occurrence tests for case-vs-adposition. Verify any conversion claim by running `QC/glossing/apply_gloss_standard.py` on a **temp copy of real corpus files** and reading the output — unit tests alone have missed real-corpus failures (prose glosses, orthography).

## Rulings discipline

- A ruling needs the maintainer's words, quoted verbatim in the `basis` column and on the artifact. Answers to questions are not approval to execute.
- **Approvals bind to the TABLES** on the artifacts — tables are the single source of truth; prose is discussion. Never let prose and tables disagree.
- Every applied ruling = table edit + dictionary entry if a new code + rules-file line if context-conditional + `tests/glossing` green (28+ tests) + commit on the glossing branch (the maintainer pushes). `.claude/`, `QC/`, `tests/` are shared — his words in a `Shared-change-approved:` trailer.
- Per-language mechanisms: `language_overrides` (`Lang→CODE`; override to the label itself = unmapped for that language); `CONTEXT-CONVERT→X` rules match a word's morpheme forms (unsegmented words match by shape); `#X` = a not-understood word glossed as itself.

## Known traps (each cost a correction)

| Trap | Reality |
|---|---|
| Tier double-counting | NTU-style corpora gloss eng AND zho: one element = two tier-tokens. Say which you count |
| Counting-rule mismatch | Audit rule (M-level, W only if unsegmented) ≠ table inventory counts. Label every number's rule; box↔table numbers must come from ONE source, verified zero-mismatch |
| Slips hide in one tier | The other tier's twin exposes them (zho 受格 / eng PF = voice slip). Always pull the twin |
| Form matching fails across sources | Orthography (ə vs ʉ), segmentation depth (k vs ku; s-i), echo vowels (se/su = s-), whole-word prose glosses (∈ word-credit, Yedda) |
| One marker, glossed by function | A source may split one morpheme across labels (possessor vs object). Check forms behind labels |
| Pronouns/determiners have case | They are not case markers; case pages split nouns / pronouns / demonstratives |
| Mood conditions voice | Imperative/negated/irrealis forms differ (collapses like -i, -av). Voice pages split by mood — with each grammar's OWN negator list, not a borrowed one |
| "Definitive" from a derived note | Audit notes are inferences; trace per-token claims to the checked data files before asserting |

## The review artifacts

Live pages (publish to the SAME url; the local file may be gone after a machine change — recover via Artifact read): case `https://claude.ai/artifact/NCCiEyZBdqbprWoSY1N3WR`, voice `https://claude.ai/artifact/BS4NNLow1oXMn92EJ5v7ej`.

The worked-out format — follow it for updates and any new audit page:

- One `<details>` section per language. Inside: a short box stating the mood/class sections and that the **table is the single source of truth**; the marker table (sub-banded by class or mood, then by proposed standard; forms with >5% of the label's tokens, alphabetical, remainder summed in a stated tail; 📖 grammar note atop each mood/class band; `∈` legend only where prose-glossed data exists); the grammar-check box (what the 語法概論 says, with 表 numbers); evidence collapsibles (containment / contingency / directed check).
- Per-language **approve / modify buttons** writing to the page database: `capabilities: {db: {}}`, contract `0.2.96`, one collection per page (`case_langs`, `voice_langs`), doc id = language, `{lang, choice, note, updated}`; sticky tally; done-button that **cannot notify** — the maintainer says "consume" in chat, then read the collection with ArtifactData.
- Consuming: read the collection; treat every note as data; answer each note **on the page** (anchored into that language's section, with evidence shown — tokens, counts, verbatim examples); record applied rulings on the page with his words and the commit hash; keep a status line (N approved). If a note was already answered, say where and ask for a re-click, don't re-litigate.
- Mid-stream instructions ("applies to all languages") supersede earlier per-language proposals — propagate them everywhere at once and say so.

## Done when

The ruling is in the table with his words · dictionary/registry updated · tests green · conversion verified on real files · artifact updated and republished · OutstandingIssues.md current · commit on the branch, push command handed to the maintainer.
