#!/usr/bin/env python3
"""
XML Baseline Test Script
Analyzes the existing Paiwan XML file to establish baseline metrics for future scraping validation.
"""

import xml.etree.ElementTree as ET
import json
import os
from datetime import datetime

def analyze_xml_file(xml_file_path):
    """
    Analyze the XML file and return comprehensive statistics.
    
    Args:
        xml_file_path: Path to the XML file to analyze
    
    Returns:
        dict: Dictionary containing various metrics
    """
    try:
        # Parse the XML file
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        metrics = {
            'file_path': xml_file_path,
            'analysis_date': datetime.now().isoformat(),
            'file_size_bytes': os.path.getsize(xml_file_path)
        }
        
        # Count elements
        s_elements = root.findall('.//S')
        w_elements = root.findall('.//W')
        transl_elements = root.findall('.//TRANSL')
        form_elements = root.findall('.//FORM')
        
        metrics['element_counts'] = {
            'S': len(s_elements),
            'W': len(w_elements),
            'TRANSL': len(transl_elements),
            'FORM': len(form_elements)
        }
        
        # Analyze text content
        s_text_lengths = []
        w_text_lengths = []
        transl_text_lengths = []
        form_text_lengths = []
        
        s_total_chars = 0
        w_total_chars = 0
        transl_total_chars = 0
        form_total_chars = 0
        
        # Count S element content (FORM tags within S elements)
        for s_elem in s_elements:
            s_form = s_elem.find('FORM')
            if s_form is not None and s_form.text:
                text = s_form.text.strip()
                length = len(text)
                s_text_lengths.append(length)
                s_total_chars += length
        
        # Count W element content (FORM tags within W elements)
        for w_elem in w_elements:
            w_form = w_elem.find('FORM')
            if w_form is not None and w_form.text:
                text = w_form.text.strip()
                length = len(text)
                w_text_lengths.append(length)
                w_total_chars += length
        
        # Count TRANSL element content
        for transl_elem in transl_elements:
            if transl_elem.text:
                text = transl_elem.text.strip()
                length = len(text)
                transl_text_lengths.append(length)
                transl_total_chars += length
        
        # Count all FORM element content
        for form_elem in form_elements:
            if form_elem.text:
                text = form_elem.text.strip()
                length = len(text)
                form_text_lengths.append(length)
                form_total_chars += length
        
        metrics['text_statistics'] = {
            'S_sentences': {
                'total_characters': s_total_chars,
                'average_length': round(sum(s_text_lengths) / len(s_text_lengths), 2) if s_text_lengths else 0,
                'min_length': min(s_text_lengths) if s_text_lengths else 0,
                'max_length': max(s_text_lengths) if s_text_lengths else 0,
                'count': len(s_text_lengths)
            },
            'W_words': {
                'total_characters': w_total_chars,
                'average_length': round(sum(w_text_lengths) / len(w_text_lengths), 2) if w_text_lengths else 0,
                'min_length': min(w_text_lengths) if w_text_lengths else 0,
                'max_length': max(w_text_lengths) if w_text_lengths else 0,
                'count': len(w_text_lengths)
            },
            'TRANSL_translations': {
                'total_characters': transl_total_chars,
                'average_length': round(sum(transl_text_lengths) / len(transl_text_lengths), 2) if transl_text_lengths else 0,
                'min_length': min(transl_text_lengths) if transl_text_lengths else 0,
                'max_length': max(transl_text_lengths) if transl_text_lengths else 0,
                'count': len(transl_text_lengths)
            },
            'ALL_FORM_elements': {
                'total_characters': form_total_chars,
                'average_length': round(sum(form_text_lengths) / len(form_text_lengths), 2) if form_text_lengths else 0,
                'min_length': min(form_text_lengths) if form_text_lengths else 0,
                'max_length': max(form_text_lengths) if form_text_lengths else 0,
                'count': len(form_text_lengths)
            }
        }
        
        # Count attributes
        s_with_audio = len([s for s in s_elements if 'audio_url' in s.attrib])
        transl_with_lang = len([t for t in transl_elements if 'xml:lang' in t.attrib])
        
        metrics['attribute_statistics'] = {
            'S_elements_with_audio_url': s_with_audio,
            'TRANSL_elements_with_xml_lang': transl_with_lang,
            'percentage_S_with_audio': round((s_with_audio / len(s_elements)) * 100, 2) if s_elements else 0,
            'percentage_TRANSL_with_lang': round((transl_with_lang / len(transl_elements)) * 100, 2) if transl_elements else 0
        }
        
        # Unique audio URLs
        audio_urls = set()
        for s_elem in s_elements:
            if 'audio_url' in s_elem.attrib:
                audio_urls.add(s_elem.attrib['audio_url'])
        
        metrics['unique_audio_urls'] = len(audio_urls)
        
        # Sample audio URLs (first 5)
        metrics['sample_audio_urls'] = list(audio_urls)[:5]
        
        return metrics
        
    except ET.ParseError as e:
        return {'error': f'XML parsing error: {str(e)}'}
    except FileNotFoundError:
        return {'error': f'File not found: {xml_file_path}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def save_baseline_metrics(metrics, output_file):
    """Save metrics to JSON file for future comparison."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def compare_metrics(baseline_file, new_metrics):
    """Compare new metrics with baseline metrics."""
    try:
        with open(baseline_file, 'r', encoding='utf-8') as f:
            baseline = json.load(f)
        
        comparison = {
            'comparison_date': datetime.now().isoformat(),
            'differences': {}
        }
        
        # Compare element counts
        for element_type in ['S', 'W', 'TRANSL', 'FORM']:
            baseline_count = baseline['element_counts'].get(element_type, 0)
            new_count = new_metrics['element_counts'].get(element_type, 0)
            if baseline_count != new_count:
                comparison['differences'][f'{element_type}_count'] = {
                    'baseline': baseline_count,
                    'new': new_count,
                    'difference': new_count - baseline_count
                }
        
        # Compare text statistics
        for text_type in ['S_sentences', 'W_words', 'TRANSL_translations']:
            baseline_chars = baseline['text_statistics'][text_type]['total_characters']
            new_chars = new_metrics['text_statistics'][text_type]['total_characters']
            if baseline_chars != new_chars:
                comparison['differences'][f'{text_type}_characters'] = {
                    'baseline': baseline_chars,
                    'new': new_chars,
                    'difference': new_chars - baseline_chars
                }
        
        return comparison
        
    except FileNotFoundError:
        return {'error': f'Baseline file not found: {baseline_file}'}
    except Exception as e:
        return {'error': f'Comparison error: {str(e)}'}

def print_metrics_summary(metrics):
    """Print a human-readable summary of the metrics."""
    if 'error' in metrics:
        print(f"Error: {metrics['error']}")
        return
    
    print("=== Paiwan XML File Analysis ===")
    print(f"File: {metrics['file_path']}")
    print(f"Analysis Date: {metrics['analysis_date']}")
    print(f"File Size: {metrics['file_size_bytes']:,} bytes")
    print()
    
    print("Element Counts:")
    for element, count in metrics['element_counts'].items():
        print(f"  {element}: {count:,}")
    print()
    
    print("Text Statistics:")
    for text_type, stats in metrics['text_statistics'].items():
        print(f"  {text_type}:")
        print(f"    Total characters: {stats['total_characters']:,}")
        print(f"    Average length: {stats['average_length']}")
        print(f"    Min/Max length: {stats['min_length']}/{stats['max_length']}")
        print(f"    Count: {stats['count']:,}")
        print()
    
    print("Attribute Statistics:")
    for attr, value in metrics['attribute_statistics'].items():
        print(f"  {attr}: {value}")
    print()
    
    print(f"Unique Audio URLs: {metrics['unique_audio_urls']}")
    print("Sample Audio URLs:")
    for url in metrics['sample_audio_urls']:
        print(f"  {url}")

def print_comparison_summary(comparison):
    """Print a human-readable summary of the comparison."""
    if 'error' in comparison:
        print(f"Error: {comparison['error']}")
        return
    
    print("=== Comparison Results ===")
    print(f"Comparison Date: {comparison['comparison_date']}")
    
    if not comparison['differences']:
        print("✅ No differences found! The new file matches the baseline perfectly.")
        return
    
    print("❗ Differences found:")
    for key, diff in comparison['differences'].items():
        print(f"  {key}:")
        print(f"    Baseline: {diff['baseline']:,}")
        print(f"    New: {diff['new']:,}")
        print(f"    Difference: {diff['difference']:+,}")
        print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Paiwan XML files and compare against baseline')
    parser.add_argument('--compare', metavar='XML_FILE', 
                       help='Compare a new XML file against the baseline')
    parser.add_argument('--baseline', default='Scripts/baseline_metrics.json',
                       help='Path to baseline metrics file (default: Scripts/baseline_metrics.json)')
    parser.add_argument('--update-baseline', action='store_true',
                       help='Update the baseline with current XML file analysis')
    
    args = parser.parse_args()
    
    baseline_file = args.baseline
    
    if args.compare:
        # Compare mode
        print(f"Comparing {args.compare} against baseline...")
        new_metrics = analyze_xml_file(args.compare)
        
        if 'error' in new_metrics:
            print(f"Error analyzing new file: {new_metrics['error']}")
        else:
            print_metrics_summary(new_metrics)
            print("\n" + "="*50)
            
            comparison = compare_metrics(baseline_file, new_metrics)
            print_comparison_summary(comparison)
            
    else:
        # Default mode: analyze current XML and create/update baseline
        xml_file = "Final_XML/Paiwan_Yedda_Blog.xml"
        
        print("Analyzing XML file...")
        metrics = analyze_xml_file(xml_file)
        
        # Print summary
        print_metrics_summary(metrics)
        
        # Save baseline metrics
        if 'error' not in metrics:
            if args.update_baseline or not os.path.exists(baseline_file):
                print(f"\nSaving baseline metrics to {baseline_file}...")
                save_baseline_metrics(metrics, baseline_file)
                print("Baseline metrics saved successfully!")
            else:
                print(f"\nBaseline file already exists at {baseline_file}")
                print("Use --update-baseline to overwrite, or --compare to compare against it")
            
            print(f"\nTo compare future scraping results, run:")
            print(f"python Scripts/test_xml_baseline.py --compare <new_xml_file>")
        else:
            print("Cannot save baseline due to errors.")