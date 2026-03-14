#!/bin/bash

# Convert the 6 missing M4A/AAC files (with .mp3 extensions) to WAV using ffmpeg

echo "Converting missing M4A/AAC files to WAV using ffmpeg..."

# Array of files that need conversion
declare -a files_to_convert=(
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_221"
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_222"
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_231"
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_233"
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_234"
    "Final_audio/ju_xing_pian_gao_zhong_sentence_patterns_senior_high/Amis/Xiuguluan_Amis/128"
)

converted=0
failed=0

for base_path in "${files_to_convert[@]}"; do
    mp3_file="${base_path}.mp3"
    wav_file="${base_path}.wav"
    
    echo "Converting: $(basename "$mp3_file") (M4A/AAC)"
    
    if ffmpeg -i "$mp3_file" -ar 16000 -ac 1 "$wav_file" -y >/dev/null 2>&1; then
        echo "  ✓ Success"
        ((converted++))
    else
        echo "  ✗ Failed"
        ((failed++))
    fi
done

echo ""
echo "Conversion completed:"
echo "  Successfully converted: $converted files"
echo "  Failed: $failed files"

if [[ $converted -gt 0 ]]; then
    echo ""
    echo "Verifying created files:"
    for base_path in "${files_to_convert[@]}"; do
        wav_file="${base_path}.wav"
        if [[ -f "$wav_file" ]]; then
            size=$(ls -lh "$wav_file" | awk '{print $5}')
            echo "  ✓ $(basename "$wav_file") exists ($size)"
        fi
    done
fi

# Clean up test files
rm -f test_output.wav test_output_ffmpeg.wav