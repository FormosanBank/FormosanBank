#!/bin/bash

# Fast parallel script to convert MP3 files to WAV format in-place
# Creates .wav files alongside .mp3 files in the same directories
# Parameters: 16000 Hz, mono

set -e  # Exit on any error

SOURCE_DIR="Final_audio"
LOG_FILE="conversion.log"

# Check if sox is installed
if ! command -v sox &> /dev/null; then
    echo "Error: sox is not installed. Please install it first."
    echo "On macOS: brew install sox"
    echo "On Ubuntu: sudo apt-get install sox"
    exit 1
fi

echo "Starting parallel in-place conversion of MP3 files to WAV (16kHz, mono)"
echo "Directory: $SOURCE_DIR"

# Count total files for progress tracking
TOTAL_FILES=$(find "$SOURCE_DIR" -name "*.mp3" | wc -l | tr -d ' ')
echo "Total MP3 files to convert: $TOTAL_FILES"
echo "Log file: $LOG_FILE"
echo "----------------------------------------"

# Clear log file
> "$LOG_FILE"

# Function to convert a single file
convert_file() {
    local mp3_file="$1"
    local wav_file="${mp3_file%.mp3}.wav"
    local relative_path="${mp3_file#$SOURCE_DIR/}"
    
    # Skip if WAV already exists
    if [[ -f "$wav_file" ]]; then
        echo "SKIP: $relative_path (WAV exists)" >> "$LOG_FILE"
        return 0
    fi
    
    # Convert using sox
    if sox "$mp3_file" -r 16000 -c 1 "$wav_file" 2>/dev/null; then
        echo "SUCCESS: $relative_path" >> "$LOG_FILE"
        return 0
    else
        echo "FAILED: $relative_path" >> "$LOG_FILE"
        return 1
    fi
}

# Export function for parallel processing
export -f convert_file
export SOURCE_DIR LOG_FILE

# Get number of CPU cores for optimal parallel processing
if command -v nproc &> /dev/null; then
    CORES=$(nproc)
elif command -v sysctl &> /dev/null; then
    CORES=$(sysctl -n hw.ncpu)
else
    CORES=4
fi

echo "Using $CORES parallel processes"

# Process files in parallel using xargs
find "$SOURCE_DIR" -name "*.mp3" -print0 | \
    xargs -0 -n 1 -P "$CORES" -I {} bash -c 'convert_file "$@"' _ {}

echo "----------------------------------------"
echo "Conversion completed!"

# Count results from log
CONVERTED=$(grep -c "SUCCESS:" "$LOG_FILE" 2>/dev/null || echo "0")
FAILED=$(grep -c "FAILED:" "$LOG_FILE" 2>/dev/null || echo "0")
SKIPPED=$(grep -c "SKIP:" "$LOG_FILE" 2>/dev/null || echo "0")

echo "Successfully converted: $CONVERTED files"
echo "Failed conversions: $FAILED files" 
echo "Skipped (already exist): $SKIPPED files"

# Final count verification
FINAL_COUNT=$(find "$SOURCE_DIR" -name "*.wav" | wc -l | tr -d ' ')
echo "Total WAV files in directory: $FINAL_COUNT"

if [[ $FAILED -gt 0 ]]; then
    echo ""
    echo "Failed files (see $LOG_FILE for details):"
    grep "FAILED:" "$LOG_FILE" | head -10
    if [[ $FAILED -gt 10 ]]; then
        echo "... and $((FAILED - 10)) more (check log file)"
    fi
fi