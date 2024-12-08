import re
import os
import xml.etree.ElementTree as ET
import nltk
from nltk.corpus import words

extend_words = set(words.words())
additional_words = {"CIA", "SARS-CoV-2", "COVID", "Puerto Rico", "Factbook"}
extend_words.update(additional_words)

def swap_fullwidth_punctuation(text):
    """
    Swap full-width parentheses, colon, comma, question mark, and period with regular parentheses, colon, comma, question mark, and period.
    
    :param text: The input text
    :return: The text with full-width punctuation replaced by regular punctuation
    """
    # Define the mapping of full-width punctuation to regular punctuation
    # Also convert square brackets to parentheses
    fullwidth_to_regular = {
        '（': '(',
        '）': ')',
        '：': ':',
        '，': ',',
        '？': '?',
        '。': '.',
        '》': '"',
        '《': '"',
        '」': '"',
        '「': '"',
        '、': ',',
        '】': ')',
        '【': '(',
        ']': ')',
        '[': '(',
        '〔': '(',
        '〕': ')'
    }
    
    # Create a regular expression pattern to match any of the full-width punctuation characters
    pattern = re.compile('|'.join(map(re.escape, fullwidth_to_regular.keys())))
    
    # Define a function to replace each match with the corresponding regular punctuation
    def replace(match):
        return fullwidth_to_regular[match.group(0)]
    
    # Use re.sub to replace all full-width punctuation with regular punctuation
    return pattern.sub(replace, text)

def remove_big_blocks(text, file_path):
    pattern = r'\n.*?[\u4e00-\u9fff]{5}.*?[\u4e00-\u9fff]{5}.*?[\u4e00-\u9fff]{5}.*?\n'
    matches = list(re.finditer(pattern, text))
    modifications = []
    for match in matches:
        # Make sure it's 75% or more Chinese characters
        lenoriginal = len(match.group(0))
        lenchinese = len(re.sub(r'[^0-9\s.,;:!?%&@#*+\-/\\^$|~`<>\[\u4e00-\u9fff]', '', match.group(0)))
        if lenchinese >= lenoriginal * 0.75:
            match_start = match.start()
            match_end = match.end()
            modifications.append((match_start, match_end))
    
    # Apply and log the modifications in reverse order to avoid messing up the indices
    with open('remove_large_blocks.log', 'a') as log_file:
        for start, end in sorted(modifications, reverse=True):
            log_file.write(f"File: {file_path if file_path else 'N/A'}\n")
            log_file.write(f"Text: {text[start:end]}\n")
            log_file.write("\n")
            text = text[:start] + " " + text[end:]
    
    return text

def remove_empty_parentheses(text, file_path):
    """
    Remove empty parentheses
    """
    # Find parentheses with only punctuation or whitespace inside
    pattern = r'\([.,;:!?\'"()\s]*?\)'
    matches = list(re.finditer(pattern, text))
    # Create a list to store the modifications
    modifications = []
    for match in matches:
        # Find the line containing the match
        match_start = match.start()
        match_end = match.end()
        modifications.append((match_start, match_end))
    
    # Apply and log the modifications in reverse order to avoid messing up the indices
    with open('remove_empty_parentheses.log', 'a') as log_file:
        for start, end in sorted(modifications, reverse=True):
            log_file.write(f"File: {file_path if file_path else 'N/A'}\n")
            log_file.write(f"Text: {text[start:end]}\n")
            log_file.write("\n")
            text = text[:start] + " " + text[end:]
    
    return text

def remove_continuous_otherlang(text, file_path):
    """
    Remove continuous other language text
    """

    # Remove sequences of 25 or more characters that are not standard Latin letters
    pattern = r'[^A-Za-z0-9\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\s.,;:!?\'"()\-]{4,}[^A-Za-z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]{17,}[^A-Za-z0-9\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\s.,;:!?\'"()\-]{4,}'
    matches = list(re.finditer(pattern, text))
    # Create a list to store the modifications
    modifications = []
    if matches:
        for match in matches:
            # Make sure it's not just numerals, punctuation, and white space
            if re.match(r'[（(][0-9\s.,;:!?%&@#*+\-/\\^$|~`<>\[\]{}"\'()\u3000-\u303F\uFF00-\uFFEF\uFE30-\uFE4F，。]{0,50}[）)]', match.group(0)):
                continue
            # Find the line containing the match
            match_start = match.start()
            match_end = match.end()
            modifications.append((match_start, match_end))
            
    # Apply and log the modifications in reverse order to avoid messing up the indices
    with open('remove_character_strings.log', 'a') as log_file:
        for start, end in sorted(modifications, reverse=True):
            forlog = text[max(0,start-50):start] + "|||" + text[start:end] + "|||" + text[end:min(len(text),end+50)]
            # Get 50 characters before and after the match
            log_file.write(f"File: {file_path if file_path else 'N/A'}\n")
            log_file.write(f"Text: {forlog}\n")
            log_file.write("\n")
            text = text[:start] + " " + text[end:]

    # Remove sequences of 10 or more Chinese, Japanese, or Korean characters. Punctuation and whitespace are allowed.
    modifications = []
    pattern = r'[\u3000-\u303F\uFF00-\uFFEF\uFE30-\uFE4F\u4E00-\u9FFF]{2,}[0-9\u3000-\u303F\uFF00-\uFFEF\uFE30-\uFE4F\u4E00-\u9FFF\s.,;:!?\'"()\-]{6,}[\u3000-\u303F\uFF00-\uFFEF\uFE30-\uFE4F\u4E00-\u9FFF]{2,}'    
    matches = list(re.finditer(pattern, text))
    if matches:
        for match in matches:
            # Remove whitespace and punctuation from the matches
            match_text = re.sub(r'[\s.,;:!?\'"()\-]', '', match.group(0))
            if len(match_text) >= 10:
                # Find the line containing the match
                match_start = match.start()
                match_end = match.end()
                modifications.append((match_start, match_end))

    # Apply and log the modifications in reverse order to avoid messing up the indices
    with open('remove_character_strings.log', 'a') as log_file:
        for start, end in sorted(modifications, reverse=True):
            forlog = text[max(0,start-50):start] + "|||" + text[start:end] + "|||" + text[end:min(len(text),end+50)]
            # Get 50 characters before and after the match
            log_file.write(f"File: {file_path if file_path else 'N/A'}\n")
            log_file.write(f"Text: {forlog}\n")
            log_file.write("\n")
            text = text[:start] + " " + text[end:]

    return text

def remove_probable_references(text, filepath):
    """
    Remove probable references
    """

    # Find sequences consisting of a new line that starts with a number, followed by a period.
    # The sequence ends with (and contains) a new line.
    pattern = r'(?<=\n)\d+\..*?(?=\n|$)'
    matches = list(re.finditer(pattern, text))
    for match in matches:
        # How much of the text is neither English nor involves latin characters?

        # Get the text inside the parentheses
        match_text = match.group(0)
        lenmatch = len(match_text)
        # parse into individual words
        match_words = nltk.word_tokenize(match_text)
        # remove all english words from match_text
        for word in match_words:
            # Need to try capitalized and lowercase versions both.
            if nltk.WordNetLemmatizer().lemmatize(word.lower()) in extend_words or nltk.WordNetLemmatizer().lemmatize(word) in extend_words:
                match_text = re.sub(r'\b' + re.escape(word) + r'\b', '', match_text)

        # if the remaining latin characters are less than 50% of the original length,
        # remove
        latin_pattern = r'[^A-Za-z0-9\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]'
        remaining_latin = re.sub(latin_pattern, '', match_text)
        if len(remaining_latin) < lenmatch/2:
            with open('remove_possible_citations.log', 'a') as log_file:
                text = text.replace(match.group(0), '\n') #go ahead and remove from text
                log_file.write(f"File: {filepath if filepath else 'N/A'}:\n")
                log_file.write(f"Removed: {match.group(0)}\n")
                log_file.write("\n")

    return text

def remove_annotations(text, filepath):
    # Remove strings of Japanese, Chinese, Korean, Cyrillic, English words, or Spanish words
    # that are fully enclosed in parentheses. Punctuation (including Japanese, Korean, and Chinese punctuation) is allowed.
    # First, identify each pairs of parentheses. Limit to 250 characters in between (otherwise, probably an error)
    pattern = r'[（(][^（）()]{0,500}[）)]'
    matches = list(re.finditer(pattern, text))
    # Create a list to store the modifications
    modifications = []

    if matches:
        # identify instances where the text inside the parentheses is mostly chinese, japanese, korean, cyrillic, english, or spanish
        for match in matches:
            # Get the text inside the parentheses
            match_text = match.group(0)
            match_start = match.start()
            match_end = match.end()
            # If the text inside is only numerals and punctuation, ignore it
            if re.match(r'[（(][0-9\s.,;:!?%&@#*+\-/\\^$|~`<>\[\]{}"\'()\u3000-\u303F\uFF00-\uFFEF\uFE30-\uFE4F，。]{0,50}[）)]', match_text):
                continue
            # If the text inside variants of "sowal", tends to be parenthetical translations
            if re.search("sowal:", match_text):
                modifications.append((match_start, match_end))
            # If the text inside is marked in Chinese as a romanization, tends to be parenthetical translations
            elif re.search("羅馬化:", match_text):
                modifications.append((match_start, match_end))
            else:
                lenmatch = len(match_text)
                # parse into individual words
                match_words = nltk.word_tokenize(match_text)
                # remove all english words from match_text
                for word in match_words:
                    # Need to try capitalized and lowercase versions both.
                    if nltk.WordNetLemmatizer().lemmatize(word.lower()) in extend_words or nltk.WordNetLemmatizer().lemmatize(word) in extend_words:
                        match_text = re.sub(r'\b' + re.escape(word) + r'\b', '', match_text)

                # if there are fewer than 5 latin, extended latin, supplemental latin  characters left in 
                # match_text or the remaining latin characters are less than 25% of the original length,
                # remove
                latin_pattern = r'[^A-Za-z0-9\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]'
                remaining_latin = re.sub(latin_pattern, '', match_text)
                if len(remaining_latin) < 5 and len(remaining_latin) < lenmatch/4:
                    modifications.append((match_start, match_end))

    # Apply the modifications in reverse order to avoid messing up the indices
    for start, end in sorted(modifications, reverse=True):
        with open('remove_Annotations.log', 'a') as log_file:
            forlog = text[max(0,start-50):start] + "|||" + text[start:end] + "|||" + text[end:min(len(text),end+50)]
            # Get 50 characters before and after the match
            log_file.write(f"File: {filepath if filepath else 'N/A'}\n")
            log_file.write(f"Text: {forlog}\n")
            log_file.write("\n")
            text = text[:start] + " " + text[end:]

    return text

def modify_xml(input_dir, output_dir, lang_code, lang_name):
    """
    Modify the XML files to remove other languages
    """
    # Create the output directory if it does not exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get the list of XML files in the input directory
    xml_files = [f for f in os.listdir(input_dir) if f.endswith('.xml')]

    # Loop through each XML file
    for xml_file in xml_files:
        # Read the XML file
        file_path = os.path.join(input_dir, xml_file)
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            print(f"Error parsing {file_path}: {e}")
            continue
        # Process the XML file
        for s_element in root.findall('.//S'):
            form_element = s_element.find('FORM')
            if form_element is not None:
                text = form_element.text
                if text:
                    text = swap_fullwidth_punctuation(text) #otherwise, tokenization is screwy
                    text = remove_big_blocks(text, os.path.join(input_dir, xml_file))
                    text = remove_annotations(text, os.path.join(input_dir, xml_file))
                    text = remove_probable_references(text, os.path.join(input_dir, xml_file))
                    text = remove_continuous_otherlang(text, os.path.join(input_dir, xml_file))
                    text = remove_empty_parentheses(text, os.path.join(input_dir, xml_file)) # clean up empty parentheses
                    
                    form_element.text = text # Update the text in the XML
                    # Write the modified XML content to the output directory
                    # Convert the tree to a string
                    xml_str = ET.tostring(tree.getroot(), encoding='unicode')

                    # Parse the string with minidom for pretty-printing
                    from xml.dom.minidom import parseString
                    dom = parseString(xml_str)
                    pretty_xml_str = dom.toprettyxml(indent='  ')

                    # Write the pretty-printed XML to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(pretty_xml_str)

    # Print a message indicating the completion of the modification process
    print(f"Modified XML files for {lang_name} language")


def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    lang_codes = {"Amis":"ami", "Atayal":"tay", "Saisiyat":"xsy", "Thao":"ssf", "Seediq":"trv", "Bunun":"bnn", 
                  "Paiwan":"pwn", "Rukai":"dru", "Truku":"trv", "Kavalan":"ckv", "Tsou":"tsu", "Kanakanavu":"xnb", 
                  "Saaroa":"sxr", "Puyuma":"pyu", "Yami":"tao", "Sakizaya":"szy"}
    for lang in [ "Amis","Seediq","Atayal", "Sakizaya", "Paiwan"]:
        print(f"Scrubbing {lang}")
        modify_xml(os.path.join(curr_dir, "Final_XML",lang), os.path.join(curr_dir, "Final_XML", lang), lang_codes[lang], lang)    

if __name__ == "__main__":
    main()