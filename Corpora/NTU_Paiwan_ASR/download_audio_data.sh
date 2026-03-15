#!/bin/bash

# Script to download all FormosanBank NTU_Paiwan_ASR datasets using git lfs clone
# This script finds all datasets starting with "NTU_Paiwan_ASR" and downloads them one by one

set -e  # Exit on any error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "🔍 Finding all FormosanBank NTU_Paiwan_ASR datasets..."

# Check if git is installed
echo "🔧 Checking prerequisites..."
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first:"
    echo "   brew install git"
    exit 1
fi

# Check if Hugging Face CLI is installed
if ! command -v hf &> /dev/null; then
    echo "❌ Hugging Face CLI is not installed. Please install it first:"
    echo "   pip install huggingface_hub[cli]"
    echo "   # or: pip install --upgrade huggingface_hub"
    exit 1
fi

# Check if jq is installed (for JSON parsing)
if ! command -v jq &> /dev/null; then
    echo "❌ jq is not installed. Please install it first:"
    echo "   brew install jq"
    exit 1
fi

# Ensure Git LFS is properly installed and configured
echo "🔧 Setting up Git LFS..."
if ! command -v git-lfs &> /dev/null && ! git lfs version &> /dev/null; then
    echo "❌ Git LFS is not installed. Please install Git LFS first:"
    echo "   brew install git-lfs"
    exit 1
fi

if ! git lfs install; then
    echo "❌ Failed to set up Git LFS configuration."
    exit 1
fi

# Get list of all FormosanBank datasets and filter for NTU_Paiwan_ASR ones
echo "Fetching dataset list from FormosanBank organization..."
datasets=$(hf datasets ls --author FormosanBank --limit 100 --format json 2>/dev/null | jq -r '.[] | select(.id | startswith("FormosanBank/NTU_Paiwan_ASR_")) | .id | sub("FormosanBank/"; "")')

if [[ -z "$datasets" ]]; then
    echo "❌ No NTU_Paiwan_ASR datasets found or unable to fetch dataset list."
    echo "💡 Make sure you're logged in: hf auth login"
    echo "💡 And that the FormosanBank organization exists and has public datasets"
    echo "💡 Also check if jq is installed: brew install jq"
    exit 1
fi

echo "📋 Found the following NTU_Paiwan_ASR datasets:"
echo "$datasets"
echo ""

# Create downloads directory
download_dir="$SCRIPT_DIR/Audio"
mkdir -p "$download_dir"
echo "📁 Downloads will be saved to: $download_dir"
echo ""

# Download each dataset
total_datasets=$(echo "$datasets" | wc -l)
current=1

for dataset in $datasets; do
    echo "📦 [$current/$total_datasets] Downloading: FormosanBank/$dataset"
    
    # Clone to a temp directory, then merge into $download_dir
    temp_dir=$(mktemp -d)
    
    # Clone using git lfs into temp dir
    echo "   🚀 Cloning to temp directory..."
    if git lfs clone "https://huggingface.co/datasets/FormosanBank/$dataset" "$temp_dir/dataset"; then
        echo "   ✅ Successfully cloned: $dataset"
        
        # Merge contents into download_dir (rsync merges directories, filenames are unique so no overwrites)
        echo "   🔀 Merging into $download_dir..."
        rsync -a "$temp_dir/dataset/" "$download_dir/"
        
        # Show size contribution
        size=$(du -sh "$temp_dir/dataset" 2>/dev/null | cut -f1 || echo "unknown")
        echo "   📊 Dataset size: $size"
    else
        echo "   ❌ Failed to download: $dataset"
        echo "   🔄 You can retry this specific dataset with:"
        echo "       git lfs clone https://huggingface.co/datasets/FormosanBank/$dataset <temp_dir>"
    fi
    
    # Clean up temp dir
    rm -rf "$temp_dir"
    
    echo ""
    ((current++))
done

echo "🎉 Download process completed!"
echo "📁 All datasets downloaded to: $download_dir"

# Summary
echo ""
echo "📊 Summary:"
echo "Total NTU_Paiwan_ASR datasets found: $total_datasets"
downloaded=$(find "$download_dir" -maxdepth 1 -type d ! -path "$download_dir" | wc -l)
echo "Successfully downloaded: $downloaded"

if [[ $downloaded -lt $total_datasets ]]; then
    echo "⚠️  Some downloads may have failed. Check the output above for details."
fi

echo ""
echo "🗂️  Downloaded datasets:"
ls -la "$download_dir"

python "$SCRIPT_DIR/CodeAndDocs/extract_audio_clips.py" --xml_root "$SCRIPT_DIR/XML" --audio_root "$SCRIPT_DIR/Audio"
