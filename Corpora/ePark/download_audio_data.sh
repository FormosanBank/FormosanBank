#!/bin/bash

# Script to download all FormosanBank ePark datasets using git lfs clone
# This script finds all datasets starting with "ePark" and downloads them one by one

set -e  # Exit on any error

echo "🔍 Finding all FormosanBank ePark datasets..."

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

# Get list of all FormosanBank datasets and filter for ePark ones
echo "Fetching dataset list from FormosanBank organization..."
datasets=$(hf datasets list --author FormosanBank --limit 100 --format json 2>/dev/null | jq -r '.[] | select(.id | startswith("FormosanBank/ePark_")) | .id | sub("FormosanBank/"; "")')

if [[ -z "$datasets" ]]; then
    echo "❌ No ePark datasets found or unable to fetch dataset list."
    echo "💡 Make sure you're logged in: hf auth login"
    echo "💡 And that the FormosanBank organization exists and has public datasets"
    echo "💡 Also check if jq is installed: brew install jq"
    exit 1
fi

echo "📋 Found the following ePark datasets:"
echo "$datasets"
echo ""

# Create downloads directory
download_dir="./Audio"
mkdir -p "$download_dir"
echo "📁 Downloads will be saved to: $download_dir"
echo ""

# Download each dataset
total_datasets=$(echo "$datasets" | wc -l)
current=1

for dataset in $datasets; do
    echo "📦 [$current/$total_datasets] Downloading: FormosanBank/$dataset"
    
    # Clean up dataset name for directory (remove ePark_ prefix and replace any forward slashes with underscores)
    clean_name=$(echo "$dataset" | sed 's/^ePark_//' | tr '/' '_')
    target_dir="$download_dir/$clean_name"
    
    # Skip if already exists
    if [[ -d "$target_dir" ]]; then
        echo "   ⏭️  Directory $target_dir already exists, skipping..."
        ((current++))
        continue
    fi
    
    # Clone using git lfs
    echo "   🚀 Cloning to $target_dir..."
    if git lfs clone "https://huggingface.co/datasets/FormosanBank/$dataset" "$target_dir"; then
        echo "   ✅ Successfully downloaded: $dataset"
        
        # Show size of downloaded dataset
        size=$(du -sh "$target_dir" 2>/dev/null | cut -f1 || echo "unknown")
        echo "   📊 Dataset size: $size"
    else
        echo "   ❌ Failed to download: $dataset"
        echo "   🔄 You can retry this specific dataset with:"
        echo "       git lfs clone https://huggingface.co/datasets/FormosanBank/$dataset $target_dir"
    fi
    
    echo ""
    ((current++))
done

echo "🎉 Download process completed!"
echo "📁 All datasets downloaded to: $download_dir"

# Summary
echo ""
echo "📊 Summary:"
echo "Total ePark datasets found: $total_datasets"
downloaded=$(find "$download_dir" -maxdepth 1 -type d ! -path "$download_dir" | wc -l)
echo "Successfully downloaded: $downloaded"

if [[ $downloaded -lt $total_datasets ]]; then
    echo "⚠️  Some downloads may have failed. Check the output above for details."
fi

echo ""
echo "🗂️  Downloaded datasets:"
ls -la "$download_dir"