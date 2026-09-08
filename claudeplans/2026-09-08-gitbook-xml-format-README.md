# GitBook XML-format doc patch (Task 8)

**Fix round 1 (2026-09-08):** the patch below was regenerated after a
rendering-defect fix in `QC/validation/attributes_catalogue.py`. The
"Allowed values" cell for enumerated attributes (e.g. `FORM/@kindOf` →
`` `original | standard | alternate` ``) contained unescaped `|`
characters — backticks do not protect a pipe inside a GFM table cell, so
those three rows (`FORM/@kindOf`, `PHON/@kindOf`, `TRANSL/@kindOf`) would
have rendered with spilled/misaligned columns on GitHub and on the docs
site. The generator now escapes that cell the same way it already escaped
the documentation cell; `ATTRIBUTES.md` and this patch were regenerated
from the fix. See `.superpowers/sdd/2026-09-08-alternate-form-standardization/task-8-report.md`
for the full fix report (root-cause file, tests, commands run).

**Fix round 2 (2026-09-08, final review):** two wording fixes landed in
`QC/validation/xml_template.xsd` — `S/@id`'s `-opt` suffix now cites
POL-028 (POL-026 never mentions `-opt`; POL-028's scope clause does), and
`FORM/@kindOf`'s V150 description now reads "overlap it **and** stay in
proportion to it" (V150 flags if either condition fails, i.e. both must
hold — the old "or" stated a disjunction that was never the rule).
`ATTRIBUTES.md` and this patch were regenerated from those two fixes and
reapplication against the live `formosanbank-xml-format.md` was reverified
by the scratch-copy method.

This is a patch for a **different repository**,
`../FormosanBankGitbook` (`en-us/the-bank-architecture/formosanbank-xml-format.md`,
the canonical English page). It could not be committed directly here: that
repo is a separate git repository shared with other sessions, and this
sandbox blocks branch/commit/status operations against it. So the finished
edit is delivered as a patch file for a human (or a session with write
access to that repo) to apply.

## What the patch changes and why

1. **`<TRANSL>` `kindOf` bullet** — the old text ("The translation type,
   method, or provenance") read as an open licence to attach any provenance
   string to any `TRANSL`, and is why Glosbe carries 4,157 meaningless
   S-level uses of the attribute. Replaced with the ratified wording:
   `kindOf` is `original`/`standard`, meaningful only at W/M level (a gloss
   axis), and forbidden on sentence-level `TRANSL` (validator rule V151).

2. **`<FORM>` `alternate` bullet** — the old text ("A genuine alternate form
   retained alongside the main tiers") was vague enough to license a real
   data defect (an `alternate` FORM used for a competing *word*, not a
   spelling variant). Replaced with the ratified wording: `alternate` is a
   spelling variant of a sibling FORM, must have a non-alternate sibling,
   must be proportionate in length to it (neither more than 2x the other),
   and a competing word belongs in its own `<S>` per POL-027. Cites POL-028
   and validator rules V149 (HARD) / V150 (SOFT).

3. **New "Every attribute, in one place" section**, appended at the end of
   the page (after "Validation"). States the attribute set is closed (no
   `anyAttribute` in the schema) and that adding one requires a schema
   change, docs, a regenerated catalogue, and a policy entry (POL-053).
   Beneath that intro, it pastes the full attribute inventory from this
   repo's `QC/validation/ATTRIBUTES.md` (itself generated from
   `QC/validation/xml_template.xsd` by `attributes_catalogue.py`), with each
   `## ` heading demoted to `#### ` so the eight per-element tables (TEXT,
   S, W, M, FORM, PHON, TRANSL, AUDIO — 30 attributes total) nest under the
   new section instead of competing with the page's existing `### `
   headings.

Only the English (`en-us`) canonical page is touched. Other language
versions are out of scope per the task brief.

## Second, separate change required: re-sync `policies.md`

This branch also edits `POLICIES.md` (POL-028, POL-053, and an amendment
to POL-025). `/workspace/FormosanBankGitbook/.github/workflows/tests.yaml`
checks out FormosanBank@main and asserts that repo's synced
`en-us/the-bank-architecture/policies.md` matches FormosanBank's canonical
`POLICIES.md` byte-for-byte. Once this branch merges to FormosanBank main,
that assertion starts failing — the GitBook repo's copy is stale — and it
stays failing until someone re-syncs it. This is **unrelated to the patch
above**: the patch touches `formosanbank-xml-format.md`, the policies sync
touches `policies.md`, and they must be applied as two separate changes.

To re-sync, in the GitBook repo:

```bash
cd /workspace/FormosanBankGitbook
python sync_upstream_docs.py
git status --short   # confirm only policies.md changed
```

Commit and push (or PR) the result the same way as any other GitBook
change. Until this is done, `tests.yaml` in the GitBook repo will fail on
every push/PR there, not because of anything wrong in that repo but
because its copy of the policies page is out of date relative to
FormosanBank@main.

## How to apply

```bash
cd /workspace/FormosanBankGitbook
git status --short   # confirm no unrelated uncommitted work first
git checkout -b docs/xml-attribute-inventory
git apply /workspace/FormosanBank/.claude/worktrees/alternate-form-standardization/claudeplans/2026-09-08-gitbook-xml-format.patch
```

(Adjust the patch path if applying from a different worktree/checkout of
FormosanBank.)

## Commit message to use

```
Document the full XML attribute inventory; close the TRANSL/@kindOf ad-hoc licence

The kindOf line described the attribute as "the translation type, method,
or provenance", which reads as permission to attach any provenance string
to any TRANSL. Restrict it to original|standard at W/M level only, matching
POL-028/POL-053 and validator rule V151.

Also publishes every allowed attribute, generated from the XSD, so an
attribute legal in the schema can no longer be a validation surprise.
```

## After applying

Run the GitBook repo's own test suite before committing/pushing:

```bash
cd /workspace/FormosanBankGitbook
python -m pytest tests/ -q
```

If `manage_corpus_pages.py`'s linter complains about the new section,
follow its message — it governs page structure. (This wasn't run as part
of producing this patch, since doing so would require operating inside the
FormosanBankGitbook repo, which this sandbox does not allow from here.)

## How the patch was verified to apply cleanly

Two independent checks, both against the live current content of
`en-us/the-bank-architecture/formosanbank-xml-format.md` in
`/workspace/FormosanBankGitbook` as of 2026-09-08:

1. `cd /workspace/FormosanBankGitbook && git apply --check <patch>` —
   exited 0 with no complaints. (The brief's suggested invocation using
   `--git-dir=... --work-tree=...` from outside that directory failed with
   "No such file or directory" — a path-resolution quirk of that form, not
   a real problem with the patch — so the check was instead run the
   standard way, `cd`'d into the repo. `git apply --check` is a pure dry
   run: it does not stage, write, or touch the working tree, and `git
   status`/`git diff --stat` immediately after showed no changes and the
   target file's checksum was unchanged.)
2. Independently, the target file was copied to a scratch directory (no
   `.git` present) and the patch applied there for real with plain `git
   apply` (which works outside a repository). The result was byte-identical
   to the intended final content built directly from the brief's specified
   edits and `QC/validation/ATTRIBUTES.md`.

Both checks agree the patch applies cleanly and produces the intended
result.
