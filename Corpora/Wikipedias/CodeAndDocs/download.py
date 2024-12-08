import requests
import wikipediaapi
import re
import os
import pickle
import regex
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime
from tqdm import tqdm

# Retry decorator function
def retry(retries=3, delay=2, backoff=2):
    def retry_decorator(func):
        def wrapper(*args, **kwargs):
            tries = retries
            current_delay = delay  # Use a local variable for delay
            while tries > 0:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    tries -= 1
                    print(f"Error: {str(e)}. Retrying... ({retries - tries}/{retries})")
                    time.sleep(current_delay)
                    current_delay *= backoff  # Apply exponential backoff to the local variable
            raise Exception("Failed after retries")
        return wrapper
    return retry_decorator

def get_titles(lang_code, titles_path):
    """
    Retrieve article titles from a specific language Wikipedia
    """
    print(f"getting titles of {lang_code}")
    curr_titles_path = os.path.join(titles_path, lang_code)
    if os.path.exists(curr_titles_path):
        with open (curr_titles_path, 'rb') as fp:
            titles = pickle.load(fp)
        return titles

    # Construct the Wikipedia API URL using the language code
    url = f"https://{lang_code}.wikipedia.org/w/api.php"

    # Set the parameters for the API request
    # - 'action': 'query' is used to perform a query on Wikipedia
    # - 'format': 'json' ensures the response is in JSON format
    # - 'list': 'allpages' requests a list of all pages on the Wikipedia
    # - 'limit': '500' limits the number of pages retrieved in one request to 500
    params = {
        'action': 'query',
        'format': 'json',
        'list': 'allpages',
        'limit': '500'
    }

    all_pages = list()

    # Loop to handle paginated results from the API
    while True:
        # Send the API request and get the response in JSON format
        re = requests.get(url, params).json()

        # Check if the 'query' and 'allpages' keys exist in the response
        if re.get('query') and re['query'].get('allpages'):
            # Extend the all_pages list with the retrieved pages
            all_pages.extend(re['query']['allpages'])

        # Break the loop if there are no more pages to retrieve (no 'continue' key)
        if 'continue' not in re:
            break
        # Update the parameters with the 'continue' key to get the next set of pages
        params.update(re['continue'])

    titles = [page['title'] for page in all_pages]
    with open(curr_titles_path, 'wb') as fp:
        pickle.dump(titles, fp)
    return titles


@retry(retries=3)
def read_article(title, wiki_wiki, lang_path):
    brackets = r'\(\)|\{\}|\[\]'

    # Clean up the page name by removing newline characters and special characters
    title_search = title.replace('\n', '')
    title = re.sub(r'\.', '', title)  # Remove periods
    title = re.sub(r'/', '', title)          # Remove slashes
    title = re.sub(r' ', '_', title)         # Replace spaces with underscores
    title = title.replace('\n', '')          # Ensure no newline characters

    # Fetch the page info using the Wikipedia API
    page_info = wiki_wiki.page(title_search)
    if page_info.exists():
        try:
            # Save the text to a file
            with open(os.path.join(lang_path, title + '.txt'), 'w', newline='', encoding='utf-8') as file:
                file.write(page_info.text)

        except Exception as e:
            print(f"Error processing article '{title}': {str(e)}")
    else:
        print(f"Page '{title}' does not exist.")

    
def download_articles(titles, lang_path, lang_code):
    wiki_wiki = wikipediaapi.Wikipedia('Amis_language (merlin@example.com)', lang_code)
    if not os.path.exists(lang_path):
        os.makedirs(lang_path)

    with ThreadPoolExecutor(max_workers=10) as executor:  # 10 threads for parallel downloading
        future_to_article = {executor.submit(read_article, title, wiki_wiki, lang_path): title for title in titles}
        
        for future in tqdm(as_completed(future_to_article), desc=f"downloading articles of {lang_code}", total=len(titles)):
            future.result()  # This will call read_article and get the result
        
def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    lang_codes = {"Amis":"ami", "Atayal":"tay", "Saisiyat":"xsy", "Thao":"ssf", "Seediq":"trv", "Bunun":"bnn", 
                  "Paiwan":"pwn", "Rukai":"dru", "Truku":"trv", "Kavalan":"ckv", "Tsou":"tsu", "Kanakanavu":"xnb", 
                  "Saaroa":"sxr", "Puyuma":"pyu", "Yami":"tao", "Sakizaya":"szy"}
    for lang in ["Amis", "Seediq", "Atayal", "Sakizaya", "Paiwan"]:
        titles = get_titles(lang_codes[lang], os.path.join(curr_dir, "Titles"))
        download_articles(titles, os.path.join(curr_dir, "Articles", lang), lang_codes[lang])    

if __name__ == "__main__":
    main()