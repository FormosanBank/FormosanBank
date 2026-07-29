#!/usr/bin/env bash

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPORA_DIR="$SCRIPT_DIR/Corpora"

if [[ ! -d "$CORPORA_DIR" ]]; then
    echo "Error: Corpora directory not found at $CORPORA_DIR" >&2
    exit 1
fi

found_count=0
succeeded_count=0
failed_corpora=()

for corpus_dir in "$CORPORA_DIR"/*; do
    [[ -d "$corpus_dir" ]] || continue
    script_path="$corpus_dir/download_audio_data.sh"
    [[ -f "$script_path" ]] || continue

    corpus_name="$(basename "$corpus_dir")"
    ((found_count += 1))
    echo "==> $corpus_name"

    if "$script_path" "$@"; then
        ((succeeded_count += 1))
    else
        failed_corpora+=("$corpus_name")
    fi
done

failed_count=${#failed_corpora[@]}
echo
echo "Audio download summary: found=$found_count succeeded=$succeeded_count failed=$failed_count"

if ((found_count == 0)); then
    echo "No corpus audio download scripts were found." >&2
    exit 1
fi

if ((failed_count > 0)); then
    printf 'Failed corpora: %s\n' "${failed_corpora[*]}" >&2
    exit 1
fi

echo "All public audio downloads completed successfully."
