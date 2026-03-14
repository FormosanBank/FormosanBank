#!/usr/bin/env python3
"""
Script to rename audio files by replacing Chinese prefixes with English folder names.

For example:
Final_audio/hui_ben_ping_tai_picture_book_platform/Saaroa/Saaroa/繪本平台_Saaroa_148873.mp3
-> Final_audio/hui_ben_ping_tai_picture_book_platform/Saaroa/Saaroa/hui_ben_ping_tai_picture_book_platform_Saaroa_148873.mp3
"""

import os
import re
from pathlib import Path

def extract_chinese_prefix(filename):
    """Extract Chinese character prefix from filename."""
    match = re.match(r'[\u4e00-\u9fff]+', filename)
    if match:
        return match.group()
    return None

def rename_audio_file(file_path):
    """Rename an audio file by replacing Chinese prefix with English folder name."""
    try:
        path = Path(file_path)
        filename = path.name
        
        # Check if filename has Chinese characters
        chinese_prefix = extract_chinese_prefix(filename)
        if not chinese_prefix:
            print(f"No Chinese prefix found in: {file_path}")
            return False
        
        # Get the folder 3 levels up from the file
        # Path structure: Final_audio/folder_name/language/dialect/file.mp3
        parts = path.parts
        if len(parts) >= 4 and parts[0] == 'Final_audio':
            folder_three_levels_up = parts[1]  # The main category folder
        else:
            print(f"Warning: Unexpected path structure for {file_path}")
            return False
        
        # Create the new filename by replacing Chinese prefix
        remainder = filename[len(chinese_prefix):]
        if remainder.startswith('_'):
            remainder = remainder[1:]  # Remove leading underscore
        
        new_filename = f"{folder_three_levels_up}_{remainder}"
        new_file_path = path.parent / new_filename
        
        # Check if the new file already exists
        if new_file_path.exists():
            print(f"Target file already exists: {new_file_path}")
            return False
        
        # Rename the file
        print(f"Renaming: {file_path}")
        print(f"     To: {new_file_path}")
        
        path.rename(new_file_path)
        return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def find_chinese_audio_files():
    """Find all audio files with Chinese characters in their names."""
    chinese_files = []
    for root, dirs, files in os.walk('Final_audio'):
        for file in files:
            if file.endswith(('.mp3', '.wav', '.m4a')):
                # Check if filename contains Chinese characters
                if re.search(r'[\u4e00-\u9fff]', file):
                    file_path = Path(root) / file
                    chinese_files.append(file_path)
    return chinese_files

def main():
    """Rename all audio files with Chinese prefixes."""
    chinese_files = find_chinese_audio_files()
    
    print(f"Found {len(chinese_files)} audio files with Chinese characters")
    print("=" * 50)
    
    if not chinese_files:
        print("No files to rename.")
        return
    
    # Auto-confirm for batch processing
    print(f"Starting to rename {len(chinese_files)} files...")
    print("This may take several minutes...")
    
    renamed_count = 0
    for file_path in sorted(chinese_files):
        if rename_audio_file(file_path):
            renamed_count += 1
    
    print("=" * 50)
    print(f"Successfully renamed {renamed_count} out of {len(chinese_files)} files")

if __name__ == '__main__':
    main()