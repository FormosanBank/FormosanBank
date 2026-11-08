# Checklist: audio corpora

1. **One S per distinct recording.** Two sentences sharing one clip (same url/file, start, end) is V162 HARD; a clip that covers several sentences belongs to none of them and is kept as untranscribed audio (maintainer, 2026-10-16: "We don't have a mechanism for multiple audio files for one S block, and i don't want one").

2. **Printed alternatives with audio.** A sentence whose original FORM prints a slash or an optional parenthesis does not carry the clip (V163 SOFT): the recording read one option. The clip stays as an untranscribed item (maintainer, 2026-10-16).

3. **Audio identity.** sha256 per file; the container's first bytes against the extension (V106 — WebM/Opus and MP4 under `.mp3` names reached a dataset); byte-identical "duplicate" recordings versus different ones.
   How: `validate_audio.py` on local files; the Hugging Face LFS listing without downloading.

4. **Hub parity.** The XML's `AUDIO/@file` set equals the dataset's files (`validate_hf_audio.py`, blocking in CI); `sync_hf_audio.py` dry run before the PR; `--apply` is the maintainer's call; the revision SHA goes into `audio_sources.json`.

5. **Boundary changes after text edits.** A rebuild that changes sentence spans leaves clips to re-slice; `sync_hf_audio.py` lists them.
   Example: NTU — 96 clips to slice before parity passed.

6. **No download script writes XML.** Audio download is not a build step (POL-038/047); `download_audio_data.sh` and any `post_download` hook in `audio_sources.json` only fetch (the static test warns on a hook that writes).
   Example: Wilang's `download_audio.py` wrote published XML.

7. **Audio seconds.** `statistics/audio_durations.csv` is anchored to the audio count at compute time (P005); a changed count means a refresh with `refresh-audio-stats` — on demand, never in CI.

8. **Untranscribed audio** is published as such, not dropped and not attached to the nearest sentence.
