"""
Character Perturbation Robustness Test Suite - Comprehensive Documentation

This test suite measures the robustness of n-gram-based language statistics when text is
perturbed by character substitution. It helps evaluate whether a corpus's distributional
properties are stable under character-level noise.
"""

# CHARACTER PERTURBATION ROBUSTNESS TEST SUITE

## Overview

The Character Perturbation Robustness Test Suite evaluates the stability of orthographic statistics
across Formosan languages. For each language/dialect combination, it:

1. **Generates a combined corpus** from multiple sources (ePark, ILRDF_Dicts, Paiwan_Stories, NTUFormosanCorpus)
2. **Samples 1/5 of sentences** as a target corpus (4/5 as reference)
3. **Measures baseline n-gram statistics** at character and word levels (1-3 grams)
4. **Performs character perturbation** by swapping the most frequent character with a random character
5. **Measures perturbed n-gram statistics** on the modified target corpus
6. **Computes metric deltas** (changes in cosine similarity and KL divergence) between baseline and perturbed

## Test Methodology

### Corpus Generation

The test suite pulls data from four primary sources:
- **ePark/**: Park corpus (web texts)
- **ILRDF_Dicts/**: Indigenous Languages Research and Development Foundation dictionaries
- **Paiwan_Stories/**: Narrative texts
- **NTUFormosanCorpus/**: NTU linguistic corpus

For each source, it extracts the "standard" orthography (normalized spelling) for a given
dialect of a given language.

### Train/Test Split

- **Reference corpus (80%)**: Full context for n-gram frequency estimation
- **Target corpus (20%)**: Tested against reference to measure similarity
  - A 20% split (1/5) is chosen to provide sufficient data for robust statistics while
    representing a true "held-out" set for robustness evaluation

### Character-Level Metrics

At the **character level**, the test computes:
- **Jaccard Similarity**: Proportion of shared unique characters (baseline = 1.0)
- **Overlap Coefficient**: Minimum proportion of shared characters
- **Cosine Similarity**: Similarity between character n-gram frequency vectors
- **Euclidean Distance**: L2 distance between frequency vectors
- **KL Divergence**: Kullback-Leibler divergence from baseline to perturbed

### Word-Level Metrics

At the **word level**, the same metrics are computed, but over word (token) sequences instead
of character sequences. This tests whether perturbation affects higher-level linguistic structure.

### Perturbation Strategy

1. Extract the most frequently occurring character in the target corpus
2. Randomly select a different character from the target corpus
3. Perform a character substitution: every occurrence of the most frequent character
   is replaced with the random character
4. Re-compute all metrics on the perturbed corpus
5. Compute absolute changes (deltas) between baseline and perturbed metrics

**Rationale**: Swapping the most frequent character produces the largest potential impact
on distributional statistics, making robustness failures more visible.

## N-gram Levels

The test computes metrics at:
- **1-grams (unigrams)**: Single characters (or words)
- **2-grams (bigrams)**: Consecutive pairs
- **3-grams (trigrams)**: Consecutive triplets

This tests robustness at multiple granularities of linguistic structure.

## Laplace Smoothing

All probability estimates use Laplace smoothing (add-one smoothing):
- Each n-gram count is incremented by 1 before normalization
- This ensures zero-frequency n-grams are not treated as impossible events
- Standard practice in NLP for avoiding zero-probability issues

## Usage

### Basic Test Run

Run tests for default languages and sources:

```bash
python QC/orthography/test_character_perturbation_robustness.py \
  --output-dir test_results/my_test_run
```

### Custom Languages

Test only specific languages:

```bash
python QC/orthography/test_character_perturbation_robustness.py \
  --languages ami tay pwn \
  --output-dir test_results/subset_test
```

### Custom Sources

Test with a subset of sources:

```bash
python QC/orthography/test_character_perturbation_robustness.py \
  --sources ePark ILRDF_Dicts \
  --output-dir test_results/sparse_test
```

### Combined Custom Configuration

```bash
python QC/orthography/test_character_perturbation_robustness.py \
  --languages ami pwn tay \
  --sources ePark NTUFormosanCorpus \
  --test-ratio 0.25 \
  --output-dir test_results/custom_run
```

## Output Files

### Direct Test Output

```
test_results/my_test_run/
├── test_run_YYYYMMDD_HHMMSS.log      # Detailed execution log
├── all_results.json                   # Aggregated results (all tests)
├── summary_report.txt                 # Human-readable summary
└── {lang}_{dialect}_results.json      # Individual results per language/dialect
    (e.g., ami_Central_results.json)
```

### Result File Structure

Each result file contains:

```json
{
  "language": "ami",
  "dialect": "Central",
  "sources": ["ePark", "ILRDF_Dicts"],
  "corpus_stats": {
    "total_sentences": 1234,
    "reference_sentences": 987,
    "target_sentences": 247,
    "test_ratio": 0.2,
    "total_characters": 45678,
    "unique_characters": 42
  },
  "perturbation": {
    "max_freq_character": "a",
    "swapped_with_character": "u",
    "character_frequency": 5432
  },
  "baseline_metrics": {
    "character": {
      "1": {
        "jaccard_similarity": 1.0,
        "overlap_coefficient": 1.0,
        "cosine_similarity": 0.98,
        "euclidean_distance": 0.15,
        "kl_divergence": 0.02,
        ...
      },
      ...
    },
    "word": { ... }
  },
  "perturbed_metrics": { ... },
  "metric_deltas": {
    "character": {
      "1": {
        "cosine_similarity": 0.05,
        "kl_divergence": 0.10
      },
      ...
    },
    "word": { ... }
  },
  "timestamp": "2026-06-29T15:30:45.123456"
}
```

## Result Analysis

### Using test_runner.py

#### Generate Comparative Report

```bash
python QC/orthography/test_runner.py \
  --load-results test_results/my_test_run \
  --output-report test_results/comparative_analysis.txt
```

This produces a human-readable report comparing:
- Results by language
- Results by dialect
- Statistical summaries (mean, std dev, min, max, median)
- Breakdown by n-gram length

#### Export to CSV

```bash
python QC/orthography/test_runner.py \
  --load-results test_results/my_test_run \
  --export-csv test_results/results.csv
```

Produces a spreadsheet-ready CSV with one row per test result and columns for:
- Language, dialect, sources
- Corpus statistics (sentence count, unique characters)
- Perturbation details (which character was swapped)
- All metric deltas at each n-gram length and level

#### Compare Multiple Test Runs

```bash
python QC/orthography/test_runner.py \
  --compare-runs test_results/run1 test_results/run2 test_results/run3 \
  --output-comparison test_results/cross_run_comparison.txt
```

Useful for tracking improvements in corpus stability over time.

## Interpreting Results

### What Good Results Look Like

- **Low cosine similarity deltas** (< 0.05): Character perturbation has minimal impact on
  n-gram distributions. Indicates robust statistics.
- **Low KL divergence deltas** (< 0.1): Minimal information-theoretic divergence from baseline.
- **Consistent behavior across n-gram lengths**: Robustness at unigrams, bigrams, and trigrams.
- **Similar patterns at character and word levels**: Coherent linguistic structure.

### What Poor Results Might Indicate

- **High cosine similarity deltas** (> 0.2): Character swap significantly changes distribution.
  May indicate:
  - Insufficient corpus size or diversity
  - Over-reliance on a single high-frequency character
  - Non-standard orthography where one character is crucial

- **High KL divergence deltas** (> 0.3): Large information-theoretic shift.
  May indicate the corpus is brittle to perturbations.

- **Asymmetric deltas** (character-level >> word-level or vice versa):
  May indicate tokenization issues or multilevel dependencies.

### Statistical Benchmarks

Based on typical Formosan language corpora:
- **Well-resourced languages** (Amis, Paiwan): Expected deltas 0.02-0.10
- **Under-resourced languages** (Tsou, Saisiyat): Expected deltas 0.05-0.20
- **Small dialect samples**: May see deltas > 0.20

## Troubleshooting

### No Results Generated

**Problem**: Test completes but no results files are created.

**Causes**:
1. Corpus sources not found (check `Corpora/` directory structure)
2. Language/dialect combination not present in any source
3. Insufficient corpus text (< 2 sentences)

**Solution**:
- Check logs in `test_run_YYYYMMDD_HHMMSS.log`
- Verify corpus directories are correctly named
- Check that dialect name matches `dialects.csv` exactly (case-sensitive)

### Missing orthography file

**Problem**: Tokenization fails with "Cannot find orthography file"

**Cause**: Language orthography table not present in `Orthographies/Ortho113/`

**Solution**:
- Check that `Orthographies/Ortho113/{lang}.tsv` exists
- Add missing language orthography if needed

### Memory errors on large corpora

**Problem**: Process crashes with memory error on large sources

**Cause**: Combined corpus is too large for available RAM

**Solution**:
- Run tests with fewer sources
- Run tests for fewer languages per invocation
- Increase available system memory

## Advanced Usage

### Extending the Test Suite

To add custom metrics or analyses:

1. **Edit `compute_reference_target_metrics()`** to add new similarity measures
2. **Edit `analyze_corpus_partition()`** to add new analysis levels (e.g., morpheme-level)
3. **Modify perturbation strategy** in `test_language_dialect()` to test different character swaps

### Custom Perturbation Strategies

The current suite swaps the most frequent character. To test other strategies:

1. Replace this line in `test_language_dialect()`:
   ```python
   max_freq_char = max(target_char_info['character_frequency'], ...)
   ```

2. With alternatives like:
   ```python
   # Random character swap
   max_freq_char = random.choice(list(target_char_info['unique_characters']))
   
   # Least frequent character swap
   max_freq_char = min(target_char_info['character_frequency'], ...)
   
   # N-gram substitution (requires custom logic)
   ```

## References

### Related Work

- n-gram robustness testing in computational linguistics
- Character-level perturbation analysis (e.g., adversarial robustness in OCR)
- Corpus validation and quality assessment

### Metrics Definitions

**Cosine Similarity**: $\cos(\theta) = \frac{\vec{A} \cdot \vec{B}}{|\vec{A}||\vec{B}|}$
- Measures angle between frequency vectors
- Range: [-1, 1], typically [0, 1] for positive frequencies
- 1 = identical distributions, 0 = orthogonal

**KL Divergence**: $D_{KL}(P || Q) = \sum_i P(i) \log \frac{P(i)}{Q(i)}$
- Measures information-theoretic divergence from baseline to perturbed
- Range: [0, ∞], where 0 = identical distributions
- Not symmetric: $D_{KL}(P||Q) \neq D_{KL}(Q||P)$

**Jaccard Similarity**: $J(A, B) = \frac{|A \cap B|}{|A \cup B|}$
- Proportion of shared unique elements
- Range: [0, 1], where 1 = identical sets

**Overlap Coefficient**: $\text{OC}(A, B) = \frac{|A \cap B|}{\min(|A|, |B|)}$
- Proportion of shared elements relative to smaller set
- Range: [0, 1]

## Contributing

To improve the test suite:

1. Report issues or unexpected results
2. Propose new metrics or analysis methods
3. Contribute language-specific orthography tables
4. Extend perturbation strategies

## License

Part of the FormosanBank project. See [LICENSE](../../LICENSE) for details.

## Contact

For questions or issues, file an issue in the FormosanBank repository.
