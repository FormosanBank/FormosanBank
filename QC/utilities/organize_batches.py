import os
import math
from pathlib import Path
import shutil
import argparse


def main(parent_folder, batch_size=10000):
    """
    Traverse all subfolders of a parent folder recursively. If a folder contains more than the
    specified batch_size, create batches and distribute files among those batches.

    Args:
        parent_folder (str): Path to the parent folder.
        batch_size (int): Maximum number of files per batch. Default is 10,000.
    """
    parent_folder = Path(parent_folder)

    if not parent_folder.is_dir():
        print(f"The provided parent folder '{parent_folder}' does not exist or is not a directory.")
        return

    # Recursively traverse all subfolders
    for subfolder in parent_folder.rglob('*'):
        if subfolder.is_dir():
            if ".cache" in (str(subfolder)) or ".git" in (str(subfolder)):
                continue
            files = [file for file in subfolder.iterdir() if file.is_file()]  # Get all files in the folder
            num_files = len(files)
            
            if num_files > batch_size:
                # Calculate number of batches required
                num_batches = math.ceil(num_files / batch_size)
                print(f"Organizing '{subfolder}' with {num_files} files into {num_batches} batches...")

                for batch_num in range(1, num_batches + 1):
                    # Create batch folder
                    batch_folder = subfolder / f"batch_{batch_num}"
                    batch_folder.mkdir(exist_ok=True)

                    # Move files into the batch folder
                    batch_files = files[(batch_num - 1) * batch_size : batch_num * batch_size]
                    for file in batch_files:
                        shutil.move(str(file), str(batch_folder))
                
                print(f"Finished organizing '{subfolder}' into batches.")
            else:
                print(f"'{subfolder}' has {num_files} files, no batching required.")

    print("Organization complete.")

# Example usage:
# Replace '/path/to/parent/folder' with the actual path to your parent folder
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Divide audio directory into batches")
    parser.add_argument('--path', help="the directory to iterate through and check if any of its sub-dirs has more than 10k files")
    args = parser.parse_args()
    if not os.path.exists(args.path):
        parser.error("entered path doesn't exist")
    
    main(args.path)
    25186/96769