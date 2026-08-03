---
name: audit-gloss-scrape
description: Audit a fresh scrape of morphosyntactically glossed text (a linguistics paper or grammar whose interlinear examples became FormosanBank XML) and produce a report ranking what a human should check. Aligns the XML against the source PDF/TXT for dropped examples, lost orthography, and text-vs-gloss misalignment. Use early in a dev repo's life, before run-qc-pipeline and audit-dev-repo.
---

# audit-gloss-scrape

Triage aid for glossed-text scrapes. Human eyes will see this data regardless;
this skill's job is to **order their attention**, not to gate anything.

Runs in a `Formosan-<Name>/` dev repo, **before** `run-qc-pipeline` and
`audit-dev-repo`. **Read-only** — never modify the dev repo, the source, or
`Corpora/`.

## Step 0 — Orientation (REQUIRED)

Read `FormosanBank/CLAUDE.md` (auto-loaded) for the XML schema and the
`original` vs `standard` distinction, then
`docs/superpowers/specs/2026-08-03-audit-gloss-scrape-design.md` for what each
G rule means and why it exists.

Two conventions that override the scraping guide students are given:

1. **M-tier notation follows the repo, not the guide.** The guide says an M
   FORM is "just the letters"; in fact infix Ms keep `-X-` (V067) and clitic
   Ms keep `=` (V066). Do not report those as defects.
2. **Markers in S-`FORM[@kindOf="original"]` are legal.** Both the segmented
   and unsegmented style are acceptable (maintainer decision, 2026-08-03).
   Only an inconsistent *mix* is worth reporting (G010).

## Inputs (gather via AskUserQuestion if missing)

- `repo_path` — the dev repo, e.g. `../Formosan-<Name>/`. Run from
  `FormosanBank` with the dev repo added via `--add-dir`.
- `source` — the **true source** document. Auto-discovery prefers a PDF over a
  `.txt`, deliberately: a `.txt` beside it is usually the scraper's own
  intermediate, and auditing against it validates only the second hop of
  `PDF → text → XML` while silently trusting the first — which is exactly
  where OCR and column-shredding damage happens.

## Procedure (pause at each ▣)

### 1. Discover and confirm the inputs

```bash
python QC/validation/audit_gloss_scrape.py --repo ../Formosan-<Name> --csv logs/gloss-audit.csv
```

The script prints its source candidates and marks the one it chose.

▣ Confirm with the maintainer which file is the **true source** versus a
scraper intermediate. If both exist, note that the intermediate is available
for attributing damage to a specific hop.

### 2. Judge extraction quality BEFORE reading any finding

Find the `G023` row in the CSV. It reports the extractor, line count,
candidate count, detected example regions, and how many XML sentences matched.

**This gates Group C.** Interlinear PDFs shred badly under text extraction;
when they do, `G021` ("source example missing from XML") is an artifact of the
extractor rather than a fact about the corpus. If the matched fraction is low,
say so plainly and either fall back to `--no-source` or hand-check a sample
against the PDF instead of quoting coverage numbers.

▣ Present the G023 numbers and get the maintainer's call on whether Group C
results are usable.

### 3. Run the existing validators too

The audit covers gaps, not the whole surface. Run these **as their own
scripts** — do not wrap them or paraphrase their output:

```bash
python QC/validation/validate_xml.py     by_path --path <xml> --csv logs/v-xml.csv
python QC/validation/validate_text.py    by_path --path <xml> --csv logs/v-text.csv
python QC/validation/validate_glosses.py by_path --path <xml> --csv logs/v-gloss.csv
```

These own `*` residue (V129), slashes (V122), `∅` propagation (V124/V125/V140),
ISO 639-3 codes (V035), footnote leaks (V137–V139) and the V060–V068 gloss
rules. Note that the `∅` rules are **blind to a corpus that spells null `ø`** —
if `G006` fired, treat every V120/V123–V125/V140 pass as unverified until the
null symbol is normalised.

### 4. Triage the findings

Read the CSV. For each rule that fired, open the XML at the cited ids **and**
the source at the cited lines. Rank by:

- **Structural damage first** — `G001` (text/gloss disagree on segmentation)
  and `G004` (infix root not rejoined) invalidate the M tier beneath them.
- **Silent data loss next** — `G021` (dropped example), `G022` (lost
  orthographic characters), `G020` (sentence not in the source).
- **Systematic slips next** — `G006` (null spelling), `G010` (half-applied
  transformation), `G005` (label typos). These are usually one fix for many
  rows.
- **Cosmetic last** — `G012`, `G007`.

Distinguish *what the script flagged* from *what you verified by opening the
file*. A finding you have not opened is a candidate, not a finding.

▣ Present the ranked triage with concrete samples; get the maintainer's call
on each class before writing anything.

### 5. Write the report

Only after sign-off, write `claudeplans/gloss-audit-<Repo>.md`:

- The G023 extraction numbers and what they license you to claim.
- Findings ranked as above, each citing **file + element id + a source/XML
  sample**.
- What the audit did *not* check (Group C skipped, PDF unreadable, rules whose
  preconditions were not met).
- Recommended remediation, in the scrape scripts — not by hand-editing XML.

## Notes

- Quote real output. Counts come from the CSV, not from memory.
- The script exits 0 whatever it finds; severity ranks triage priority only.
  Do not report "the audit passed".
- False positives are expected on `G002`/`G005`/`G010` — they are statistical.
  Say so rather than presenting them as defects.
