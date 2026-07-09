"""
Character Perturbation Robustness Test Suite - Quick Start Guide

This test suite measures how stable n-gram statistics are when text undergoes
character-level perturbation (swapping the most frequent character with a random one).
"""

# CHARACTER PERTURBATION ROBUSTNESS TEST SUITE - README

## Quick Start (60 seconds)

### 1. Run a quick test
```bash
cd QC/orthography/
python test_character_perturbation_robustness.py \
  --languages ami pwn \
  --sources ePark ILRDF_Dicts \
  --output-dir test_results/quick_run
```

Expected output: 2 languages × ~2 dialects each = ~4 JSON result files in ~3 minutes

### 2. View results
```bash
# Text summary
cat test_results/quick_run/summary_report.txt

# JSON data
python test_runner.py \
  --load-results test_results/quick_run \
  --output-report test_results/quick_run/analysis.txt

# Spreadsheet export
python test_runner.py \
  --load-results test_results/quick_run \
  --export-csv test_results/quick_run/results.csv
```

### 3. Interpret results

Look at **metric_deltas** in the JSON output:

```json
"metric_deltas": {
  "character": {
    "1": {
      "cosine_similarity": 0.03,  // Small change = robust
      "kl_divergence": 0.05
    }
  }
}
```

- **Low deltas (< 0.1)**: Robust statistics, good corpus quality
- **High deltas (> 0.3)**: Brittle statistics, may indicate issues
- **Consistent across levels**: Linguistically coherent corpus

## What This Tests

For each language/dialect in each corpus source:

1. **Split corpus**: 80% reference, 20% target
2. **Measure baseline**: Compute n-gram statistics (1, 2, 3-grams) at character and word levels
3. **Perturb**: Swap most frequent character with random character
4. **Measure perturbed**: Recompute statistics on modified target
5. **Compute deltas**: How much did each metric change?

Metrics computed:
- **Cosine Similarity**: Similarity between frequency vectors (0-1, higher=more similar)
- **KL Divergence**: Information-theoretic distance (0+, lower=more similar)
- (Also: Jaccard, Overlap Coefficient, Euclidean Distance - see detailed docs)

### XML Corpus Integrity Validation

In addition to robustness testing, the suite performs **automatic validation** of XML corpus files:

1. **Correctness Check**: For each language/dialect, validates that metric deltas are within healthy thresholds
   - Healthy threshold: Δ < 0.15 (robust statistics)
   - Anomalous threshold: Δ > 0.25 (potentially corrupted or contaminated corpus)

2. **Cross-Language Analysis**: Analyzes character set overlaps between languages to detect:
   - Language-specific orthography usage
   - Potential corpus contamination (unexpected character overlaps)
   - Character set consistency across dialects

3. **Corpus Integrity Reports**: Generates detailed validation reports in JSON format:
   - Per-dialect validation checks (PASS/WARN/FAIL status)
   - Identified integrity issues
   - Cross-language character set statistics

**Output files:**
- `{lang}_{dialect}_validation.json` - Individual validation results
- `validation_results.json` - Aggregated validation data (loaded in comparative reports)
- Summary statistics included in `summary_report.txt`

**Interpretation:**
- ✓ PASS = Corpus is robust and well-formed
- ⚠ WARN = Corpus shows slightly elevated deltas but is acceptable
- ✗ FAIL = Corpus shows anomalous deltas, likely corpus issues

## File Structure

```
QC/orthography/
├── test_character_perturbation_robustness.py  [MAIN TEST SUITE - runs robustness + validation]
├── test_runner.py                             [RESULTS ANALYZER - includes validation analysis]
├── test_config.py                             [CONFIGURATION PROFILES]
├── run_tests.sh                               [BASH WRAPPER]
├── TEST_SUITE_DOCUMENTATION.md                [DETAILED DOCS]
└── README.md                                  [THIS FILE]
```

## Usage Patterns

### Pattern 1: Quick Iteration
```bash
# Fast test for development
python test_character_perturbation_robustness.py \
  --languages ami pwn \
  --sources ePark \
  --output-dir results/iteration_1
```

### Pattern 2: Full Suite
```bash
# Complete test of all 7 languages with all sources
python test_character_perturbation_robustness.py \
  --output-dir results/full_suite_run
# Languages default: ami tay bnn pwn pyu dru trv
# Sources default: ePark ILRDF_Dicts Paiwan_Stories NTUFormosanCorpus
```

### Pattern 3: Language-Specific
```bash
# Test single language across all dialects
python test_character_perturbation_robustness.py \
  --languages pwn \
  --output-dir results/paiwan_analysis
```

### Pattern 4: Source-Specific
```bash
# Compare robustness across corpus sources
python test_character_perturbation_robustness.py \
  --languages ami tay \
  --sources ePark \
  --output-dir results/epark_focus

python test_character_perturbation_robustness.py \
  --languages ami tay \
  --sources ILRDF_Dicts \
  --output-dir results/ilrdf_focus
```

### Pattern 5: Analysis
```bash
# Analyze results from a previous run
python test_runner.py \
  --load-results results/full_suite_run \
  --output-report results/analysis.txt \
  --export-csv results/data.csv

# Compare multiple runs
python test_runner.py \
  --compare-runs results/run1 results/run2 results/run3 \
  --output-comparison results/cross_run_analysis.txt
```

## Output Structure

```
results/my_test_run/
├── test_run_20260629_150000.log              # Execution log
├── summary_report.txt                         # Human-readable summary (includes validation results)
├── all_results.json                           # Aggregated robustness test results
├── validation_results.json                    # Aggregated XML validation results
├── ami_Central_results.json                   # Per-language/dialect robustness results
├── ami_Central_validation.json                # Per-language/dialect validation results
├── pwn_Central_results.json
├── pwn_Central_validation.json
├── ... (one pair per language/dialect tested)
├── comparative_analysis.txt                   # (After running test_runner.py with validation analysis)
└── results.csv                                # (After running test_runner.py)
```

## Result JSON Format

Each `{lang}_{dialect}_results.json` contains:

```json
{
  "language": "ami",
  "dialect": "Central",
  "sources": ["ePark", "ILRDF_Dicts"],
  "corpus_stats": {
    "total_sentences": 1234,
    "unique_characters": 42
  },
  "perturbation": {
    "max_freq_character": "a",
    "character_frequency": 5432
  },
  "baseline_metrics": {
    "character": {
      "1": { "cosine_similarity": 0.98, "kl_divergence": 0.02, ... },
      "2": { ... },
      "3": { ... }
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
    }
  }
}
```

The **metric_deltas** section is the key: how much did each metric change?

## XML Corpus Validation JSON Format

Each `{lang}_{dialect}_validation.json` contains:

```json
{
  "language": "ami",
  "dialect": "Central",
  "sources": ["ePark", "ILRDF_Dicts"],
  "validation_checks": [
    {
      "check_id": "V001",
      "check_name": "character_1gram_delta",
      "threshold_healthy": 0.15,
      "threshold_anomalous": 0.25,
      "value": 0.08,
      "status": "PASS"
    },
    {
      "check_id": "V002",
      "check_name": "word_1gram_delta",
      "threshold_healthy": 0.15,
      "threshold_anomalous": 0.25,
      "value": 0.12,
      "status": "PASS"
    }
  ],
  "corpus_integrity": {
    "status": "PASS",
    "issues": []
  },
  "cross_language_stats": {
    "unique_characters": 48,
    "character_overlaps": [
      {
        "other_language": "pwn",
        "other_dialect": "Central",
        "overlap_percentage": 15.2,
        "shared_characters": 7
      }
    ]
  }
}
```

**Validation statuses:**
- `PASS`: Corpus passes health check (deltas < threshold_healthy)
- `WARN`: Corpus in warning zone (deltas between thresholds)
- `FAIL`: Corpus fails check (deltas > threshold_anomalous)

## Interpretation Guide

### For Corpus Quality Assessment

```
Delta < 0.05: EXCELLENT robustness
Delta 0.05-0.10: GOOD robustness  
Delta 0.10-0.20: ACCEPTABLE (monitor)
Delta 0.20-0.30: POOR (investigate)
Delta > 0.30: VERY POOR (likely issues)
```

### For Validation Thresholds

- **Healthy (< 0.15)**: Corpus is well-formed and robust, no intervention needed
- **Warning (0.15-0.25)**: Corpus acceptable but monitor for potential issues
- **Anomalous (> 0.25)**: Corpus may have contamination or mislabeling, investigate

### For Language-Specific Patterns

**High character-level deltas, low word-level deltas**
→ Robust word sequences despite character disruption

**Low character-level deltas, high word-level deltas**
→ Character-level structure is stable but word patterns are fragile

**Consistent deltas across all gram lengths**
→ Robustness is uniform across scales

**High variance across gram lengths**
→ Uneven quality or dependency on specific n-gram frequencies

## Configuration Profiles

Pre-configured profiles in `test_config.py`:

- **FULL**: All 7 languages, all 4 sources (~30 min)
- **QUICK**: Amis + Paiwan, 2 sources (~3 min)
- **MINIMAL**: Single language + source (~1 min)
- **DEEP**: Extended analysis with bootstrapping (~20 min)
- **UNDER_RESOURCED**: Focus on less-resourced languages (~10 min)

Use via:
```python
from test_config import get_profile
config = get_profile('QUICK')
# languages = config['languages']
# sources = config['sources']
```

## Performance Notes

| Profile | Duration | Output Size | Best For |
|---------|----------|-------------|----------|
| MINIMAL | 1 min | 1 MB | Quick validation |
| QUICK | 3 min | 5 MB | Development iteration |
| FULL | 30 min | 50 MB | Complete evaluation |
| DEEP | 20 min | 25 MB | In-depth analysis |

Factors affecting speed:
- Corpus size (larger = slower)
- Number of dialects found (varies per language)
- Text processing (tokenization, n-gram extraction)

## Troubleshooting

### Problem: "No corpus found for {lang}/{dialect}"
**Solution**: 
- Verify corpus directory exists under `Corpora/`
- Check dialect name matches exactly (case-sensitive)
- Review logs in `test_run_*.log`

### Problem: "Cannot find orthography file"
**Solution**:
- Ensure `Orthographies/Ortho113/{lang}.tsv` exists
- Add missing orthography table if needed

### Problem: Results directory exists but is empty
**Solution**:
- Check permissions on output directory
- Review execution log for errors
- Verify sufficient disk space

### Problem: Test runs very slowly
**Solution**:
- Start with QUICK profile instead of FULL
- Use fewer languages/sources
- Close other applications to free memory

## Testing the Test Suite

Validate that the test suite works correctly:

```bash
# Run minimal test
python test_character_perturbation_robustness.py \
  --languages ami \
  --sources ePark \
  --output-dir test_results/validation

# Check output
ls test_results/validation/*.json
# Should see: ami_*.json files

# Analyze results
python test_runner.py \
  --load-results test_results/validation
```

## Command Reference

### Main Test Suite
```bash
python test_character_perturbation_robustness.py \
  --languages LANG1 LANG2 ...
  --sources SOURCE1 SOURCE2 ...
  --output-dir OUTPUT_DIR
  --test-ratio 0.2 (default: 1/5)
```

### Results Analyzer
```bash
python test_runner.py \
  --load-results RESULTS_DIR        # Analyze existing results
  --output-report FILE              # Save analysis report
  --export-csv FILE                 # Export to CSV
  --compare-runs DIR1 DIR2 DIR3     # Compare multiple runs
  --output-comparison FILE          # Save comparison
```

### Bash Wrapper (convenience)
```bash
./run_tests.sh --full               # Full test
./run_tests.sh --quick              # Quick test
./run_tests.sh --languages ami pwn  # Custom languages
./run_tests.sh --analyze RESULTS_DIR
```

## Adding New Languages

To test a new language:

1. Ensure language exists in `dialects.csv` with correct codes
2. Ensure orthography table exists at `Orthographies/Ortho113/{lang}.tsv`
3. Ensure corpus data exists in target `Corpora/` sources
4. Run: `python test_character_perturbation_robustness.py --languages {lang}`

## For Developers

To extend the test suite:

1. **New metrics**: Edit `compute_reference_target_metrics()`
2. **New perturbation strategies**: Edit `test_language_dialect()`
3. **New analysis types**: Edit `test_runner.py` analyzer functions
4. **New profiles**: Add to `TEST_PROFILES` in `test_config.py`

## Citation

If you use this test suite in research, please cite the FormosanBank project:

```
FormosanBank: A unified corpus collection for the 16 Formosan languages
[Full citation available in repository README]
```

## Support

For issues or questions:
1. Check logs in `test_run_*.log`
2. Review detailed docs in `TEST_SUITE_DOCUMENTATION.md`
3. Consult configuration profiles in `test_config.py`
4. File an issue in the FormosanBank repository

## Next Steps

After running tests:
1. **Review**: Check `summary_report.txt` for overview
2. **Analyze**: Run `test_runner.py` for comparative analysis
3. **Export**: Export to CSV for spreadsheet analysis
4. **Compare**: Compare multiple runs to track improvements
5. **Visualize**: Use CSV data in visualization tools (Excel, R, Python)

---

**Last Updated**: 2026-06-29
**Version**: 1.0
**Maintainer**: FormosanBank QC Team
