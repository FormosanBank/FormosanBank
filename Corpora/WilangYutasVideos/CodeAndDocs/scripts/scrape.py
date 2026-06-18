import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp

# URL of the channel's videos page
channel_url = "https://www.youtube.com/@wilangyutas9297/videos"

# Set current working directory to ../raw_scrape
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")
os.chdir("raw_scrape")

# Configure yt-dlp to extract video IDs without downloading videos
ydl_opts = {
    'extract_flat': True,      # Only extract metadata (no full download)
    'quiet': True,
    'skip_download': True,
    'dump_single_json': True,
}

# Extract video list from the channel
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    channel_info = ydl.extract_info(channel_url, download=False)

# The 'entries' key contains a list of videos
videos = channel_info.get('entries', [])
print(f"Found {len(videos)} videos on the channel.")

# Instantiate the API (required in v1.x)
api = YouTubeTranscriptApi()

# Process each video
for video in videos:
    # Depending on the metadata, video id might be in 'id' or 'url'
    video_id = video.get('id') or video.get('url')
    if not video_id:
        print("Could not determine video ID, skipping...")
        continue

    # Extract and sanitize the video title
    video_title = video.get('title', 'untitled')
    # Remove any character that is not alphanumeric, whitespace, underscore or hyphen
    video_title = re.sub(r'[^\w\s-]', '', video_title).strip()
    # Replace any whitespace or hyphen with underscore
    video_title = re.sub(r'[-\s]+', '_', video_title)

    print(f"Processing video {video_title}_{video_id}...")

    try:
        # List available transcripts and find a manual (non-auto-generated) zh-TW one.
        # We explicitly reject auto-generated transcripts — they are useless for Atayal.
        transcript_list = api.list(video_id)
        manual_transcripts = [t for t in transcript_list if not t.is_generated]

        if not manual_transcripts:
            print(f"  No manual transcript available for {video_id}, skipping...")
            continue

        # Prefer zh-TW; fall back to the first other manual track if zh-TW is absent
        zh_tw = next((t for t in manual_transcripts if t.language_code == 'zh-TW'), None)
        chosen = zh_tw if zh_tw else manual_transcripts[0]

        if chosen.language_code != 'zh-TW':
            print(f"  Warning: no zh-TW track; using {chosen.language_code!r} for {video_id}")

        entries = list(chosen.fetch())

        # Skip entries that are entirely whitespace (gaps in the caption upload)
        entries = [e for e in entries if e.text.strip()]

        # Create filename using the video title and id (e.g., "MyVideoTitle_6VK6KU3zHD0.txt")
        filename = f"{video_title}_{video_id}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(f"{entry.start}: {entry.text}\n")

        print(f"  Saved {len(entries)} entries to {filename}.")

    except Exception as e:
        print(f"  An error occurred for video {video_id}: {e}")
