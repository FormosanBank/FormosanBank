from huggingface_hub import snapshot_download, login
import argparse
import os
import shutil
from pathlib import Path
import time 

def replace_symlinks_in_folder(folder):
    """Recursively replaces symlinks inside a folder with the actual files."""
    
    for root, dirs, files in os.walk(folder):
        for name in files:
            file_path = os.path.join(root, name)
            
            if os.path.islink(file_path):  # Check if it's a symlink
                rel_target = os.readlink(file_path)
                
                # Convert to absolute path
                if os.path.isabs(rel_target):
                    abs_target = rel_target
                else:
                    abs_target = os.path.join(os.path.dirname(file_path), rel_target)
                
                # Ensure the actual file exists
                if not os.path.exists(abs_target):
                    print(f"Warning: Target file for {file_path} does not exist! Skipping...")
                    continue

                try:
                    # Remove the symlink
                    os.remove(file_path)
                    
                    # Move the actual file in place of the symlink
                    shutil.move(abs_target, file_path)
                    # print(f"Replaced symlink: {file_path} -> {abs_target}")

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

def check_batches(parent_folder):
    """
    Traverse all subfolders of a parent folder recursively. If a folder contains
    `batch_*` subfolders, move the files back into the parent folder and delete the batch folders.

    Args:
        parent_folder (str): Path to the parent folder.
    """
    parent_folder = Path(parent_folder)

    if not parent_folder.is_dir():
        print(f"The provided parent folder '{parent_folder}' does not exist or is not a directory.")
        return

    # Recursively traverse all subfolders
    for subfolder in parent_folder.rglob('*'):
        if subfolder.is_dir() and any(child.name.startswith("batch_") for child in subfolder.iterdir() if child.is_dir()):
            print(f"Found batches in '{subfolder}'. Reversing...")

            # Process all `batch_*` subfolders
            for batch_folder in sorted(subfolder.glob("batch_*")):
                if batch_folder.is_dir():
                    # print(str(batch_folder))
                    # continue
                    # Move all files in the batch folder to the parent folder
                    for file in batch_folder.iterdir():
                        shutil.move(file, str(subfolder))

                    # Remove the empty batch folder
                    batch_folder.rmdir()
            
            print(f"Finished reversing batches in '{subfolder}'.")
    
    print("Reverse process complete.")


def download_huggingface_repo(repo_id, output_dir, folders):
    """
    Download specific folders from a Hugging Face repository.

    Args:
        repo_id (str): The Hugging Face repository ID (e.g., "username/repo_name").
        output_dir (str): The directory where the files will be saved.
        folders (list): List of folder names to download (e.g., ["language1", "language2"]).
    """

    # Use `allow_patterns` to filter for specific folders
    while True:
        try:
            cache_dir = snapshot_download(
                repo_id=repo_id,
                repo_type="dataset",
                allow_patterns=[f"{folder}/*" for folder in folders],
                max_workers=100,
            )
            print("Download completed successfully:", cache_dir)
            break  # Exit loop if successful

        except Exception as e:
            print(f"Download failed: {e}")
            print("Retrying in 3 seconds...")
            time.sleep(3)  # Wait before retrying
    
    

    # Move files from the cache to the output directory
    for folder in folders:
        #replace symlink files with actual ones
        replace_symlinks_in_folder(os.path.join(cache_dir, folder))
        
        src_folder = os.path.join(cache_dir, folder)
        dst_folder = os.path.join(output_dir, folder)
        
        if os.path.exists(src_folder):
            shutil.move(src_folder, dst_folder)
            print(f"Downloaded language: {folder}")
        else:
            print(f"Folder not found in the repository: {folder}")



def main(XML_path, corpus, languages, possiblelangs):
    if languages == ['All']:
        languages = possiblelangs[corpus]
    audio_output = XML_path.replace("XML", "audio")
    os.makedirs(audio_output, exist_ok=True)
    download_huggingface_repo(f"wmohamed24/{corpus}", audio_output, languages)
    check_batches(audio_output)

if __name__ == "__main__":

    possiblelangs = {"ILRDF_Dicts": ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu'],
             "NTU_Paiwan_ASR": ['Paiwan']}

    parser = argparse.ArgumentParser(description="Download the audio files for a corpus from HuggingFace")
    parser.add_argument('--XML_Path', help="The path containing the XML files")
    parser.add_argument('--corpus', help="The corpus for which audio is to be retrieved (currently supports ILRDF_Dicts)")
    parser.add_argument('--languages', nargs='+', help="The languages you want to download for the specified corpus. please provide a list. You can set to 'All' if you want to download all languages in the corpus")
    args = parser.parse_args()
    if not args.XML_Path:
        parser.error("Please provide the XML path")
    if not args.corpus:
        parser.error("Please provide the corpus name")
    if not args.languages:
        parser.error("Please provide the list of languages")
    if not os.path.exists(args.XML_Path):
        parser.error("entered path doesn't exist")
    if args.corpus not in possiblelangs.keys():
        parser.error("corpus is wrong or isn't supported")
    if args.languages != ['All'] and not all(lang in possiblelangs[args.corpus] for lang in args.languages):
        parser.error("please enter either 'All' or a list of valid languages for the specified corpus")
    
    main(args.XML_Path, args.corpus, args.languages, possiblelangs)