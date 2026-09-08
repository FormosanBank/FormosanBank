import requests
from bs4 import BeautifulSoup
import json
import time
import xml.etree.ElementTree as ET
from collections import Counter
import re
import os
import random
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout

# Get the directory of the currently executing script
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)
print("Current Working Directory:", os.getcwd())

BASE_URL = "https://glosbe.com/ami/zh/"
all_translations = []
sentence_id = 1

# Path to the XML file
xml_file = "../reference_amis/Amis.xml"

# List of User-Agents for randomization
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.2 Safari/605.1.15"
]

# Function to extract words from <FORM> elements
def extract_words(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    words = []
    for form in root.findall(".//FORM"):
        text = form.text
        if text:
            tokens = re.findall(r"\b[\w'-]+\b", text)
            words.extend(tokens)

    return words

# Function to find the 500 most common words
def find_most_common_words(words):
    word_counter = Counter(words)
    most_common_words = word_counter.most_common(500)
    return [word for word, count in most_common_words]

# Function to extract translations from the HTML
def extract_translations(soup, query):
    global sentence_id
    translations = []

    translation_blocks = soup.find_all("div", class_="odd:bg-slate-100 px-1")

    for block in translation_blocks:
        try:
            formosan_div = block.find("div", lang="ami")
            formosan_text = formosan_div.get_text(separator=" ").strip() if formosan_div else None

            chinese_div = block.find("div", lang="zh")
            chinese_text = chinese_div.get_text(separator=" ").strip() if chinese_div else None

            if formosan_text and chinese_text:
                translations.append({
                    "id": sentence_id,
                    "query": query,
                    "formosan": formosan_text,
                    "chinese": chinese_text,
                })
                sentence_id += 1
        except Exception as e:
            print(f"Error parsing block: {e}")

    return translations

# Function to make a request with retries
def make_request(url, session, max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            print(f"Making request to {url} with User-Agent: {headers['User-Agent']}")
            response = session.get(url, headers=headers, stream=True, timeout=10)
            response.raise_for_status()  # This will raise an exception for 4xx/5xx errors
            return response
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                print(f"404 Error: The URL {url} was not found. Skipping this word.")
                return None
            else:
                print(f"HTTP Error: {http_err}. Retrying ({retries}/{max_retries})...")
        except (ChunkedEncodingError, ConnectionError, Timeout) as e:
            retries += 1
            print(f"Request error: {e}. Retrying ({retries}/{max_retries})...")
            time.sleep(5 + random.uniform(0, 3))  # Randomized delay before retrying
    print("Max retries reached. Skipping this request.")
    return None


# Function to scrape translations for a given word
def scrape_word(word, session):
    query_url = BASE_URL + word
    translations = []
    page_number = 1

    while True:
        print(f"Scraping {query_url} (page {page_number})...")
        response = make_request(query_url, session)
        if not response:
            break

        soup = BeautifulSoup(response.text, "html.parser")
        translations.extend(extract_translations(soup, query_url))

        load_more_button = soup.find("button", {"data-element": "fragment-loader"})
        if not load_more_button:
            break

        fragment_url = load_more_button["data-fragment-url"]
        query_url = "https://glosbe.com" + fragment_url
        page_number += 1

        # Randomized delay to avoid rate limiting
        time.sleep(1 + random.uniform(0, 1))

    return translations

# Main script
def main():
    global all_translations

    words = extract_words(xml_file)
    common_words = find_most_common_words(words)

    # Create a session
    with requests.Session() as session:
        for word in common_words:
            translations = scrape_word(word, session)
            all_translations.extend(translations)

    # Save to JSON file
    with open("../json/amis_chinese_translations.json", "w", encoding="utf-8") as f:
        json.dump(all_translations, f, ensure_ascii=False, indent=4)

    print(f"Scraping completed. Total translations collected: {len(all_translations)}")

if __name__ == "__main__":
    main()
