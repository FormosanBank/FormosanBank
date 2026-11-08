# Checklist: sentences with translations (no W/M)

Narratives, scripture, blogs, grammar examples without glossing, parallel sentence sets.

1. **Source extent.** Chapters, verses, posts or stories the source has versus the records built; a marker-driven parser cannot see narrative (every-corpus item 1).
   Example: Seediq-Chang's chapters 5 and 6; HundredPaiwanStories' missing story-091 sentence and nine final words.

2. **Sentence boundaries.** Where the source breaks at an internal `!`/`?` or a quotation, the build must not split a sentence; where the source runs sentences together, the build must not invent boundaries.
   Example: Safolu — g0v broke examples at an internal `!`/`?` (36 translation fixes).

3. **Translation coverage and language.** Every S has its TRANSL(s); each TRANSL's `xml:lang` matches its script (V143); English published as `zho` and Chinese as `eng` have both happened.
   How: a translation-coverage splice test; V143.

4. **Out-of-language runs in the FORM.** English, German or French prose caught by the scrape (G017), Han characters or kana in a FORM (G019), Ilocano or other passages a reader must judge.
   Example: nine Amis Wikipedia biographies with Ilocano passages; two Seediq records mostly English.

5. **Corrections to the book itself, as opposed to OCR corrections.** Each departure from the print carries author, reason, who reviewed it, and the maintainer's words; never write "what the book prints" unless verified against the page.
   Example: Seediq-Chang — eight silent departures, each later ruled and noted.

6. **Parallel corpora.** Align by the shared translation, not by sentence id (ePark is five-dialect parallel); the same clip under two readings is V162.

7. **Duplicates by corpus type** (POL-022): narratives may legitimately repeat; dictionaries and grammar example collections should not. Report the within-corpus and cross-corpus counts and let the maintainer decide.
