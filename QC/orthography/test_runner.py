"""
Test runner and analysis utilities for character perturbation robustness tests.

Provides:
  - Easy test execution with progress tracking
  - Results aggregation and analysis
  - Comparative statistics across languages/dialects
  - CSV export for analysis in spreadsheets
"""

import json
import os
import csv
import argparse
from pathlib import Path
from collections import defaultdict
import numpy as np
from datetime import datetime
import logging


def setup_logging(log_file=None):
    """Configure logging."""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if log_file:
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(level=logging.INFO, format=log_format)
    return logging.getLogger(__name__)


def load_results(results_dir):
    """Load all JSON results from a directory (excluding aggregate files)."""
    results = []
    results_dir = Path(results_dir)
    
    # Skip aggregate files: all_results.json, validation_results.json
    for json_file in results_dir.glob("*_results.json"):
        if json_file.name in ["all_results.json", "validation_results.json"]:
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Only add if it's a dict (individual result), not a list
                if isinstance(data, dict):
                    results.append(data)
        except Exception as e:
            logging.warning(f"Failed to load {json_file}: {e}")
    
    return results


def load_validation_results(results_dir):
    """Load all validation results from a directory (excluding aggregate files)."""
    validation_results = []
    results_dir = Path(results_dir)
    
    for json_file in results_dir.glob("*_validation.json"):
        # Skip aggregate file: validation_results.json
        if json_file.name == "validation_results.json":
            continue
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Only add if it's a dict (individual result), not a list
                if isinstance(data, dict):
                    validation_results.append(data)
        except Exception as e:
            logging.warning(f"Failed to load validation results {json_file}: {e}")
    
    return validation_results


def analyze_validation_results(validation_results):
    """
    Analyze XML corpus integrity validation results.
    
    Returns aggregated statistics and summaries.
    """
    analysis = {
        'passed': 0,
        'warned': 0,
        'failed': 0,
        'by_language': defaultdict(lambda: {'passed': 0, 'warned': 0, 'failed': 0}),
        'issues': [],
        'cross_language_patterns': []
    }
    
    for result in validation_results:
        lang = result.get('language', 'unknown')
        dialect = result.get('dialect', 'unknown')
        
        for check in result.get('validation_checks', []):
            status = check.get('status', 'unknown')
            if status == 'PASS':
                analysis['passed'] += 1
                analysis['by_language'][lang]['passed'] += 1
            elif status == 'WARN':
                analysis['warned'] += 1
                analysis['by_language'][lang]['warned'] += 1
            elif status == 'FAIL':
                analysis['failed'] += 1
                analysis['by_language'][lang]['failed'] += 1
        
        # Collect issues
        for issue in result.get('corpus_integrity_issues', []):
            analysis['issues'].append({
                'language': lang,
                'dialect': dialect,
                'issue': issue
            })
        
        # Collect cross-language patterns
        if result.get('cross_language_overlaps'):
            analysis['cross_language_patterns'].append({
                'language': lang,
                'dialect': dialect,
                'char_count': result['cross_language_overlaps'].get('char_count', 0),
                'overlaps': result['cross_language_overlaps'].get('language_overlaps', [])
            })
    
    return analysis


def analyze_metric_deltas(results):
    """
    Analyze metric deltas across all test results.
    
    Returns aggregated statistics for cosine similarity and KL divergence changes.
    """
    analysis = {
        'by_language': defaultdict(lambda: defaultdict(list)),
        'by_gram_length': defaultdict(lambda: defaultdict(list)),
        'overall': defaultdict(list),
    }
    
    metrics = ['cosine_similarity', 'kl_divergence']
    
    for result in results:
        lang = result['language']
        
        for level in ['character', 'word']:
            for gram_length in result['metric_deltas'][level]:
                for metric in metrics:
                    delta = result['metric_deltas'][level][gram_length][metric]
                    
                    key = f"{level}_{metric}"
                    analysis['by_language'][lang][key].append(delta)
                    analysis['by_gram_length'][gram_length][key].append(delta)
                    analysis['overall'][key].append(delta)
    
    return analysis


def generate_comparative_report(results, output_file=None):
    """Generate a comparative analysis report across all test results."""
    report_lines = []
    
    report_lines.append("=" * 100)
    report_lines.append("Character Perturbation Robustness Test Suite - Comparative Analysis")
    report_lines.append(f"Generated: {datetime.now().isoformat()}")
    report_lines.append("=" * 100)
    
    # Summary statistics
    report_lines.append(f"\nTotal Test Results: {len(results)}")
    report_lines.append(f"Languages tested: {len(set(r['language'] for r in results))}")
    report_lines.append(f"Dialects tested: {len(set((r['language'], r['dialect']) for r in results))}")
    
    # Organize by language
    by_language = defaultdict(list)
    for result in results:
        by_language[result['language']].append(result)
    
    report_lines.append("\n" + "=" * 100)
    report_lines.append("RESULTS BY LANGUAGE")
    report_lines.append("=" * 100)
    
    for lang in sorted(by_language.keys()):
        lang_results = by_language[lang]
        report_lines.append(f"\n{lang.upper()} ({len(lang_results)} dialect(s)):")
        report_lines.append("-" * 100)
        
        for result in lang_results:
            dialect = result['dialect']
            report_lines.append(f"\n  {dialect}:")
            
            # Corpus stats
            stats = result['corpus_stats']
            report_lines.append(f"    Corpus: {stats['total_sentences']} sentences, " +
                              f"{stats['total_characters']} chars, {stats['unique_characters']} unique")
            
            # Perturbation info
            pert = result['perturbation']
            report_lines.append(f"    Perturbation: '{pert['max_freq_character']}' " +
                              f"(freq={pert['character_frequency']}) -> " +
                              f"'{pert['swapped_with_character']}'")
            
            # Metric deltas
            deltas = result['metric_deltas']
            report_lines.append(f"    Character-level changes (Δcosine / ΔKL):")
            for gram in sorted(deltas['character'].keys()):
                cs_delta = deltas['character'][gram]['cosine_similarity']
                kl_delta = deltas['character'][gram]['kl_divergence']
                report_lines.append(f"      {gram}-gram: {cs_delta:.6f} / {kl_delta:.6f}")
            
            report_lines.append(f"    Word-level changes (Δcosine / ΔKL):")
            for gram in sorted(deltas['word'].keys()):
                cs_delta = deltas['word'][gram]['cosine_similarity']
                kl_delta = deltas['word'][gram]['kl_divergence']
                report_lines.append(f"      {gram}-gram: {cs_delta:.6f} / {kl_delta:.6f}")
    
    # Statistical summary
    report_lines.append("\n" + "=" * 100)
    report_lines.append("STATISTICAL SUMMARY")
    report_lines.append("=" * 100)
    
    analysis = analyze_metric_deltas(results)
    
    report_lines.append("\nOverall Metric Changes (all tests combined):")
    report_lines.append("-" * 100)
    for metric in ['character_cosine_similarity', 'character_kl_divergence', 
                   'word_cosine_similarity', 'word_kl_divergence']:
        if metric in analysis['overall']:
            values = analysis['overall'][metric]
            report_lines.append(f"  {metric}:")
            report_lines.append(f"    Mean: {np.mean(values):.6f}")
            report_lines.append(f"    Std Dev: {np.std(values):.6f}")
            report_lines.append(f"    Min: {np.min(values):.6f}")
            report_lines.append(f"    Max: {np.max(values):.6f}")
            report_lines.append(f"    Median: {np.median(values):.6f}")
    
    report_lines.append("\nBy Grammar Length:")
    report_lines.append("-" * 100)
    for gram_length in sorted(analysis['by_gram_length'].keys()):
        report_lines.append(f"  {gram_length}-grams:")
        for metric in ['character_cosine_similarity', 'character_kl_divergence',
                       'word_cosine_similarity', 'word_kl_divergence']:
            if metric in analysis['by_gram_length'][gram_length]:
                values = analysis['by_gram_length'][gram_length][metric]
                report_lines.append(f"    {metric}: mean={np.mean(values):.6f}, " +
                                  f"std={np.std(values):.6f}, max={np.max(values):.6f}")
    
    report_text = "\n".join(report_lines)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        logging.info(f"Comparative report saved to {output_file}")
    
    return report_text


def export_to_csv(results, output_file):
    """
    Export test results to CSV for analysis in spreadsheets.
    
    One row per test result, with columns for all metrics.
    """
    if not results:
        logging.warning("No results to export")
        return
    
    # Prepare rows
    rows = []
    for result in results:
        base_row = {
            'language': result['language'],
            'dialect': result['dialect'],
            'sources': ','.join(result['sources']),
            'total_sentences': result['corpus_stats']['total_sentences'],
            'unique_characters': result['corpus_stats']['unique_characters'],
            'max_freq_char': result['perturbation']['max_freq_character'],
            'char_frequency': result['perturbation']['character_frequency'],
            'swapped_with': result['perturbation']['swapped_with_character'],
        }
        
        # Add all metric deltas
        for level in ['character', 'word']:
            for gram_length in sorted(result['metric_deltas'][level].keys()):
                deltas = result['metric_deltas'][level][gram_length]
                for metric in ['cosine_similarity', 'kl_divergence']:
                    col_name = f"{level}_{gram_length}g_{metric}"
                    base_row[col_name] = deltas[metric]
        
        rows.append(base_row)
    
    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        logging.info(f"Results exported to CSV: {output_file}")
    else:
        logging.warning("No rows to export")


def compare_results_across_runs(result_dirs):
    """
    Compare results from multiple test runs.
    
    Useful for tracking robustness improvements over time.
    """
    comparison = {}
    
    for result_dir in result_dirs:
        timestamp = Path(result_dir).name
        results = load_results(result_dir)
        analysis = analyze_metric_deltas(results)
        comparison[timestamp] = analysis
    
    # Generate comparison report
    report_lines = []
    report_lines.append("=" * 100)
    report_lines.append("Cross-Run Comparison")
    report_lines.append(f"Comparing {len(result_dirs)} test runs")
    report_lines.append("=" * 100)
    
    # Overall statistics comparison
    report_lines.append("\nOverall Mean Changes by Run:")
    report_lines.append("-" * 100)
    
    for timestamp in sorted(comparison.keys()):
        analysis = comparison[timestamp]
        report_lines.append(f"\n{timestamp}:")
        
        for metric in ['character_cosine_similarity', 'character_kl_divergence',
                       'word_cosine_similarity', 'word_kl_divergence']:
            if metric in analysis['overall']:
                mean_val = np.mean(analysis['overall'][metric])
                report_lines.append(f"  {metric}: {mean_val:.6f}")
    
    return "\n".join(report_lines)


def main(args):
    """Main test runner."""
    logger = setup_logging()
    
    if args.load_results:
        logger.info(f"Loading results from {args.load_results}")
        results = load_results(args.load_results)
        validation_results = load_validation_results(args.load_results)
        
        if not results and not validation_results:
            logger.warning("No results loaded")
            return
        
        logger.info(f"Loaded {len(results)} test results and {len(validation_results)} validation results")
        
        # Generate comparative report
        if args.output_report:
            report = generate_comparative_report(results, args.output_report)
            
            # Append validation analysis if available
            if validation_results:
                val_analysis = analyze_validation_results(validation_results)
                report += "\n\n" + "=" * 100 + "\n"
                report += "XML CORPUS INTEGRITY VALIDATION SUMMARY\n"
                report += "=" * 100 + "\n\n"
                report += f"Validation Checks:\n"
                report += f"  Passed: {val_analysis['passed']}\n"
                report += f"  Warned: {val_analysis['warned']}\n"
                report += f"  Failed: {val_analysis['failed']}\n\n"
                
                if val_analysis['issues']:
                    report += "Corpus Integrity Issues:\n"
                    for issue in val_analysis['issues']:
                        report += f"  - {issue['language'].upper()}/{issue['dialect']}: {issue['issue']}\n"
                    report += "\n"
                
                if val_analysis['cross_language_patterns']:
                    report += "Cross-Language Character Set Analysis:\n"
                    for pattern in val_analysis['cross_language_patterns']:
                        report += f"  {pattern['language'].upper()}/{pattern['dialect']}: "
                        report += f"{pattern['char_count']} unique characters\n"
                        if pattern['overlaps']:
                            for overlap in pattern['overlaps']:
                                report += f"    - {overlap['language']}: {overlap['overlap_percentage']}% overlap\n"
                    report += "\n"
            
            with open(args.output_report, 'w', encoding='utf-8') as f:
                f.write(report)
            logger.info(f"Report saved to {args.output_report}")
            print(report)
        
        # Export to CSV
        if args.export_csv:
            export_to_csv(results, args.export_csv)
            logger.info(f"CSV export saved to {args.export_csv}")
    
    if args.compare_runs:
        logger.info(f"Comparing {len(args.compare_runs)} test runs")
        comparison = compare_results_across_runs(args.compare_runs)
        print(comparison)
        
        if args.output_comparison:
            with open(args.output_comparison, 'w', encoding='utf-8') as f:
                f.write(comparison)
            logger.info(f"Comparison report saved to {args.output_comparison}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test runner and analysis utilities for character perturbation tests"
    )
    parser.add_argument(
        '--load-results',
        type=str,
        help='Directory containing test results to analyze'
    )
    parser.add_argument(
        '--output-report',
        type=str,
        help='Output file for comparative analysis report'
    )
    parser.add_argument(
        '--export-csv',
        type=str,
        help='Export results to CSV file for spreadsheet analysis'
    )
    parser.add_argument(
        '--compare-runs',
        type=str,
        nargs='+',
        help='Compare results across multiple test run directories'
    )
    parser.add_argument(
        '--output-comparison',
        type=str,
        help='Output file for cross-run comparison report'
    )
    
    args = parser.parse_args()
    
    if not any(vars(args).values()):
        parser.print_help()
    else:
        main(args)
