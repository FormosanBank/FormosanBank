#!/bin/bash

# Script to check if MP3 versions exist for missing WAV files

echo "Checking for MP3 versions of missing WAV files..."
echo "=================================================="

# List of missing WAV files with their expected paths
declare -a missing_files=(
    "Final_audio/yue_du_shu_xie_pian_reading_writing/Seediq/Duda_Seediq/yue_du_shu_xie_pian_reading_writing_Duda_Seediq_82.wav"
    "Final_audio/yue_du_shu_xie_pian_reading_writing/Seediq/Duda_Seediq/yue_du_shu_xie_pian_reading_writing_Duda_Seediq_85.wav"
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_221.wav"
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_222.wav"
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_231.wav"
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_233.wav"
    "Final_audio/wen_hua_pian_cultural_section/Amis/Xiuguluan_Amis/wen_hua_pian_cultural_section_1_Xiuguluan_Amis_234.wav"
    "Final_audio/ju_xing_pian_gao_zhong_sentence_patterns_senior_high/Amis/Xiuguluan_Amis/128.wav"
)

mp3_exists=0
mp3_missing=0
wav_exists=0

for wav_file in "${missing_files[@]}"; do
    # Convert WAV path to MP3 path
    mp3_file="${wav_file%.wav}.mp3"
    
    echo ""
    echo "Checking: $(basename "$wav_file")"
    echo "  WAV path: $wav_file"
    echo "  MP3 path: $mp3_file"
    
    # Check if WAV exists (should be missing according to report)
    if [[ -f "$wav_file" ]]; then
        echo "  ✓ WAV file exists (report may be outdated)"
        ((wav_exists++))
    else
        echo "  ✗ WAV file missing (confirmed)"
        
        # Check if MP3 exists
        if [[ -f "$mp3_file" ]]; then
            echo "  ✓ MP3 file exists - conversion needed"
            ((mp3_exists++))
        else
            echo "  ✗ MP3 file also missing"
            ((mp3_missing++))
            
            # Check if directory exists
            mp3_dir="$(dirname "$mp3_file")"
            if [[ -d "$mp3_dir" ]]; then
                echo "    Directory exists, checking for similar files:"
                ls -la "$mp3_dir" | head -5
            else
                echo "    Directory doesn't exist: $mp3_dir"
            fi
        fi
    fi
done

echo ""
echo "Summary:"
echo "========"
echo "WAV files that actually exist: $wav_exists"
echo "MP3 files found (need conversion): $mp3_exists" 
echo "Files completely missing: $mp3_missing"

if [[ $mp3_exists -gt 0 ]]; then
    echo ""
    echo "Files that need conversion:"
    for wav_file in "${missing_files[@]}"; do
        mp3_file="${wav_file%.wav}.mp3"
        if [[ -f "$mp3_file" && ! -f "$wav_file" ]]; then
            echo "  sox \"$mp3_file\" -r 16000 -c 1 \"$wav_file\""
        fi
    done
fi