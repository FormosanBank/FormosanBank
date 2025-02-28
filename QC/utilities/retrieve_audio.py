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


def download_huggingface_repo(repo_id, langs):
    """
    Download specific folders from a Hugging Face repository.

    Args:
        repo_id (str): The Hugging Face repository ID (e.g., "username/repo_name").
        output_dir (str): The directory where the files will be saved.
        folders (list): List of folder names to download (e.g., ["language1", "language2"]).
    """
    if 'ePark' in repo_id:
        ePark_topics = {'ePark1_Batch1':['ep1_九階教材'], 'ePark1_Batch2':['ep1_九階教材'],
                        'ePark2_Batch1':['ep2_學習詞表', 'ep2_情境族語'], 
                        'ePark2_Batch2':['ep2_文化篇', 'ep2_族語短文', 'ep2_生活會話篇', 'ep2_閱讀書寫篇'],
                        'ePark3_Batch1':['ep3_句型篇國中', 'ep3_句型篇高中', 'ep3_情境族語', 'ep3_繪本平台'],
                        'ePark3_Batch2':['ep3_圖畫故事篇', 'ep3_文化篇', 'ep3_族語短文', 'ep3_生活會話篇', 'ep3_閱讀書寫篇']}
        dirs = ePark_topics[repo_id]

    # print(repo_id, dirs)
    # Use `allow_patterns` to filter for specific folders
    if 'ePark' not in repo_id:
        while True:
            try:
                cache_dir = snapshot_download(
                    repo_id=f"wmohamed24/{repo_id}",
                    repo_type="dataset",
                    allow_patterns=[f"{lang}/*" for lang in langs],
                    max_workers=100,
                )
                print("Download completed successfully:", cache_dir)
                break  # Exit loop if successful

            except Exception as e:
                print(f"Download didn't finish, Retrying in 3 seconds...")
                # print("Retrying in 3 seconds...")
                time.sleep(3)  # Wait before retrying
    
    else:
        while True:
            try:
                cache_dir = snapshot_download(
                    repo_id=f"wmohamed24/{repo_id}",
                    repo_type="dataset",
                    allow_patterns=[f"{topic}/{lang}/*" for lang in langs for topic in dirs],
                    max_workers=100,
                )
                print("Download completed successfully:", cache_dir)
                break  # Exit loop if successful

            except Exception as e:
                print(f"Download didn't finish, Retrying in 3 seconds...")
                # print("Retrying in 3 seconds...")
                time.sleep(3)  # Wait before retrying

    return cache_dir



def main(args, possiblelangs):

    organize_by = args.organize_by
    if args.organize_by == "by_corpus":
        XML_path, corpus = args.XML_Path, args.corpus 
    elif args.organize_by == "by_language":
        output_path = args.output_dir
    languages = args.languages

    corpus_repo = {'ILRDF_Dicts': ['ILRDF_Dicts'], 'NTU_Paiwan_ASR': ['NTU_Paiwan_ASR'], 
                   'ePark': ['ePark1_Batch1', 'ePark1_Batch2', 'ePark2_Batch1', 'ePark2_Batch2', 'ePark3_Batch1', 'ePark3_Batch2']}
    
    if organize_by == "by_corpus":
        if languages == ['All']:
            languages = possiblelangs[corpus]
    else:
        if languages == ['All']:
            languages = possiblelangs["ILRDF_Dicts"]

    if organize_by == "by_corpus":
        audio_output = XML_path.replace("XML", "audio")
        os.makedirs(audio_output, exist_ok=True)
    else:
        os.makedirs(output_path, exist_ok=True)

    if organize_by == "by_language":
        corpora = list(corpus_repo.keys())
    else:
        corpora = [corpus]

    for corpus in corpora:
        caches = list()
        for repo in corpus_repo[corpus]:
            caches.append(download_huggingface_repo(repo, languages))
        
        if organize_by == "by_language":
            audio_output = os.path.join(output_path, corpus)
            os.makedirs(audio_output, exist_ok=True)
        
        for cache_dir in caches:
            # Move files from the cache to the output directory
            for folder in os.listdir(cache_dir):
                if not os.path.isdir(os.path.join(cache_dir, folder)):
                    continue
                #replace symlink files with actual ones
                replace_symlinks_in_folder(os.path.join(cache_dir, folder))
                
                src_folder = os.path.join(cache_dir, folder)
                dst_folder = os.path.join(audio_output, folder)
                
                if os.path.exists(src_folder):
                    if not os.path.exists(dst_folder):
                        shutil.move(src_folder, dst_folder)
                    else:
                        for item in os.listdir(src_folder):
                            shutil.move(os.path.join(src_folder, item), os.path.join(dst_folder, item))
                else:
                    print(f"Folder not found in the repository: {folder}")
    check_batches(audio_output)

if __name__ == "__main__":

    possiblelangs = {"ILRDF_Dicts": ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu'],
             "NTU_Paiwan_ASR": ['Paiwan'],
             "ePark": ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']}

    parser = argparse.ArgumentParser(description="Download the audio files for a corpus from HuggingFace")
    parser.add_argument('organize_by', choices=['by_language', 'by_corpus'], help="Whether to download audio files organized by corpus or by language")
    parser.add_argument('--XML_Path', help="The path containing the XML files. Required when organize_by is by_corpus")
    parser.add_argument('--corpus', help="The corpus for which audio is to be retrieved (currently supports ILRDF_Dicts). Required when organize_by is by_corpus")
    parser.add_argument('--output_dir', help="The output directory to save audio_files. Required when organize_by is by_language")
    parser.add_argument('--languages', nargs='+', help="The languages you want to download for the specified corpus. please provide a list. You can set to 'All' if you want to download all languages. Always required")
    args = parser.parse_args()
    
    if not args.languages:
        parser.error("Please provide the list of languages")

    if args.organize_by == "by_corpus":
        if not args.XML_Path:
            parser.error("Please provide the XML path")
        if not args.corpus:
            parser.error("Please provide the corpus name")
        if not os.path.exists(args.XML_Path):
            parser.error("entered path doesn't exist")
        if args.corpus not in possiblelangs.keys():
            parser.error("corpus is wrong or isn't supported")
        if args.languages != ['All'] and not all(lang in possiblelangs[args.corpus] for lang in args.languages):
            parser.error("please enter either 'All' or a list of valid languages for the specified corpus")
    elif args.organize_by == "by_language":
        if not args.output_dir:
            parser.error("Please provide the output directory")
        if args.languages != ['All'] and not all(lang in possiblelangs["ILRDF_Dicts"] for lang in args.languages):
            parser.error("please enter either 'All' or a list of valid languages")
        
    main(args, possiblelangs)