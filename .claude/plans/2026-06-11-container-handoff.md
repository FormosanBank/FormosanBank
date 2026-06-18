# Handoff: continuing inside the dev container

**Written:** 2026-06-11, from a host-side Claude session, just before the first
"Reopen in Container". The host conversation does NOT carry into the container
(separate `~/.claude`), so this note is the continuity bridge.

## Where we are

Working branch: **`feature/claude-tooling-phase-0`**.

This branch is implementing sub-project **E** (Claude Code project tooling) from
[`2026-05-27-e-claude-code-tooling-implementation.md`](2026-05-27-e-claude-code-tooling-implementation.md).
Broader context is in [`2026-05-27-roadmap.md`](2026-05-27-roadmap.md).

### Done + committed on this branch
- **Task 1** — `.claude/hooks/block-statistics-edits.py` (PreToolUse hook blocking edits under `statistics/`) + test. Registered in `.claude/settings.json`.
- **Task 2** — `.claude/hooks/check-venv.py` (SessionStart hook warning on missing/incomplete `.venv`) + test. Also in `.claude/settings.json`.
- **Task 3** — `.claude/skills/setup-new-dev-repo.md` + templates.

### Paused (not yet implemented)
- **Task 4** — `.claude/skills/run-qc-pipeline.md` + summary template. Full spec is in the implementation plan, Task 4.
- **Task 5** — `.claude/skills/port-corpus-in.md` + README template. Spec in the plan, Task 5.
- Final code review of the whole E branch.

### Container work (this detour)
- `.devcontainer/` (Dockerfile, devcontainer.json, postCreate.sh, README.md) was built because an empirical test proved the **host has no active sandbox** — a permitted python script wrote to `~/` on the bare host.
- The container image builds and **isolation is verified**: inside the container, `/Users` does not exist and writes outside `/workspace` fail. Only `~/Documents/Projects/Formosan` (mounted at `/workspace`) is reachable.
- `.devcontainer/` is currently **untracked** (not committed) — decide whether to commit it.

## First steps inside the container

1. The `postCreate.sh` should have built a Linux `.venv` at `/workspace/FormosanBank/.venv` (named volume). Confirm: `.venv/bin/python --version` → 3.13.x, and `.venv/bin/python -c "import lxml, pandas, regex"` succeeds.
2. **Auth:** the macOS Keychain login did NOT cross into Linux. If Claude isn't authenticated, run `claude login` once; the token persists in the `formosanbank-claude-auth` volume.
3. Sanity-check isolation yourself: `ls /Users 2>&1` (should fail), `ls /workspace` (should list all Formosan repos).
4. You can now run prompt-free safely *inside the container* — the boundary, not the prompt, is the safety layer.

## Resuming the actual work

To continue E: pick up **Task 4** from the implementation plan. The subagent-driven
workflow we were using dispatches a fresh implementer per task, then a spec review,
then a code-quality review, fixing issues between. Tasks 1–3 were done that way.

## Open follow-ups
- Network firewall (egress allowlist) for the container — deferred; currently open network.
- Decide whether `.devcontainer/` gets committed.
- The `formosanbank-dev-test` Docker image (used for CLI verification) can be removed: `docker rmi formosanbank-dev-test`.
