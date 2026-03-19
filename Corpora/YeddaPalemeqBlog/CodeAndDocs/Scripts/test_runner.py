#!/usr/bin/env python3
"""
Test runner for XML baseline validation
Demonstrates how to use the baseline test system
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return its output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def test_baseline_exists():
    """Test that baseline file exists and is readable."""
    baseline_file = "Scripts/baseline_metrics.json"
    if not os.path.exists(baseline_file):
        print("❌ Baseline file does not exist!")
        return False
    
    print("✅ Baseline file exists")
    return True

def test_xml_file_exists():
    """Test that the XML file exists."""
    xml_file = "XML/Paiwan_Yedda_Blog.xml"
    if not os.path.exists(xml_file):
        print("❌ XML file does not exist!")
        return False
    
    print("✅ XML file exists")
    return True

def test_self_comparison():
    """Test comparing the XML file against itself (should show no differences)."""
    print("\n🧪 Testing self-comparison (should show no differences)...")
    
    cmd = "python Scripts/test_xml_baseline.py --compare XML/Paiwan_Yedda_Blog.xml"
    returncode, stdout, stderr = run_command(cmd)
    
    if returncode != 0:
        print(f"❌ Self-comparison failed with error: {stderr}")
        return False
    
    if "No differences found" in stdout:
        print("✅ Self-comparison passed - no differences found as expected")
        return True
    else:
        print("❌ Self-comparison failed - unexpected differences found")
        print("Output:")
        print(stdout)
        return False

def main():
    """Run all tests."""
    print("=== Baseline Test Validation ===")
    
    tests = [
        ("Checking baseline file", test_baseline_exists),
        ("Checking XML file", test_xml_file_exists),
        ("Testing self-comparison", test_self_comparison),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! The baseline system is working correctly.")
        
        print("\n📖 Usage Examples:")
        print("1. Create/update baseline:")
        print("   python Scripts/test_xml_baseline.py")
        
        print("\n2. Compare a new XML file:")
        print("   python Scripts/test_xml_baseline.py --compare path/to/new_file.xml")
        
        print("\n3. Update baseline forcefully:")
        print("   python Scripts/test_xml_baseline.py --update-baseline")
        
        return True
    else:
        print("❌ Some tests failed. Please check the setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)