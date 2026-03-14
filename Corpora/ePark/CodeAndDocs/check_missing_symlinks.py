#!/usr/bin/env python3
"""
Check if all missing files are broken symlinks.
"""

import re
from pathlib import Path

def check_missing_files():
    """Check the nature of all missing files."""
    
    missing_files_report = Path("missing_audio_files.txt")
    if not missing_files_report.exists():
        print("missing_audio_files.txt not found!")
        return
    
    # Extract file paths from the report
    missing_paths = []
    with open(missing_files_report, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith("Expected path: "):
                # Extract the path after "Expected path: "
                path_str = line.strip()[len("Expected path: "):]
                missing_paths.append(Path(path_str))
    
    print(f"Found {len(missing_paths)} missing file paths to check\n")
    
    # Stats
    total_files = len(missing_paths)
    broken_symlinks = 0
    missing_completely = 0
    other = 0
    completely_missing_files = []
    
    # Check each file
    for i, file_path in enumerate(missing_paths, 1):
        if i <= 10 or i % 100 == 0:  # Show first 10 and every 100th
            print(f"Checking {i}/{total_files}: {file_path.name}")
        
        if file_path.is_symlink():
            # It's a symlink - check if target exists
            try:
                target = file_path.readlink()
                target_exists = file_path.exists()  # This checks if target exists
                if not target_exists:
                    broken_symlinks += 1
                    if i <= 5:  # Show details for first few
                        print(f"  → BROKEN SYMLINK: points to {target}")
                else:
                    other += 1
                    if i <= 5:
                        print(f"  → Valid symlink: points to {target}")
            except Exception as e:
                other += 1
                if i <= 5:
                    print(f"  → Error reading symlink: {e}")
        elif file_path.exists():
            other += 1
            if i <= 5:
                print(f"  → File exists but verification missed it somehow")
        else:
            missing_completely += 1
            completely_missing_files.append(str(file_path))
            if i <= 5:
                print(f"  → Completely missing (not even a symlink)")
    
    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"{'='*60}")
    print(f"Total missing files: {total_files}")
    print(f"Broken symlinks: {broken_symlinks}")
    print(f"Completely missing: {missing_completely}")
    print(f"Other (valid symlinks, etc.): {other}")
    print()
    
    if broken_symlinks == total_files:
        print("✅ ALL missing files are broken symlinks!")
    elif broken_symlinks > 0:
        percentage = (broken_symlinks / total_files) * 100
        print(f"📊 {percentage:.1f}% of missing files are broken symlinks")
    else:
        print("❌ No broken symlinks found among missing files")
    
    if completely_missing_files:
        print(f"\n🔍 THE {len(completely_missing_files)} COMPLETELY MISSING FILES:")
        print("=" * 60)
        for i, missing_file in enumerate(completely_missing_files, 1):
            print(f"{i}. {missing_file}")

if __name__ == "__main__":
    check_missing_files()