#!/bin/bash

# More efficient parallel script to convert MP3 files to WAV format
# Uses GNU parallel-style approach for better performance monitoring

set -e  # Exit on any error

SOURCE_DIR="Final_audio"
LOG_FILE="conversion_efficient.log"

# Check if sox is installed
if ! command -v sox &> /dev/null; then
    echo "Error: sox is not installed. Please install it first."
    echo "On macOS: brew install sox"
    echo "On Ubuntu: sudo apt-get install sox"
    exit 1
fi

echo "Starting efficient parallel conversion of MP3 files to WAV (16kHz, mono)"
echo "Directory: $SOURCE_DIR"

# Count total files for progress tracking
TOTAL_FILES=$(find "$SOURCE_DIR" -name "*.mp3" | wc -l | tr -d ' ')
echo "Total MP3 files to convert: $TOTAL_FILES"
echo "Log file: $LOG_FILE"

# Get number of CPU cores
if command -v nproc &> /dev/null; then
    CORES=$(nproc)
elif command -v sysctl &> /dev/null; then
    CORES=$(sysctl -n hw.ncpu)
else
    CORES=4
fi

echo "Using $CORES parallel processes"
echo "Monitor with: ps aux | grep sox"
echo "----------------------------------------"

# Clear log file
> "$LOG_FILE"

# Create temporary script for each conversion
TEMP_SCRIPT=$(mktemp)
cat > "$TEMP_SCRIPT" << 'EOF'
#!/bin/bash
mp3_file="$1"
wav_file="${mp3_file%.mp3}.wav"

# Skip if WAV already exists
if [[ -f "$wav_file" ]]; then
    echo "SKIP: $(basename "$mp3_file")" 
    exit 0
fi

# Convert using sox
if sox "$mp3_file" -r 16000 -c 1 "$wav_file" 2>/dev/null; then
    echo "SUCCESS: $(basename "$mp3_file")"
    exit 0
else
    echo "FAILED: $(basename "$mp3_file")"
    exit 1
fi
EOF

chmod +x "$TEMP_SCRIPT"

# Use xargs for direct parallel execution
find "$SOURCE_DIR" -name "*.mp3" -print0 | \
    xargs -0 -n 1 -P "$CORES" "$TEMP_SCRIPT" | \
    tee -a "$LOG_FILE"

# Clean up
rm "$TEMP_SCRIPT"

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