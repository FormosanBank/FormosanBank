#!/usr/bin/env python3
"""
Download audio from YouTube URLs in the XML file and create AUDIO elements.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, parse_qs

def install_yt_dlp():
    """Install yt-dlp if not available"""
    try:
        import yt_dlp
        return True
    except ImportError:
        print("Installing yt-dlp...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            import yt_dlp
            return True
        except Exception as e:
            print(f"Failed to install yt-dlp: {e}")
            return False

def extract_video_id(youtube_url):
    """Extract video ID from YouTube URL"""
    if 'youtube.com' in youtube_url:
        if '/embed/' in youtube_url:
            # Format: https://www.youtube.com/embed/VIDEO_ID
            return youtube_url.split('/embed/')[-1].split('?')[0]
        elif 'watch?v=' in youtube_url:
            # Format: https://www.youtube.com/watch?v=VIDEO_ID
            parsed = urlparse(youtube_url)
            return parse_qs(parsed.query).get('v', [None])[0]
    elif 'youtu.be' in youtube_url:
        # Format: https://youtu.be/VIDEO_ID
        return youtube_url.split('/')[-1].split('?')[0]
    return None

def download_youtube_audio(video_id, output_dir, sentence_id):
    """Download audio from YouTube video and convert to WAV"""
    if not video_id:
        return None
    
    try:
        import yt_dlp
        
        # Create output filename using sentence ID
        audio_filename = f"{sentence_id}.wav"
        audio_path = output_dir / audio_filename
        
        # Skip if file already exists
        if audio_path.exists():
            print(f"⏭  Skipping existing file: {audio_filename}")
            return audio_filename
        
        # yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'outtmpl': str(output_dir / f'{sentence_id}.%(ext)s'),
        }
        
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        print(f"Downloading audio from: {video_url}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        return audio_filename
        
    except Exception as e:
        print(f"Error downloading audio for video {video_id}: {e}")
        return None

def process_xml_file(xml_file_path, output_xml_path, audio_dir):
    """Process XML file to add AUDIO elements and download audio files"""
    
    # Parse XML
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return False
    
    # Create audio directory if it doesn't exist
    audio_dir.mkdir(exist_ok=True)
    
    # Find all S elements with audio_url attributes
    sentences_with_audio = root.findall(".//S[@audio_url]")
    print(f"Found {len(sentences_with_audio)} sentences with audio URLs")
    
    processed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for s_element in sentences_with_audio:
        audio_url = s_element.get('audio_url')
        sentence_id = s_element.get('id')
        
        if not audio_url or not sentence_id:
            print(f"Missing audio_url or id attribute in sentence element")
            failed_count += 1
            continue
            
        # Extract video ID
        video_id = extract_video_id(audio_url)
        if not video_id:
            print(f"Could not extract video ID from: {audio_url}")
            failed_count += 1
            continue
        
        # Download audio
        audio_path = audio_dir / f"{sentence_id}.wav"
        file_existed = audio_path.exists()
        
        audio_filename = download_youtube_audio(video_id, audio_dir, sentence_id)
        if audio_filename:
            # Add AUDIO element to the sentence if it doesn't exist
            existing_audio = s_element.find("AUDIO")
            if existing_audio is None:
                audio_element = ET.SubElement(s_element, "AUDIO")
                audio_element.set("file", audio_filename)
                audio_element.set("source", "youtube")
            
            # Track whether this was new or skipped
            if file_existed:
                skipped_count += 1
            else:
                processed_count += 1
                print(f"✓ Downloaded: {audio_filename}")
        else:
            failed_count += 1
            print(f"✗ Failed to download: {audio_url}")
    
    # Save modified XML
    try:
        tree.write(output_xml_path, encoding='utf-8', xml_declaration=True)
        print(f"\nXML saved to: {output_xml_path}")
        print(f"📥 New downloads: {processed_count} audio files")
        print(f"⏭  Skipped existing: {skipped_count} audio files")
        print(f"✗ Failed downloads: {failed_count}")
        print(f"📊 Total sentences with audio: {processed_count + skipped_count}")
        return True
    except Exception as e:
        print(f"Error saving XML: {e}")
        return False

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Download audio from YouTube URLs in XML file')
    parser.add_argument('--fresh', action='store_true', 
                        help='Delete existing Audio directory and start fresh')
    args = parser.parse_args()
    
    # Check if we can install/import yt-dlp
    if not install_yt_dlp():
        print("Cannot proceed without yt-dlp")
        return 1
    
    # Set up paths
    project_dir = Path(__file__).parent.parent
    xml_file = project_dir / "XML" / "Paiwan_Yedda_Blog.xml"
    output_xml = project_dir / "XML" / "Paiwan_Yedda_Blog.xml"
    audio_dir = project_dir / "Audio"
    
    # Check if XML file exists
    if not xml_file.exists():
        print(f"XML file not found: {xml_file}")
        return 1
    
    # Handle fresh start option
    if args.fresh and audio_dir.exists():
        print(f"🗑  Deleting existing audio directory: {audio_dir}")
        shutil.rmtree(audio_dir)
        print("   Starting fresh download...")
    
    print(f"Processing XML file: {xml_file}")
    print(f"Audio files will be saved to: {audio_dir}")
    print(f"Updated XML will be saved to: {output_xml}")
    print()
    
    # Process the XML file
    success = process_xml_file(xml_file, output_xml, audio_dir)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())