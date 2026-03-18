#!/bin/bash

# Script to download all FormosanBank Whitehorn datasets using git lfs clone
# This script finds all datasets starting with "Whitehorn" and downloads them one by one

set -e  # Exit on any error

echo "🔍 Downloading FormosanBank Whitehorn dataset..."

# Check if git is installed
echo "🔧 Checking prerequisites..."
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first:"
    echo "   brew install git"
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

if ! git lfs install; then
    echo "❌ Failed to set up Git LFS configuration."
    exit 1
fi

# Create downloads directory
download_dir="./Audio"
echo "📁 Audio files will be saved to: $download_dir"

# Check if already exists
if [[ -d "$download_dir" ]]; then
    echo "⏭️  Directory $download_dir already exists, skipping download..."
    echo "🗂️  Current contents:"
    ls -la "$download_dir"
    exit 0
fi

echo ""
echo "📦 Downloading FormosanBank/Whitehorn_Collection..."

# Clone using git lfs
echo "🚀 Cloning Whitehorn_Collection..."
if git lfs clone "https://huggingface.co/datasets/FormosanBank/Whitehorn_Collection" "Whitehorn_Collection"; then
    echo "✅ Successfully downloaded Whitehorn_Collection"
    
    # Rename to Audio
    echo "📁 Renaming Whitehorn_Collection to Audio..."
    mv "Whitehorn_Collection" "$download_dir"
    
    # Show size
    size=$(du -sh "$download_dir" 2>/dev/null | cut -f1 || echo "unknown")
    echo "📊 Dataset size: $size"
else
    echo "❌ Failed to download Whitehorn_Collection"
    echo "🔄 You can retry with:"
    echo "    git lfs clone https://huggingface.co/datasets/FormosanBank/Whitehorn_Collection"
    exit 1
fi

echo "🎉 Download completed successfully!"

echo ""
echo "🗂️  Audio directory contents:"
ls -la "$download_dir"