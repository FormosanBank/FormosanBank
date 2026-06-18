import os
import re
import csv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import yt_dlp

# Change these as needed
CHANNEL_NAME = "Wilang Yutas"
CHANNEL_URL = "https://www.youtube.com/@wilangyutas9297/videos"
OUTPUT_CSV = "wilang_yutas_report.csv"

# For example, if you want to store everything in ../raw_scrape:
os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir("..")
os.chdir("issues")

# Configure yt-dlp to extract video IDs/metadata without downloading videos
ydl_opts = {
    'extract_flat': True,      # Only extract metadata (no full download)
    'quiet': True,
    'skip_download': True,
    'dump_single_json': True,
}

def main():
    # Use yt-dlp to get info on the channel's videos
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        channel_info = ydl.extract_info(CHANNEL_URL, download=False)

    # The 'entries' key contains a list of videos
    videos = channel_info.get('entries', [])
    print(f"Found {len(videos)} videos on the channel: {CHANNEL_NAME}")

    # Prepare to write results to CSV
    with open(OUTPUT_CSV, mode="w", encoding="utf-8", newline="") as csvfile:
        writer = csv.writer(csvfile)
        # Write the header row
        writer.writerow(["Video Channel", "Video Link", "Video Title", "Issue"])

        # Process each video
        for video in videos:
            video_id = video.get('id') or video.get('url')
            if not video_id:
                # If we somehow can’t get an ID, skip
                print("Could not determine video ID, skipping...")
                continue

            # Construct YouTube watch URL
            video_link = f"https://www.youtube.com/watch?v={video_id}"

            # Extract and sanitize the video title
            video_title = video.get('title', 'untitled')
            # Remove any character that is not alphanumeric, whitespace, underscore or hyphen
            sanitized_title = re.sub(r'[^\w\s-]', '', video_title).strip()
            # Replace any whitespace or hyphen with underscore
            sanitized_title = re.sub(r'[-\s]+', '_', sanitized_title)

            print(f"Processing video: {video_title} ({video_id})")

            # Default issue is "No Transcript" if we fail to find one
            issue = "No Transcript"

            try:
                # Try to fetch transcript in Traditional Chinese ("zh-TW")
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['zh-TW'])

                # If transcript was fetched successfully, check for missing parts
                missing_parts = any(entry['text'].strip() == "" for entry in transcript)
                if missing_parts:
                    issue = "Missing Parts From Transcript"
                else:
                    issue = "All Good"

            except (TranscriptsDisabled, NoTranscriptFound):
                # Either transcripts are disabled or no transcript found in zh-TW
                issue = "No Transcript"
            except Exception as e:
                print(f"An error occurred for video {video_id}: {e}")
                # We can leave issue as "No Transcript" or set to something else if desired

            # Write row to CSV
            writer.writerow([CHANNEL_NAME, video_link, video_title, issue])

    print(f"\nDone! Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
