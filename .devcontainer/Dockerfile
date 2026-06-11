# FormosanBank isolated dev container.
# Python 3.12 (NOT 3.13): the pinned scipy==1.13.1 / numpy==2.0.2 predate
# Python 3.13 and ship no cp313 wheels, so 3.13 forces a from-source scipy
# build (needs gfortran + BLAS). 3.12 has prebuilt Linux wheels for every pin
# in requirements.txt -> no compilation. Functionally identical for this code.
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Tooling the QC + audio pipelines need beyond Python:
#   git-lfs : audio assets pulled via LFS
#   jq      : used by download_audio_data.sh scripts
# (git, build tools, and a non-root `vscode` user already ship in the base image.)
# Drop the bundled yarn apt source first: its GPG key is expired in the base
# image and breaks `apt-get update`. We don't need yarn here.
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends git-lfs jq \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install --system

# Claude Code CLI, so you can run `claude` in any container terminal (the
# multi-agent pattern: several terminals, each its own prompt-free session).
# The npm package needs Node; install it from NodeSource first.
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g @anthropic-ai/claude-code \
    && rm -rf /var/lib/apt/lists/*

# Python deps are installed at container-create time (postCreate.sh) against the
# live requirements.txt from the mount, into a named-volume .venv — not baked
# into the image — so the env always matches the current requirements.txt and
# the macOS host .venv is never used inside the container.
