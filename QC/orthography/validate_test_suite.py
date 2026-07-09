#!/usr/bin/env python
"""
Validation script for Character Perturbation Robustness Test Suite

Checks that:
1. All required files exist
2. Dependencies are installed
3. Corpus data is accessible
4. Orthography files are present
5. Test suite can be executed

Usage:
    python validate_test_suite.py [--fix]
    
Options:
    --fix: Attempt to fix common issues automatically
    --verbose: Print detailed diagnostic information
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import importlib.util


class ValidationResult:
    """Track validation check results."""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
        
    def add_check(self, name, status, details=""):
        """Add a check result."""
        self.checks.append({
            'name': name,
            'status': status,
            'details': details
        })
    
    def add_warning(self, message):
        """Add a warning."""
        self.warnings.append(message)
    
    def add_error(self, message):
        """Add an error."""
        self.errors.append(message)
    
    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for c in self.checks if c['status'] == 'PASS')
        failed = sum(1 for c in self.checks if c['status'] == 'FAIL')
        
        print(f"\nChecks: {passed} passed, {failed} failed (total {len(self.checks)})")
        
        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  ⚠ {w}")
        
        if self.errors:
            print(f"\nErrors ({len(self.errors)}):")
            for e in self.errors:
                print(f"  ✗ {e}")
        
        print(f"\nOverall Status: {'PASSED ✓' if not self.errors else 'FAILED ✗'}")
        print("=" * 80 + "\n")
        
        return len(self.errors) == 0


def check_file_exists(filepath, required=True):
    """Check if a file exists."""
    exists = os.path.isfile(filepath)
    status = "PASS" if exists else "FAIL"
    req_text = "(required)" if required else "(optional)"
    details = f"Found at {filepath}" if exists else f"Not found: {filepath} {req_text}"
    return status, details


def check_directory_exists(dirpath):
    """Check if a directory exists."""
    exists = os.path.isdir(dirpath)
    status = "PASS" if exists else "FAIL"
    details = f"Found at {dirpath}" if exists else f"Not found: {dirpath}"
    return status, details


def check_python_module(module_name):
    """Check if a Python module can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return "FAIL", f"Module {module_name} not found"
        return "PASS", f"Module {module_name} is available"
    except (ImportError, ModuleNotFoundError) as e:
        return "FAIL", f"Module {module_name} import failed: {e}"


def check_csv_file(filepath):
    """Check if a CSV file is readable."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            f.readline()
        return "PASS", f"CSV file readable: {filepath}"
    except Exception as e:
        return "FAIL", f"CSV file not readable: {e}"


def validate_test_suite(verbose=False):
    """Run all validation checks."""
    result = ValidationResult()
    
    base_dir = Path(".").resolve()
    
    print("\n" + "=" * 80)
    print("VALIDATING CHARACTER PERTURBATION ROBUSTNESS TEST SUITE")
    print("=" * 80)
    
    # 1. Check base directory structure
    print("\n[1/6] Checking directory structure...")
    
    for required_dir in ["Corpora", "Orthographies", "QC/orthography", "dialects.csv"]:
        full_path = base_dir / required_dir
        if "/" in required_dir or required_dir.endswith(".csv"):
            # It's a file
            status, details = check_file_exists(str(full_path), required=True)
        else:
            # It's a directory
            status, details = check_directory_exists(str(full_path))
        
        if status == "FAIL":
            result.add_error(f"Required directory/file missing: {required_dir}")
        
        result.add_check(f"Directory: {required_dir}", status, details)
    
    # 2. Check test suite files
    print("[2/6] Checking test suite files...")
    
    test_suite_files = [
        "QC/orthography/test_character_perturbation_robustness.py",
        "QC/orthography/test_runner.py",
        "QC/orthography/test_config.py",
        "QC/orthography/run_tests.sh",
    ]
    
    for test_file in test_suite_files:
        status, details = check_file_exists(test_file, required=True)
        if status == "FAIL":
            result.add_error(f"Test suite file missing: {test_file}")
        result.add_check(f"Test file: {Path(test_file).name}", status, details)
    
    # 3. Check dependencies
    print("[3/6] Checking Python dependencies...")
    
    required_modules = [
        "numpy",
        "pandas",
        "matplotlib",
        "argparse",
        "json",
    ]
    
    for module in required_modules:
        status, details = check_python_module(module)
        if status == "FAIL":
            result.add_error(f"Missing dependency: {module}")
        result.add_check(f"Dependency: {module}", status, details)
    
    # 4. Check orthography files
    print("[4/6] Checking orthography files...")
    
    languages = ["ami", "tay", "bnn", "pwn", "pyu", "dru", "trv"]
    ortho_dir = base_dir / "Orthographies/Ortho113"
    
    if os.path.isdir(ortho_dir):
        ortho_files = list(ortho_dir.glob("*.tsv"))
        ortho_langs = {f.stem for f in ortho_files}
        
        for lang in languages:
            ortho_file = ortho_dir / f"{lang}.tsv"
            if os.path.isfile(ortho_file):
                status, details = check_file_exists(str(ortho_file), required=False)
            else:
                status, details = "FAIL", f"Orthography file missing: {lang}.tsv"
                result.add_warning(f"Orthography file missing for language: {lang}")
            
            result.add_check(f"Orthography: {lang}", status, details)
    else:
        result.add_error(f"Orthography directory not found: {ortho_dir}")
    
    # 5. Check corpus sources
    print("[5/6] Checking corpus sources...")
    
    sources = ["ePark", "ILRDF_Dicts", "Paiwan_Stories", "NTUFormosanCorpus"]
    corpora_dir = base_dir / "Corpora"
    
    if os.path.isdir(corpora_dir):
        available_sources = [d.name for d in corpora_dir.iterdir() if d.is_dir()]
        
        for source in sources:
            source_path = corpora_dir / source
            if source_path.is_dir():
                status, details = "PASS", f"Source available: {source}"
            else:
                status, details = "FAIL", f"Source not found: {source}"
                result.add_warning(f"Corpus source missing: {source}")
            
            result.add_check(f"Corpus source: {source}", status, details)
    else:
        result.add_error(f"Corpora directory not found: {corpora_dir}")
    
    # 6. Check dialects.csv
    print("[6/6] Checking dialect configuration...")
    
    dialects_file = base_dir / "dialects.csv"
    if os.path.isfile(dialects_file):
        status, details = check_csv_file(str(dialects_file))
        if status == "PASS":
            # Try to load and check languages
            try:
                import pandas as pd
                df = pd.read_csv(dialects_file)
                unique_langs = df['Language'].unique()
                
                for lang in languages:
                    if lang.capitalize() in unique_langs or lang in unique_langs:
                        pass  # Language found
                    else:
                        result.add_warning(f"Language not found in dialects.csv: {lang}")
                
                status, details = "PASS", f"dialects.csv loaded, {len(unique_langs)} languages found"
            except Exception as e:
                status, details = "FAIL", f"Error reading dialects.csv: {e}"
        
        result.add_check("Dialect configuration", status, details)
    else:
        result.add_error("dialects.csv not found")
    
    return result


def run_minimal_test():
    """Run a minimal test to verify functionality."""
    print("\n" + "=" * 80)
    print("RUNNING MINIMAL FUNCTIONALITY TEST")
    print("=" * 80 + "\n")
    
    try:
        print("Attempting to run minimal test suite...")
        cmd = [
            "python",
            "QC/orthography/test_character_perturbation_robustness.py",
            "--languages", "ami",
            "--sources", "ePark",
            "--output-dir", "test_results/validation_test"
        ]
        
        if sys.platform == "win32":
            # Windows
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        else:
            # Unix-like
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✓ Minimal test PASSED")
            print("\nTest output:")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            return True
        else:
            print("✗ Minimal test FAILED")
            print("\nError output:")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("✗ Minimal test TIMEOUT (exceeded 120 seconds)")
        return False
    except Exception as e:
        print(f"✗ Minimal test ERROR: {e}")
        return False


def print_recommendations(result):
    """Print recommendations based on validation results."""
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80 + "\n")
    
    if result.errors:
        print("CRITICAL ISSUES TO FIX:")
        for i, error in enumerate(result.errors, 1):
            print(f"  {i}. {error}")
        print("\n  → Fix these issues before running tests\n")
    
    if result.warnings:
        print("OPTIONAL IMPROVEMENTS:")
        for i, warning in enumerate(result.warnings, 1):
            print(f"  {i}. {warning}")
        print("\n  → These are optional but may affect test completeness\n")
    
    print("NEXT STEPS:")
    print("  1. Fix any critical errors above")
    print("  2. Review test documentation: QC/orthography/README_TEST_SUITE.md")
    print("  3. Run a quick test: python QC/orthography/test_character_perturbation_robustness.py \\")
    print("                         --languages ami pwn --sources ePark")
    print("  4. Analyze results: python QC/orthography/test_runner.py --load-results test_results/...")


def main(args):
    """Main validation entry point."""
    
    # Change to repo root if needed
    if not os.path.exists("dialects.csv"):
        # Try to find repo root
        for _ in range(5):
            if os.path.exists("dialects.csv"):
                break
            os.chdir("..")
        
        if not os.path.exists("dialects.csv"):
            print("ERROR: Could not find FormosanBank repository root (dialects.csv)")
            sys.exit(1)
    
    # Run validation
    result = validate_test_suite(verbose=args.verbose)
    
    # Print summary
    success = result.print_summary()
    
    # Print recommendations
    print_recommendations(result)
    
    # Optionally run minimal test
    if success and args.test:
        test_success = run_minimal_test()
        if not test_success:
            print("\n✗ Minimal test failed. See output above for details.")
            sys.exit(1)
    
    # Exit with appropriate code
    if success:
        print("\n✓ Validation PASSED - Test suite is ready to use!")
        print("\nQuick start:")
        print("  python QC/orthography/test_character_perturbation_robustness.py \\")
        print("    --languages ami pwn --sources ePark --output-dir test_results/my_test")
        sys.exit(0)
    else:
        print("\n✗ Validation FAILED - Fix issues above and try again")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate Character Perturbation Robustness Test Suite setup"
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run a minimal functionality test after validation'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed diagnostic information'
    )
    
    args = parser.parse_args()
    main(args)
