#!/usr/bin/env bash
# Optional source refresh (POL-047): re-fetch the channel's caption files into
# CodeAndDocs/raw_scrape/. Never run by generate_xml.sh. Afterwards, review every
# change to raw_scrape/ before rebuilding; the build reads only committed files.
# Needs network access and: pip install yt-dlp youtube-transcript-api
set -euo pipefail
CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${PYTHON:-python3}" -c "import yt_dlp, youtube_transcript_api" 2>/dev/null || {
    echo "refresh_source.sh needs: pip install yt-dlp youtube-transcript-api" >&2; exit 2; }
exec "${PYTHON:-python3}" "$CODEDOCS/scripts/scrape.py"
