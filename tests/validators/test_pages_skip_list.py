"""pages.yaml skips its push build exactly when Corpus Metrics will rebuild the site.

The docs site is rebuilt after every Corpus Metrics run (workflow_run), so its
push trigger ignores merges whose files all match Corpus Metrics' push paths.
If the two lists drift, a merge touching only a path Corpus Metrics no longer
watches would get no site build at all.
"""
from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"


def _on(name):
    data = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    return data.get("on", data.get(True))


def test_pages_push_skip_list_equals_corpus_metrics_push_paths():
    skip = _on("pages.yaml")["push"]["paths-ignore"]
    metrics = _on("corpus-metrics.yaml")["push"]["paths"]
    assert sorted(skip) == sorted(metrics), (
        "pages.yaml push paths-ignore must equal corpus-metrics.yaml push paths; "
        f"only in pages: {sorted(set(skip) - set(metrics))}, "
        f"only in corpus-metrics: {sorted(set(metrics) - set(skip))}")
