# Rights enforcement: canonical licences, a merge check, documented provenance (design)

**Status:** approved 2026-09-05 (maintainer: "looks good. Let's do that.";
audio consolidation added 2026-09-05 on the maintainer's question).
Establishes POL-042/043/044/045.

## Problem

Nothing in FormosanBank governs corpus rights. `POLICIES.md` has no entry on
licensing or permission evidence; `TEXT/@copyright` is free text validated by
nothing; and the corpus README templates carry only a `**License:**` line with
no requirement that it agree with the XML or say where the right came from.

Two failures followed, both observed in the August 2026 RE-PORT batch.

1. **Rights were removed on inference.** Five open PRs replace a Creative
   Commons licence with bespoke permission prose, each reasoning that the
   paperwork visible to the reviewer does not *prove* the licence: #179 ILRDF
   (16 files, `CC-BY-NC` → "Copyrighted; permission required outside applicable
   fair use"), #167 HundredPaiwanStories (100 files, `public domain` → "not a
   Creative Commons license"), #165 SEALS33, #174 MontgomeryTexts, #181
   WakelinTexts. #167 was subsequently overturned by the maintainer, who holds
   the correspondence the reviewer could not see. The evidence lives outside
   the repository, so absence of evidence in the repository is not evidence of
   absence — but nothing encoded that.

2. **The field is not machine-checkable.** Fifteen distinct `@copyright`
   strings are live across 26 corpora, including a transposed typo
   (`CC NC-BY`, RauDong, 20 files), six hyphenation and versioning variants of
   the same handful of licences, and three prose sentences. No validator reads
   the field; no CI job notices when it changes.

## Decision

Five mechanisms, ordered from the narrowest to the widest.

### 1. A canonical vocabulary

`rights_vocabulary.csv` at the repository root, joining `languages.csv`,
`dialects.csv` and `standards.csv` as a registry rather than a table hidden in
code (POL-039). Columns: `value`, `hf_license`, `url`, `notes`. The
`hf_license` column carries the Hugging Face slug, so that form is a lookup
rather than a second judgement (see §5).

Every `TEXT/@copyright` must equal one entry exactly. Initial contents:

```
value,hf_license,url,notes
CC BY 4.0,cc-by-4.0,https://creativecommons.org/licenses/by/4.0/,
CC BY-SA 4.0,cc-by-sa-4.0,https://creativecommons.org/licenses/by-sa/4.0/,
CC BY-NC 4.0,cc-by-nc-4.0,https://creativecommons.org/licenses/by-nc/4.0/,
CC BY-NC-SA 4.0,cc-by-nc-sa-4.0,https://creativecommons.org/licenses/by-nc-sa/4.0/,
CC BY-NC-ND 4.0,cc-by-nc-nd-4.0,https://creativecommons.org/licenses/by-nc-nd/4.0/,
public domain,,,not a licence; no rights reserved
```

Where a corpus's current value names no version, it normalizes to **4.0**
(maintainer ruling, 2026-09-05).

**No exceptions.** A corpus whose rights cannot be expressed as one of these
values is not published in FormosanBank, however genuine the permission behind
it. Permission that does not amount to a licence belongs in the README prose
and in the maintainer's records, not in `@copyright`.

Provenance does not live in this field. Where a corpus currently carries a
sentence (`Song, Limei (2018)… Licensed to FormosanBank under CC BY-NC 4.0 by
permission of the author (Li-May Sung).`; `CC BY-NC according to the frozen
amis-safolu README…`), the licence token stays in `@copyright` and the
sentence moves to the README's Rights section.

### 2. Two HARD validator rules

New module `QC/validation/rules/rights.py`, registered in the `RULES` list at
the bottom of `QC/validation/rules/hard.py`:

- **V160 HARD `copyright_present`** — `TEXT/@copyright` exists and is non-empty.
- **V161 HARD `copyright_in_vocabulary`** — the value equals a
  `rights_vocabulary.csv` entry exactly. The finding message names the offending
  value and lists the allowed set.

Both apply to published XML only. Validator discovery already skips
`CodeAndDocs/` (commit `eeac73977`), so pre-correction snapshots and source
ledgers held there are unaffected.

Both run inside the existing finding framework, so `validate_xml.py` reports
them in its summary and CSV, and the existing `xml-validation` CI job fails the
pull request. That job validates files changed by the PR, which is the only
path by which a non-conforming value can enter.

V161 is deliberately exact-match rather than a pattern. A pattern would accept
`CC BY-NC according to the frozen amis-safolu README…` — a sentence that
mentions a licence is not a licence declaration — and the `CC NC-BY` typo
demonstrates that free text admits errors no reader catches.

### 3. A merge check against `main`

`QC/validation/rights_delta.py` and `.github/workflows/rights-comparison.yaml`,
modelled on the existing `QC/tokens_delta.py` / `token-comparison.yaml` pair.

The script computes `{corpus → sorted set of @copyright values}` from the XML
at two refs and reports the difference as a table. The workflow runs on
`pull_request` and on `push` to `main`, comparing against the PR base or the
previous push, and **fails on any change**: a licence replaced, a licence added
or removed from a corpus's set, or a corpus disappearing entirely.

There is no committed baseline. A baseline would be redundant state that can
itself drift, and the comparison it enables is exactly what a merge check
already has available. The consequence is that a legitimate rights change —
including the RauDong typo fix — lands only by a maintainer overriding a red
required check. That friction is the point: it is the single hardest step in
the design, and it is placed on the operation the project most wants to be
deliberate. The maintainer confirmed this on 2026-09-05 — *"I actually like
the requirement of overriding a red required check for changes to rights. That
seems the right level of pushback."* — so there is no label-based escape hatch.

### 4. Documented provenance

`tests/corpora/test_rights_documentation.py` asserts, for every corpus under
`Corpora/`:

- the README contains a `## Rights` section;
- that section contains a `**License:**` line whose value is in the vocabulary
  and equals the `@copyright` carried by that corpus's XML;
- that section contains a `**Rights source:**` line, non-empty, of the shape
  `<grantor>, <YYYY-MM-DD>; evidence: ask maintainer`, where the date is when
  the permission was granted or last confirmed.

Example:

```markdown
## Rights

**License:** CC BY-NC 4.0
**Rights source:** R. J. Early, 2026-08-22; evidence: ask maintainer

R. J. Early granted FormosanBank permission to publish these texts and
supplied the source document. The permission correspondence is held by the
maintainer and is not distributed with the corpus.
```

The prose beneath is required by policy and unchecked by the test — grading it
is not something a test can do, and pretending otherwise would produce a test
that passes on filler. What the test does catch is the failure that actually
occurred: the XML and the documentation disagreeing about the licence.

`evidence: ask maintainer` rather than naming a system: the evidence store may
change, but the instruction to a reader who needs it will not.

`README.template.md` in the `port-corpus-in` skill gains the section, and
`{{LICENSE}}` moves into it.

On the GitBook side, `manage_corpus_pages.py check --strict` gains a rule that
each corpus page has a `## Copyright` section naming a vocabulary value. That
is a change in the `FormosanBankGitbook` repository and ships as its own pull
request.

### 5. Audio rights are derived, not recorded

`AUDIO-PERMISSIONS.md` already states the rule: *"If a corpus's XML is
published under `Corpora/` in FormosanBank, its associated audio is public
under the same license recorded in the XML."* `audio_permissions.json` repeats
it as `publication_rule`. The licence stored per audio source is therefore a
copy of something the XML already says — the duplication POL-039 exists to
prevent, and the reason a rights change has to be made twice (as #179 does).

It is also true in fact. Across all 22 entries, every published source's
licence equals its corpus's XML licence; the only two that differ are the
private development repositories `NTU_Paiwan_Raw` and `ePark3_Raw`, which
correctly carry no licence at all.

So the derived fields come out of `audio_permissions.json`:

- **Removed:** `license`, `hf_license`, `version_basis`, `basis`.
- **Kept**, because none of it is derivable: `permission_id`, `corpus`,
  `xml_path`, `status`, `access`, `hf_repositories`, `approval_record`.

A loader in `QC/validation/rights.py` resolves a source's licence by reading
the `@copyright` of the XML at its `xml_path`, and its Hugging Face slug by
looking up the `hf_license` column of `rights_vocabulary.csv`. A source whose
`status` is not published resolves to no licence, which is what the two private
repositories already record.

`QC/validation/validate_hf_audio.py` currently compares the two values through
a `license_family()` helper that strips versions and normalizes spelling —
a workaround for the very inconsistency the vocabulary removes. With the value
derived, there is nothing to compare: the comparison, the helper, and the
`hf_license`/`basis` presence checks all delete.

`AUDIO-PERMISSIONS.md` splits along the same seam. Its policy text — the
publication boundary, the version rule, the private-repository rule — moves to
POLICIES.md, which is where policy belongs and which the JSON already points at
via its `policy` field. Its licence table is generated from the JSON plus the
XML, or dropped in favour of pointing at them.

**Assumption made explicit:** one licence per corpus. A corpus whose items
carried different rights could not be expressed this way. That case does not
exist today and is deliberately not designed for (maintainer, 2026-09-05: "if
we ever have a situation where there are different rights for different items
in the same corpus, we'll deal with that then"). POL-042 states the assumption
so the next reader knows it was chosen rather than overlooked.

### 6. POLICIES.md — a new Rights section

- **POL-042 · licence vocabulary.** Every published `TEXT/@copyright` is one of
  the values in `rights_vocabulary.csv`: a Creative Commons licence or
  `public domain`. No exceptions. A corpus that cannot make that claim is not
  published. One licence per corpus: per-item rights variation is not
  representable and is not designed for. Enforced by V160/V161.
- **POL-043 · rights claims are not removed on inference.** An existing rights
  claim in published XML is never removed or weakened on the grounds that the
  reviewer could not find its evidence. Permission evidence is held by the
  maintainer, not in the repository, so its absence here proves nothing. A
  reviewer who doubts a claim escalates; only a positive finding — the source
  says otherwise, or the grant is known not to exist — justifies a change.
- **POL-044 · rights changes are interrogated at merge.** Any change to a
  corpus's licence, in either direction, fails
  `.github/workflows/rights-comparison.yaml` and lands only by explicit
  maintainer override. The README's `**Rights source:**` line names the grantor
  and the date; the evidence itself stays with the maintainer.
- **POL-045 · audio inherits the XML licence.** Audio published for a corpus
  carries that corpus's XML licence; audio for an unpublished corpus is not
  licensed for reuse. The licence is therefore never recorded separately —
  `audio_permissions.json` stores only what cannot be derived (repositories,
  access, status, approval pointer). Absorbs the policy text formerly in
  `AUDIO-PERMISSIONS.md`.

## What this forces, and in what order

The gate cannot go green while `main` violates it. Three corpora do; two are
now resolved.

| Corpus | Current value | Disposition |
|---|---|---|
| RauDong | `CC NC-BY` (20 files) | Transposition of `CC BY-NC`. Fixed by committed script (POL-038) to `CC BY-NC 4.0`. |
| Nowbucyang-Truku-Thesis | `© Lowking Wei-Cheng Hsu / 許韋晟. Used by FormosanBank with permission.` (1 file) | **Resolved 2026-09-05:** the corpus is `CC BY-NC 4.0`, granted by Nowbucyang (Lowking Wei-Cheng Hsu / 許韋晟). The attribution sentence moves to the README Rights section. |
| Glosbe | `© Glosbe and/or respective contributors…` (8 files) | No CC licence. Under POL-042 must be relicensed or unpublished. **Open — the last blocker.** |

Licence versions are settled: where a value names no version it normalizes to
4.0 (maintainer ruling, 2026-09-05). That removes what would otherwise have
been a per-corpus research task across ten corpora.

Implementation order follows from the gate:

1. `rights_vocabulary.csv`; a normalization script under `QC/utilities/`;
   RauDong's typo; Nowbucyang's licence; the Glosbe decision; Song's, Safolu's
   and Nowbucyang's provenance sentences moved to their READMEs.
2. V160/V161 and their unit tests — turned on only once step 1 leaves `main`
   conforming.
3. `rights_delta.py` and `rights-comparison.yaml`.
4. The audio consolidation: strip the derived fields from
   `audio_permissions.json`, add the loader, simplify `validate_hf_audio.py`,
   move `AUDIO-PERMISSIONS.md`'s policy text into POLICIES.md.
5. `test_rights_documentation.py`, the README template, and the 26 corpus
   README Rights sections.
6. POLICIES.md §5; the GitBook `manage_corpus_pages.py` rule as a separate PR
   there.

Steps 2–6 are independent of one another and all depend on step 1.

## Consequences for the open batch

Five RE-PORT pull requests become non-mergeable as written, because each moves
a corpus out of the vocabulary: #165 SEALS33, #167 HundredPaiwanStories, #174
MontgomeryTexts, #179 ILRDF, #181 WakelinTexts. Each needs its `@copyright`
restored to a vocabulary value and its provenance prose moved to the README's
Rights section, where POL-043 says it belonged all along.

This is the intended effect. The batch's rights judgements were made by
reviewers reasoning from an absence, and POL-042 removes the discretion that
made those judgements possible.

## Testing

- Unit tests for V160/V161 over fixtures: missing attribute, empty attribute,
  each vocabulary value, a hyphenation variant, the `CC NC-BY` typo, a prose
  sentence containing a valid token.
- A test that `rights_vocabulary.csv` parses, has unique values, and that every
  corpus under `Corpora/` conforms. This test fails until step 1 completes and
  is therefore written in step 1 and enabled at its end.
- Unit tests for `rights_delta.py` over two synthetic trees: unchanged,
  licence swapped, corpus added, corpus removed.
- `test_rights_documentation.py` doubles as the documentation test and the
  XML↔README consistency test.
- Audio derivation: a published source resolves to its corpus's XML licence and
  the matching `hf_license` slug; an unpublished source resolves to none; a
  source whose `xml_path` does not exist raises rather than defaulting. The
  existing `validate_hf_audio.py` tests are updated to drop the licence
  comparison they no longer need.

## Out of scope

Per-item rights within a corpus. POL-042 assumes one licence per corpus and
says so; the case does not exist today.

The ad-hoc per-corpus rights files that have appeared without documentation —
`ILRDF_Dicts/CodeAndDocs/source_data/RIGHTS.md` (in #179) and
`Nowbucyang-Truku-Thesis/CodeAndDocs/data/processed/rights_and_permission_notes.md`
(on `main`, different name, different path, different format) — are superseded
by the README Rights section and should be removed when their corpora are
touched. Neither is referenced by any documentation, template or skill.
