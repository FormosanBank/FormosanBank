#!/bin/bash

# Script to check every main folder in Corpora for download_audio_data.sh
# and execute it if found

set -e  # Exit on any error

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORPORA_DIR="$SCRIPT_DIR/Corpora"

echo "Checking for download_audio_data.sh scripts in Corpora subfolders..."
echo "Corpora directory: $CORPORA_DIR"
echo

# Check if Corpora directory exists
if [[ ! -d "$CORPORA_DIR" ]]; then
    echo "Error: Corpora directory not found at $CORPORA_DIR"
    exit 1
fi

# Counter for found scripts
found_count=0
executed_count=0

# Iterate through each subdirectory in Corpora
for dir in "$CORPORA_DIR"/*; do
    # Skip if not a directory
    if [[ ! -d "$dir" ]]; then
        continue
    fi
    
    # Get just the folder name
    folder_name=$(basename "$dir")
    
    # Check for download_audio_data.sh in this directory
    script_path="$dir/download_audio_data.sh"
    
    if [[ -f "$script_path" ]]; then
        echo "✓ Found download_audio_data.sh in: $folder_name"
        ((found_count++))
        
        # Make the script executable
        echo "  Making script executable..."
        chmod +x "$script_path"
        
        # Execute the script from within its directory
        echo "  Executing script..."
        (
            cd "$dir"
            if ./download_audio_data.sh; then
                echo "  ✓ Successfully executed download_audio_data.sh in $folder_name"
                ((executed_count++))
            else
                echo "  ✗ Failed to execute download_audio_data.sh in $folder_name"
            fi
        )
        echo
    else
        echo "- No download_audio_data.sh found in: $folder_name"
    fi
done

echo
echo "Summary:"
echo "  Found $found_count download_audio_data.sh scripts"
echo "  Successfully executed $executed_count scripts"

if [[ $found_count -eq 0 ]]; then
    echo "No download_audio_data.sh scripts were found in any Corpora subfolder."
elif [[ $executed_count -eq $found_count ]]; then
    echo "All found scripts executed successfully!"
else
    echo "Some scripts failed to execute. Check the output above for details."
fi