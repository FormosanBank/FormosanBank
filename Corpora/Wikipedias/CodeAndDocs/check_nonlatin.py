import os
import re
import xml.etree.ElementTree as ET

curr_dir = os.path.dirname(os.path.abspath(__file__))
# Log file to write the results
log_file = 'non_latin.log'

# Regular expression to match non-Latin characters
non_latin_regex = re.compile(r'[^A-Za-z0-9\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF]+')

with open(log_file, 'w', encoding='utf-8') as log:
    for lang in ["Amis", "Seediq", "Atayal", "Sakizaya", "Paiwan"]:
        input_dir = os.path.join(curr_dir, "Final_XML",lang)
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
                        for match in list(re.finditer(non_latin_regex, text)):
                            # Filter matches to include only those with 6 or more non-Latin characters, excluding whitespace
                                non_latin_sequence = match.group()
                                # Remove whitespace from the sequence
                                non_latin_sequence_no_whitespace = re.sub(r'\s', '', non_latin_sequence)
                                # Check if the sequence has 6 or more non-Latin characters
                                if len(non_latin_sequence_no_whitespace) >= 6:
                                    # Find the line containing the match
                                    match_start = match.start()
                                    match_end = match.end()
                                    
                                    # Get 50 characters before and after the match
                                    start_context = max(0, match_start - 50)
                                    end_context = min(len(text), match_end + 50)
                                    original = text[start_context:end_context]
                                    log.write(f"File: {file_path if file_path else 'N/A'}\n")
                                    log.write(f"Text: {original}\n")
                                    log.write("\n")
