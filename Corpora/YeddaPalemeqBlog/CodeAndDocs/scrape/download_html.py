#!/usr/bin/env python3
"""
Download all HTML content from Yedda Palemeq's blog and save locally.
This allows us to scrape from local files instead of re-downloading during development.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import argparse
import time
from urllib.parse import urlparse
import hashlib

def get_safe_filename(url):
    """Convert URL to a safe filename"""
    # Use URL hash to create unique, filesystem-safe filenames
    url_hash = hashlib.md5(url.encode()).hexdigest()
    # Also include a readable part
    parsed = urlparse(url)
    path_part = parsed.path.strip('/').replace('/', '_')
    if len(path_part) > 50:
        path_part = path_part[:50]
    return f"{path_part}_{url_hash}.html"

def download_all_html(output_dir="html_cache", max_pages=None, delay=0.5):
    """
    Download all blog post HTML and index pages, saving them locally.
    
    Args:
        output_dir: Directory to save HTML files
        max_pages: Maximum number of index pages to process (None for all)
        delay: Delay between requests in seconds
    """
    base_url = "https://yeddapalemeq.blogspot.com/"
    current_url = base_url
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Keep track of what we've downloaded
    url_mapping = {}
    page_count = 0
    total_posts = 0
    
    print(f"Starting download to {output_dir}/")
    print(f"Delay between requests: {delay}s")
    
    while current_url:
        page_count += 1
        print(f"\nProcessing index page {page_count}: {current_url}")
        
        # Check if we've reached the page limit
        if max_pages and page_count > max_pages:
            print(f"Reached page limit ({max_pages}). Stopping.")
            break
        
        try:
            # Download index page
            response = requests.get(current_url)
            response.raise_for_status()
            
            # Save index page
            index_filename = get_safe_filename(current_url)
            index_path = os.path.join(output_dir, index_filename)
            
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            url_mapping[current_url] = index_filename
            print(f"  Saved index page: {index_filename}")
            
            # Parse to find individual posts
            soup = BeautifulSoup(response.content, 'html.parser')
            posts = soup.find_all('div', class_='post-outer')
            
            print(f"  Found {len(posts)} posts on this page")
            
            for post in posts:
                # Extract post URL
                title_elem = post.find('h3', class_='post-title')
                if not title_elem or not title_elem.find('a'):
                    continue
                    
                post_url = title_elem.find('a').get('href', '').strip()
                title_text = title_elem.get_text(strip=True)
                
                # Skip if not a "Paiwan Every Day" post (case-insensitive to handle typos
                # like 'Paiwa Every Day' (post 412), 'Paiwan Every Da' (post 587),
                # 'Paiwan Every day' (post 594), and 'Paiwan NNN' (posts 618/619) in the blogger's titles)
                title_lower = title_text.lower()
                if not (title_lower.startswith('paiwan every day') or
                        title_lower.startswith('paiwa every day') or
                        title_lower.startswith('paiwan every da') or
                        title_lower.startswith('paiwan 6')):
                    continue
                
                # Check if we already have this post
                post_filename = get_safe_filename(post_url)
                post_path = os.path.join(output_dir, post_filename)
                
                if os.path.exists(post_path):
                    print(f"    Skipping {title_text} (already downloaded)")
                    url_mapping[post_url] = post_filename
                    continue
                
                try:
                    # Download individual post
                    print(f"    Downloading: {title_text}")
                    post_response = requests.get(post_url)
                    post_response.raise_for_status()
                    
                    with open(post_path, 'w', encoding='utf-8') as f:
                        f.write(post_response.text)
                    
                    url_mapping[post_url] = post_filename
                    total_posts += 1
                    
                    # Delay between requests to be polite
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    print(f"    Error downloading {post_url}: {e}")
                    continue
            
            # Find next page
            older_link = soup.find('a', class_='blog-pager-older-link')
            current_url = older_link['href'] if older_link else None
            
            # Delay between index pages
            if delay > 0 and current_url:
                time.sleep(delay)
                
        except Exception as e:
            print(f"Error processing index page {current_url}: {e}")
            break
    
    # Save URL mapping for the scraper to use
    mapping_path = os.path.join(output_dir, 'url_mapping.json')
    with open(mapping_path, 'w', encoding='utf-8') as f:
        json.dump(url_mapping, f, ensure_ascii=False, indent=2)
    
    print(f"\nDownload complete!")
    print(f"Total index pages: {page_count}")
    print(f"Total posts downloaded: {total_posts}")
    print(f"URL mapping saved to: {mapping_path}")
    print(f"HTML files saved to: {output_dir}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download all HTML from Yedda Palemeq blog')
    parser.add_argument('--output-dir', default='html_cache', 
                       help='Directory to save HTML files (default: html_cache)')
    parser.add_argument('--max-pages', type=int, 
                       help='Maximum number of index pages to process (default: all)')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay between requests in seconds (default: 0.5)')
    
    args = parser.parse_args()
    
    download_all_html(
        output_dir=args.output_dir,
        max_pages=args.max_pages, 
        delay=args.delay
    )