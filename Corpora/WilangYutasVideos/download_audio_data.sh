#!/bin/bash

# Downloads the Audio/ folder from FormosanBank/YutasWilang on HuggingFace.
# Mirrors the structure uploaded by QC/utilities/upload_to_hf.py:
#   HF repo root  →  local Audio/
#   (e.g. Atayal/*.wav inside the repo lands in Audio/Atayal/*.wav locally)
# Usage: ./download_audio_data.sh

set -e  # Exit on any error

export HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1}
export HF_HUB_ENABLE_HF_TRANSFER=${HF_HUB_ENABLE_HF_TRANSFER:-0}

REPO_NAME="FormosanBank/YutasWilang"
AUDIO_DIR="Audio"

echo "Starting HuggingFace dataset download..."

# Check if hf command is available
if ! command -v hf &> /dev/null; then
    echo "Error: 'hf' command not found. Please install huggingface_hub CLI:"
    echo "pip install huggingface_hub[cli]"
    exit 1
fi

mkdir -p "$AUDIO_DIR"

echo "Repo : $REPO_NAME"
echo "Dest : $AUDIO_DIR/"
echo ""

if hf download "$REPO_NAME" \
        --repo-type=dataset \
        --local-dir "$AUDIO_DIR"; then
    echo ""
    echo "✓ Download complete."
    echo "  Files are in $AUDIO_DIR/"
else
    echo ""
    echo "✗ Download failed."
    exit 1
fi
