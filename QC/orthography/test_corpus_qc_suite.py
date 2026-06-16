import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bag_of_sentence_analysis import n_gram_analysis


def test_n_gram_analysis_returns_character_and_word_ngram_metrics(tmp_path):
    stats = n_gram_analysis(
        lang="Paiwan",
        ref_corpus="a b c",
        target_corpus="a b d",
        logs_dir=str(tmp_path),
        n=3,
        laplace=True,
        save_plots=False,
        verbose=False,
    )

    assert "average_interpolated_conditional_probability_proportion" in stats
    assert "n_gram_statistics" in stats
    ngram_stats = stats["n_gram_statistics"]

    for gram_length in ("1", "2", "3"):
        assert gram_length in ngram_stats
        assert "character" in ngram_stats[gram_length]
        assert "word" in ngram_stats[gram_length]
        assert "jaccard_similarity" in ngram_stats[gram_length]["word"]
        assert "cosine_similarity" in ngram_stats[gram_length]["character"]
