import os
from xml.etree.ElementTree import parse, tostring
from tqdm import tqdm
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def dlAudio(url, audioPath, dlRate=1024*1024*5, maxRetries=10, retryDelay=5):
    # Function to download an audio file with retry mechanism
    retries = 0
    while retries < maxRetries:
        try:
            # Download the file in streaming mode
            with requests.get(url, stream=True, timeout=60) as response:
                response.raise_for_status()

                # Write the audio data to the file in chunks
                with open(audioPath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=dlRate):
                        file.write(chunk)
                break  # Exit loop if download is successful
        except:
            # Retry in case of failure, with a delay
            retries += 1
            time.sleep(retryDelay)
            
            # If max retries reached, skip the file
            if retries == maxRetries:
                print(f'Skipped {os.path.basename(audioPath)}')


def dlHelper(urls):
    # Function to manage parallel downloading of multiple audio files
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit download tasks to the executor
        futures = {executor.submit(dlAudio, url, audioPath): url for url, audioPath in urls}
        
        # Process each completed future
        for future in tqdm(as_completed(futures), total=len(urls)):
            url = futures[future]
            try:
                future.result()  # Wait for result and handle exceptions if any
            except Exception as e:
                print(f"Error occurred while downloading {url}: {e}")


def download_audios(xml_path, toDo):
    # Function to parse XML files and initiate downloads
    for lang in toDo:
        # Define path to the XML file for each language
        file = os.path.join(xml_path, lang, lang + ".xml")
        data = parse(file)  # Parse the XML file
        root = data.getroot()

        # Create a dictionary of sentence IDs to audio URLs
        urlPairs = {k.attrib['id']: k[2].attrib['url'] for k in root}

        # Prepare list of URLs for downloading
        urls = list()
        print(f"Processing {lang}...")
        for i, (sentenceID, url) in enumerate(urlPairs.items()):
            # Ensure data consistency by checking sentence ID and URL
            assert root[i].attrib['id'] == sentenceID
            assert root[i][2].attrib['url'] == url

            # Define path to save the audio file and add to download list
            audioPath = os.path.join(xml_path, lang, 'audio', sentenceID + '.mp3')
            urls.append((url, audioPath))
        
        # Download all audio files in parallel
        # dlHelper(urls)

        # Update XML file with local audio file paths
        for elem in root:
            elem[2].attrib['file'] = elem.attrib['id'] + ".mp3"

        # Save the modified XML structure back to the file
        xml_str = tostring(root, encoding='utf-8').decode('utf8')
        with open(os.path.join(xml_path, lang, lang + ".xml"), 'w', encoding='utf-8') as f:
            f.write(xml_str)


def main():
    # Define the base directory and folder for XML files
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    XML_FOLDER = "Final_XML"
    
    # Language codes for each language to be processed
    lang_codes = {
        "Amis": "ami", "Atayal": "tay", "Saisiyat": "xsy", "Thao": "ssf", "Seediq": "trv", "Bunun": "bnn",
        "Paiwan": "pwn", "Rukai": "dru", "Truku": "trv", "Kavalan": "ckv", "Tsou": "tsu", "Kanakanavu": "xnb",
        "Saaroa": "sxr", "Puyuma": "pyu", "Yami": "tao", "Sakizaya": "szy"
    }
    
    # Define which languages to process
    done = []  # List of already processed languages
    toDo = [i for i in lang_codes if i not in done]  # Languages left to process

    # Ensure audio directories exist for each language
    for lang in lang_codes:
        audioDir = os.path.join(curr_dir, XML_FOLDER, lang, 'audio')
        if not os.path.exists(audioDir):
            os.makedirs(audioDir)

    # Start the audio download process for each language
    download_audios(os.path.join(curr_dir, XML_FOLDER), toDo)    


if __name__ == "__main__":
    main()
