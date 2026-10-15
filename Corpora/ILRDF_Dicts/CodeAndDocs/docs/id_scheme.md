# Sentence and entry ids

Ids are `<Language>_<source GUID>`, e.g.
`Amis_20a69646-e70a-f011-bd65-00155db40116`. Dictionary entries take a `d`
before the GUID; split records take a trailing `_a`, `_b`, `_c`.

## Why not a content hash

The 2026-08-23 build derived ids from a truncated SHA-256 of the sentence's own
original FORM. That is immune to upstream reordering, but it stabilises the
wrong axis: the id survives only while the text never changes. Every OCR fix,
POL-001 restoration, or punctuation correction retires one id and mints
another — the worst possible behaviour for a corpus whose stated purpose is
progressive source-fidelity correction.

It also forecloses `manual_edits.xml`. `apply_manual_edits.py` matches records
by `S/@id`, while POL-030 and POL-002 send hand edits to the *original* tier —
the very tier the hash is derived from. A recorded edit changes the text, the
next build mints a different id, and the record targets an id that no longer
exists: an orphaned no-op that silently does nothing.

## Why the source GUID

The ILRDF API assigns a GUID to every word, explanation, and sentence item.
Verified across all 16 committed snapshots on 2026-09-05:

- 211,595 sentence items, **0** without an id
- 210,502 distinct GUIDs, **0** carrying more than one distinct text,
  translation, or audio set
- **0** GUIDs appearing in more than one language
- every GUID matches the canonical 8-4-4-4-12 shape
- the sentence, word and explanation GUID spaces are pairwise **disjoint**
  (210,502 / 144,029 / 169,859, zero overlap)

## Why the GUID is carried whole

Truncating to 16 hex digits buys brevity and costs the two things that matter:
an id can no longer be grepped straight back to the snapshot, and a truncated
key carries a collision risk the whole key does not. Checked before adopting
the long form: `S/@id` is `xs:string` in the XSD with no format rule (V039
checks uniqueness within a file, V081 checks `TEXT/@id` across corpora), and
hyphenated `S` ids are already published in NTUFormosanCorpus (12,410),
Song-Kanakanavu-Grammar (1,569) and HundredPaiwanStories (5).

The `d` on entry ids is legibility, not collision insurance — the GUID spaces
are already disjoint. The GUID still appears verbatim inside the id, so
grepping a raw GUID finds the record either way.

## Dedup and the canonical id

The same sentence often appears under several headwords. 21,057 distinct texts
carry two or more GUIDs (36,421 extra GUIDs). Records are merged by normalized
original text, keeping every distinct translation, and the merged record's id
is the **lowest GUID in the group**.

One consequence to know: a correction that makes two previously distinct texts
identical will merge them and retire one id. That is rare, `tests/test_ids.py`
fails loudly if ids stop being unique, and `source_data/published_ids.csv`
catches it as a declared change rather than a silent one.

## Splitting

A record that the source packed with more than one example, or with
alternatives that resolve into separate readings, becomes several `S` elements
whose ids take a letter suffix: `Atayal_<guid>_a`, `_b`, `_c`. Each is a
declared addition in `published_ids.csv`; the parent row becomes
`status=split-parent`.

## Migration from the 2026-08-23 build

Every id changes. No id from that build is preserved. Nothing downstream had
consumed them — it was never merged.
