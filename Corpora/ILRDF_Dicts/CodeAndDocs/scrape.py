import re
import os
import requests
import json
import PyPDF2 as ppdf
import string
import pickle
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


def getWords(lang: string) -> list:  # Function to extract words from PDF for a given language
    # Construct file path to the PDF dictionary of the specified language
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dicts", lang + ".pdf")
    
    # Read the PDF content
    all_tx = []
    with open(filepath, 'rb') as f:
        reader = ppdf.PdfReader(f)
        for num in range(len(reader.pages)):
            page = reader.pages[num]
            all_tx.append(page.extract_text())

    # Combine all text from the pages
    fullstring = ""
    for line in all_tx:
        fullstring += line
    
    # Split text by line and filter for words marked with a special character (★)
    sep = fullstring.split("\n")
    words = [word for word in sep if "★" in word]
    
    # Extract word phrases that match the pattern
    phrase = r"^([a-zA-Z'ʉ0-9\s]+)"
    return [result.group().replace(" ", "") for word in words if (result := re.search(phrase, word))]


def getData(lang: str, qw: str, TRIBES: dict, URL: str) -> 'str or dict':
    # Prepare API request payload with required parameters
    ask = {
        "FMT": 1,
        "account": "E202403005",
        "TribesCode": TRIBES[lang],
        "qw": qw
    }

    try:
        # Send a POST request to the API with the data
        jsn_response = requests.post(URL, data=ask)
        text = json.loads(jsn_response.text)
        
        # Check if request was successful, return extracted data if yes
        assert jsn_response.status_code == 200
        return text["GenericData"]['DATA']
    except requests.exceptions.RequestException as e:
        # Handle request errors and log
        print(f"Request failed with {qw}: {e}")
        return "FAIL"
    except Exception as e:
        # General error handling
        return "FAIL"


def processWords(lang, words, TRIBES, URL):
    word_sent_dict, fails = {}, []

    # Initialize ThreadPoolExecutor for handling multiple threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit tasks to process each word asynchronously
        futures = {executor.submit(getData, lang, query, TRIBES, URL): query for query in words}
        
        # Iterate over completed futures
        for future in tqdm(as_completed(futures), total=len(words)):
            query = futures[future]
            try:
                # Fetch the result from each future
                response = future.result()
                
                # Handle results based on response content
                if response == 'FAIL':
                    fails.append(query)  # Log failed queries
                word_sent_dict[query] = response
            except Exception as e:
                # Log any errors that occur during processing
                print(f"Error occurred while processing {query}: {e}")
                fails.append(query)

    return word_sent_dict, fails


def main():
    # Define base URL for the API
    URL = "https://e-dictionary.ilrdf.org.tw/wsReDictionary.htm"

    # Define the original dictionary of tribe codes with corresponding language names
    original_dict = {
        2: 'Amis', 6: 'Atayal', 24: 'Paiwan', 22: 'Bunun', 38: 'Puyma', 28: 'Rukai', 35: 'Tsou',
        13: 'Saisiyat', 42: 'Yami', 14: 'Thao', 34: 'Kavalan', 33: 'Truku', 43: 'Sakizaya', 16: 'Seediq',
        37: 'Saaroa', 36: 'Kanakanavu'
    }

    # Swap keys and values in the dictionary for easier lookups
    TRIBES = {v: k for k, v in original_dict.items()}

    # Define the list of languages to process
    NAMES = ["Amis"]

    # Set up paths for saving results and intermediate data
    base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.PickleScrapes')
    words_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "words_list")

    # Create directories if they do not exist
    if not os.path.exists(base_path):
        os.mkdir(base_path)
    if not os.path.exists(words_path):
        os.mkdir(words_path)

    # Create directories for each language in base_path
    for name in NAMES:
        check = os.path.join(base_path, name)
        if not os.path.exists(check):
            os.mkdir(check)
    done = []

    for lang in NAMES:
        # Skip processing if language already completed
        if lang in done:
            continue
        
        # Fetch or load the list of words for the current language
        print(f"Processing {lang}")
        print(f"\tGetting wordlist...")
        words_pickle_path = os.path.join(words_path, lang)
        if os.path.exists(words_pickle_path):
            with open(words_pickle_path, 'rb') as fp:
                words = pickle.load(fp)
        else:
            words = set(getWords(lang))  # Retrieve words from PDF if not cached
            words = sorted(list(words))
            words = [w for w in words if any(char.isalnum() for char in w)]
            with open(words_pickle_path, 'wb') as fp:
                pickle.dump(words, fp)
        
        # Initialize storage for results and failed queries
        word_sent_dict, fails, seen = dict(), list(), set()
        lang_pickle = os.path.join(base_path, lang)

        # Process words through the API to retrieve meanings/sentences
        print(f"\tDoing API requests...")
        word_sent_dict, fails = processWords(lang, words, TRIBES, URL)
        print("\nFinished API calls")
        
        # Save the results and failed queries
        with open(os.path.join(lang_pickle, f'{lang}_ckpt_END.pkl'), 'wb') as f: 
            pickle.dump(word_sent_dict, f)
        with open(os.path.join(lang_pickle, f'{lang}_fails_END.pkl'), 'wb') as f: 
            pickle.dump(fails, f)


if __name__ == "__main__":
    main()
