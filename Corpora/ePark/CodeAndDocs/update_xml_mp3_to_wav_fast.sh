#!/bin/bash

# Fast parallel script to replace .mp3 with .wav in all XML files
# Updates file references to match the converted audio files

set -e  # Exit on any error

SOURCE_DIR="Final_XML"
LOG_FILE="xml_update_fast.log"

echo "Starting fast parallel replacement of .mp3 with .wav in XML files"
echo "Directory: $SOURCE_DIR"
echo "Log file: $LOG_FILE"
echo "----------------------------------------"

# Clear log file
> "$LOG_FILE"

# Count total XML files
TOTAL_FILES=$(find "$SOURCE_DIR" -name "*.xml" | wc -l | tr -d ' ')
echo "Total XML files to process: $TOTAL_FILES"

# Function to process a single file
process_file() {
    local xml_file="$1"
    local relative_path="${xml_file#$SOURCE_DIR/}"
    
    # Check if file contains AUDIO elements with file attributes ending in .mp3
    if grep -q 'file="[^"]*\.mp3"' "$xml_file"; then
        # Replace .mp3 with .wav only in file attributes of AUDIO elements
        if sed -i '' 's/file="\([^"]*\)\.mp3"/file="\1.wav"/g' "$xml_file" 2>/dev/null; then
            # Count how many replacements were made
            local replacements=$(grep -o 'file="[^"]*\.wav"' "$xml_file" | wc -l | tr -d ' ')
            echo "MODIFIED: $relative_path ($replacements replacements)" >> "$LOG_FILE"
            return 0
        else
            echo "ERROR: Failed to modify $relative_path" >> "$LOG_FILE"
            return 1
        fi
    else
        echo "SKIP: $relative_path (no file=*.mp3 attributes)" >> "$LOG_FILE"
        return 0
    fi
}

# Export function for parallel processing
export -f process_file
export SOURCE_DIR LOG_FILE

# Get number of CPU cores
if command -v nproc &> /dev/null; then
    CORES=$(nproc)
elif command -v sysctl &> /dev/null; then
    CORES=$(sysctl -n hw.ncpu)
else
    CORES=4
fi

echo "Using $CORES parallel processes"

# Process files in parallel using xargs
find "$SOURCE_DIR" -name "*.xml" -print0 | \
    xargs -0 -n 1 -P "$CORES" -I {} bash -c 'process_file "$@"' _ {}

echo "----------------------------------------"
echo "Processing completed!"

# Count results from log
MODIFIED=$(grep -c "MODIFIED:" "$LOG_FILE" 2>/dev/null || echo "0")
ERRORS=$(grep -c "ERROR:" "$LOG_FILE" 2>/dev/null || echo "0")
SKIPPED=$(grep -c "SKIP:" "$LOG_FILE" 2>/dev/null || echo "0")

echo "Files modified: $MODIFIED"
echo "Files skipped (no .mp3 refs): $SKIPPED"
echo "Errors: $ERRORS"

if [[ $MODIFIED -gt 0 ]]; then
    echo ""
    echo "Sample modified files:"
    grep "MODIFIED:" "$LOG_FILE" | head -5
    if [[ $MODIFIED -gt 5 ]]; then
        echo "... and $((MODIFIED - 5)) more (check $LOG_FILE)"
    fi
fi

if [[ $ERRORS -gt 0 ]]; then
    echo ""
    echo "Errors encountered:"
    grep "ERROR:" "$LOG_FILE"
fi

# Final verification
echo ""
echo "Performing verification..."
TOTAL_WAV_FILE_ATTRS=$(find "$SOURCE_DIR" -name "*.xml" -exec grep -l 'file="[^"]*\.wav"' {} \; 2>/dev/null | wc -l | tr -d ' ')
TOTAL_MP3_FILE_ATTRS=$(find "$SOURCE_DIR" -name "*.xml" -exec grep -l 'file="[^"]*\.mp3"' {} \; 2>/dev/null | wc -l | tr -d ' ')

echo "XML files with file=\"*.wav\" attributes: $TOTAL_WAV_FILE_ATTRS"
echo "XML files with file=\"*.mp3\" attributes: $TOTAL_MP3_FILE_ATTRS"

if [[ $TOTAL_MP3_FILE_ATTRS -eq 0 ]]; then
    echo "✓ All file=\"*.mp3\" attributes successfully replaced with file=\"*.wav\""
else
    echo "⚠ Warning: $TOTAL_MP3_FILE_ATTRS files still contain file=\"*.mp3\" attributes"
fi