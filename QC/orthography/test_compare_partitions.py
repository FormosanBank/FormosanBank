import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from orthography_compare import compare_partitioned_corpora


def test_compare_partitioned_corpora_returns_reference_target_and_combined_summary() -> None:
    reference_corpus = "maku aicu. cima aicu."
    target_corpus = "maku aicu. aicu maku."

    result = compare_partitioned_corpora(
        reference_corpus=reference_corpus,
        target_corpus=target_corpus,
        lang="Paiwan",
        num_sim=2,
        ref_ratio=0.5,
        seed=0,
        verbose=False,
        save_plots=False,
    )

    assert set(result.keys()) == {"reference", "target", "combined"}
    assert "jaccard_similarity" in result["reference"]
    assert "jaccard_similarity" in result["target"]
    assert "jaccard_similarity" in result["combined"]
