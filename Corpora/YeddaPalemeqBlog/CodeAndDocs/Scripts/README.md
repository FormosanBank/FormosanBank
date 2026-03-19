# XML Baseline Testing System

This directory contains a testing system to validate Paiwan XML scraping results against a known baseline.

## Files

- `test_xml_baseline.py` - Main analysis and comparison script
- `baseline_metrics.json` - Baseline metrics from the reference XML file
- `test_runner.py` - Test validation script

## Baseline Metrics

The baseline was established from `Final_XML/Paiwan_Yedda_Blog.xml` with these key metrics:

- **640 sentences** (`<S>` elements)
- **4,526 words** (`<W>` elements) 
- **5,078 translations** (`<TRANSL>` elements)
- **5,166 forms** (`<FORM>` elements)
- **36,776 characters** in sentence text
- **39,223 characters** in word text
- **202,792 characters** in translation text
- **639 unique audio URLs** (99.84% of sentences have audio)

## Usage

### Analyze the current XML file and create/view baseline:
```bash
python Scripts/test_xml_baseline.py
```

### Compare a new XML file against the baseline:
```bash
python Scripts/test_xml_baseline.py --compare path/to/new_file.xml
```

### Update the baseline (when you want to change the reference):
```bash
python Scripts/test_xml_baseline.py --update-baseline
```

### Run validation tests:
```bash
python Scripts/test_runner.py
```

## What gets compared

The comparison checks:
- **Element counts**: Number of `<S>`, `<W>`, `<TRANSL>`, and `<FORM>` tags
- **Text content**: Total character counts within each element type
- **Structural integrity**: Presence of expected attributes and content

## Example Output

When comparing files, you'll see output like:

```
=== Comparison Results ===
Comparison Date: 2026-03-17T16:31:12.125774

✅ No differences found! The new file matches the baseline perfectly.
```

Or if differences are found:

```
❗ Differences found:
  S_count:
    Baseline: 640
    New: 642
    Difference: +2
```

## Integration with Scraping Scripts

Use this system to validate your scraping scripts:

1. Run your scraper to generate a new XML file
2. Compare it against the baseline: `python Scripts/test_xml_baseline.py --compare new_output.xml`
3. Review any differences to ensure they're expected improvements, not regressions
4. Update the baseline if the new version is better: `python Scripts/test_xml_baseline.py --update-baseline`