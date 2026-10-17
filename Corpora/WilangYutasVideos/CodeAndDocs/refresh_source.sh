#!/usr/bin/env bash
# Optional source refresh (POL-047). Never run by generate_xml.sh. Needs network access.
#
#   refresh_source.sh captions   re-fetch the channel's caption files into CodeAndDocs/raw_scrape/
#                                (needs: pip install yt-dlp youtube-transcript-api)
#   refresh_source.sh audio      download each video's audio and cut the per-sentence and
#                                untranscribed clips into Audio/Atayal/ (needs: yt-dlp, ffmpeg, ffprobe)
#
# Order after new captions: run `captions`, review every change to raw_scrape/, rebuild with
# generate_xml.sh, then run `audio` (it cuts clips from the rebuilt XML's timings, read-only).
# If the untranscribed clips it prints differ from CodeAndDocs/video_manifest.tsv, update the
# manifest and rebuild. Neither step writes XML.
set -euo pipefail
CODEDOCS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PYTHON:-python3}"
case "${1:-}" in
  captions)
    "$PY" -c "import yt_dlp, youtube_transcript_api" 2>/dev/null || {
        echo "needs: pip install yt-dlp youtube-transcript-api" >&2; exit 2; }
    exec "$PY" "$CODEDOCS/scripts/scrape.py" ;;
  audio)
    "$PY" -c "import yt_dlp, lxml" 2>/dev/null || { echo "needs: pip install yt-dlp lxml" >&2; exit 2; }
    command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null || { echo "needs ffmpeg and ffprobe on PATH" >&2; exit 2; }
    exec "$PY" "$CODEDOCS/scripts/download_audio.py" ;;
  *)
    sed -n '2,15p' "$0" >&2; exit 2 ;;
esac
