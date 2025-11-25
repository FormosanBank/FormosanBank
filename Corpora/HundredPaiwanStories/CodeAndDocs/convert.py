import os
import sys
import argparse
from pathlib import Path
from lxml import etree

def apply_conversions_to_xml_files(folder_path, conversions, create_backup=True):
    """
    Loop through all XML files in a folder and replace text using conversions dictionary
    Only applies to FORM elements where kindOf="standard"
    """
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ Folder not found: {folder_path}")
        return False
    
    # Find all XML files
    xml_files = list(folder.glob("*.xml"))
    
    if not xml_files:
        print(f"❌ No XML files found in {folder_path}")
        return False
    
    print(f"Found {len(xml_files)} XML files to process...")
    
    # Track statistics
    total_files = 0
    modified_files = 0
    total_replacements = 0
    
    for xml_file in xml_files:
        try:
            # Parse the XML file without preserve_whitespace
            tree = etree.parse(str(xml_file))
            root = tree.getroot()
            
            file_replacements = 0
            file_modified = False
            
            # Find ONLY FORM elements with kindOf="standard"
            standard_forms = root.xpath('.//FORM[@kindOf="standard"]')
            
            if not standard_forms:
                print(f"  {xml_file.name}: no FORM[@kindOf='standard'] elements found")
                total_files += 1
                continue
            
            for form_element in standard_forms:
                if form_element.text:
                    original_text = form_element.text
                    modified_text = original_text
                    
                    # Apply each conversion
                    for old_char, new_char in conversions.items():
                        if old_char in modified_text:
                            count = modified_text.count(old_char)
                            modified_text = modified_text.replace(old_char, new_char)
                            file_replacements += count
                            
                            if count > 0:
                                print(f"  {xml_file.name}: {old_char} → {new_char} ({count} times) in standard form")
                    
                    # Update the element text if changes were made
                    if modified_text != original_text:
                        form_element.text = modified_text
                        file_modified = True
            
            # Write back if changes were made
            if file_modified:
                # Create backup only if requested
                backup_created = False
                if create_backup:
                    backup_path = xml_file.with_suffix('.xml.backup')
                    # Read original file for backup
                    with open(xml_file, 'r', encoding='utf-8') as f:
                        original_content = f.read()
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    backup_created = True
                
                # Write modified XML
                tree.write(str(xml_file), encoding='utf-8', xml_declaration=True)
                
                modified_files += 1
                total_replacements += file_replacements
                
                if backup_created:
                    print(f"✓ Modified {xml_file.name} ({file_replacements} replacements in STANDARD forms only, backup: {backup_path.name})")
                else:
                    print(f"✓ Modified {xml_file.name} ({file_replacements} replacements in STANDARD forms only, no backup)")
            else:
                print(f"  {xml_file.name}: no changes needed in standard forms")
            
            total_files += 1
            
        except Exception as e:
            print(f"❌ Error processing {xml_file.name}: {e}")
    
    # Summary
    print(f"\n" + "="*50)
    print(f"SUMMARY:")
    print(f"="*50)
    print(f"Total files processed: {total_files}")
    print(f"Files modified: {modified_files}")
    print(f"Total character replacements: {total_replacements}")
    print(f"🎯 Only FORM elements with kindOf='standard' were modified")
    print(f"🎯 FORM elements with kindOf='original' were left unchanged")
    
    if modified_files > 0:
        print(f"\n✅ Conversion complete!")
        if create_backup:
            print(f"📁 Original files backed up with .backup extension")
        else:
            print(f"⚠️ No backup files created (--no-backup used)")
        return True
    else:
        print(f"\nℹ️ No files needed modification")
        return False

def preview_conversions(folder_path, conversions):
    """
    Preview what changes would be made without actually modifying files
    Only shows changes for FORM elements where kindOf="standard"
    """
    folder = Path(folder_path)
    xml_files = list(folder.glob("*.xml"))
    
    print(f"PREVIEW - Changes that would be made in: {folder_path}")
    print(f"(Only in FORM elements with kindOf='standard')")
    print(f"="*50)
    
    total_changes = 0
    
    for xml_file in xml_files[:5]:  # Preview first 5 files
        try:
            # Parse the XML file without preserve_whitespace
            tree = etree.parse(str(xml_file))
            root = tree.getroot()
            
            file_changes = 0
            
            # Find ONLY FORM elements with kindOf="standard"
            standard_forms = root.xpath('.//FORM[@kindOf="standard"]')
            
            if not standard_forms:
                print(f"  {xml_file.name}: no FORM[@kindOf='standard'] elements")
                continue
            
            for form_element in standard_forms:
                if form_element.text:
                    text = form_element.text
                    
                    for old_char, new_char in conversions.items():
                        count = text.count(old_char)
                        if count > 0:
                            print(f"  {xml_file.name}: {old_char} → {new_char} ({count} times) in standard form")
                            file_changes += count
            
            if file_changes == 0:
                print(f"  {xml_file.name}: no changes needed in standard forms")
            
            total_changes += file_changes
            
        except Exception as e:
            print(f"❌ Error reading {xml_file.name}: {e}")
    
    if len(xml_files) > 5:
        print(f"  ... and {len(xml_files) - 5} more files")
    
    print(f"\nTotal changes across all files: {total_changes}")
    print(f"🎯 Only FORM[@kindOf='standard'] elements will be changed")
    print(f"🎯 FORM[@kindOf='original'] elements will remain unchanged")
    return total_changes > 0

def main():
    parser = argparse.ArgumentParser(description='Convert special characters in XML files (only in FORM elements with kindOf="standard")')
    parser.add_argument('folder_path', 
                        help='Path to folder containing XML files')
    parser.add_argument('--no-preview', 
                        action='store_true', 
                        help='Skip preview and apply changes directly')
    parser.add_argument('--no-backup', 
                        action='store_true', 
                        help='Do not create backup files')
    
    args = parser.parse_args()
    
    # Configuration
    conversions = {"ʔ":"'", "ḍ": "dr", "ts": "c", "ł": "lj", "Ḍ": "Dr", "Ts": "C", "Ł": "Lj"}
    
    print("XML Character Conversion Script")
    print("="*50)
    print(f"Target folder: {args.folder_path}")
    print(f"Target: FORM elements with kindOf='standard' ONLY")
    print(f"Conversions to apply:")
    for old, new in conversions.items():
        print(f"  {old} → {new}")
    
    if args.no_backup:
        print("⚠️ Backup files will NOT be created")
    else:
        print("📁 Backup files will be created (.backup extension)")
    print()
    
    # Check if folder exists
    if not os.path.exists(args.folder_path):
        print(f"❌ Folder not found: {args.folder_path}")
        sys.exit(1)
    
    # Preview changes first (unless --no-preview)
    if not args.no_preview:
        has_changes = preview_conversions(args.folder_path, conversions)
        
        if not has_changes:
            print("No changes needed. Exiting.")
            sys.exit(0)
        
        # Ask for confirmation
        response = input(f"\nProceed with modifications? (y/N): ").strip().lower()
        
        if response != 'y':
            print("Operation cancelled")
            sys.exit(0)
    
    # Apply conversions
    success = apply_conversions_to_xml_files(args.folder_path, conversions, create_backup=not args.no_backup)
    
    if success:
        print(f"\n🎉 Successfully converted characters in STANDARD forms only!")
        print(f"🎯 Original forms were preserved unchanged")
    else:
        print(f"\n⚠️ No files were modified")

if __name__ == "__main__":
    main()