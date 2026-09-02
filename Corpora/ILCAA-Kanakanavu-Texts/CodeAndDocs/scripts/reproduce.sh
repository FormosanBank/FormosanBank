#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
python_bin="${PYTHON:-$repo_root/.venv/bin/python}"
first_digest="$(mktemp)"
trap 'rm -f "$first_digest"' EXIT

cd "$repo_root"
make verify PYTHON="$python_bin"
make digest PYTHON="$python_bin" > "$first_digest"
make verify PYTHON="$python_bin"
second_digest="$(make digest PYTHON="$python_bin")"

if [[ "$(cat "$first_digest")" != "$second_digest" ]]; then
  echo "Two-pass reproduction digest mismatch" >&2
  exit 1
fi

diff -qr "$repo_root/XML" "$repo_root/../XML"
printf '%s\n' "$second_digest"
