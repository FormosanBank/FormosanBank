# tests/utilities/test_count_tokens.py
"""count_tokens.py emits {LanguageName: [total, {dialect: tokens}]} JSON.
Shape is consumed by tokens_delta.py / plot_counts.py / plot_deltas.py
and the token-comparison workflow — keep it stable."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "QC" / "count_tokens.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "stats_corpus" / "MiniCorpus"


def test_json_shape_and_language_resolution(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "Corpora" / "MiniCorpus")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path / "Corpora")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)

    assert data["Amis"][0] == 6
    assert data["Amis"][1] == {"Haian": 5, "Not Specified": 1}
    assert data["Truku"] == [2, {"Truku": 2}]
    assert data["Seediq"] == [3, {"unknown": 3}]
    # Every known language is present (zero-seeded), so deltas across
    # checkouts never KeyError.
    assert data["Bunun"] == [0, {}]
    assert len(data) >= 17
