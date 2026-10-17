# Checklist: re-port (the corpus already exists on main)

Diff both sides against the **merge base**, not main's tip. The predecessor is what makes id changes, removals and rights changes legible.

1. **The content delta, and the audit artifact that explains it.** Run what CI runs:
   ```bash
   rm -rf /tmp/base && mkdir -p /tmp/base && git archive <merge-base> -- Corpora/<Name> | tar -x -C /tmp/base
   <python> QC/validation/content_delta.py --base /tmp/base/Corpora --head Corpora --corpus <Name>
   ```
   Every red line (TEXT ids removed or renamed, S removed or renumbered, counts down per tier, dialect or licence changed) blocks the merge until the maintainer overrides it. The audit's deliverable is one page for the PR: a row per class of change with its count, **the decision it traces to** (a quoted ruling from the decision log, a disclosure in the PR body, a POL entry) or the flag **"no approved decision found"**. Rows with the flag are questions; rows with a trace are what the override is for. (The shape the maintainer asked for on PRs #173 and #164: "an audit artifact that explains the changes and why they were expected and flag any that didn't result from decisions explicitly approved.")
   Example rows: #199 `TEXT/@dialect → unknown` ×8 — nothing found — *no approved decision*; #166 Dutch TRANSL removed ×26 — body: "removes the 26 misplaced Matthew 18 copies" — traced.

2. **Ids kept** (POL-037). 0 of N surviving is a breaking change to announce, with a reason, never a cleanup.
   Example: #179 rehashed all 98,837 ILRDF ids.

3. **Removals disclosed with counts** (POL-051). Silence is the finding, not the deletion.
   Example: #164 removed 18,943 sentence AUDIO, 407,868 original PHON and 20 TRANSL that neither the body nor the review table mentioned.

4. **Dialect kept.** `TEXT/@dialect` per TEXT against the merge base; a value collapsing to `unknown` routes `trv` records to Seediq.

5. **Licence kept, or changed on purpose** (POL-043/044). `rights_delta.py` red by design; a downgrade from absence is a finding against the PR.

6. **Reversals explicit** (POL-050). A change that undoes something merged cites the commit or POL entry it supersedes (re-adding a standard tier a ruling removed is the recurring case).

7. **The pending lists.** A re-port is when the corpus's lines in `generate_xml_pending.txt`, `provenance_pending.txt`, `readme_sections_pending.txt` and `xml_dir_pending.txt` go (CI refuses a PR whose rebuilt corpus still shelters on one).

8. **The PR body is a claim about one SHA.** Re-check counts at the head you audit, not the commit the body describes (Wilang's "no sentences removed" was true at the body's commit and false at the head).

9. **Provenance refreshed by the build** (POL-052). A rebuilt corpus with September's commit in `provenance.json` is a stale record (the static test warns).
