# Isolated dev container for FormosanBank

This `.devcontainer/` runs Claude Code (and everything it spawns) inside a Linux
container that can see **only** `~/Documents/Projects/Formosan` and nothing else
on your host. It's the enforcement layer that the host-level permission system
and the built-in sandbox do **not** provide: a stray `python` script physically
cannot read or write outside the mounted project, because the rest of your
filesystem does not exist inside the container.

## Why this exists

Permission rules gate *which commands Claude runs* but not *what those commands
do once running*. An empirical test on the bare host showed a permitted python
script writing to the home directory and reading the home dir listing — the
host sandbox was not active. This container closes that hole at the kernel level.

## What's mounted

| Host path | Container path | Notes |
|---|---|---|
| `~/Documents/Projects/Formosan` | `/workspace` | The whole parent dir — supports cross-repo workflows (port-corpus-in, gitbook sync). |
| (named volume `formosanbank-venv`) | `/workspace/FormosanBank/.venv` | Linux-native venv; shadows the macOS host `.venv`. |
| (named volume `formosanbank-claude-auth`) | `/home/vscode/.claude` | Persists the in-container Claude login. |

Nothing else from the host is visible.

## Daily use

1. Make sure Docker is running (`docker info` succeeds). Set Docker Desktop to
   launch at login so this is zero-effort.
2. In VS Code, open the FormosanBank folder, then run **Dev Containers: Reopen
   in Container** (Command Palette). First build takes a few minutes; subsequent
   opens reuse the cached image and persisted volumes.
3. The Claude Code extension runs **inside** the container automatically. Work
   in the chat panel as usual — but now prompt-free is safe, because the
   container is the boundary.

### Multiple concurrent agents

Open additional VS Code windows on other worktrees and Reopen each in a
container, **or** open multiple Claude chat panels in one container window, **or**
run the `claude` CLI in multiple container terminals (the CLI is baked into the
image). Each is a peer session; you orchestrate across them (there is no built-in
"dispatch to container and report back" for local containers — that UX only
exists for Anthropic's cloud agents, which would send code off-machine).

## Authentication

On macOS your Claude subscription token lives in the Keychain, which does not
exist in a Linux container. So the **first** time you use the container, run:

```bash
claude login
```

The OAuth token is stored in `/home/vscode/.claude` (the persisted volume), so
this is a one-time step, not per-session.

## Going prompt-free safely

Once you trust the boundary, you can run Claude in bypass-permissions mode
*inside the container* — the isolation, not the prompt, is your safety layer.
Do this only inside the container, never on the bare host.

## Verifying isolation yourself

From inside the container:

```bash
python3 -c "open('/etc/should-not-write','w')"   # should fail: read-only / not permitted
ls /Users 2>&1                                     # should fail: path doesn't exist in container
ls /workspace                                      # should show your Formosan repos
```

## Network

Currently open (needed for pip, Hugging Face audio downloads, git push). A
follow-up can add the Anthropic reference firewall to allowlist only required
domains (Anthropic API, Hugging Face, GitHub) if you want egress containment.

## Portability note

This directory is committed to the repo. It assumes the
`~/Documents/Projects/Formosan` layout (referenced via `${localEnv:HOME}` in
`devcontainer.json`), so it works on any machine that follows the same parent-dir
structure; on a different layout, adjust the `workspaceMount` source.
