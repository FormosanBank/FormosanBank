#!/usr/bin/env python3
"""
Wrapper script to run standardize.py on a single XML file by creating a temporary directory.
"""
import os
import sys
import tempfile
import shutil
import subprocess
import argparse

def main():
    parser = argparse.ArgumentParser(description='Run standardize.py on a single XML file')
    parser.add_argument('--xml_path', required=True, help='Path to the XML file')
    parser.add_argument('--tsv_path', required=True, help='Path to the TSV file')
    parser.add_argument('--target_column', help='Target column for standardization')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.xml_path):
        print(f"Error: XML file does not exist: {args.xml_path}")
        sys.exit(1)
    
    if not os.path.exists(args.tsv_path):
        print(f"Error: TSV file does not exist: {args.tsv_path}")
        sys.exit(1)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy the XML file to temp directory
        filename = os.path.basename(args.xml_path)
        temp_file_path = os.path.join(temp_dir, filename)
        shutil.copy2(args.xml_path, temp_file_path)
        
        # Build command for standardize.py
        cmd = [
            'python', 
            '../FormosanBank/QC/utilities/standardize.py',
            '--corpora_path', temp_dir,
            '--tsv_path', args.tsv_path
        ]
        
        if args.target_column:
            cmd.extend(['--target_column', args.target_column])
        
        # Run standardize.py
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("Standardization completed successfully!")
            if result.stdout:
                print("Output:", result.stdout)
            
            # Copy the modified file back
            shutil.copy2(temp_file_path, args.xml_path)
            print(f"Modified file saved back to: {args.xml_path}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error running standardize.py: {e}")
            if e.stderr:
                print("Error output:", e.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()