# Outstanding issues

Open questions with no approved mapping. Each entry names the thing, the
reason it is open, and where the evidence lives. Resolved entries move to
the bottom with their ruling.

## Open

- **Pronouns left as words** (2026-11-27, pronoun glosses page NSfDfqWnj1j6R3vhD2ei3x; the conversion to person-number
  labels is in Resolved). Kept as the source wrote them, undecided:
  - bare *you*, number not stated (HPS, Wakelin 41, NTU, …): "you (number not stated) -> undecided, goes on todo";
  - possessive pronouns (*my, your(s), his, our(INCL), their*; 我的, 你的, 他的 …): "These all go on undecided list, keep
    their original forms.";
  - Wakelin *her* (30): object or possessive, not decidable without reading each;
  - Wakelin *you(pl)*: Wakelin's rules record "( ) in data, probable discrepancy" for parentheses, so "(pl)" may not be
    a number marker;
  - English pronoun words in NTU, ILCAA-Kanakanavu, Sakizaya-Affixes, Song-Kanakanavu-Grammar and Nowbucyang: mostly
    not pronouns. `I` / `i` gloss a morpheme *i* (NTU 120 `I` + 8 `i` of form *i*, 3 of form *'i*; ILCAA 95; Sakizaya 3; Song 3;
    Nowbucyang 1), and NTU's `HE` / `ME` / `US` are Tsou *-he*, Kanakanavu *me-* and *padaka* 美國. NTU's other `I` forms are
    still to check: *smani* 14, *zaka* 8, *aka* 5, *wo* 2, *'ecikia* 2, …;
  - 21 glosses that hold a pronoun but are copied whole because of an unhandled parenthesis (NTU and Song
    `=一下(客氣)=你.主格`, Song `=我.主格（`, Wakelin `(spend.the.night)-we`, `we-incl(EA)`, …; see "Parentheses
    other than Rule 7").
- **NTU Kanakanavu *=kita* labelled exclusive 4 times** (2026-11-27): the same form is inclusive 5 times in NTU and
  inclusive throughout ILCAA (*=kita* 49) and Wild-Lehmann (*kita* 9). Converted as written (`1PL.EXCL`); to ask the NTU
  maintainer.

- **NTU Bunun misspelled linker labels, deferred** (maintainer 2026-11-24, linker-or-conjunction page, card bunun_typos:
  "Defer with the other low-frequency anomalies"): 8 Bunun *tu* words with eng LNK whose zho gloss is 連擊詞 ×5 (row
  UNDECIDED), 聯繫詞 ×1, 連繫詞詞 ×1, 繫詞 ×1 (no rows) — copied verbatim on the zho standard tier.
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
  - **Left out of the Yedda verb-voice table, to be figured out** (maintainer,
    2026-11-26: "Note that our gloss standardization todos should mention all
    the ones we are currently leaving out as something to be figured out.").
    Several are also on the running list of questions for an expert.
    - left out by the maintainer's round-1 answers (11): `pinavelian`, `pinaquzip`, `tja-kuda-in`, `s<in>i-pu-aljak-an`, `kinsa`, `tja-si-ka-ma-nguaq`, `pa-cu-cun-an`, `kuda-kuda-in`, `kiljivak-an`, `kuda-kuda-in`, `veric-an`
    - she calls them nominalizations (11): `si-qa-qivu-an`, `si-vecik-an`, `ka-calisi-yan`, `s<in>kez-an`, `q<in>um-an`, `pu-alju-an`, `p<en>a-calivat-an`, `v<in>arung-an`, `lja-k<in>a-luljay-an`, `p<in>a-cun-an`, `p<in>u-aljak-an`
    - left out by the maintainer's round-3 answers (7): `u-cevung-i`, `icaquanan`, `siniljaui`, `sinatjezan`, `qavai-n`, `d<em><in>udu`, `su-qeljev-i`
    - left out by the maintainer's round-4 answers (2): `ma-alim`, `u-qaca-nga`
    - also left out by rule: repeat tokens with no gloss at all, and voices known only from HundredPaiwanStories
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
  atom-level make→CAUS would mislabel ~106 verb/root tokens to catch ~5. `make` IS
  a separator via its lexical atom (sep28). UPDATE 2026-11-17: opt-in positional
  context patterns (`^X` initial / `X$` non-initial) now exist (added for the Bunun
  處格 fix), so a `make&^sane → CAUS` rule is now technically possible — but the
  ~5-token payoff still needs the maintainer to re-open this; not implemented.

- **Bunun iskus-a=s — 1 token keeps zho 處格 on a verbal suffix (2026-11-17).** The
  Bunun 處格-on-verbal-an fix (`處格@Bunun&an$ → LV`, maintainer's "fix the zho side"
  ruling) covers the 13 suffixal -an tokens but not this one, whose suffix is the
  -a allomorph ('lead.along-LF=...', Bunun.xml). A `-a` context pattern over-fires
  on any word containing a morpheme a; no pattern isolates this single token.
  Candidate future fix: a per-token manual edit, if ever worth it.
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
  For pronoun clusivity this is settled (2026-11-27, pronoun glosses page round 2, "Periods: 1PL.INCL / 1PL.EXCL"):
  HPS we(INCL) is now 1PL.INCL; HPS our(INCL) (possessive, kept as written) and the other non-voice codes remain open.
- **Affixes glossed as themselves in words with no voice code** (2026-11-17, maintainer on the unvoiced-verbs
  audit, round 10: "Leave as glossed; list them (with the tables) in OutstandingIssues for the source
  maintainers"). 994 words carry no voice code anywhere but contain a morpheme glossed as itself (e.g. Sakizaya
  sa "SA", Seediq <n>) whose form some glosser of the same language glosses with a voice code at least 3 times.
  Full list, one row per word with each form's language-wide gloss counts:
  `ScopingReview/self_glossed_voice_affixes.tsv`. By corpus: NTU Sakizaya 368, Amis 238, Seediq 75, Kanakanavu 64,
  Kavalan 51, Bunun 48, Saisiyat 6, Atayal 4, Tsou 1; Sakizaya-Affixes 78; ILCAA 30; Nowbucyang (Truku) 20; Song
  6; Lin (Amis) 3; Amis-Pa-Verbs 2. Largest forms (language-wide: voice / itself / other code / lexical): Amis sa
  198 words (24/223/5/38), Sakizaya ka 161 (46/227/6/61), Sakizaya sa 135 (55/143/418/256, mostly DM), Sakizaya ni
  125 (12/173/41/78), Sakizaya pi 65, Seediq n 53 (59/139/166/15, mostly PFV), Kavalan an 49 (698/50/603/51),
  Kanakanavu a 48. Most look like deliberate self-glosses (the same forms are often glossed DM, LOC, NMLZ, GEN,
  PFV), and many words are nouns or numerals by their own word glosses. 115 words are on forms voice-glossed at
  least 3 times and twice as often as not (column meets_threshold); 182 were already found by the unvoiced-verbs
  audit (column in_unvoiced_audit; 22 of them on bare_forms_not_given_voice.tsv, the other 160 never voice-glossed
  as a stem). No change made; for the corpus maintainers.
- **Chinese-tier Rule 7 glosses whose English twin is codes only** (2026-11-17): after RauDong's labels
  虛/使/祈/疊/動綴 became codes, a few zho glosses still read as Rule 7 because their Chinese piece may itself be a
  label, not a lexical gloss: RauDong 要(AV) (eng AV.CAUS), 參與(AV) and 能(AV) (eng AV); NTU 期使(PV) (eng PV.IMP;
  期使 is probably a typo of 祈使), 大(AV) (eng PROG), 花(AV) (eng AV.SII), 擁抱(AV), 抓(AV) (eng AV). One each;
  to put to the maintainer.

- **HPS standalone `a` (`c` "construct marker") not before a voice-marked word — 2,092 copied as `c`
  (2026-11-24, Paiwan a page round 2 r5: "UNDECIDED"; r1: "All other cases should revert to 'c' and remain
  UNDECIDED.").** Only the 527 before a word whose source gloss has af/pf/lf/if became LNK. Paiwan *a* is both
  the non-personal nominative marker and the linker (排灣語語法概論 PDF p.56 「有一個連繫詞a，出現在動詞之間、動詞和否定詞之間或
  名詞之間」, p.73 「非人名的主格標記a」); Early & Whitehorn gloss both `c` and use `f` "focus" (now NOM) only for ti and the
  nominative pronouns; Ferrell 1982 p.53: "a (equational construction marker for noun phrase)". Nothing we hold
  marks part of speech (Ferrell has no category field), so nouns and modifiers after *a* cannot be told apart
  mechanically. The 2,092 by the next word's source gloss: bare English word 836, other multi-part 429,
  reduplicated 228, another function code 188, stat 148, possessive 119, num 77, ti / nominative pronoun 33,
  voice code + nom (nominalized) 29 (left as c by the maintainer: "Leave them as c (527 → LNK)"), name 5.
  YeddaPalemeqBlog splits its *a* LIG 729 / nominative 769 / unglossed 278. Evidence page:
  https://claude.ai/artifact/Agn19a9QEMKWCpGtLC6MUx
- **HPS `a-zua` 'c-that' ×409 (+ a-za~zua ×9, a-zua~zua ×1) — copied as `c` (2026-11-24, round 2 r2: "leave as
  UNDECIDED and put this specific issue in our todos for gloss standardization.").** Sources disagree: YeddaPalemeqBlog's
  glossers call this *a-* the subject case marker ("that. a 'subject case marker'; the root is zua 'that, those'.", 10
  tokens) and *azua* "that, nominative demonstrative pronoun" (2); 排灣語語法概論 PDF p.72 (5-3a) writes *a zua vavayan*
  as two words glossed 主格 那 女人; Ferrell 1982 p.362 has *a-zua* 'that, those' and *nu-a-zua a tsautsau* 'of those
  people', where *a-zua* follows the genitive *nu-*. In HPS the stem also takes i- loc ×172, ta-/tua- obl ×42,
  nua- by/of ×19.
- **HPS `a-ravats` 'c-true' ×112 — copied as `c` (2026-11-24, round 2 r3: "and leave c and UNDECIDED and in our
  todos.").** No source calls this *a-* nominative: Ferrell 1982 p.243 "ravats true / a ravats genuine(ly), truly;
  very / ui a ravats yes, that's true!"; 排灣語語法概論 PDF p.144 writes *aravac* as one word glossed 很 'very', between
  two linkers (*gemaljusun a aravac a 'eman* 慢<主焦>=你.主格 連繫詞 很 連繫詞 吃<主焦>); YeddaPalemeqBlog *aravac*
  'very, quite' ×110. Typical HPS use: *masalu aravats azua vavayan* 'The girl was very pleased.'
- **HPS `a-i-tsu` 'c-loc-this' ×13 and `a-nema-aya` 'c-what-say' ×1 — copied as `c` (2026-11-24, round 2 r4: "and
  leave c and UNDECIDED and in our todos.").** Not yet researched; 排灣語語法概論 PDF p.60 writes *[a icu a vurati]* 主題
  'this sweet potato (topic)' with *a icu* as two words, unglossed.

## Resolved

- **HPS `red~stem` in word glosses** (maintainer 2026-11-27, HPS gloss abbreviations page JmCfWcQZsGwM2UE9KXM1dL,
  card b1: "Apply, tests first"): `~` is a separator in the HPS rules file (Leipzig Rule 10), so `red~being` → `RED~being`
  like the morpheme glosses. 1,188 word glosses; 4 also convert a ruled code behind the `~` (`red~remove` → `RED~REV`,
  `red~past.era` → `RED~PST.era` ×2, `red~af` → `RED~AV`).
- **Pronouns as person-number labels** (maintainer 2026-11-27, chat: "I prefer 2SG and 2PL to you.SG and you.PL. Same for
  1SG and 1PL and 3SG and 3PL. Can we apply anywhere we've standardized differently so far?"; pronoun glosses page
  NSfDfqWnj1j6R3vhD2ei3x: p1 short codes "Apply", p2 RauDong "Apply", p4 English words "Otherwise approved", p6 Chinese
  tiers "Apply", p7 and p8 "Agree", round 2 p3b "Periods: 1PL.INCL / 1PL.EXCL (Recommended)" and t1 "Yes, add it, tests
  first"). 20,051 standard glosses in 15 corpora: 1S/2S/3S/1P/2P/3P → 1SG/…/3PL (NTU, Amis-Pa-Verbs, Huteson-Rukai);
  RauDong 3.S → 3SG (ATOMS→, new rule); clusivity → 1PL.INCL / 1PL.EXCL (NTU 1P(IN)/1PI, ILCAA 1INCL, Wild-Lehmann
  1PI/1PE, Naomi-Tsukida 1PLIN/1PLEX, HPS we(inc)/we(exc), Chinese 含/除/包含式/排除); English pronoun words in HPS, Wakelin and
  Li-Conjunction-Thao (where they gloss pronoun forms); 我/你/他/她/我們/你們/他們/咱們 in 7 Chinese tiers; HPS 3rd.pers → 3.
  Pronouns inside a lexical gloss stay words (thank.you). Left as words: see Open, "Pronouns left as words".

- **Tsou NAF/非主焦 and NAV — the preverbal auxiliaries (i, o, os, oho)** (resolved 2026-11-12, entry moved
  2026-11-26). RULED (maintainer 2026-11-12): "Sounds like NAF->NAF. This is how grammar and our sources handle
  auxiliaries for Tsou. This should be explained in our dictionary." (registered in `supplementary_codes.tsv`).
  Until 2026-11-26 the Atayal-only rule `NAF&-i → OV` also matched the Tsou auxiliary morpheme *i*, turning 305 of
  these words into OV; it is now scoped to Atayal. On 2026-11-26 all 443 Tsou words whose NTU English label is NAF
  or NAV read NAF on the English standard tier: 415 labelled AUX by NTU, 5 i-si/i-he auxiliaries without the AUX
  label, and 23 words with adverbial meanings (na'na 'very' ×7, aka 'always' ×3, …), whose status is open on the
  2026-11-26 Tsou voice-gloss audit page.
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

- **Tsou 予格 ×1 (teoteai-neni) — UNDECIDED, on the todo list (maintainer 2026-11-18:
  "The lone 予格 token should be UNDECIDED and go on our todo list.").** The zho label
  予格 sits on the benefactive voice suffix -neni; the eng twin BF converts to OV (4th-voice
  ruling), so the standard tiers currently disagree on this one morpheme (zho 予格 verbatim,
  eng OV). The 予格 row stays UNDECIDED with its Saisiyat→DAT override; nothing fires for Tsou.
