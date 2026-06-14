# Data-quality issues found in the ILRDF online dictionaries (draft note for the Foundation)

*Prepared 2026-06-14 from a full re-scrape of all 16 languages via the current
`e-dictionary.ilrdf.org.tw` API. This is a draft for Josh to adapt into an email to ILRDF / the
web developers. All evidence is reproducible from the API; attached CSVs give the per-record
detail.*

We re-scraped the 16 dictionaries through the new API and, while preparing the data for the
FormosanBank corpus, found three issues that appear to originate in the dictionary database
itself (not in our processing). We have repaired what we safely can and are sending the rest back
for source correction.

## 1. The `ʉ` character is corrupted to `?` in some records

In the three orthographies that use **`ʉ` (U+0289)** — Saaroa, Kanakanavu, Tsou — some example
sentences come back from the API with every `ʉ` replaced by a literal `?`.

**This is in the database, not in transmission.** For the Saaroa headword `hliangahli`, the API
returns three example sentences in a single response:

- `… mʉcʉkʉhlʉ?` — correct (the `ʉ` arrives properly encoded)
- `… mucukuhlu.` — a plain-`u` variant
- `… m?c?k?hl?` — the **same word** with every `ʉ` replaced by `?`

So the server returns clean `ʉ` and corrupted `?` *in the same payload* — the corruption is in the
stored record. It cannot be fixed by re-fetching.

**Scope:** 110 affected example sentences across the three languages.

- **71 we repaired automatically** — where the same word appears uncorrupted elsewhere in the
  dictionary, we restored `ʉ`. (Attached: `ilrdf-q-corruption-FIXED.csv`, for your confirmation.)
- **24 we could not repair** — no uncorrupted copy of the word exists anywhere, so the original
  spelling is lost to us. **These need correction at the source.** (Attached:
  `ilrdf-q-corruption-NOTFIXED.csv` — language, headword, the corrupted word, and the full
  sentence so each record can be located.)

## 2. Missing spaces around `?` (a separate, smaller issue)

In several other languages a real question mark is run together with the following token, e.g.
Kavalan `… tangi?B: …` where the dialogue should read `… tangi? B: …` (speaker label `B`). 15
such cases were detected. These are not dropped letters; likely a formatting/whitespace issue in
the records. (Attached: `ilrdf-questionmark-spacing-artifacts.csv`.)

## 3. Audio coverage dropped versus the previous system

For **6,384 example sentences that had audio in the previous dictionary system, the current API
returns no audio at all** (we confirmed there is no audio for these texts anywhere in the new API
responses). They concentrate in Kanakanavu (1,729), Saaroa (1,366), Tsou (717), Saisiyat (631),
Puyuma (377). This looks like audio that did not carry over in the migration to the new system.
(Attached: `ilrdf-audio-coverage-regression.csv`.)

Separately — and consistent with what we discussed earlier — **draft entries (`frequency = 0`)
were found to carry mis-attributed audio** (the recording belonged to a different, published
sentence). We now exclude `frequency = 0` drafts from the corpus, which removes the systematic
cases. Residual mismatches inside published entries can only be found by listening; we have an
acoustic screening pipeline for that and it is in progress.

## What would help most from ILRDF

1. Correct the `ʉ → ?` records (24 unrecoverable cases attached; the 71 we fixed are attached for
   confirmation that our reconstruction matches your intended spelling).
2. Confirm whether the audio for the ~6,384 regressed sentences still exists and can be re-linked
   in the new system.
3. Let us know whether the `frequency` flag is the right signal for "published vs draft," so we
   exclude exactly the right entries.

### Attachments (in `FormosanBank/claudeplans/`)
- `ilrdf-q-corruption-FIXED.csv` — 61 word repairs we applied (for confirmation)
- `ilrdf-q-corruption-NOTFIXED.csv` — 24 unrecoverable `ʉ→?` records (need source fix)
- `ilrdf-questionmark-spacing-artifacts.csv` — 15 missing-space `?` cases
- `ilrdf-audio-coverage-regression.csv` — 6,384 sentences that lost audio vs the old system
