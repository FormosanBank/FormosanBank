#!/usr/bin/env python3

import os
import json
import re
import argparse
import html
import xml.etree.ElementTree as ET
from xml.dom import minidom
from bs4 import BeautifulSoup

# Define yellow text elements to ignore for specific blog posts
# Format: (url_identifier, [list_of_exact_text_matches_to_ignore])
YELLOW_TEXT_IGNORE_LIST = [
    # Post 588: Ignore grammatical markers, keep only the main sentence
    ("paiwan-every-day-588-dudu-tjaljaduduan", ["an", "en", "in"]),
    # Post 525: Add specific ignores for this post (to be determined)
    ("paiwan-every-day-525-angac-pangac", ["pualju a tjainan."]),  # Example - may need adjustment
    ("paiwan-every-day-524-angata", ["angata"]),
    ("paiwan-every-day-523-angalj", ["angalj"]),
    ("paiwan-every-day-522-anga", ["anga", "vaik-anga", "ti kam(a)-anga", "ti Utjung-anga"]),
    ("paiwan-every-day-502-aladji", ["aladji"]),
    ("paiwan-every-day-494-aken-tiaken", ["a-ken"]),
    ("paiwan-every-day-493-ainu-inu", ["inu", "a-inu"]),
    ("paiwan-every-day-491-agu-quzip", ["agu"]),
    ("paiwan-every-day-488-adjaq-cakar", ["adjaq"]),
    ("paiwan-every-day-487-adam-qayaqayam", ["adam"]),

]

def preprocess_gloss(gloss_text):
    """
    Preprocess gloss text to fix specific formatting issues.
    Currently handles: "a;LIG" -> "a: LIG"
    """
    if gloss_text.strip() == "a;LIG":
        return "a: LIG"
    return gloss_text

def extract_example_numbers_from_title(title):
    """Extract example numbers from blog post title."""
    match = re.search(r'Paiwan Every Day (\d+(?:/\d+)*)', title, re.IGNORECASE)
    if not match:
        return []
    
    numbers_str = match.group(1)
    if '/' in numbers_str:
        return [int(n.strip()) for n in numbers_str.split('/')]
    else:
        return [int(numbers_str)]

def handle_664665_special_case(soup):
    """Special handler for post 664/665 where first example has no sentence."""
    blocks = []
    
    # Block 1: Only gloss and audio (extract word from first gloss)
    block1 = {
        'paiwan_text': 'pai',  # Will be updated from gloss if found
        'translation': None,
        'glosses': None,
        'audio_url': None
    }
    
    # Block 2: The actual sentence example
    block2 = {
        'paiwan_text': 'pai, samalji a ku salasaladj tua patjara mavuca a caucau.',
        'translation': None,
        'glosses': None,
        'audio_url': None
    }
    
    # Find post body and extract components
    post_body = soup.find(class_='post-body')
    if post_body:
        # Look for glosses
        gloss_text = post_body.get_text()
        if 'Word gloss' in gloss_text or 'Glossary' in gloss_text or "Glossary:" in gloss_text:
            all_lists = post_body.find_all(['ol', 'ul'])
            for list_elem in all_lists:
                items = list_elem.find_all('li')
                if items and len(items) >= 2:
                    sample_text = ' '.join([item.get_text()[:100] for item in items[:3]])
                    if any(indicator in sample_text.lower() for indicator in 
                           [':', 'actor focus', 'person', 'root is', 'gen', 'nom', 'obl', 'lig']):
                        # For 664/665: Block 1 has simple "pai" gloss, Block 2 gets all numbered glosses
                        all_gloss_items = [preprocess_gloss(li.get_text(strip=True)) for li in items]
                        block1['glosses'] = ['pai: look, thereupon, filler to initiate a new topic']
                        block2['glosses'] = all_gloss_items if all_gloss_items else []
                        
                        # Extract Paiwan word from first gloss for block1
                        if all_gloss_items:
                            first_gloss = all_gloss_items[0]
                            # Extract word before first colon (format: "pai: look, thereupon...")
                            if ':' in first_gloss:
                                paiwan_word = first_gloss.split(':')[0].strip()
                                if paiwan_word:
                                    block1['paiwan_text'] = paiwan_word
                        break
        
        # Look for translation
        full_text = ''.join(list(post_body.stripped_strings))
        translation_patterns = ["Free translation:", "English translation:", "In English:", "Translation:", "Ferrell's translation:", "Ferrell's translation(p. 59):", "In Engllish:"]
        stop_patterns = ['Word gloss:', 'Glossary:', 'Morphological breakdown:', 'Reading:', 'Voice file:', 'Audio:', 'Listen:', 'From klokah.org']
        
        for pattern in translation_patterns:
            if pattern in full_text:
                start_pos = full_text.find(pattern) + len(pattern)
                end_pos = len(full_text)
                for stop_pattern in stop_patterns:
                    stop_pos = full_text.find(stop_pattern, start_pos)
                    if stop_pos != -1 and stop_pos < end_pos:
                        end_pos = stop_pos
                
                translation_text = full_text[start_pos:end_pos].strip()
                if translation_text:
                    # Assign translation to block2 (the actual sentence)
                    block2['translation'] = translation_text[:100] + "..." if len(translation_text) > 100 else translation_text
                    break
        
        # Look for audio
        iframes = post_body.find_all('iframe')
        audio_urls = []
        for iframe in iframes:
            src = iframe.get('src', '')
            if 'youtube.com/embed/' in src:
                audio_urls.append(src)
        
        # Assign different audio URLs to different blocks
        if len(audio_urls) >= 1:
            block1['audio_url'] = audio_urls[0]
        if len(audio_urls) >= 2:
            block2['audio_url'] = audio_urls[1]
    
    blocks.append(block1)
    blocks.append(block2)
    return blocks

def handle_588_special_case(soup):
    """Handle post 588 which has one main example plus grammatical highlight markers that should be ignored."""
    blocks = []
    
    # This post has one main example: "tjaljaduduan aken tua venca."
    # The other yellow highlights are just grammatical markers (-an, -en, -in) and should be ignored
    
    block = {
        'paiwan_text': 'tjaljaduduan aken tua venca.',
        'translation': 'I am most mad about lying.',
        'glosses': ['tjalja-dudu-an: the most anger. tjalja- \'superlative\'; the root is dudu \'anger, mad, piss off\'; -an \'NMZ\'.', 'aken: I, 1st person SIN NOM', 'tua: by or about', 'v(e)<en>ca: to lie, AV. The root is veca \'dishonest, lie\'.'],
        'audio_url': 'https://www.youtube.com/embed/72bmI-BqdmA'
    }
    
    blocks.append(block)
    return blocks

def handle_652653654_special_case(soup):
    """Handle the specific structure of the 652653654 post with 3 separate examples."""
    blocks = []
    
    # The three examples with their known content:
    block1 = {
        'paiwan_text': 'pai, mayanan maya penurpur a su kaka.',
        'translation': 'Do not yet disturb your brother.',
        'glosses': None,
        'audio_url': None
    }
    
    block2 = {
        'paiwan_text': 'pai, maya manu seman-neka-aravac tua zuma.',
        'translation': 'Do not act like so disrespectful to other people.',
        'glosses': None,
        'audio_url': None
    }
    
    block3 = {
        'paiwan_text': 'pai, kiumalju. semiaq sa su sikudan.',
        'translation': 'Come, change to a new leaf. What you did is shameful.',
        'glosses': None,
        'audio_url': None
    }
    
    # Find post body and extract components
    post_body = soup.find(class_='post-body')
    if post_body:
        # Extract glosses for each block
        # For many posts, block 1 has a simple gloss (not in <ol>) and block 2+ have numbered glosses
        all_lists = post_body.find_all('ol')
        
        # Check if this is a multi-day post (like 664/665) where block 1 has simple gloss
        text_content = post_body.get_text()
        
        if len(all_lists) == 1 and ('For ' in text_content and ':' in text_content):
            # Single numbered list, but block 1 might have simple gloss
            # Block 1: Look for pattern "word: definition" before the numbered list
            pre_list_text = ""
            ol_element = all_lists[0]
            for element in post_body.contents:
                if element == ol_element:
                    break
                if hasattr(element, 'get_text'):
                    pre_list_text += element.get_text()
                elif isinstance(element, str):
                    pre_list_text += element
            
            # Extract simple gloss from pre-list text 
            import re
            # Look for pattern like "pai: thus, hence, thereupon..."
            simple_gloss_match = re.search(r'([a-zA-Z]+):\s*([^.]+\.?)', pre_list_text)
            if simple_gloss_match:
                word = simple_gloss_match.group(1)
                definition = simple_gloss_match.group(2).strip()
                block1['glosses'] = [f"{word}: {definition}"]
            
            # Block 2 gets the numbered list
            items = all_lists[0].find_all('li')
            if items:
                block2['glosses'] = [preprocess_gloss(li.get_text(strip=True)) for li in items]
        else:
            # Traditional assignment for posts with multiple numbered lists
            # Block 1 glosses (first ol)
            if len(all_lists) >= 1:
                items = all_lists[0].find_all('li')
                if items:
                    block1['glosses'] = [preprocess_gloss(li.get_text(strip=True)) for li in items]
            
            # Block 2 glosses (second ol)
            if len(all_lists) >= 2:
                items = all_lists[1].find_all('li')
                if items:
                    block2['glosses'] = [preprocess_gloss(li.get_text(strip=True)) for li in items]
                    
            # Block 3 glosses (third ol)
            if len(all_lists) >= 3:
                items = all_lists[2].find_all('li')
                if items:
                    block3['glosses'] = [preprocess_gloss(li.get_text(strip=True)) for li in items]
        
        # Extract audio URLs
        iframes = post_body.find_all('iframe')
        audio_urls = []
        for iframe in iframes:
            src = iframe.get('src', '')
            if 'youtube.com/embed/' in src:
                audio_urls.append(src)
        
        # Assign audio URLs to blocks
        if len(audio_urls) >= 1:
            block1['audio_url'] = audio_urls[0]
        if len(audio_urls) >= 2:
            block2['audio_url'] = audio_urls[1]
        if len(audio_urls) >= 3:
            block3['audio_url'] = audio_urls[2]
    
    blocks.append(block1)
    blocks.append(block2)
    blocks.append(block3)
    return blocks

def find_example_blocks(soup, url=None):
    """Find example blocks in the HTML."""
    blocks = []
    
    # Special case handler for specific problematic posts
    if url and "paiwan-every-day-664665-pai" in url:
        return handle_664665_special_case(soup)
       
    # Special case for the 652653654 post with 3 pai examples
    if url and "paiwan-every-day-652653654-pai" in url:
        return handle_652653654_special_case(soup)
    
    # Find all yellow highlighted text (Paiwan text) - support both yellow formats
    yellow_elements = []
    for tag in ['span', 'b', 'i']:
        # Find elements with either #fcff01 or yellow background
        elements = soup.find_all(tag, style=lambda x: x and 
            ('background-color: #fcff01' in x or 'background-color: yellow' in x))
        yellow_elements.extend(elements)
    
    # Sort elements by their position in the document
    def get_position(element):
        """Get rough position of element in document for sorting."""
        position = 0
        for prev in element.find_all_previous():
            position += 1
        return position
    
    yellow_elements.sort(key=get_position)
    
    # Filter out ignored yellow elements for specific posts
    if url:
        for url_identifier, ignore_list in YELLOW_TEXT_IGNORE_LIST:
            if url_identifier in url:
                # Remove yellow elements whose text exactly matches ignore list
                yellow_elements = [elem for elem in yellow_elements 
                                 if elem.get_text(strip=True) not in ignore_list]
                break
    
    # Group consecutive yellow elements into single examples
    grouped_texts = []
    i = 0
    while i < len(yellow_elements):
        # Extract text, preserve non-breaking spaces as '&nbsp;', then strip
        current_text = yellow_elements[i].get_text().replace('\u00a0', ' ').strip()
        if not current_text:
            i += 1
            continue
        
        # Start a new group with the current element
        group_texts = [current_text]
        group_elements = [yellow_elements[i]]
        
        # Look ahead for consecutive yellow elements
        j = i + 1
        while j < len(yellow_elements):
            next_element = yellow_elements[j]
            next_text = next_element.get_text().replace('\u00a0', ' ').strip()
            
            if not next_text:
                j += 1
                continue
                
            # Check if we should group liberally based on element characteristics
            # If we have very short elements mixed with regular text, group everything
            very_short_elements = sum(1 for elem in yellow_elements if len(elem.get_text().replace('\u00a0', ' ').strip()) <= 2)
            total_elements = len(yellow_elements)
            
            # If more than 20% of elements are very short (apostrophes, single chars), 
            # be very liberal about grouping
            if very_short_elements / total_elements > 0.2:
                # Group all remaining elements together
                while j < len(yellow_elements):
                    next_element = yellow_elements[j]
                    next_text = next_element.get_text().replace('\u00a0', ' ').strip()
                    if next_text:  # Skip empty elements
                        group_texts.append(next_text)
                        group_elements.append(next_element)
                    j += 1
                break
                
            # Use text-based approach to check if elements should be grouped
            # Get the full post HTML and find positions of the actual yellow elements
            post_body = yellow_elements[i].find_parent('div', class_='post-body')
            if post_body:
                post_html = str(post_body)
                
                # Find the HTML representations of the LAST element in current group and the next element
                current_element = group_elements[-1]  # Use last element from current group
                current_element_html = str(current_element)
                next_element_html = str(next_element)
                
                # Find positions in the HTML - use finditer to handle duplicates
                current_element_html = str(current_element)
                next_element_html = str(next_element)
                
                # Find all occurrences of both elements
                current_matches = list(re.finditer(re.escape(current_element_html), post_html))
                next_matches = list(re.finditer(re.escape(next_element_html), post_html))
                
                current_pos = -1
                next_pos = -1
                
                # For current element, use the last match (since we want the one we just processed)
                if current_matches:
                    current_pos = current_matches[-1].start()
                
                # For next element, find the first match that comes after current_pos
                for match in next_matches:
                    if match.start() > current_pos:
                        next_pos = match.start()
                        break
                
                if current_pos == -1 or next_pos == -1 or next_pos <= current_pos:
                    # Can't find positions or they're in wrong order, don't group
                    break
                
                # Get HTML between them
                between_html = post_html[current_pos + len(current_element_html):next_pos]
                
                # Remove HTML tags to get actual text content
                between_text = re.sub(r'<[^>]+>', '', between_html)
                between_text = between_text.replace('&nbsp;', ' ').strip()
                
                # Special handling for very short elements (like apostrophes, single words)
                current_text = group_elements[0].get_text().replace('\u00a0', ' ').strip()
                is_very_short_current = len(current_text) <= 2
                is_very_short_next = len(next_text) <= 2
                
                # If current or next element is very short (apostrophe, single character), be more lenient
                if is_very_short_current or is_very_short_next:
                    threshold = 200  # Much higher threshold for short elements
                else:
                    threshold = 10   # Normal threshold for regular elements
                
                # If there's substantial text between them, don't group
                if len(between_text) > threshold:
                    break
            else:
                # Can't find post body, don't group
                break
                
            # Group them
            group_texts.append(next_text)
            group_elements.append(next_element)
            current_text = ' '.join(group_texts)  # Update for next iteration
            j += 1
        
        # If every line starts with a speaker label (e.g. "A:sentence..."), strip those labels.
        # This handles dialog examples where each yellow span is prefixed with a speaker name and colon.
        is_dialog = False
        if len(group_texts) > 1 and all(re.match(r'^[A-Za-z]+:', t) for t in group_texts):
            group_texts = [re.sub(r'^[A-Za-z]+:', '', t).strip() for t in group_texts]
            is_dialog = True

        # Combine all texts in this group
        combined_text = ' '.join(group_texts)
        
        # Clean up translation markers that might have been included in yellow text
        translation_markers = ['Free translation:', 'English translation:', 'In English:', 'Translation:', "Ferrell's translation:", "Ferrell's translation (p. 70)", "Ferrell translation:", "Ferrell's translation (p. 59):", "Free translaion:", "In Engllish:"]
        cleaned_text = combined_text
        found_marker_in_text = None
        for marker in translation_markers:
            if marker in cleaned_text:
                # Check if marker is at the end
                if cleaned_text.endswith(marker):
                    cleaned_text = cleaned_text[:-len(marker)].strip()
                    found_marker_in_text = marker
                    break
                # Also check for marker at the end with no period
                marker_no_colon = marker.rstrip(':')
                if cleaned_text.endswith(marker_no_colon):
                    cleaned_text = cleaned_text[:-len(marker_no_colon)].strip()
                    found_marker_in_text = marker
                    break
        
        grouped_texts.append((cleaned_text, group_elements[0], group_elements[-1], found_marker_in_text, is_dialog))  # Store first, last elements, found marker, and dialog flag
        i = j  # Move to the next ungrouped element
    
    # Now process each grouped text as a block using contiguous approach
    # For each Paiwan text block, find its translation/glosses/audio in the content
    # that appears after it but before the next Paiwan text block
    
    # Get the full post body text and HTML for text-based content extraction
    post_body = soup.find(class_='post-body')
    if not post_body:
        return blocks
    
    full_text = post_body.get_text()
    post_html = str(post_body)
    
    for i, grouped_item in enumerate(grouped_texts):
        # Handle both old and new tuple formats for backward compatibility
        if len(grouped_item) == 5:
            paiwan_text, first_element, last_element, found_marker_in_text, is_dialog = grouped_item
        elif len(grouped_item) == 4:
            paiwan_text, first_element, last_element, found_marker_in_text = grouped_item
            is_dialog = False
        else:
            paiwan_text, first_element, last_element = grouped_item
            found_marker_in_text = None
            is_dialog = False
            
        block = {
            'paiwan_text': paiwan_text,
            'translation': None,
            'glosses': None,
            'audio_url': None
        }
        
        # Use text-based approach to extract content for this block
        # Find the position of the LAST element in this Paiwan text group
        # This ensures we get content after the complete example
        last_element_text = last_element.get_text().replace('\u00a0', ' ').strip()
        current_pos = full_text.find(last_element_text)
        
        # If we found a translation marker in the Paiwan text, we need to look for the translation 
        # immediately after where the marker was in the original text
        if found_marker_in_text:
            # Find the position of the marker in the full text
            marker_pos = full_text.find(found_marker_in_text, current_pos)
            if marker_pos != -1:
                # Start looking for translation content after the marker
                current_pos = marker_pos + len(found_marker_in_text)
        
        # Determine the end position (next Paiwan text or end of post)
        if i + 1 < len(grouped_texts):
            if len(grouped_texts[i + 1]) == 4:
                next_first_element = grouped_texts[i + 1][1].get_text(strip=True)
            else:
                next_first_element = grouped_texts[i + 1][1].get_text(strip=True)
            next_pos = full_text.find(next_first_element, current_pos)
            if next_pos == -1:
                end_pos = len(full_text)
            else:
                end_pos = next_pos
        else:
            end_pos = len(full_text)
        
        # Extract the text content for this block
        if current_pos != -1:
            block_content_text = full_text[current_pos + len(last_element_text):end_pos]
        else:
            block_content_text = ''
        
        # Extract translation from this block's text content
        translation_patterns = ['Free translation:', 'English translation:', 'In English:', 'Translation:', "Ferrell's translation:", "Ferrell's translation (p. 70)", "Ferrell translation:", "Ferrell's translation (p. 59):", "Free translaion:", "In Engllish:"]
        stop_patterns = ['Word gloss:', 'Glossary:', 'Morphological breakdown:', 'Voice file:', 'Audio:', 'Listen:', "Reading:"]
        
        # If we found a translation marker in the Paiwan text, we know the translation comes immediately after
        if found_marker_in_text:
            # Look for translation right after the marker position
            translation_start = current_pos
            translation_end = len(block_content_text)
            
            # Find the end of the translation (stop at glossary or other markers)
            for stop_pattern in stop_patterns:
                stop_pos = block_content_text.find(stop_pattern, translation_start - current_pos)
                if stop_pos != -1:
                    translation_end = current_pos + stop_pos
                    break
            
            # Extract the translation text
            if translation_start < translation_end:
                translation_text = full_text[translation_start:translation_end].strip()
                if translation_text and len(translation_text) > 5:
                    # Clean up translation text - take first sentence/line
                    cleaned_translation = translation_text.split('\n')[0].strip()
                    cleaned_translation = cleaned_translation.split('.')[0] + '.' if '.' in cleaned_translation else cleaned_translation
                    # Remove common artifacts
                    for stop_pattern in stop_patterns:
                        cleaned_translation = cleaned_translation.replace(stop_pattern, '').strip()
                    if cleaned_translation:
                        block['translation'] = cleaned_translation
        
        # If no translation found yet, use the original pattern matching approach
        if not block['translation']:
            for pattern in translation_patterns:
                if pattern in block_content_text:
                    start_pos = block_content_text.find(pattern) + len(pattern)
                    end_pos_trans = len(block_content_text)
                    for stop_pattern in stop_patterns:
                        stop_pos = block_content_text.find(stop_pattern, start_pos)
                        if stop_pos != -1 and stop_pos < end_pos_trans:
                            end_pos_trans = stop_pos
                    
                    translation_text = block_content_text[start_pos:end_pos_trans].strip()
                    if translation_text and len(translation_text) > 5:
                        # Clean up translation text
                        cleaned_translation = translation_text.split('\n')[0].strip()
                        # Remove common artifacts
                        cleaned_translation = cleaned_translation.replace('Word gloss:', '').strip()
                        if cleaned_translation:
                            block['translation'] = cleaned_translation
                            break
            
            # If still no translation, search the entire post content
            if not block['translation']:
                # Check the full post content for translation patterns with improved extraction
                for pattern in translation_patterns + ['In English:', 'English:', 'Translation:']:
                    if pattern in full_text:
                        # Extract from full post
                        start_pos = full_text.find(pattern) + len(pattern)
                        
                        # Try multiple approaches to extract the translation
                        # 1. First line after the pattern
                        lines = full_text[start_pos:start_pos+300].split('\n')
                        translation_candidate = lines[0].strip() if lines else ""
                        
                        # 2. If first line is empty, try next non-empty line
                        if not translation_candidate:
                            for line in lines[1:4]:  # Check next 3 lines
                                line = line.strip()
                                if line and len(line) > 5:
                                    translation_candidate = line
                                    break
                        
                        # 3. If still empty, try to get content after pattern ignoring line breaks
                        if not translation_candidate:
                            content_after = full_text[start_pos:start_pos+200].strip()
                            # Split by common separators and take first meaningful chunk
                            for sep in ['\n\n', 'Word gloss', 'Reading:', 'Glossary:']:
                                if sep in content_after:
                                    translation_candidate = content_after.split(sep)[0].strip()
                                    if translation_candidate:
                                        break
                        
                        if translation_candidate and len(translation_candidate) > 5:
                            # Clean up the translation
                            translation_candidate = translation_candidate.replace('\n', ' ').strip()
                            # Remove common artifacts
                            translation_candidate = translation_candidate.replace('Word gloss:', '').strip()
                            if translation_candidate:
                                block['translation'] = translation_candidate
                                break


        if block['translation']:
            #if we found a translation, make sure it doesn't have extra words
            stop_patterns = ['Word gloss:', 'World gloss', 'Glossary:', 'Morphological breakdown:', 'Reading:', 'Voice file:', 'Audio:', 'Listen:', 'From klokah.org']
            for stop_pattern in stop_patterns:
                if stop_pattern in block['translation']:
                    block['translation'] = block['translation'].split(stop_pattern)[0].strip()
            # Strip speaker labels from dialog translations (e.g. "A: sentence. B: sentence." -> "sentence. sentence.")
            if is_dialog:
                block['translation'] = re.sub(r'(?:^|(?<=[.!?])\s*)[A-Za-z]+:\s*', ' ', block['translation']).strip()

        # Extract glosses from the HTML content for this block
        gloss_patterns = ['Word gloss', 'Glossary', 'World gloss:', 'Glossary:', 'gloss']
        
        # Use block-specific approach to find glosses
        if not block['glosses']:
            if not block['glosses']:
                # Search using the element's HTML string (robust against nested tags)
                last_element_html = str(last_element)
                current_html_pos = post_html.find(last_element_html)
                # Fallback to plain text if HTML search fails
                if current_html_pos == -1:
                    last_element_text = last_element.get_text(strip=True)
                    current_html_pos = post_html.find(last_element_text)
                    last_element_html = last_element_text
                block_html = None  # Initialize to prevent NameError
                
                if current_html_pos != -1:
                    if i + 1 < len(grouped_texts):
                        next_first_elem = grouped_texts[i + 1][1]
                        next_first_html = str(next_first_elem)
                        next_html_pos = post_html.find(next_first_html, current_html_pos + len(last_element_html))
                        if next_html_pos == -1:
                            next_first_text = next_first_elem.get_text(strip=True)
                            next_html_pos = post_html.find(next_first_text, current_html_pos + len(last_element_html))
                        if next_html_pos == -1:
                            block_html = post_html[current_html_pos:]
                        else:
                            block_html = post_html[current_html_pos:next_html_pos]
                    else:
                        block_html = post_html[current_html_pos:]
                
                # Parse the HTML section for this block only if we found the content
                if block_html:
                    block_soup = BeautifulSoup(block_html, 'html.parser')
                    
                    # First try: Look for HTML ordered/unordered lists
                    lists = block_soup.find_all(['ol', 'ul'])
                    
                    for list_elem in lists:
                        items = list_elem.find_all('li')
                        if items and len(items) >= 2:
                            sample_text = ' '.join([item.get_text()[:100] for item in items[:3]])
                            # Check for gloss indicators
                            if any(indicator in sample_text.lower() for indicator in 
                                   [':', 'actor focus', 'person', 'root is', 'gen', 'nom', 'obl', 'lig', 'will', 'disappear', 'custom', 'first', 'language']):
                                glosses = []
                                for li in items:
                                    gloss_text = li.get_text(strip=True)
                                    if ':' in gloss_text and len(gloss_text) > 3:
                                        glosses.append(preprocess_gloss(gloss_text))
                                
                                if glosses:
                                    block['glosses'] = glosses
                                    break
            
            # Second try: Look for explicit numbered patterns in text if HTML lists didn't work
            if not block['glosses']:
                for pattern in gloss_patterns:
                    if pattern in block_content_text:
                        
                        # Find the start of glosses after the pattern
                        pattern_pos = block_content_text.find(pattern)
                        if pattern_pos != -1:
                            gloss_start = pattern_pos + len(pattern)
                            gloss_text = block_content_text[gloss_start:].strip()
                            
                            # Remove the colon if it's at the start
                            if gloss_text.startswith(':'):
                                gloss_text = gloss_text[1:].strip()
                            
                            # Split glosses by common separators and clean them up
                            if gloss_text and len(gloss_text) > 10:  # Only if substantial content
                                # Check for numbered glossary format first (explicit numbers)
                                # Pattern: "1. word: definition 2. word: definition" etc.
                                numbered_pattern = r'\d+\.\s*([^:]+:[^0-9]+?)(?=\d+\.|$)'
                                numbered_matches = re.findall(numbered_pattern, gloss_text, re.DOTALL)
                                
                                if numbered_matches and len(numbered_matches) >= 2:
                                    # Found explicit numbered glossary format
                                    cleaned_glosses = []
                                    for match in numbered_matches:
                                        entry = match.strip()
                                        # Clean up whitespace and line breaks
                                        entry = re.sub(r'\s+', ' ', entry)
                                        if ':' in entry and len(entry) > 5:
                                            cleaned_glosses.append(preprocess_gloss(entry))
                                    
                                    if cleaned_glosses:
                                        block['glosses'] = cleaned_glosses
                                        break
                                
                                # Third try: Split by newlines and look for colon-separated entries
                                if not block['glosses']:
                                    lines = [line.strip() for line in gloss_text.split('\n') if line.strip()]
                                    gloss_lines = []
                                    
                                    for line in lines:
                                        # Stop at common section markers
                                        if any(stop in line for stop in ['Reading:', 'Voice file:', 'Audio:', 'Listen:']):
                                            break
                                        # Include lines that look like glosses
                                        if ':' in line and len(line) > 5 and not line.startswith('http'):
                                            gloss_lines.append(preprocess_gloss(line))
                                    
                                    if gloss_lines and len(gloss_lines) >= 2:
                                        block['glosses'] = gloss_lines
                                        break
                                
                                # Fourth try: Original pattern-based approach as final fallback
                                if not block['glosses']:
                                    # First try to split by sentence endings followed by a word and colon
                                    # This should catch patterns like "...definition. nextword: next definition"
                                    entries = re.split(r'\.(?=\s*[a-zA-Z][^:]*:)', gloss_text)
                                    
                                    if len(entries) < 2:
                                        # If that didn't work, try splitting by parenthetical endings followed by word and colon
                                        # This catches patterns like "...(LOC)nextword: definition"
                                        entries = re.split(r'\)(?=\s*[a-zA-Z][^:]*:)', gloss_text)
                                    
                                    if len(entries) < 2:
                                        # Fallback: just take the first reasonable chunk as a single gloss
                                        # Limit to first sentence or reasonable length
                                        first_part = gloss_text.split('.')[0] if '.' in gloss_text else gloss_text[:150]
                                        if ':' in first_part and len(first_part) > 10:
                                            entries = [first_part]
                                        else:
                                            entries = []
                                    
                                    cleaned_glosses = []
                                    for entry in entries:
                                        entry = entry.strip()
                                        # Add back period if it was removed by split
                                        if entry and not entry.endswith('.') and not entry.endswith(')') and len(entry) > 20:
                                            entry += '.'
                                        # Only include entries that look like glosses (contain colon and reasonable length)
                                        if ':' in entry and len(entry) > 5 and len(entry) < 300:
                                            cleaned_glosses.append(entry)
                                    
                                    if cleaned_glosses:
                                        block['glosses'] = cleaned_glosses
                                        break
        
        if block['glosses']:
            # If we found glosses, make sure the last one doesn't have extra words
            stop_patterns = ['Word gloss:', 'Read:', 'Glossary:', 'Morphological breakdown:', 'Reading:', 'Voice file:', 'Audio:', 'Listen:', 'From klokah.org']
            last_gloss = block['glosses'][-1]
            for stop_pattern in stop_patterns:
                if stop_pattern in last_gloss:
                    last_gloss = last_gloss.split(stop_pattern)[0].strip()
            if last_gloss:
                block['glosses'][-1] = last_gloss            

        # Extract audio from the HTML content for this block
        last_element_html = str(last_element)
        current_html_pos = post_html.find(last_element_html)
        if current_html_pos == -1:
            last_element_html = last_element.get_text(strip=True)
            current_html_pos = post_html.find(last_element_html)
        block_html = None  # Initialize to prevent NameError
        
        if current_html_pos != -1:
            if i + 1 < len(grouped_texts):
                next_first_elem = grouped_texts[i + 1][1]
                next_first_html = str(next_first_elem)
                next_html_pos = post_html.find(next_first_html, current_html_pos + len(last_element_html))
                if next_html_pos == -1:
                    next_html_pos = post_html.find(next_first_elem.get_text(strip=True), current_html_pos + len(last_element_html))
                if next_html_pos == -1:
                    block_html = post_html[current_html_pos:]
                else:
                    block_html = post_html[current_html_pos:next_html_pos]
            else:
                block_html = post_html[current_html_pos:]
        
        # Parse the HTML section for this block only if we found the content
        if block_html:
            block_soup = BeautifulSoup(block_html, 'html.parser')
            iframes = block_soup.find_all('iframe')
            
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'youtube.com/embed/' in src:
                    block['audio_url'] = src
                    break
        
        # If no audio found in block-specific HTML, try searching the entire post
        # This handles cases where audio is outside the yellow text block area
        if not block.get('audio_url'):
            post_soup = BeautifulSoup(post_html, 'html.parser')
            all_iframes = post_soup.find_all('iframe')
            
            for iframe in all_iframes:
                src = iframe.get('src', '')
                if 'youtube.com/embed/' in src:
                    block['audio_url'] = src
                    break
        
        blocks.append(block)
    
    return blocks

def analyze_blog_posts(max_posts=None, show_details=False, specific_urls=None, return_blocks=False):
    """Analyze Paiwan Every Day blog posts.
    
    Args:
        max_posts: Maximum number of posts to analyze (None for all)
        show_details: Whether to show detailed content for each block
        specific_urls: List of specific URLs to analyze (None for all)
        return_blocks: If True, return all processed blocks instead of analysis
    """
    
    # Load URL mapping
    with open('html_cache/url_mapping.json', 'r') as f:
        url_mapping = json.load(f)
    
    mismatches = []
    perfect_matches = []
    all_blocks = []  # For collecting blocks when return_blocks=True
    
    if not return_blocks:
        if max_posts:
            print(f"TESTING ON FIRST {max_posts} POSTS:")
        elif specific_urls:
            print(f"TESTING ON {len(specific_urls)} SPECIFIC POSTS:")
        else:
            print("TESTING ON ALL POSTS:")
        print("="*80)
    
    count = 0
    for url, filename in url_mapping.items():
        # Check if this is a Paiwan Every Day post
        # Note: post 412 has a typo in its URL slug ('paiwa-every-day' instead of 'paiwan-every-day')
        # Posts 445 and 556 have non-standard slugs ('paiwan.html') with no number in the URL
        NON_STANDARD_POST_URLS = {
            'https://yeddapalemeq.blogspot.com/2021/05/paiwan.html',  # Post 445
            'https://yeddapalemeq.blogspot.com/2021/09/paiwan.html',  # Post 556
            'https://yeddapalemeq.blogspot.com/2021/10/paiwan-every-da-587.html',  # Post 587 with non-standard slug
            'https://yeddapalemeq.blogspot.com/2021/11/paiwan-618619-kasiv.html',  # Posts 618/619; slug missing 'every-day'
        }
        url_lower = url.lower()
        if ('paiwan-every-day' not in url_lower and 'paiwa-every-day' not in url_lower
                and url not in NON_STANDARD_POST_URLS):
            continue
        
        # If specific URLs provided, only process those
        if specific_urls and url not in specific_urls:
            continue

        if url and "paiwan-every-day-543-aw-ay" in url:
            #skip this one since it is complex to handle.
            continue

        if url and "paiwan-every-day-545-aw-ay" in url:
            #skip this one since it is complex to handle.
            continue

        if url and "paiwan-every-day-66-gang" in url:
            #skip this one since it is complex to handle.
            continue

        if url and "paiwan-every-day-197-zemululj" in url:
            #skip this one since it is complex to handle.
            continue

        # If max_posts specified, stop after reaching limit
        count += 1
        if max_posts and count > max_posts:
            break
        
        filepath = f'html_cache/{filename}'
        if not os.path.exists(filepath):
            continue
            
        if not return_blocks:
            if max_posts:
                print(f"\n{count}. Analyzing: {url}")
            else:
                print(f"\nAnalyzing: {url}")
        elif return_blocks:
            print(f"Processing: {url}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except Exception as e:
            if not return_blocks:
                print(f"  ❌ Error reading file: {e}")
            else:
                print(f"  Error reading file: {e}")
            continue
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except Exception as e:
            if not return_blocks:
                print(f"  ❌ Error parsing HTML: {e}")
            else:
                print(f"  Error parsing HTML: {e}")
            continue
        
        # Get the title
        title_elem = soup.find('h3', class_='post-title')
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        
        # Extract expected number of examples
        expected_numbers = extract_example_numbers_from_title(title)
        expected_count = len(expected_numbers)
        
        # Find actual blocks
        try:
            blocks = find_example_blocks(soup, url)
        except Exception as e:
            if not return_blocks:
                print(f"  ❌ Error finding blocks: {e}")
            else:
                print(f"  Error finding blocks: {e}")
            continue
        
        # Post-processing for specific posts that need block merging
        if url and "paiwan-every-day-538-au-qau" in url and len(blocks) == 2:
            # Merge the two blocks for post 538
            merged_block = {
                'paiwan_text': blocks[0]['paiwan_text'] + ' ' + blocks[1]['paiwan_text'],
                'translation': '',
                'glosses': blocks[1]['glosses'],  # Use glosses from second block
                'audio_url': blocks[1]['audio_url']  # Use audio from second block
            }
            
            # Concatenate translations if they exist
            translations = []
            if blocks[0]['translation']:
                translations.append(blocks[0]['translation'])
            if blocks[1]['translation']:
                translations.append(blocks[1]['translation'])
            merged_block['translation'] = ' '.join(translations) if translations else None
            
            blocks = [merged_block]
        
        # Post-processing for post 551552553 that has 3 blocks sharing one audio
        if url and "paiwan-every-day-551552553-ciupan" in url and len(blocks) == 3:
            # Concatenate all three blocks into one
            merged_block = {
                'paiwan_text': '',
                'translation': '',
                'glosses': [],
                'audio_url': None
            }
            
            # Concatenate Paiwan texts
            paiwan_texts = []
            for block in blocks:
                if block['paiwan_text']:
                    paiwan_texts.append(block['paiwan_text'])
            merged_block['paiwan_text'] = ' '.join(paiwan_texts)
            
            # Concatenate translations
            translations = []
            for block in blocks:
                if block['translation']:
                    translations.append(block['translation'])
            merged_block['translation'] = ' '.join(translations) if translations else None
            
            # Concatenate glosses
            all_glosses = []
            for block in blocks:
                if block['glosses']:
                    all_glosses.extend(block['glosses'])
            merged_block['glosses'] = all_glosses if all_glosses else None
            
            # Use the audio from any block that has it
            for block in blocks:
                if block['audio_url']:
                    merged_block['audio_url'] = block['audio_url']
                    break
            
            blocks = [merged_block]
        
        # If we're just collecting blocks, add them and continue
        if return_blocks:
            for i, block in enumerate(blocks):
                block['url'] = url
                block['title'] = title
                block['sentence_id'] = generate_sentence_id(url, i + 1)
                all_blocks.append(block)
            continue
        
        actual_count = len(blocks)
        
        print(f"Title: {title}")
        print(f"Expected: {expected_count}, Found: {actual_count}")
        
        # Show detailed content if requested
        if show_details:
            for i, block in enumerate(blocks, 1):
                print(f"\n  === Block {i} ===")
                print(f"  Paiwan Text: {block['paiwan_text']}")
                
                if block['translation']:
                    print(f"  Translation: {block['translation'][:200]}{'...' if len(block['translation']) > 200 else ''}")
                else:
                    print(f"  Translation: ❌ NOT FOUND")
                
                if block['glosses']:
                    print(f"  Glosses ({len(block['glosses'])} items):")
                    for j, gloss in enumerate(block['glosses'][:3]):  # Show first 3
                        print(f"    {j+1}. {gloss[:100]}{'...' if len(gloss) > 100 else ''}")
                    if len(block['glosses']) > 3:
                        print(f"    ... and {len(block['glosses']) - 3} more")
                else:
                    print(f"  Glosses: ❌ NOT FOUND")
                
                if block['audio_url']:
                    print(f"  Audio: ✓ {block['audio_url']}")
                else:
                    print(f"  Audio: ❌ NOT FOUND")
        
        if actual_count == expected_count:
            # Check if all components are found
            all_complete = True
            missing_components = []
            for i, block in enumerate(blocks):
                block_issues = []
                
                # Special case for 664/665: Block 1 doesn't need translation or Paiwan text
                is_special_case_block1 = (url and "paiwan-every-day-664665-pai" in url and i == 0)
                
                if not block['translation'] and not is_special_case_block1:
                    block_issues.append('translation')
                if not block['glosses']:
                    block_issues.append('glosses')
                if not block['audio_url']:
                    block_issues.append('audio')
                if block_issues:
                    all_complete = False
                    missing_components.append(f"Block {i+1}: {', '.join(block_issues)}")
            
            if all_complete:
                perfect_matches.append(url)
                print(f"Status: ✓ Perfect match")
            else:
                mismatches.append({
                    'url': url,
                    'title': title,
                    'expected': expected_count,
                    'actual': actual_count,
                    'issue': 'missing_components',
                    'details': missing_components,
                    'blocks': blocks
                })
                print(f"Status: ✗ Missing components: {'; '.join(missing_components)}")
                # Show details for problematic posts
                for i, block in enumerate(blocks[:2]):  # Show first 2 blocks
                    print(f"  Block {i+1}: {block['paiwan_text'][:60]}{'...' if len(block['paiwan_text']) > 60 else ''}")
        else:
            mismatches.append({
                'url': url,
                'title': title,
                'expected': expected_count,
                'actual': actual_count,
                'issue': 'count_mismatch',
                'details': [],
                'blocks': blocks
            })
            print(f"Status: ✗ Count mismatch")
            # Show details for problematic posts
            for i, block in enumerate(blocks[:2]):  # Show first 2 blocks
                print(f"  Block {i+1}: {block['paiwan_text'][:60]}{'...' if len(block['paiwan_text']) > 60 else ''}")
    
    # If return_blocks mode, just return the collected blocks
    if return_blocks:
        return all_blocks
    
    print("\n" + "="*80)
    print("TEST RESULTS:")
    print("="*80)
    print(f"Total test posts: {len(perfect_matches) + len(mismatches)}")
    print(f"Perfect matches: {len(perfect_matches)}")
    print(f"Problematic posts: {len(mismatches)}")
    
    # Write detailed problematic posts to log file
    if mismatches:
        log_filename = 'problematic_posts.log'
        with open(log_filename, 'w', encoding='utf-8') as log_file:
            log_file.write("PROBLEMATIC BLOG POSTS ANALYSIS\n")
            log_file.write("="*80 + "\n\n")
            
            for mismatch in mismatches:
                log_file.write(f"URL: {mismatch['url']}\n")
                log_file.write(f"Title: {mismatch['title']}\n")
                log_file.write(f"Expected: {mismatch['expected']}, Found: {mismatch['actual']}\n")
                log_file.write(f"Issue: {mismatch['issue']}\n")
                
                if mismatch['details']:
                    log_file.write(f"Details: {'; '.join(mismatch['details'])}\n")
                
                # Show found blocks
                if mismatch['blocks']:
                    log_file.write("Found blocks:\n")
                    for i, block in enumerate(mismatch['blocks']):
                        log_file.write(f"  Block {i+1}:\n")
                        log_file.write(f"    Text: {block['paiwan_text']}\n")
                        log_file.write(f"    Translation: {'✓' if block['translation'] else '✗'}\n")
                        log_file.write(f"    Glosses: {'✓' if block['glosses'] else '✗'}\n")
                        log_file.write(f"    Audio: {'✓' if block['audio_url'] else '✗'}\n")
                
                log_file.write("\n" + "-"*60 + "\n\n")
        
        print(f"\nDetailed problematic posts written to: {log_filename}")
    
    return mismatches, perfect_matches

def get_post_number_from_url(url):
    """Extract post number from URL for use in sentence ID."""
    # Correct known URL typos where the blogger used the wrong number in the slug
    URL_NUMBER_CORRECTIONS = {
        'paiwan-every-day-93-nguaq-sarunguaq': '293',   # Dec 2020 post; "93" is a typo for "293"
        'paiwan-every-day-320-leva-maleva': '321',       # Jan 2021 post; "320" is a typo for "321"
        '2021/05/paiwan.html': '445',                    # Post 445; slug has no post number
        '2021/09/paiwan.html': '556',                    # Post 556; slug has no post number
        '2021/10/paiwan-every-da-587.html': '587',       # Post 587; slug missing 'y' in 'day'
        '2021/11/paiwan-618619-kasiv.html': '618619',    # Posts 618/619; slug missing 'every-day'
    }
    for slug, corrected_number in URL_NUMBER_CORRECTIONS.items():
        if slug in url:
            return corrected_number
    # Also match the typo slug 'paiwa-every-day' (missing 'n') used in post 412
    match = re.search(r'paiwa?n?-every-da?y?-(\d+)', url)
    if match:
        return match.group(1)
    return "unknown"

def generate_sentence_id(url, block_index):
    """Generate a unique sentence ID based on URL and block index."""
    post_number = get_post_number_from_url(url)
    return f"S{post_number}_{block_index}"

def normalize_for_matching(text):
    """Normalize text for gloss matching by removing dashes, punctuation and converting to lowercase."""
    import string
    # Remove common punctuation including angle brackets, curly quotes, and apostrophes for matching.
    # Apostrophes represent glottal stops in Paiwan but are often omitted in morphological glosses
    # (e.g. na'ivu'ivu is glossed as na-ivu-ivu), so we strip them for matching purposes.
    text = text.translate(str.maketrans('', '', ',.!?;:()<>\u201c\u201d\u2018\u2019\''))
    # Remove dashes and convert to lowercase
    return text.replace('-', '').lower().strip()

def extract_word_from_gloss(gloss):
    """Extract the Paiwan word from a gloss entry (before the colon)."""
    if ':' in gloss:
        word_part = gloss.split(':')[0].strip()
        # Note: Keep morphological markers like <em> for linguistic accuracy
        # They will be escaped in XML output
        return word_part
    return gloss.strip()

def extract_word_from_gloss_with_parentheses_handling(gloss):
    """Extract word from gloss, handling parentheses and alternative forms by trying different variations."""
    base_word = extract_word_from_gloss(gloss)
    
    # Handle alternative form patterns like "kuor'u:" and "'uorku:"
    if base_word.startswith("kuor‘u") or base_word.startswith("‘uorku") or base_word.startswith("’uorku"):
        # These indicate the word could be either "ku" or "'u"
        return ["ku", "‘u" ,"’u", "'u"]  # Include variations with different apostrophe styles and without apostrophes   

    # Handle 'aorka
    if base_word.startswith("'aorka") or base_word.startswith("‘aorka") or base_word.startswith("’aorka"):
        return ["'a", "ka", "‘a", "’a"]  # Include both with and without apostrophe

    # Handle virasiorvurati
    if base_word.startswith("virasiorvurati"):
        return ["virasi", "vurati"]  # Include the original form

    # Handle ‘atuaorkatua
    if base_word.startswith("‘atuaorkatua") or base_word.startswith("’atuaorkatua") or base_word.startswith("'atuaorkatua"):
        return ["'atua", "katua", "‘atua", "’atua"]  # Include both with and without apostrophe

    # Handle taortua
    if base_word.startswith("taortua"):
        return ["ta", "tua"]  # Include the original form

    # If no parentheses, return original
    if '(' not in base_word and ')' not in base_word:
        return [base_word]
    
    # Create variations:
    # 1. Without parentheses and their content
    import re
    without_parentheses = re.sub(r'\([^)]*\)', '', base_word).strip()
    
    # 2. With parentheses content but without the parentheses themselves
    with_content_no_parens = re.sub(r'[()]', '', base_word).strip()
    
    # Return list of variations to try, prioritizing without parentheses
    variations = []
    if without_parentheses and without_parentheses != base_word:
        variations.append(without_parentheses)
    if with_content_no_parens and with_content_no_parens != base_word and with_content_no_parens != without_parentheses:
        variations.append(with_content_no_parens)
    
    # Always include the original as a fallback
    if base_word not in variations:
        variations.append(base_word)
    
    return variations

def escape_xml_content(text):
    """Escape special XML characters while preserving linguistic markers."""
    if not text:
        return text
    # Escape XML special characters
    text = text.replace('&', '&amp;')  # Must be first
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text

def split_sentence_words(sentence):
    """Split sentence into words, handling punctuation properly."""
    import re
    # Split on whitespace and remove empty strings
    words = sentence.split()
    cleaned_words = []
    
    for word in words:
        # Strip leading curly/straight double-quotes (used as quotation formatting, never phonemic)
        cleaned_word = re.sub(r'^[\u201c\u201d"]+', '', word)
        # Remove trailing punctuation and curly/straight double-quotes
        cleaned_word = re.sub(r'[.,:;!?()“”"]+$', '', cleaned_word)
        if cleaned_word:  # Only add non-empty words
            cleaned_words.append(cleaned_word)
    
    return cleaned_words

def match_words_to_glosses(sentence, glosses, sentence_id):
    """Match words in sentence to glosses using improved algorithm."""

    # Create error log file if it doesn't exist
    log_file = "gloss_matching_errors.log"
    
    # Split sentence into words (removing punctuation)
    words = split_sentence_words(sentence)
    word_elements = []
    
    current_gloss_index = 0
    used_glosses = set()  # Track which glosses have been used
    
    for word_index, word in enumerate(words):
        word_id = f"{sentence_id}W{word_index + 1}"
        
        # Normalize word for matching
        normalized_word = normalize_for_matching(word)
        
        matched_gloss = None

        glossed_word = word  # Default to original word; may update if we find a gloss match with a variation
        
        # Try to match with current unused gloss
        if current_gloss_index < len(glosses):
            current_gloss = glosses[current_gloss_index]
            gloss_word_variations = extract_word_from_gloss_with_parentheses_handling(current_gloss)
            
            # Try each variation to find a match
            for gloss_word in gloss_word_variations:
                normalized_gloss_word = normalize_for_matching(gloss_word)
                if normalized_word == normalized_gloss_word:
                    matched_gloss = current_gloss
                    glossed_word = gloss_word  # Use the specific variation that matched
                    used_glosses.add(current_gloss_index)
                    current_gloss_index += 1
                    break
        
        # If no match with current gloss, check all glosses for reuse (removing restriction)
        if matched_gloss is None:
            for prev_index in range(len(glosses)):
                # Allow reuse of already matched glosses for alternative forms
                prev_gloss = glosses[prev_index]
                gloss_word_variations = extract_word_from_gloss_with_parentheses_handling(prev_gloss)
                
                # Try each variation to find a match
                found_match = False
                for gloss_word in gloss_word_variations:
                    normalized_gloss_word = normalize_for_matching(gloss_word)
                    if normalized_word == normalized_gloss_word:
                        matched_gloss = prev_gloss
                        glossed_word = gloss_word  # Use the specific variation that matched
                        used_glosses.add(prev_index)
                        # Update current_gloss_index to continue from next gloss
                        if prev_index >= current_gloss_index:
                            current_gloss_index = prev_index + 1
                        found_match = True
                        break
                
                if found_match:
                    break
                
        # Create word element
        word_data = {
            'id': word_id,
            'word': glossed_word,  # Use original word with any punctuation
            'gloss': matched_gloss
        }
        word_elements.append(word_data)
        
        # If no match was found, advance current_gloss_index conservatively
        if matched_gloss is None:
            # Only advance if we're still looking at unused glosses
            while current_gloss_index < len(glosses) and current_gloss_index in used_glosses:
                current_gloss_index += 1
    
    # Check for unused glosses and log errors
    unused_glosses = []
    for i, gloss in enumerate(glosses):
        if i not in used_glosses:
            unused_glosses.append(f"Gloss {i + 1}: {gloss}")  # Use 1-based indexing for display
    
    if unused_glosses:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\nSentence {sentence_id}: {sentence}\n")
            f.write(f"Unused glosses ({len(unused_glosses)}): \n")
            for unused in unused_glosses:
                f.write(f"  - {unused}\n")
    
    return word_elements

def create_xml(blocks):
    """Create XML structure from blog post blocks with detailed word-level glosses."""
    
    # Initialize error log
    log_file = "gloss_matching_errors.log"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("Gloss Matching Error Log\n")
        f.write("========================\n")
    
    # Create root element
    root = ET.Element("TEXT")
    root.set("id", "Yedda_Ljeljeng_lja_Palemek's_Blog")
    root.set("xml:lang", "pwn")
    root.set("source", "https://yeddapalemeq.blogspot.com/")
    root.set("dialect", "Southern")
    root.set("citation", "Palemeq, Y. (2021). Yedda Palemeq. Retrieved May 19, 2026, from https://yeddapalemeq.blogspot.com/")
    root.set("BibTeX_citation", '@misc{palemeq2021yeddapalemeq, author = {Palemeq, Yedda}, title = {Yedda Palemeq}, year = {2021}, howpublished = {\\url{https://yeddapalemeq.blogspot.com/}}, note = {Retrieved May 19, 2026} }')
    root.set("copyright", "CC BY-NC 4.0")

    # Add each block as a sentence element
    for block in blocks:
        # Skip blocks without valid Paiwan text
        if not block['paiwan_text']:
            continue
        
        # Create sentence element
        s_elem = ET.SubElement(root, "S")
        s_elem.set("id", block['sentence_id'])
        
        # Add audio URL if available
        if block['audio_url']:
            s_elem.set("audio_url", block['audio_url'])
            audio_elem = ET.SubElement(s_elem, "AUDIO")
            audio_elem.set("source", block['audio_url'])
            audio_elem.set("file", s_elem.get("id") + ".wav")  # Assuming we will save audio files with sentence ID as filename

        # Add source URL
        s_elem.set("source", block['url'])
        
        # Apply specific text corrections before processing
        corrected_paiwan_text = block['paiwan_text']
        if corrected_paiwan_text == "madadet aravac azua nusinitalem a kasiw.":
            corrected_paiwan_text = "madadet aravac azua nu sinitalem a kasiw."
        corrected_paiwan_text = corrected_paiwan_text.replace("yí pó", "yípó").replace("ā yí", "āyí")

        # Add the Paiwan text as FORM element
        form_elem = ET.SubElement(s_elem, "FORM")
        form_elem.set("kindOf", "original")
        form_elem.text = escape_xml_content(corrected_paiwan_text)
        
        # Add translation if available
        if block['translation']:
            transl_elem = ET.SubElement(s_elem, "TRANSL")
            transl_elem.set("xml:lang", "en")
            transl_elem.text = escape_xml_content(block['translation'])
        
        # Process word-level glosses (if there are none, do not include word-level elements)
        if block['glosses']:
            # Apply specific gloss corrections before processing
            corrected_glosses = []
            for gloss in block['glosses']:
                gloss = gloss.replace("yí pó", "yípó").replace("ā yí", "āyí")
                if gloss == "tja-(k)/'(a)ma: our father.tja- 'our, 1st peron PL GEN INCL'; the root iskamaor 'ama'father, dad'.":
                    corrected_glosses.append("tja-'ma: our father.tja- 'our, 1st peron PL GEN INCL'; the root iskamaor 'ama'father, dad'.")
                elif gloss == "ka-kuda- (a)n":
                    corrected_glosses.append("ka-kuda-n")
                else:
                    corrected_glosses.append(gloss)

            word_elements = match_words_to_glosses(corrected_paiwan_text, corrected_glosses, block['sentence_id'])
            
            for word_data in word_elements:
                w_elem = ET.SubElement(s_elem, "W")
                w_elem.set("id", word_data['id'])
                raw_word_text = html.unescape(word_data['word'])
                
                # Add FORM element
                form_elem = ET.SubElement(w_elem, "FORM")
                form_elem.set("kindOf", "original")
                form_elem.text = escape_xml_content(raw_word_text)
                
                # Add TRANSL element if gloss exists
                if word_data['gloss']:
                    # Extract translation part (after colon)
                    if ':' in word_data['gloss']:
                        translation = word_data['gloss'].split(':', 1)[1].strip()
                    else:
                        translation = word_data['gloss'].strip()
                    
                    if translation:  # Only add if translation is not empty
                        transl_elem = ET.SubElement(w_elem, "TRANSL")
                        transl_elem.set("xml:lang", "en")
                        transl_elem.text = escape_xml_content(translation)
                
                # Now add M elements for morphological segmentation if the gloss contains hyphens
                all_morphemes = []
                if raw_word_text and '-' in raw_word_text:
                    morphemes = raw_word_text.split('-')
                    for morph in morphemes:
                        morph = morph.strip()
                        if morph:  # Only add non-empty morphemes
                            if "<" in morph or ">" in morph:
                                # If the morpheme contains angle brackets, extract content inside and enclose in hyphens
                                # Also extract any content outside the angle brackets a morpheme separated by -
                                # So "kan<em>a" would yield ["kan-a", "em"] and "ta<em>ortua" would yield ["ta-ortua", "em"]
                                match = re.match(r'^(.*?)<([^<>]+)>(.*?)$', morph)
                                if match:
                                    before, infix, after = match.groups()
                                    outer_parts = [part.strip() for part in (before, after) if part.strip()]
                                    sub_morphs = []
                                    if outer_parts:
                                        sub_morphs.append('-'.join(outer_parts))
                                    if infix.strip():
                                        sub_morphs.append("-"+infix.strip()+"-")
                                else:
                                    sub_morphs = [morph]
                                all_morphemes.extend(sub_morphs)
                            else:
                                all_morphemes.append(morph)
                elif raw_word_text and ('<' in raw_word_text or '>' in raw_word_text):
                    # Infix with no hyphens, e.g. l<em>angeda -> ["langeda", "-em-"]
                    match = re.match(r'^(.*?)<([^<>]+)>(.*?)$', raw_word_text)
                    if match:
                        before, infix, after = match.groups()
                        outer_parts = [p.strip() for p in (before, after) if p.strip()]
                        if outer_parts:
                            all_morphemes.append('-'.join(outer_parts))
                        if infix.strip():
                            all_morphemes.append('-' + infix.strip() + '-')
                    else:
                        all_morphemes.append(raw_word_text.strip())
                else:
                    all_morphemes.append(raw_word_text.strip())

                for morph in all_morphemes:
                    if morph:
                        m_elem = ET.SubElement(w_elem, "M")
                        m_elem.set('id', f"{word_data['id']}M{all_morphemes.index(morph) + 1}")
                        m_form_elem = ET.SubElement(m_elem, "FORM")
                        m_form_elem.set("kindOf", "original")
                        m_form_elem.text = escape_xml_content(morph)


    
    return root

def prettify_xml(elem):
    """Return a pretty-printed XML string."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def generate_xml():
    """Generate XML from all blog posts."""
    print("Starting XML generation from blog structure analysis...")
    
    # Create XML directory if it doesn't exist
    os.makedirs('XML', exist_ok=True)
    
    # Collect all blocks using existing analysis logic
    print("Collecting blog posts for XML generation...")
    blocks = analyze_blog_posts(return_blocks=True)
    print(f"\nFound {len(blocks)} total text blocks")
    
    # Filter out blocks without valid Paiwan text
    valid_blocks = [b for b in blocks if b['paiwan_text']]
    
    # Create XML
    xml_root = create_xml(blocks)
    
    # Generate pretty XML
    xml_content = prettify_xml(xml_root)
    
    # Write to file
    output_file = "XML/Paiwan_Yedda_Blog.xml"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    print(f"\nXML generated successfully: {output_file}")
    print(f"Total sentences exported: {len(valid_blocks)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze Paiwan Every Day blog posts')
    parser.add_argument('--max-posts', type=int, help='Maximum number of posts to analyze')
    parser.add_argument('--details', action='store_true', help='Show detailed content for each block')
    parser.add_argument('--urls', nargs='+', help='Specific URLs to analyze')
    parser.add_argument('--generate-xml', action='store_true', help='Generate XML from all blog posts')
    
    args = parser.parse_args()
    
    if args.generate_xml:
        generate_xml()
    else:
        # Convert URL list if provided
        specific_urls = args.urls if args.urls else None
        analyze_blog_posts(max_posts=args.max_posts, show_details=args.details, specific_urls=specific_urls)