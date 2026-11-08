# Checklist: dictionaries, wordlists, lexicons

Four kinds in the bank, each with its own failure: a printed book scrape (Blust, Poinsot), a live web source (Safolu, ILRDF, Glosbe), a typed spreadsheet (Fey), a manuscript wordlist (Utrecht). Dictionaries are sentence corpora in FormosanBank: the published records are the example sentences and headword forms, with their glosses.

1. **Entry structure.** What a record is (headword, sense, example, note) and how the build splits it; every entry format gets an invariant and a defect list.
   How: sample ten entries per format against the page; `audit_gloss_scrape.py --source` where the source has a text layer.
   Example: Blust — row clustering 3.1 pt too tight split headers; Poinsot — wrapped lines became headwords.

2. **Bound roots, homograph subscripts, index pointers.** Bound roots are not words (Blust: deleting them would have removed a third of the corpus — measure before applying a sweeping instruction); homograph numbers and "see X" pointers are notation, not text.
   How: count each class first; put the counts to the maintainer with examples before any rule.

3. **Shared tails after a slash; lexicographic notation in headword forms.** `a/b-c` may mean `a-c / b-c`; parentheses may mark optional material or a sense note.
   How: the notation key (every-corpus item 6); a review page per question class; "is this one case, or a rule?" — two rules reproduced 39 of 39 Blust slash rulings.

4. **Dedup policy.** Repeated attestations across entries are expected; remove only when the base FORM and every TRANSL agree after cleaning (POL-022), and keep a survivor.
   Example: Blust — 10 of 15 "duplicates" carried different Mandarin; Safolu — the old build merged 140 examples with different meanings.

5. **Upstream drift for web sources.** Pin the snapshot with a sha256 manifest; `refresh_source.sh` separate from the build; classify every pin-vs-HEAD difference.
   Example: Safolu follows g0v editors' revisions; ILRDF withdrew 1,256 sentences between releases.

6. **Lost diacritics and stress marks.** Count "letters only one system has" and accents that land one letter early.
   Example: Blust — 139 fields lose the stress acute; 75 accents one letter early.

7. **Rulings kept as data.** `entry-rulings.json` (facts about the printed source the validator stops reporting), `curated-readings.json` (readings no rule derives), `settled-readings.json` (a ruling a rule later derives, kept as a regression test). See `Corpora/Blust-Thao-Dictionary/README.md`.
