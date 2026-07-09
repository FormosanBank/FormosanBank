"""
TESTING CHECKLIST

Character Perturbation Robustness Test Suite - Pre/Post Test Checklist

Use this checklist to verify the test suite setup and execution.
"""

# TESTING CHECKLIST

## Pre-Test Setup (10 minutes)

### File Verification
- [ ] Verify all test files exist in QC/orthography/:
  - [ ] test_character_perturbation_robustness.py
  - [ ] test_runner.py
  - [ ] test_config.py
  - [ ] validate_test_suite.py
  - [ ] run_tests.sh

- [ ] Verify documentation files exist:
  - [ ] README_TEST_SUITE.md
  - [ ] TEST_SUITE_DOCUMENTATION.md
  - [ ] COMPREHENSIVE_TEST_SUITE_SUMMARY.md
  - [ ] TESTING_CHECKLIST.md (this file)

### Environment Verification
- [ ] Python 3.11+ installed: `python --version`
- [ ] Current directory is FormosanBank root: `ls dialects.csv`
- [ ] Required Python packages installed:
  ```bash
  python -c "import numpy, pandas, matplotlib; print('OK')"
  ```

### Data Verification
- [ ] Corpora directory exists: `ls Corpora/`
- [ ] At least one corpus source present:
  - [ ] Corpora/ePark/
  - [ ] Corpora/ILRDF_Dicts/
  - [ ] Corpora/Paiwan_Stories/
  - [ ] Corpora/NTUFormosanCorpus/
- [ ] Orthographies directory exists: `ls Orthographies/Ortho113/`
- [ ] Language orthography files (at least 1):
  - [ ] ami.tsv
  - [ ] tay.tsv
  - [ ] bnn.tsv
  - [ ] pwn.tsv
- [ ] dialects.csv exists and is readable:
  ```bash
  head dialects.csv
  ```

### Pre-Flight Validation
```bash
python QC/orthography/validate_test_suite.py --test
```
Expected output:
- [ ] ✓ All directory checks PASSED
- [ ] ✓ All test files PASSED
- [ ] ✓ All dependencies PASSED
- [ ] ✓ Dialect configuration PASSED
- [ ] ✓ Minimal functionality test PASSED

**If any checks fail:**
- [ ] Review error messages carefully
- [ ] Check that corpus directories have correct structure
- [ ] Verify orthography file names match language codes (lowercase)
- [ ] Ensure dialects.csv is properly formatted
- [ ] Resolve all issues before proceeding

## Test Execution (3-30 minutes depending on profile)

### Quick Sanity Check (2 minutes)
```bash
mkdir -p test_results
python QC/orthography/test_character_perturbation_robustness.py \
  --languages ami \
  --sources ePark \
  --output-dir test_results/sanity_check
```

Expected output:
- [ ] Script runs without errors
- [ ] Progress messages appear in console
- [ ] Completes within ~1-2 minutes
- [ ] Creates results directory: `test_results/sanity_check/`

### Verify Output Files
```bash
ls test_results/sanity_check/
```

Expected files:
- [ ] test_run_*.log (execution log)
- [ ] summary_report.txt (human-readable summary)
- [ ] all_results.json (aggregated results)
- [ ] ami_*.json (at least one language/dialect result)
  Examples: ami_Central_results.json, ami_Nataoran_results.json

### Inspect Result Content
```bash
# View summary
cat test_results/sanity_check/summary_report.txt

# View JSON structure
python -m json.tool test_results/sanity_check/ami_*.json | head -100
```

Expected in summary:
- [ ] Language name (e.g., "Amis")
- [ ] Dialect name (e.g., "Central")
- [ ] Corpus statistics (sentences, characters, unique chars)
- [ ] Perturbation info (which character was swapped)
- [ ] Metric changes (cosine similarity, KL divergence)

Expected in JSON:
- [ ] "language": "ami"
- [ ] "dialect": "[dialect_name]"
- [ ] "corpus_stats": {...}
- [ ] "metric_deltas": {"character": {...}, "word": {...}}
- [ ] Multiple n-gram lengths (1, 2, 3)

### Full Test Run (if desired)
```bash
python QC/orthography/test_character_perturbation_robustness.py \
  --languages ami tay bnn pwn \
  --sources ePark ILRDF_Dicts \
  --output-dir test_results/full_run_20260629
```

- [ ] Check elapsed time (should be ~10 minutes for 4 languages)
- [ ] Monitor memory usage (should not exceed 2GB)
- [ ] Watch for any error messages
- [ ] Verify output directory is being populated

## Post-Test Analysis (5 minutes)

### Generate Analysis Report
```bash
python QC/orthography/test_runner.py \
  --load-results test_results/sanity_check \
  --output-report test_results/sanity_check/analysis.txt \
  --export-csv test_results/sanity_check/results.csv
```

Expected output:
- [ ] Command completes without errors
- [ ] Creates analysis.txt with comparative statistics
- [ ] Creates results.csv for spreadsheet analysis

### Inspect Analysis Report
```bash
cat test_results/sanity_check/analysis.txt
```

Expected content:
- [ ] Overall metric changes (mean, std dev, min, max)
- [ ] Results grouped by language
- [ ] Results grouped by n-gram length
- [ ] Statistical summary section
- [ ] Detailed metric breakdowns

### Verify CSV Export
```bash
head -3 test_results/sanity_check/results.csv
```

Expected content:
- [ ] CSV header row with column names
- [ ] Data rows with metric values
- [ ] One row per test result
- [ ] Columns for all metrics at each gram length and level

## Result Interpretation (Understanding Output)

### Delta Value Interpretation

For each result, check the metric deltas:

**Character Level 1-gram (most important):**
```json
"metric_deltas": {
  "character": {
    "1": {
      "cosine_similarity": 0.03,
      "kl_divergence": 0.05
    }
  }
}
```

- [ ] Cosine delta < 0.05: **GOOD** - Statistics are robust
- [ ] Cosine delta 0.05-0.15: **ACCEPTABLE** - Reasonable robustness
- [ ] Cosine delta > 0.15: **POOR** - Brittle statistics

**Word Level 1-gram:**
Similar interpretation as character level

**Higher n-grams (2-gram, 3-gram):**
- [ ] Should show similar patterns to 1-grams
- [ ] Large differences might indicate tokenization issues
- [ ] Consistency across levels is a good sign

### Corpus Quality Signals

**Good Quality Corpora (all checks pass):**
- [ ] Low deltas at character level (< 0.10)
- [ ] Low deltas at word level (< 0.10)
- [ ] Consistent deltas across gram lengths
- [ ] Large corpus (> 1000 sentences)
- [ ] High unique character count (> 30)

**Potential Quality Issues (investigate if seen):**
- [ ] High character-level deltas (> 0.20)
- [ ] Inconsistent deltas across gram lengths
- [ ] Small corpus (< 100 sentences)
- [ ] Only 1-2 unique characters
- [ ] Word-level >> character-level deltas (tokenization issue)

### XML Corpus Validation Results

After test execution, check validation results:

```bash
# View validation summary in main report
cat test_results/sanity_check/summary_report.txt | grep -A 20 "XML CORPUS INTEGRITY"

# View detailed validation JSON
python -m json.tool test_results/sanity_check/*_validation.json | head -50
```

**Validation Status Interpretation:**

- [ ] **PASS**: Corpus passes all health checks
  - All metric deltas < 0.15 (healthy threshold)
  - No integrity issues detected
  - No unexpected character overlaps with other languages
  - **Action**: Corpus is ready for publication

- [ ] **WARN**: Corpus in warning zone
  - Some metric deltas between 0.15-0.25 (warning threshold)
  - May indicate data quality variation
  - **Action**: Review corpus for potential issues but acceptable

- [ ] **FAIL**: Corpus fails integrity checks
  - Metric deltas > 0.25 (anomalous threshold)
  - Likely indicates corpus contamination or mislabeling
  - Unexpected high character overlap with other languages
  - **Action**: Investigate corpus for data quality problems

**Cross-Language Character Analysis:**

Check for unexpected character overlaps:
```bash
# Extract character set statistics
grep -A 5 "cross_language_stats" test_results/sanity_check/*_validation.json
```

- [ ] Language/dialect has unique character set
- [ ] Character overlap with other languages < 20%
- [ ] High overlap might indicate:
  - Corpus contamination (mixed languages)
  - Shared romanization conventions
  - Annotation errors

## Troubleshooting During Tests

### Issue: Test runs very slowly
- [ ] Check system memory availability: `free -h` (Linux/Mac) or Task Manager (Windows)
- [ ] Close unnecessary applications
- [ ] Try QUICK profile instead of FULL
- [ ] Reduce number of languages or sources

### Issue: "No corpus found" error
- [ ] Verify Corpora/ directory structure
- [ ] Check dialect names in summary match dialects.csv exactly
- [ ] Review logs: `tail test_results/*/test_run*.log`

### Issue: Python module not found
- [ ] Reinstall dependencies: `pip install numpy pandas matplotlib`
- [ ] Verify Python version: `python --version` (need 3.11+)
- [ ] Check pip is from correct Python: `which pip` or `where pip` (Windows)

### Issue: Results directory empty after test
- [ ] Check if test completed: grep "test suite complete" test_run*.log
- [ ] Review error log: `cat test_run_*.log | grep ERROR`
- [ ] Verify output directory permissions: `ls -la test_results/`

## Quality Assurance Checks

### Sanity Checks (run after every test)
```bash
python << 'EOF'
import json
import os

results_dir = "test_results/sanity_check"
json_files = [f for f in os.listdir(results_dir) if f.endswith('_results.json')]

print(f"Found {len(json_files)} result files")

for json_file in json_files:
    with open(os.path.join(results_dir, json_file)) as f:
        data = json.load(f)
    
    print(f"\n{json_file}:")
    print(f"  Language: {data['language']}")
    print(f"  Dialect: {data['dialect']}")
    print(f"  Corpus size: {data['corpus_stats']['total_characters']} chars")
    print(f"  Has metric_deltas: {'metric_deltas' in data}")
    
    # Check deltas are reasonable
    for level in ['character', 'word']:
        for gram in data['metric_deltas'][level]:
            cs = data['metric_deltas'][level][gram]['cosine_similarity']
            kl = data['metric_deltas'][level][gram]['kl_divergence']
            if cs < 0 or cs > 1 or kl < 0:
                print(f"  WARNING: Invalid delta values in {level}-{gram}gram!")
            else:
                print(f"  {level}-{gram}gram OK (cs={cs:.3f}, kl={kl:.3f})")
EOF
```

Expected output:
- [ ] All files load successfully
- [ ] All languages and dialects shown
- [ ] All metric deltas are valid (0-1 for cosine, 0+ for KL)
- [ ] No WARNING messages

## Regression Testing (After Code Changes)

After making changes to the test suite, run this checklist:

1. **Unit Verification**
   - [ ] All syntax checks pass: `python -m py_compile test_*.py`
   - [ ] No import errors: `python -c "from test_character_perturbation_robustness import *"`

2. **Smoke Test**
   - [ ] MINIMAL profile completes: ~1 minute
   - [ ] Output structure unchanged
   - [ ] Metrics are numeric and in valid ranges

3. **Compatibility Check**
   - [ ] Results compatible with old versions: Can load and analyze
   - [ ] CSV format unchanged
   - [ ] JSON schema preserved

4. **Performance Regression**
   - [ ] QUICK profile not significantly slower
   - [ ] Memory usage reasonable (< 1GB for QUICK)
   - [ ] No unexpected warnings in logs

## Sign-Off Checklist

After completing all tests, verify:

- [ ] ✓ All pre-test setup checks passed
- [ ] ✓ Test execution completed without critical errors
- [ ] ✓ Output files created and contain valid data
- [ ] ✓ Analysis reports generated successfully
- [ ] ✓ Result interpretation makes sense (deltas in reasonable ranges)
- [ ] ✓ No concerning quality issues identified
- [ ] ✓ Test results can be analyzed with test_runner.py
- [ ] ✓ CSV export works and is readable

**Overall Test Status:**
- [ ] PASSED - All checks successful, test suite operational
- [ ] PASSED WITH WARNINGS - Some optional checks failed, suite operational
- [ ] FAILED - Critical checks failed, suite requires attention

**Date Tested:** _______________
**Tested By:** _______________
**Notes:** _______________

---

## Quick Reference: Common Commands

```bash
# Validate setup
python QC/orthography/validate_test_suite.py --test

# Run test
python QC/orthography/test_character_perturbation_robustness.py \
  --languages ami pwn \
  --output-dir test_results/my_test

# Analyze results
python QC/orthography/test_runner.py \
  --load-results test_results/my_test \
  --output-report test_results/my_test/analysis.txt \
  --export-csv test_results/my_test/results.csv

# View results
cat test_results/my_test/summary_report.txt
head -3 test_results/my_test/results.csv
```

## Support Resources

1. **README_TEST_SUITE.md** - Quick start guide (5 min read)
2. **TEST_SUITE_DOCUMENTATION.md** - Detailed documentation (30 min read)
3. **Inline code comments** - Implementation details
4. **Logs** - test_run_*.log files in each results directory
5. **Example outputs** - In test_results/ after running tests

---

For detailed information, consult the documentation files.
For immediate help, check the Troubleshooting section above.
