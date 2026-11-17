# Handoff: gloss-standardization state at the 2026-11-15 machine switch

**Written 2026-11-15** by the Claude session that ran the gloss-standardization
project, for the next session on the maintainer's new computer. The old
container's auto-memory and scratchpad do not travel; this file, the tracked
`Glossing/` directory, and the claude.ai artifacts (cloud-side, including their
databases) are the complete state. Everything here is either committed fact
(with its file) or labeled as open.

## Read first, in this order

1. `.claude/skills/gloss-standardization/SKILL.md` — the purpose-built skill:
   read-first files, evidence bar, rulings discipline, artifact format, traps.
2. `claudeplans/sweep-qa-decision-log.md` — the maintainer's rulings record
   (committed to git for the first time in this handoff commit; it previously
   lived untracked on the old machine). Binding rule from CLAUDE.md: check
   every agent-instruction line against it; never cite a ruling he didn't make.
3. `Glossing/README.md`, `Glossing/.agentnotes.md`,
   `Glossing/OutstandingIssues.md` — the machinery and the open items.
4. `claudeplans/2026-11-11-gloss-standardization-design.md` — the design record
   (also first committed here; referenced by `.agentnotes.md`).

## State of the project

The bank-wide standard gloss tier is BUILT and MERGED to main (conversion
commit 2357ee91a; scaffold PR #350 also merged). Every glossed corpus carries
`TRANSL kindOf="standard"` beside each original gloss. Machinery:
`Glossing/ConversionTables/<Corpus>.tsv` (+ `.rules.tsv`),
`Glossing/GlossDictionaries/<Language>.tsv`, `Glossing/supplementary_codes.tsv`
(the registry gate: only Leipzig or registered codes enter a standard column),
applied by `QC/glossing/apply_gloss_standard.py`.

## Open thread 1 — derivational-morphology round 1 (this branch)

Branch `glossing/derivational-scoping`, commits 0781023cc + this handoff
commit. The scoping record is
`Glossing/ScopingReview/DerivationalMorphology.md`; the per-row gloss-code
counts behind it are `Glossing/ScopingReview/deriv_counts.json` (audit rule:
M-level elements, W only when unsegmented, one count per gloss tier; each row
carries its top-5 morpheme forms).

The decision page is **https://claude.ai/artifact/TaLCcmnb2HjxiYmC7zRaZB**
("Derivational Affixes Audit"). The maintainer answers on the page; its
done-button only writes a flag — he says in chat when he has responded. Then:

- Read the page's database with the ArtifactData tool against that URL,
  collection **`deriv_langs`**. Doc ids: the 8 card keys `card_ntu_zho`,
  `card_kana_rec`, `card_inch`, `card_song_caus`, `card_hps_cause`,
  `card_hps_stat`, `card_recp_rest`, `card_ntu_stav`, plus the 14 language
  names (per-language approve/modify). Doc shape:
  `{key, choice, note, updated}`; `_meta` holds the done flag.
- Apply his answers to the conversion tables / registry / dictionaries with
  his words in the `basis` column, quote back what was applied, and republish
  the page with only what is still open (read the page source first with the
  Artifact tool's read action on the URL — that returns the full HTML; the
  local source file did not survive the machine switch).

The 8 open proposals are listed at the end of `DerivationalMorphology.md`
(A–H: NTU zho twins → Latin; the NTU Kanakanavu REC ×34 = 重現 'recurrence'
mis-caught by the REC→RECP ruling; INCH register-or-fold; Song 使動; HPS
`cause`/`stat`; leftover reciprocal rows; NTU STAV).

## Open thread 2 — case-glossing round (older, still open)

Decision page **https://claude.ai/artifact/NCCiEyZBdqbprWoSY1N3WR**. As of
2026-11-13: 5 of 13 cards approved; awaiting the maintainer's re-clicks on
Bunun / Paiwan / Rukai and his calls on the Truku 受格 ×2 and Tsou 處格→LOC
proposals — those two are written up (with the evidence) in
`Glossing/OutstandingIssues.md`. The page's db collection name is in its
source; read the page with the Artifact tool's read action.

## Open thread 3 — CI: Corpus Metrics cannot push to main

After the conversion PR merged, the Corpus Metrics workflow's auto-commit push
to main was rejected (GH013): branch ruleset 27020744 requires the status
check **"build"** (the `build` job of `.github/workflows/pages.yaml`), and a
workflow's direct push cannot carry a pre-push check. The GitHub UI does not
offer "GitHub Actions" as a bypass actor (maintainer confirmed). Pending his
pick, options as proposed:

- **A (recommended, proportionate):** delete the required-status-check rule
  from ruleset 27020744 (Settings → Rules → Rulesets → main).
- **B:** add a **deploy key** as bypass actor and make the workflow push over
  SSH — needs a change to `.github/workflows/corpus-metrics.yaml` (checkout
  with `ssh-key: ${{ secrets.METRICS_DEPLOY_KEY }}`), which is a SHARED file:
  his approval first, `Shared-change-approved:` trailer on the commit.

After either fix: re-run the failed Corpus Metrics run so
`statistics/*.csv` + history CSVs regenerate (nothing was lost —
`--history-extend` recomputes the gap). Do-not-do: a bot-opens-PR design
fails silently because GITHUB_TOKEN pushes don't trigger workflows.

## Rules that were learned the hard way (full set was in the old machine's memory)

- A ruling needs his quoted words; log them; tables are the single source of
  truth; answers to questions are not approval to execute.
- Never use one language's/source's evidence to change another language's data.
- Decision pages: one question per card, no bundled cards, options must be
  policy-legal, option text bounds the change.
- Show scale before applying a broad ruling; never delete letter strings
  without confirmation.
- He cannot open worktree files — publish artifacts or hand him paths in the
  main checkout. He pushes and opens PRs himself (`gh` doesn't run in the
  container): give two copy-paste blocks (push inside container; `gh pr
  create` outside, no worktree paths).
- `trv` = Seediq-or-Truku by `dialect`, never plain Truku.
- Shared files (`QC/`, `.github/`, `.claude/`, root files, …) change only with
  his approval asked first + the commit trailer. `Glossing/`, `Corpora/`,
  `claudeplans/` are not shared.

## Not carried over (and where to regenerate)

- Full-text extracts of the 16 語法概論 grammar PDFs — regenerate with fitz
  from `/workspace/austronesian-voice/docs/*語法概論.pdf` if that repo exists
  on the new machine.
- The collaborators' AffixCategorization sheet dump — re-read
  `/workspace/austronesian-voice/docs/AffixCategorization .xlsx` (8 sheets;
  the 4 "Verb Affixes" sheets carry the `SEPARATOR?` column).
- All decision-page HTML sources — recover any page via the Artifact tool's
  read action on its URL before republishing.
- Untracked files on the old machine NOT in this commit (listed for the
  maintainer at handoff; lost unless he copies the old `claudeplans/`):
  October ILRDF/Wilang/ePark audio-check scripts and tables,
  `fey-sheet-live.csv` (collaborator Amis dictionary sheet — kept out of the
  public repo deliberately), `talk-figures-2026-10-19/`,
  `Glossing/Leipzig-Glossing-Rules.pdf` (copyrighted), the ePark errata PDFs.
