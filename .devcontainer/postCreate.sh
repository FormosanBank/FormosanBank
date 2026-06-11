#!/usr/bin/env bash
# Runs once when the dev container is created. Builds the Linux .venv in the
# named-volume mount and installs deps from the live requirements.txt.
set -euo pipefail

WS=/workspace/FormosanBank

# Named volumes mount as root; hand them to the non-root container user.
sudo chown -R vscode:vscode "$WS/.venv" /home/vscode/.claude 2>/dev/null || true

cd "$WS"

# (Re)create the venv if it's missing OR if its Python version no longer matches
# the container's Python (e.g. after a base-image change). The venv lives in a
# persisted named volume, so a stale version would otherwise shadow the new one.
# .venv itself is the volume mountpoint and can't be removed — clear its contents.
CONTAINER_PY="$(python --version 2>&1 | awk '{print $2}')"
VENV_PY=""
if [ -x .venv/bin/python ]; then
  VENV_PY="$(.venv/bin/python --version 2>&1 | awk '{print $2}')"
fi
if [ "$VENV_PY" != "$CONTAINER_PY" ]; then
  echo "[postCreate] (re)building Linux .venv for Python $CONTAINER_PY (was: ${VENV_PY:-none}) ..."
  rm -rf .venv/* .venv/.[!.]* 2>/dev/null || true
  python -m venv --upgrade-deps .venv
fi

# Belt-and-suspenders: guarantee pip exists in the venv. `python -m venv` on a
# freshly-cleared named volume has been observed to skip the pip bootstrap,
# which silently breaks the install below; ensurepip repairs that. Use
# `python -m pip` (not the bin/pip wrapper) so it works even if the wrapper
# script is stale.
.venv/bin/python -m ensurepip --upgrade >/dev/null 2>&1 || true

echo "[postCreate] installing deps from requirements.txt ..."
.venv/bin/python -m pip install --quiet --upgrade pip
.venv/bin/python -m pip install --quiet -r requirements.txt

# `hf` CLI for audio downloads (huggingface_hub[cli] extra).
.venv/bin/python -m pip install --quiet "huggingface_hub[cli]"

# --- Claude Code plugins -------------------------------------------------
# Mirror the host's enabled plugin set so custom skills (superpowers
# workflows, pr-review-toolkit, plugin-dev, etc.) are available in the
# container. Plugins install into the persisted ~/.claude named volume, so
# this is effectively one-time (re-runs find them already present). Headless-
# safe: fetching from GitHub needs no TTY and no Claude auth. typescript-lsp
# is intentionally omitted (pure-Python project; project settings disable it).
echo "[postCreate] provisioning Claude Code plugins ..."
claude plugin marketplace add anthropics/claude-plugins-official >/dev/null 2>&1 || true
for p in superpowers code-review skill-creator github claude-md-management \
         claude-code-setup pr-review-toolkit plugin-dev hookify pyright-lsp; do
  if claude plugin install "${p}@claude-plugins-official" >/dev/null 2>&1; then
    echo "[postCreate]   + ${p}"
  else
    echo "[postCreate]   ! ${p} (skipped / already present)"
  fi
done

echo "[postCreate] done. Linux .venv ready at $WS/.venv"
echo "[postCreate] NOTE: if Claude is not yet authenticated in this container,"
echo "[postCreate]       run 'claude login' once; the token persists in the"
echo "[postCreate]       formosanbank-claude-auth volume."
