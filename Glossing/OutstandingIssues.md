# Outstanding issues

Open questions with no approved mapping. Each entry names the thing, the
reason it is open, and where the evidence lives. Resolved entries move to
the bottom with their ruling.

## Open

- **Bare forms glossed with and without voice, not given voice** (2026-11-15). The same stem is
  voice-glossed in some sentences and left unglossed in others; only stems meeting the maintainer's criterion
  ("Only when the stem is voice-glossed at least 3 times AND at least twice as often as it is not
  voice-glossed.") got voice (CONTEXT-ADD rules). The other 240 stems (1,612 words) are in
  `ScopingReview/bare_forms_not_given_voice.tsv` with the reason (voice-glossed < 3 times; < 2x as often as
  unmarked; several voices). Largest: Kanakanavu misa (voice-glossed 18, unmarked 150), Bunun sadu (15/84).
  The NTU maintainer is being asked about NTU's 458 such forms (list in austronesian-voice
  results/lemma/unvoiced/ntu_forms.csv). Evidence: austronesian-voice src/lemma/unvoiced_audit.py.
- **Parentheses other than Rule 7** (2026-11-15; updated 2026-11-16): ePark `（人名）`, NTU `(Mandarin)`, HPS
  `(name)-(name)` ×1 and `go<perf>-(place)-nom` ×1 (the only `(name)`/`(place)` not covering the whole gloss),
  Yedda `ligture (LIG)` ×1 (typo) and `ligature?` ×1… stay flagged; how to handle them is a GitHub issue
  ("Glossing: parentheses in glosses: allow Leipzig Rule 7 stem(CODE), handle all other parentheses"). HPS
  `(inc)`/`(exc)`, whole-gloss `(name)`/`(place)`, Yedda `ligature (LIG)` and NTU Rukai `1P(IN)`/`1P(EX)` are now
  converted (see Resolved).
- **NTU Kanakanavu `IN` = the suffix -in/=en, meaning undefined** (2026-11-16): 44 English + 52 Chinese glosses
  (ride-where-IN, respond=IN; one twin pair reads CAU-do-how.many-PV vs 使役-做-多少-IN). Glossed `#IN` (as
  itself) per the maintainer; to ask the NTU maintainer what it stands for.
- **NTU Rukai =nay/nayane glossed (IN) ×3** (2026-11-16): the same forms are (EX) 排除 ×56; all 3 are in
  20200530-FW-Ludwig S1–S3, both tiers agreeing. Converted as written (INCL); to ask the NTU maintainer.
- **NTU's generate_xml.sh runs apply_gloss_standard only when manual_edits.xml exists** (2026-11-16): the call sits
  inside the `if [[ -f manual_edits.xml ]]` branch, and NTU has no manual_edits.xml, so a full rebuild would not
  write the standard gloss tier. Not changed; awaiting the maintainer.
- **NTU full-form voice labels without rows** (from PR #351): 參考焦點 ×66, 受惠焦點 ×34; labels fused to a
  lexical gloss with no separator (主事焦點吃 etc., ~25); 受事/處所焦點 with a half-width slash ×2.

- **Amis locative `i` (NTU 處格/LOC, ×192/×191).** No approved mapping
  (maintainer, 2026-11-11). Reason: disagreement between NTU and the
  reference grammar — NTU glosses `i` as a locative case (處格/LOC), while
  阿美語語法概論 has no locative case in its 表5.1 (three cases only) and
  glosses `i` as 介系詞 "preposition" (ex. 5-3, i kakarayan). The same
  question exists for Paiwan `i` (排灣語語法概論 §3.4.3.4: 介詞) and is
  testable by the co-occurrence test (can an i-marked noun also take a
  case marker?).
- **Kavalan `tu`: ACC or OBL.** Two sources write oblique (NTU 斜格/OBL
  ×606, Lin OBL ×3; 噶瑪蘭語語法概論 writes 斜格) but Chang 2000 — the
  largest non-NTU source — writes 受格 ×125. Under the 2026-11-11 ruling
  ("all sources say OBL → OBL") Kavalan is the one mixed case; the pick is
  the maintainer's.
- **Bunun NTU `cia`/`saicia` glossing.** The grammar's case markers are
  a / mas(=s) / is·itu / tu(分格) / sia; `=cia` is its bound 3rd-person
  斜格/屬格 pronoun (表5.3), `(ma)saicia` the free one, and `=tia`
  (surface *cia*) the non-nominative determiner (限定詞.非主格 — NTU's
  "DIST" glosses). NTU glosses these as case; no conflict in conversion
  (labels map regardless), but the marker-vs-case-bearing distinction
  should be kept in mind when reading counts (cia ≫ mas because pronouns
  and determiners are frequent).
- **Tsou NAF/非主焦 ×437/431 and NAV ×14** — the preverbal auxiliaries
  (i, o, os, oho); undecided, needs its own ruling (voice audit page).
- **Kavalan 非主焦/NAF ×32 (suffix -a with genitive agent)** — RULED to
  stay undecided (maintainer, 2026-11-12). What we know: every token is
  V-a + a 屬格 clitic (kita 1IPL ×24, ka 1SG ×7, one 未來-marked);
  -a clauses are nearly case-marker-free (tu ×7/ya ×4/na ×3 in 30
  sentences) vs the -an→PV clauses' full marking (na ×138/tu ×124/ya ×84
  in 514); translations run hortative ('let's …'). Neither grammar
  documents a suffix -a: the 語法概論's imperatives are -ka/-ika and its
  hortatives use =pa + sentence-final ka; Chang 2000 has no such form.
- **Kavalan-Chang IF ti-/te- ×3** (ti-kiras ×2, te-kiras ×1) — converts
  →OV on Chang's own label only: no other source has the morpheme (NTU's
  ti = PFV clitic / personal marker) and the 語法概論 documents no
  instrumental ti-/te-. Park the 3 tokens instead if preferred.
- **Seediq: Tsukida's OBL (suffix -an ×7) and NTU's 受格 (×3)** — RULED
  unmapped (maintainer, 2026-11-12: "Tsukida's OBL should be left
  unmapped for now. It goes on our list of todos, with an explanation of
  the issue. Same with NTU's 受格."). The issue: Tsukida case-glosses the
  -an suffix (rebiq-an) that every other source treats as locative
  voice/derivation (NTU glosses it LF); NTU's three 受格 tokens are
  slips. At apply time, per-language unmapping = a language override
  mapping the label to itself (copied verbatim).
- **Truku: Nowbucyang 受格 ×2** (lqi-an, ktu-an — 受格 glossed on
  -an-suffixed nouns) — the same -an categorial puzzle as Tsukida's OBL;
  proposed to follow the Seediq ruling (unmapped), pending the
  maintainer's word.
- **Tsou: zho 處格 ×3 and 受格 ×6 are mostly voice slips** — 處格's eng
  twins are LF (see.LF ×2, can.LF: 處格 typed for 處焦) and 受格's are
  say.PF ×4 / look.for.PF ×1 (the known say.PF family) plus one pronoun
  whose eng tier reads 3PL.GEN. The case-page 處格→LOC (n=3) row
  therefore rests on slips; proposed (drop), pending the maintainer.
- **Saisiyat -an: focus vs nominalizer** — maintainer-confirmed todo
  (2026-11-12, with Saisiyat voice approved on this condition). The
  facts: NTU Saisiyat uses the locative-voice family exactly ONCE in the
  whole corpus (one 處焦, and it sits on ray — the locative marker, so a
  slip), and the -an morpheme (×99) is reliably glossed as the
  nominalizer: 名物化/NMZ ×93, lexical 處所 'location' ×3, 受焦 ×1,
  unglossed ×2. The grammar's 處所焦點 -an and NTU's NMZ -an are the
  same morpheme under two analyses; a Notes & Caveats line is due at
  publication.
- **ILCAA Kanakanavu CV ×114** (si; absent from B602's own abbreviation
  list) — suggestion on the voice audit page: → OV, matching NTU's si-.
- **Amis-Pa-Verbs UV ×41** — en ×13 matches NTU PV -en; Ma ×7 ambiguous
  (NTU glosses ma- both 主焦 ×280 and 受焦 ×69).
- **Rukai POSS-as-possibility-modal** (POSS.MOD ↔ 可能.情態 ×72) —
  composite flagged in the NTU row review, undecided.
- **Sakizaya `misu`** POSS ×8 vs GEN ×5 border (case audit page).
- **YeddaPalemeqBlog UV: UNMAPPED, deferred here** (maintainer,
  2026-11-12: "We should not map Yedda's UV, and instead defer to our
  todo list. Why? Because it sometimes maps to PV in HPS and sometimes
  to perfective! And most of the time it's actually telling us about a
  different word, not the one it is the gloss for. So this requires more
  effort to handle."). This supersedes the earlier r2 affix-split: the
  UV row is UNDECIDED again and the UV context rules are removed from
  the rules file. Evidence on file: HPS glosses Yedda's -en words pf but
  its ⟨in⟩ words perfective (aspect), and most UV mentions sit in prose
  describing a neighboring word.
- **RauDong NF ×658 "nominal affix"** (and VF) — surfaced by the
  gloss-dictionary gate 2026-11-11; not Leipzig, needs a decision.
- **NTU 1S/2S/3S-style person codes and the small NTU composites**
  (完成主焦, 參焦 ×68, 主焦重疊, K主焦A, T主焦A, 工焦完成貌) — UNDECIDED
  rows in their tables.

- **NTU 沒有 ×52 — left UNDECIDED (maintainer card M10, 2026-11-15: `leave` + "And put
  in our todo list in the glossing folder!").** The zho gloss 沒有 covers seven
  different language-specific negators: plain negators (Saisiyat 'oka'/'okay §10.1.1,
  Rukai kai — not covered by the Mantauran-dialect 語法概論, Tsou o'te §10.1.2.1,
  Kavalan mai, Atayal meyo, Bunun nii) and negative existentials (Kanakanavu 'akia
  否定存在動詞 PDF 69, Tsou uk'a PDF 89, Bunun uka). A single conversion would merge
  the two kinds; within Tsou even per-language overrides can't split them. One Rukai
  token's form is literally `meiyou` — possible Mandarin echo, worth inspection.
- **QUAL / INVOL (HPS qal ×161, invol ×181) — registered and converted 2026-11-15
  (card U1), to be REVISITED** (maintainer: "add to our todo list in glossing to
  revisit this, particularly when we get more glossed Paiwan data."). The Paiwan
  語法概論 does not treat the underlying prefixes (li-/sa-/⟨ar⟩; se-); the codes rest
  on Early & Whitehorn's Ch.1 definitions alone, and Yedda has no analogues yet.

- **NTU Saisiyat -an: stays NMZ per the corpus creator (Li-May Sung, email to the
  maintainer, 2026-11-15/16):** "Glossing -an as NMZ (nominalizer) doesn't
  necessarily conflict with glossing it as LV voice in many Formosan languages. I
  took a quick look at our Saisiyat stories, lots of the -an derived words mean
  nominal entities such as bicylce, animal or bottle etc. At this moment, I would
  like to have the NTU Saisiyat glossings stay as they are." Our standard tier
  already conforms: NTU Saisiyat voices are AF/PF/RF → AV/PV/OV (no LV anywhere),
  and -an NMZ ×97 (form an ×93) converts only in spelling (NMZ → Leipzig NMLZ),
  never to a voice. Related open -an items: Tsukida Seediq OBL, Nowbucyang Truku
  受格 (above). The ANALYSIS-side counting rule "-an nominalizations count as
  locative voice" (maintainer, 2026-09-28, austronesian-voice repo) is a separate
  decision that this email bears on for Saisiyat.

- **CFACT (counterfactual) — registered 2026-11-15 (card M9: "Register CFACT and map
  to that. Put in our todos that we anticipate this showing up in future for Rukai
  `ni-` and possibly Truku, Atayal, and Thao.").** Currently only NTU Tsou nte/n
  (HYP/假設) maps to it. The grammars' other counterfactual markers are barely in
  our corpora and never glossed as counterfactual: Rukai ni- (Mantauran grammar PDF
  105; NTU Rukai ni ×12 = NI/名物化/完成貌/mixed — different dialect), Truku naa
  「本來會」 (no corpus hits; nasi in Seediq data = 'pear' ×23 + 條件詞/如果 ×11),
  Atayal aki (×1, glossed 在), Saisiyat naw (×7: 條件詞/只/好像), Thao (no affix —
  conditional constructions). Revisit when such tokens appear.
- **Kanakanavu ara- homophony (sep20, 2026-11-15: "The 'take' and 'go' entries go
  into the todos in glossing folder.").** ara 'become' ×82 → COS (done); the same
  form is glossed take ×61 and go ×12 — lexical homophones left as-is; check when
  standardizing Kanakanavu lexical glosses.
- **HPS 'have' (pu-) ×220 — separator yes (sep25) + "this needs to go on todo list
  for standardization."** All 'have' tokens are the one morpheme pu-/p-u (verified);
  code proposal (PROPR?) on the page's U2 table.

- **HPS 'pair' (mare-/pare- ×118) — left unmapped (u2_pair, 2026-11-15: "Leave as
  undecided, put in todo.").** The dominant form mare- matches the Paiwan 語法概論's
  reciprocal-context mare'a examples; if an expert confirms reciprocal, RECP is the
  natural target. Revisit with expert input.
- **Reversive candidates bank-wide (u2_remove question, 2026-11-15).** HPS remove
  (su-) ×79 is separator-yes but unmapped; similar lexical glosses elsewhere:
  NTU remove ×12 / take.off ×6 / 脫 ×2 / un ×1, RauDong 'un' atoms ×16, Nowbucyang
  un ×4, ILCAA take.off ×2 + remove ×2, Wild take.off ×1, Song 脫 ×1. No code
  anywhere; REV registration would cover them if wanted later.

- **HPS 'make' (sane-) — left unmapped (q_make, 2026-11-16: "Leave as undecided and
  put on todo list, with this information.").** The information: of 112 M-level
  `make` tokens, the true denominal-prefix pattern (make-NOUN: dumpling, wing,
  child, +2 imp) is ≈5 tokens; the rest are sane-as-root (non-initial or
  voice-inflected ×81, e.g. ki-sane 'do-make', s⟨em⟩ane 'make<af>'), standalone
  verb sane ×14, and the root alang in nominalizations ×11 (si-alang-an). An
  atom-level make→CAUS would mislabel ~106 verb/root tokens to catch ~5; position-
  conditioned conversion is not supported. `make` IS a separator via its lexical
  atom (sep28). Revisit if position conditions are ever added to the converter.
- **Rule 7 for non-voice codes the source bracketed: keep the brackets, or periods everywhere?** (2026-11-17,
  maintainer: "send to outstanding issues"). The rulings on Rule 7 cover voice only: unv_notation_r4 "Rule 7
  (see(AV)), with an exception to the 2026-11-11 parentheses ruling …", unv_scope_r5 "All 12,001 with a lexical
  gloss; the 3,684 on affixes/auxiliaries stay as they are", card P1 (Wild-Lehmann voice tags) "these should remain
  Rule 7", and for the Chang grammars "RUle 7, consistent with the rest of bank." RULE7-PARENS, however, keeps any
  code-only parentheses the source wrote (codes = anything in the corpus table), so 2,718 standard glosses carry a
  non-voice code in Rule 7 brackets, e.g. HPS f.we(inc) -> f.we(INCL) (x1,364, approved from before/after tables),
  NTU Rukai 1P(IN) -> 1P(INCL). The same category therefore appears in two notations depending on the source: NTU
  Kanakanavu 我們.包含 -> 我們.INCL (period) vs NTU Rukai 1P(INCL) and HPS we(INCL) (brackets). Leipzig Rule 7 is for
  "Inherent, non-overt categories such as gender" (PDF p. 6); clusivity or case shown by a pronoun's form is overt
  (Rule 4, periods). For case in the Chang grammars the maintainer ruled period notation ("We will need our
  standardization to convert to use period notation (他.GEN) during standardization"). Open: keep the source's
  brackets for non-voice codes, or write them with periods everywhere (we.INCL, 1P.INCL)?
- **Chinese-tier Rule 7 glosses whose English twin is codes only** (2026-11-17): after RauDong's labels
  虛/使/祈/疊/動綴 became codes, a few zho glosses still read as Rule 7 because their Chinese piece may itself be a
  label, not a lexical gloss: RauDong 要(AV) (eng AV.CAUS), 參與(AV) and 能(AV) (eng AV); NTU 期使(PV) (eng PV.IMP;
  期使 is probably a typo of 祈使), 大(AV) (eng PROG), 花(AV) (eng AV.SII), 擁抱(AV), 抓(AV) (eng AV). One each;
  to put to the maintainer.

## Resolved

- **HPS (inc)/(exc), (name)/(place); NTU IN/EX, 包含/排除; Yedda ligature** (resolved 2026-11-16, unvoiced-verbs
  audit round 8): HPS inc → INCL ("INCL (Leipzig; nothing to register)"), exc → EXCL ("Yes, exc → EXCL
  (Leipzig)"), whole-gloss (name)/(place) → PN ("A: standard tier → PN; original unchanged"); NTU IN → INCL for
  Rukai and #IN for Kanakanavu, EX → EXCL, 包含/包含式 → INCL, 排除/排除式 → EXCL ("Approved EXCEPT for the -in/=en
  suffix in Kanakanavu, which should be glossed as #IN."); Yedda ligature and whole-gloss ligature (LIG) → LNK
  ("LNK, as ruled on 2026-11-11 (no new code)").
- **2 NTU word glosses stayed Rule 4** (`-carry.PV` / `-帶.PV`, `<UNCLEAR/>` child; resolved 2026-11-16): the
  standard tier was rebuilt from scratch, which converts them (`-carry(PV)`).
- **356 NTU standard glosses still read 主事焦點/受事焦點** (Grammar/Kanakanavu 145, Grammar/Seediq 211; labels
  inside angle brackets, missed by PR #351; resolved 2026-11-16, maintainer: "Yes, fix them in the same PR").

- **V122 counted Rule 7 parentheses** (opened 2026-11-15, resolved 2026-11-16): the SOFT rule
  parens_slashes_anywhere flagged every `see(AV)` (NTU 4,687 → 50,969 findings). Ruling (maintainer,
  2026-11-16): "exempt any gloss registered gloss code (including Leipzig codes) found inside parentheses when
  there is also other content in the gloss". V122 now skips such parentheses in word and morpheme glosses
  (codes from `leipzig_codes.tsv` and RULED rows of `supplementary_codes.tsv`). The 12 Chang glosses
  `他(屬格)` / `你(屬格)` stay flagged until 屬格 (UNDECIDED, proposed → GEN) is ruled.
