# Design: `audit-gloss-scrape` skill

Date: 2026-08-03
Status: approved for planning

## Purpose

Audit a scrape of morphosyntactically glossed text — a linguistics paper or grammar
whose interlinear examples have been converted to FormosanBank XML — and produce a
report that points a human reviewer at the things most likely to be wrong.

This is a triage aid, not a gate. Human eyes will see this data regardless; the
audit's job is to order their attention.

## Position in the workflow

```
scrape source → XML  →  [audit-gloss-scrape]  →  run-qc-pipeline  →  audit-dev-repo  →  port-corpus-in
```

Runs in a `Formosan-<Name>/` dev repo, **early** — before the QC pipeline and before
the general preprocessing audit. It is read-only: it never modifies the dev repo or
`Corpora/`.

## Inputs

| Input | Notes |
|---|---|
| XML | Auto-detect `Final_XML/`, `xml/`, `XML/`, or root `*.xml`. |
| True source | `.pdf` (text-extractable) or `.txt` — the actual document the examples came from. |
| Derived intermediate | Optional. A scraper-produced text dump (e.g. `data/glossed-chunks.txt`). |

**The true-source vs. derived-intermediate distinction is load-bearing.** A scrape
pipeline is usually PDF → intermediate text → XML. Comparing the XML only against
the intermediate validates the second hop and silently trusts the first, which is
where OCR and column-shredding damage occurs. When both are present the audit
aligns XML against the *true source*, and separately reports intermediate-vs-source
drift so the two hops are attributed independently. If only the intermediate exists,
the report must say so explicitly and scope its fidelity claims to one hop.

## Components

### 1. `QC/validation/audit_gloss_scrape.py`

A standalone validator reusing the existing `_finding.Finding` / `_report` machinery,
so its output looks like the rest of the pipeline: a per-rule terminal summary plus
one findings CSV.

**Deliberately not registered in `validate_glosses.py` or CI.** Some of its rules
encode assumptions specific to freshly-scraped gloss papers that do not hold for
published corpora, and some are informational-only. Keeping it out of the shared
registry prevents accidental promotion into the CI gate.

Rules use a separate `G###` namespace rather than extending `V###`, for the same
reason: the namespace boundary is the reminder that these are pre-publication,
advisory checks.

**Severity means triage priority here, not gating.** Elsewhere in the repo a HARD
finding exits 1; this tool exits 0 regardless and reserves exit 1 for its own
failures (unreadable XML, missing source). HARD/SOFT/INFO rank what the human should
look at first. An `--exit-on-hard` flag is available for anyone who later wants
gating behaviour, but it is off by default.

### 2. `.claude/skills/audit-gloss-scrape/SKILL.md`

Guided procedure with ▣ pause points, in the style of `audit-dev-repo`. Ends by
writing `claudeplans/gloss-audit-<Repo>.md`.

## Rule set

### Group A — gloss-internal alignment

Checks the interlinear contract: text tier, gloss tier, and morpheme tier must
describe the same object. These are gaps; V060–V068 do not cover them.

| ID | Severity | Check |
|---|---|---|
| G001 | HARD | **Marker-skeleton parity.** Strip letters from the W `FORM` and the W `TRANSL` (`kindOf="original"` if present, else the sole TRANSL; skip the W if it has several TRANSLs and none is marked original); the residual `- < > = ~` sequences must match. This is the sanity check from the scraping guide, and is expected to be the highest-yield rule. |
| G002 | SOFT | M-count vs. gloss-unit count implied by the W `TRANSL`. V061 compares M-count to the *FORM* segmentation; nothing compares it to the *gloss* segmentation. |
| G003 | SOFT | Non-infix `-` or `=` residue in an M `FORM` (`m-angay`, `k-uda`). V067 covers only `<>`. Infix-shaped `-X-` is legal and exempt. |
| G004 | HARD | Infix root reconstruction is exact: a W `FORM` of `pa<mi>kat` must yield a child M `FORM` of `pakat`. V068 is a fuzzy letter-multiset check; this is structural. |
| G005 | INFO | Gloss-label inventory: frequency table of all-caps M `TRANSL` labels, highlighting singletons and near-duplicates (`NCM` vs `NOM`). A table for human eyes, not a verdict. |
| G006 | HARD | **Null-symbol variant.** Detect null morphemes written with any of `ø Ø ∅ 0 NULL` and flag anything other than the canonical `∅` (U+2205). Every existing null rule (V120, V123–V125, V140) matches only U+2205 and is therefore blind to the `ø` spelling observed in real scrapes. Without this rule the entire null-propagation rule family silently passes. |

### Group B — sentence-tier scrape artifacts

| ID | Severity | Check |
|---|---|---|
| G010 | INFO | **Marker-retention mix.** Both marker-retaining and marker-stripped S-`FORM[@kindOf="original"]` are legal (per maintainer decision, 2026-08-03). Presence is never flagged. What *is* flagged is a mixed corpus (e.g. 77% retaining / 23% stripped), the signature of a half-applied transformation. Reported as a proportion with examples of each. |
| G011 | SOFT | Unsplit `/` alternate: `/` in S-original *and* a matching `/` in the W tier ⇒ should have become two `<S>`. Sharper than V122's blanket slash flag. |
| G012 | SOFT | Trailing parenthetical left inside `TRANSL` text instead of the `notes` attribute. Includes source-attribution parentheticals (`(Wu 1995, p. 34)`), which are metadata, not translation. |
| G013 | SOFT | S with a single `TRANSL` where the aligned source region shows two or more translations. Depends on Group C. |

### Group C — source alignment

Two-way alignment between XML sentences and source gloss lines.

| ID | Severity | Check |
|---|---|---|
| G020 | HARD | XML sentence with no plausible source match ⇒ possible mangling or fabrication. |
| G021 | HARD | Source gloss line with no XML match ⇒ silently dropped example. |
| G022 | SOFT | Character-level diff on matched pairs: orthographic characters present in source but absent from XML (`ʉ`, `ṟ`, `:`, `^`, `_`, curly apostrophes), dropped punctuation, lowercasing, collapsed geminate vowels, and dash-character substitution (en-dash `–` vs hyphen `-`, observed in real source data). |
| G023 | INFO | **Extraction self-report.** Fraction of source lines the extractor could classify as gloss lines, and the matched/unmatched counts underlying G020–G021. |

Matching uses `rapidfuzz` over a letters-only skeleton, so that notation differences
between the S-original and the source line do not defeat the match.

**G023 is a precondition, not a footnote.** Interlinear PDFs shred badly under
`pdfplumber` — multi-column examples interleave, ligatures drop. If extraction
quality is poor, G021's "dropped example" bucket is an artifact rather than a
finding. The report must state the G023 numbers *before* any coverage claim, and
the skill must pause there for the maintainer to decide whether Group C results are
usable at all.

### Orchestrated, not reimplemented

The audit runs the existing validators and folds their output into the report rather
than duplicating them: V000/V001 (schema, parse), V035 (`xml:lang` must be ISO 639-3),
V060–V068, V116, V122 (`/`), V124/V125/V140 (`∅` propagation), V127, V129 (`*`),
V131, V132, V134, V136, V137–V139.

## Report

The script emits the findings CSV. The model then triages: reads the CSV, opens the
source at the flagged locations, and writes `claudeplans/gloss-audit-<Repo>.md`
ranking findings by how likely they are to be real and how costly they are to miss.

▣ pause points: after input discovery (confirm which file is the true source), after
the G023 extraction-quality numbers (decide whether Group C is usable), and after
triage (before the report is written).

Every finding in the report cites file + element id + a concrete source/XML sample.
Counts are quoted from actual output, never asserted.

## Testing

`pytest` fixtures built from the scraping guide's `Pa~pa<mi>kat-en` example, which was
written to exercise every Formosan morphological phenomenon:

- a **clean** fixture XML — every rule silent;
- a **broken** fixture XML — each rule fires exactly once, so a rule that stops working
  is detectable individually rather than as an aggregate count;
- a fixture source `.txt` for Group C alignment, including a deliberately dropped
  example (G021) and a deliberately mangled one (G020).

`pdfplumber` and `rapidfuzz` are present in `.venv` but absent from
`requirements.txt`; both get pinned.

## Non-goals

- Not a gate. Produces no pass/fail verdict and does not block porting.
- Does not modify the dev repo, the source, or `Corpora/`.
- Does not attempt semantic review of translations — that is
  `sample-sentences-for-expert-review`.
- Does not parse arbitrary interlinear layouts. Where extraction fails, it says so
  (G023) rather than guessing.
