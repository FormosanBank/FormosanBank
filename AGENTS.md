# AGENTS.md

This repository's agent guidance lives in **[CLAUDE.md](CLAUDE.md)** — read that
file. Despite its name it is harness-agnostic: repo overview, development
workflow, corpus layout and XML schema, QC script conventions, and the
conventions worth preserving. Project policy rulings are in
[POLICIES.md](POLICIES.md).

This file exists so that agents which look for `AGENTS.md` find their way there.
It is deliberately a pointer and not a copy: it was previously a duplicate of
`CLAUDE.md` and silently went stale, telling agents the wrong things about the
`original` tier and about how `apply_manual_edits.py` handles no-op records.
Keep it a pointer.
