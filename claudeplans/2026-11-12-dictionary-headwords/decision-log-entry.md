## 2026-11-12 — ⏳ Dictionary headwords: Safolu + Fey missing; round 1 page published

**Maintainer:** *"Apparently when we processed Safolu, we pulled just the example sentences and didn't pull headword entries
(which would be a separate XML). Please do. Also check Virginia_Fey_Dictionary and Blust-Thao-Dictionary and Glosbe and
Cuerq-Pourrias, for the same purposes."*
**Found (origin/main 525ad4932):** headwords MISSING in Safolu (upstream docs/s: 42,273 headwords / 57,361 definitions; committed
snapshot holds only the 45,740 definitions with an example) and Fey (sheet column 詞條: 4,848 headwords / 6,115 senses; none
published). PRESENT in Blust (7,248 entry S), Glosbe (1,156 lexical S; 0 →zh headword candidates in the crawl, live site not
checkable), Cuerq-Pourrias (23,316 headword entries). Drafts in session scratchpad only (draft/safolu_headwords.py,
fey_headwords.py): Safolu 42,354 S, Fey 4,704 S, 0 HARD each on main tools. Nothing committed, no branch.
**Maintainer (same day):** *""Layout follows POL-025. " <-- see if you can distinguish between one word with multiple senses
and actual homophones, based on structure of the source."* → Safolu print (miaoski/amis-safolu f512d5b dict/*.txt): ①②③
inside one entry = one word (reliable); separate same-spelled entries = homophones OR reprints (sections 23 ', 24 loanwords)
OR repeats OR ①② split into entries ('adingo) — 882 groups, 326 align cleanly with upstream h, 556 don't. Fey: no structural
signal. Page v2 adds cards s-homophones, f-homophones (18 total).
⏳ OPEN: 18 cards on https://claude.ai/artifact/1N7xc3PCVuYYsmyynos5S4 (db collection `answers`, doc ids = card ids;
done flag `meta/round1`): s-homophones, f-homophones, s-version, s-xref, s-label, s-nochinese, s-embedded, s-heading, s-affix, s-nosense, s-stemtag,
s-synrel, s-borrow, f-split, f-xref, f-fixme, f-affix, f-see. After answers: one branch/PR for both corpora (corpus folders only).
**2026-11-15 handover (maintainer switching computers):** drafts, page source and a resume guide committed on branch
`plans/dictionary-headwords-handover`, folder `claudeplans/2026-11-12-dictionary-headwords/` — start at its `HANDOVER.md`.
Answers on the page at handover: none (db `answers` and `meta` both empty).

---
