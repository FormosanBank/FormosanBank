---
name: student-proofreading-page
description: Build a proofreading artifact on which a student checks a scraped corpus against its source book, card by card (sentence, word-by-word line with glosses, free translations), saving to the page's store or a downloaded file; and later turn the returned file into corrections for the dev repo's build. Use when asked for a review/proofreading/checking page for a Formosan-<Corpus> dev repo, or when a student's review file (or "they've finished") comes back.
---

# student-proofreading-page

The maintainer sends these pages to a student, who checks every card against the
book and emails back the downloaded file. Two parts: **build a page** and
**incorporate a returned review**. Each part pauses for the maintainer.

Files in this folder:

| File | What it does |
|---|---|
| `export_review.py` | dev repo XML + `review/review_config.json` → `review/review_baseline.json` + `review/review_page.html`, plus one image per cited PDF page in `--images-out` |
| `review_page.template.html` | the page; the exporter fills in title, guide and data |
| `apply_review.py` | the student's file (or a dump of the page's store) → `review/review_corrections.tsv` + `review/review_log.tsv` |

Run them with FormosanBank's `.venv/bin/python` (it has lxml and PyMuPDF). Everything they
write goes in the dev repo's `review/` folder, except the page images. Dev repos commit straight to main.

**Every card shows the book.** Maintainer, 2026-11-06: *"Yes, change the skill to always include
screenshots."* The student checks each card against a picture of the page on the card: the example
cut out where it can be found, the whole page otherwise, and a *Show the whole page* button either
way. Without it the student needs the PDF open beside the page; the first seven pages (2026-11-06)
shipped without pictures until he asked *"Otherwise, what is the reviewer checking?"*

Earlier rounds, for reference: Chang Seediq (`Formosan-Seediq-Chang-Reference-Grammar`,
https://claude.ai/artifact/BgZYpZeavuYmdbGwzsguKT) and Chang Kavalan
(`Formosan-Kavalan-Zhang-Reference-Grammar`, https://claude.ai/artifact/Xxz49s7wXG6PKVGTqV9ip9).
Those two used repo-specific exporters; this skill is the generic version, first
used 2026-11-06 on six repos.

## Part 1: build a page

### 1. Policies first

Re-read POLICIES.md POL-012, 016, 017, 018, 024–027, 060 and 061. The guide that
`export_review.py` writes (`guide_html`) is a plain-language summary of them:
one gloss under two words goes in one box (POL-060); no gloss printed means an
empty box (POL-061; the build writes `<UNCLEAR/>`); starred examples are
excluded, never re-starred (POL-016); optional and alternative readings are
separate cards (POL-026/027); `'` is never a quotation mark (POL-018). If a
policy has changed, stop and show the maintainer both texts before building.

### 2. Find the source PDF

On disk first (`find <repo> -iname '*.pdf'`), then in history:
`git -C <repo> log --all --diff-filter=A --name-only --format= | grep -i pdf`.
Restore a history copy with `git cat-file -p <commit>:<path>` to the path the
build expects (grep the build for `Private/`). Before writing, confirm the
destination is ignored (`git check-ignore -v <path>`); one repo's `Private/`
was not ignored, only `Private/source/`. Check the SHA-256 against the hash the
repo records, and report it.

### 3. Compare the print with the XML (pause ▣)

Render two or three example pages (PyMuPDF, ~110 dpi) and read them. Count the
lines the book prints per example (sentence / morpheme line / gloss / translation)
and the tiers the XML holds (`S` FORM, `W` FORM + TRANSL, `S` TRANSL). Don't
trust a README's claim about the source; one said "The source has no W/M tiers"
over a book that prints a gloss line under every example.

▣ If the book prints a line the XML lacks, **stop and ask**. A proofreading page
can't cheaply restore a missing tier, and a student's work on a page that later
gains one is wasted.

### 4. Locators

Every card must say which PDF page to open. If `S/@source` has one, make it
readable with `locators` in the config. If not, write `review/record_info.tsv`
(`record, locator, include`) from the build's own ledgers, and **verify** the
pages by finding each example's text on its page (Debusser: 1,066 of 1,090
confirmed). State in `pdf_note` whether page numbers are PDF or printed pages;
if printed, give the offset and check it is constant.

### 4b. Page images

Add a `page_images` block to the config (keys in the `export_review.py` docstring). The exporter
refuses to run without one.

- `pdf`: the restored PDF from step 2, under the repo's ignored `Private/`.
- `pages`: a regex over the card's readable locator; group 1 is a page number or a range
  (`"printed p\\. ([\\d-]+)"` as written in the JSON), with `offset` when the locator gives printed pages (Tsou: +20).
- `locate`: `"text"` where the PDF has a text layer (check: `sum(1 for p in doc if p.get_text().strip())`).
  The exporter finds the sentence in the page's text, cuts from it to the end of its translation,
  reads two-column pages column by column, and tries the neighbouring pages when the named one
  lacks the sentence (flag `other_page`); a sentence found nowhere shows its whole page (flag
  `not_on_page`). `"none"` for a scanned PDF: whole pages.
- `boxes`: a TSV of cuts (`record, page, x0, y0, x1, y1` as page fractions) where the corpus has
  coordinates of its own but the PDF has no text layer. Sung Seediq's `review/make_record_info.py`
  writes one from the reader's positioned text.

`--images-out` must be outside the dev repo: the images are the book, and the repo keeps the book
out of git. Use the session scratchpad (`<scratchpad>/pages/<corpus>`). At 140 dpi grayscale JPEG
(the default) a page is 50–160 KB and diacritics stay legible (Tsou `ʉ ʔ`).

**Read the cuts.** For each corpus, stack six random cuts into one image and look at them; check
the `not_on_page` and `other_page` counts the exporter prints. First runs found: a 4-"line" fallback
that stopped mid-example (an interlinear row is several PDF lines), a word list cut across both
columns, and a headword matched inside an earlier entry.

### 5. Config, dry run, and reading the flags (pause ▣)

Write `review/review_config.json` (keys in the `export_review.py` docstring),
then dry-run with `--config <scratchpad>/x/review_config.json` so nothing lands
in the repo. For every flag that fires, **read at least five flagged cards** before
trusting it:

- A flag that fires because of how the source is laid out is noise: switch it
  off (`flags_off`, or `check_words_against_sentence: false` where the word line
  is the book's morpheme line, not the sentence respelled).
- A flag that shows a **build defect** goes to the maintainer before the
  student sees the page (Puyuma 2026-11: 132 glottal `'` stripped from word edges
  in 120 sentences).

▣ Show the maintainer the flag counts, a sample of each, and every build defect,
with counts and the full list.

### 6. What the student should leave alone

List the deliberate differences between the XML and the print (character maps
in the build, quote normalization, marks the build drops, lines it ignores) and
put each in `guide_items`. Include only what you saw on a page image or in the
build code. A note the scrape left on most cards (the exporter prints these) is
corpus-wide, so it belongs in the guide, not on every card.

### 7. Export, check, publish

```bash
.venv/bin/python .claude/skills/student-proofreading-page/export_review.py --repo ../Formosan-<Name> \
    --images-out <scratchpad>/pages/<corpus>
```

Extract the inline `<script>` and run `node --check` on it. Publish
`review/review_page.html` with `capabilities: {"db": {}, "user": {}, "downloads": true}`
and `icon: "checklist"`, and the images as `files` from `<images-out>/files.json`
(`{"pages/p0053.jpg": "<path>"}`). One publish takes at most 255 files and 64 MB, so split a
larger set over several publishes to the same `url` (each adds to the files already there; a
version holds at most 511). Then run one ArtifactData `list` of `edits` (expect
empty). **Never write a test document to a live store**: in 2026-09 a deleted test
document came back from a browser that had cached it.

Adding or changing pictures does not change a card's hash (it covers only what the student
edits), so re-exporting for pictures alone is safe while a student is working; check that the
new baseline's hashes equal the old ones before publishing.

### 8. Hand over

Commit `review/` in the dev repo. Tell the maintainer:
- the page is private until shared from its Share menu;
- on a personal plan only email-invited Editors can save to the server copy, so
  everyone else works in their browser and must download a file;
- **don't re-export while a student is working**: a new baseline changes the
  card hashes, and `apply_review.py` refuses every edit made against the old
  ones. If you must re-export, bump `format` and tell the student to start fresh.

Record the page URL in memory and in the decision log.

## Part 2: incorporate a returned review

1. **Collect.** Save the emailed file under `review/`. If the page has a server
   copy, also run ArtifactData `list` `edits` with `out_dir`; compare the two and
   use the newer edit per card. Look for anything that isn't the student's (a note
   like "test", a foreign `base`).
2. **Apply.** `apply_review.py --repo ../Formosan-<Name> review/<file>.json`. Read
   every problem it lists (stale hash, count mismatch, unknown record); exit 1
   means at least one.
3. **Adjudicate (pause ▣).** Publish a decision artifact: each class of change with
   real before/after examples and counts, every note on an unchanged card as a
   question, per-item buttons plus a note box, stored in the page's db. The
   student's notes are questions, not rulings.
4. **Build.** Apply the ruled corrections through the dev repo's build, never by
   hand-editing XML (POL-038). The corrections TSV is an input the build reads at
   the stage where it still has words and glosses (before morpheme splitting,
   standardization and phonology), refusing any row whose `was` no longer matches.
   An empty gloss box becomes `<UNCLEAR/>` (POL-061); a word box holding several
   words becomes one `W` (POL-060). The Chang Seediq build
   (`review_corrections.tsv` + `review_adjudication.tsv`) is a worked example.
5. **Verify.** Regenerate, run all three validators (xml, text, glosses; all gate
   CI), diff the XML before and after, and show the maintainer the counts and
   examples of what changed.

## Traps from earlier rounds

- The Chang Seediq guide used `∅` for two different things. That's why the guide
  now treats "one gloss under two words" and "no gloss printed" separately.
- Hard-coded override tables in a build refuse corrections (Seediq
  `HAND_WRITTEN_TRANSLATIONS`, Kavalan `MORPHEME_OVERRIDES`): grep for them
  before promising a correction will land.
- An example printed twice can be one `S`: its words must agree on every card.
- A "done" button on a page can't notify Claude. The maintainer has to say so in chat.
