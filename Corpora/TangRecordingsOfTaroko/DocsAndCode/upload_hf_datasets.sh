#!/bin/bash

# Uploads the Audio/ folder to FormosanBank/TangRecordingsOfTaroko on HuggingFace.
# Audio/ must contain a Truku/ subfolder (and optionally others).
# The subfolder structure is preserved in the dataset repo.
# Usage: ./upload_hf_datasets.sh

set -e  # Exit on any error

# Reliability knobs:
# - The Hub CLI may use optional Rust backends (Xet / hf_transfer). When they misbehave,
#   uploads can fail with errors like: "Data processing error: Format error: I/O error: failed to fill whole buffer".
#   Disabling them forces the pure-Python HTTP uploader, which is slower but typically more stable.
export HF_HUB_DISABLE_XET=${HF_HUB_DISABLE_XET:-1}
export HF_HUB_ENABLE_HF_TRANSFER=${HF_HUB_ENABLE_HF_TRANSFER:-0}

# Lower parallelism tends to reduce intermittent commit/upload errors for many small files.
NUM_WORKERS=${NUM_WORKERS:-1}

REPO_NAME="FormosanBank/TangRecordingsOfTaroko"
AUDIO_DIR="Audio"

echo "Starting HuggingFace dataset upload..."

# Check if Audio directory exists
if [ ! -d "$AUDIO_DIR" ]; then
    echo "Error: Audio directory not found!"
    exit 1
fi

# Check if hf command is available
if ! command -v hf &> /dev/null; then
    echo "Error: 'hf' command not found. Please install huggingface_hub CLI:"
    echo "pip install huggingface_hub[cli]"
    exit 1
fi

file_count=$(find "$AUDIO_DIR" -type f ! -name ".DS_Store" | wc -l)
echo "Repo  : $REPO_NAME"
echo "Source: $AUDIO_DIR/  ($file_count files)"
echo ""

if hf upload-large-folder "$REPO_NAME" "$AUDIO_DIR" \
        --repo-type=dataset \
        --num-workers "$NUM_WORKERS" \
        --exclude "**/.DS_Store"; then
    echo ""
    echo "✓ Upload complete."
    echo "  https://huggingface.co/datasets/$REPO_NAME"
else
    echo ""
    echo "✗ Upload failed."
    exit 1
fi