#!/usr/bin/env python3
"""
Download missing audio files from their original URLs and place them in correct locations.
"""

import requests
import time
from pathlib import Path
from lxml import etree
import re
from urllib.parse import urlparse
import sys

def extract_missing_files():
    """Extract missing file paths and their details from the report."""
    missing_files_report = Path("missing_audio_files.txt")
    if not missing_files_report.exists():
        print("missing_audio_files.txt not found!")
        return []
    
    missing_files = []
    current_file = {}
    
    with open(missing_files_report, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and line[0].isdigit() and ". XML File:" in line:
                # New entry - save previous if exists
                if current_file:
                    missing_files.append(current_file)
                
                # Extract XML file path
                xml_file_match = re.search(r'XML File: (.+\.xml)', line)
                if xml_file_match:
                    current_file = {'xml_file': Path(xml_file_match.group(1))}
                    
            elif line.startswith("Audio filename:"):
                audio_file = line.replace("Audio filename:", "").strip()
                current_file['audio_filename'] = audio_file
                
            elif line.startswith("Expected path:"):
                expected_path = line.replace("Expected path:", "").strip()
                current_file['expected_path'] = Path(expected_path)
    
    # Don't forget the last entry
    if current_file:
        missing_files.append(current_file)
    
    return missing_files

def find_audio_url(xml_file, audio_filename):
    """Find the URL for a specific audio file in the XML."""
    try:
        tree = etree.parse(str(xml_file))
        # Find AUDIO elements with matching file attribute
        audio_elements = tree.xpath(f"//AUDIO[@file='{audio_filename}']")
        
        if audio_elements:
            url = audio_elements[0].get('url')
            return url
        else:
            print(f"  ⚠️ Audio element not found in XML for {audio_filename}")
            return None
            
    except Exception as e:
        print(f"  ❌ Error parsing XML {xml_file}: {e}")
        return None

def download_audio_file(url, output_path):
    """Download an audio file from URL to the specified path."""
    try:
        # Remove existing symlink if it exists
        if output_path.is_symlink():
            output_path.unlink()
        elif output_path.exists():
            # If it's a regular file that already exists, skip
            return True
        
        # Download with timeout and user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Write file in chunks
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Download failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error saving file: {e}")
        return False

def download_missing_audio_files():
    """Main function to download all missing audio files."""
    print("🎵 Downloading missing audio files from original URLs...")
    print("=" * 60)
    
    # Extract missing files from report
    missing_files = extract_missing_files()
    print(f"Found {len(missing_files)} missing files to process\n")
    
    # Stats
    total_files = len(missing_files)
    successful_downloads = 0
    failed_downloads = 0
    already_exist = 0
    
    for i, file_info in enumerate(missing_files, 1):
        xml_file = file_info['xml_file']
        audio_filename = file_info['audio_filename']
        expected_path = file_info['expected_path']
        
        print(f"[{i}/{total_files}] Processing: {audio_filename}")
        
        # Check if file already exists (maybe it was downloaded in a previous run)
        if expected_path.exists():
            print(f"  ✅ File already exists, skipping")
            already_exist += 1
            continue
        
        # Find URL in XML
        url = find_audio_url(xml_file, audio_filename)
        if not url:
            failed_downloads += 1
            continue
        
        print(f"  📥 Downloading from: {url}")
        
        # Download the file
        if download_audio_file(url, expected_path):
            print(f"  ✅ Successfully downloaded to: {expected_path}")
            successful_downloads += 1
        else:
            failed_downloads += 1
        
        # Brief pause to be nice to the server
        time.sleep(0.1)
        
        # Progress update every 50 files
        if i % 50 == 0:
            print(f"\n📊 Progress update after {i} files:")
            print(f"   ✅ Successful: {successful_downloads}")
            print(f"   ❌ Failed: {failed_downloads}")
            print(f"   📁 Already existed: {already_exist}")
            print()
    
    print(f"\n{'='*60}")
    print("🎯 DOWNLOAD SUMMARY:")
    print(f"{'='*60}")
    print(f"Total files processed: {total_files}")
    print(f"✅ Successfully downloaded: {successful_downloads}")
    print(f"❌ Failed downloads: {failed_downloads}")
    print(f"📁 Already existed: {already_exist}")
    
    success_rate = (successful_downloads / total_files) * 100 if total_files > 0 else 0
    print(f"\n🏆 Success rate: {success_rate:.1f}%")

if __name__ == "__main__":
    download_missing_audio_files()