"""audio-validation.yaml starts only for corpora that have audio committed to Corpora/<name>/Audio/.

Every other corpus's audio lives on Hugging Face and is never present in CI, so
the workflow is triggered by those corpora's paths alone. This test keeps the
list in step with the repository: a corpus that gains committed audio must be
added to both trigger lists, or its audio would never be checked.
"""
import subprocess
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".ogg", ".m4a")


def _corpora_with_committed_audio() -> set[str]:
    files = subprocess.run(["git", "ls-files", "-z", "Corpora"], cwd=REPO_ROOT,
                           capture_output=True, text=True, check=True).stdout.split("\0")
    # The workflow validates Corpora/<name>/Audio/ only (audio_dir="$corpus/Audio");
    # audio elsewhere, e.g. a source snapshot under CodeAndDocs/, is not its concern.
    return {f.split("/")[1] for f in files
            if f.lower().endswith(AUDIO_EXTENSIONS) and f.count("/") >= 3 and f.split("/")[2] == "Audio"}


def test_every_corpus_with_committed_audio_triggers_the_workflow():
    workflow = yaml.safe_load((REPO_ROOT / ".github/workflows/audio-validation.yaml").read_text())
    triggers = workflow.get("on", workflow.get(True))
    corpora = _corpora_with_committed_audio()
    assert corpora, "expected at least one corpus with committed audio (Paiwan_Stories)"
    for event in ("pull_request", "push"):
        paths = triggers[event]["paths"]
        missing = sorted(c for c in corpora if f"Corpora/{c}/**" not in paths)
        assert not missing, f"{event}: add 'Corpora/<name>/**' for {missing}"
