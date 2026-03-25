#!/bin/bash

# Script to download NTUFormosanCorpus audio datasets from HuggingFace:
#   FormosanBank/NTUFormosanCorpus_Grammar → Audio/Grammar/
#   FormosanBank/NTUFormosanCorpus_Stories → Audio/Stories/
#
# Usage: ./download_audio_data.sh

set -e  # Exit on any error

echo "NTUFormosanCorpus audio download"
echo ""

# Check prerequisites
if ! command -v hf &> /dev/null; then
    echo "Error: 'hf' command not found. Please install huggingface_hub CLI:"
    echo "  pip install huggingface_hub[cli]"
    exit 1
fi

mkdir -p Audio/Grammar Audio/Stories

# --- Grammar ---
echo "[1/2] Downloading FormosanBank/NTUFormosanCorpus_Grammar → Audio/Grammar/"
if hf download FormosanBank/NTUFormosanCorpus_Grammar \
        --repo-type dataset \
        --local-dir Audio/Grammar; then
    count=$(find Audio/Grammar -type f -name "*.mp3" | wc -l | tr -d ' ')
    echo "  ✓ Grammar download complete ($count mp3 files)"
else
    echo "  ✗ Grammar download failed"
fi

echo ""

# --- Stories ---
echo "[2/2] Downloading FormosanBank/NTUFormosanCorpus_Stories → Audio/Stories/"
if hf download FormosanBank/NTUFormosanCorpus_Stories \
        --repo-type dataset \
        --local-dir Audio/Stories; then
    count=$(find Audio/Stories -type f -name "*.mp3" | wc -l | tr -d ' ')
    echo "  ✓ Stories download complete ($count mp3 files)"
else
    echo "  ✗ Stories download failed"
fi

echo ""
echo "Done."