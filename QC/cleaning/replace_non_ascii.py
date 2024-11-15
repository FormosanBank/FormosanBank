from lxml import etree
# Helper function
 
# Define a dictionary for replacements of non-ASCII characters
replacement_map = {
    '\u0082': "'",  # Unicode: U+0082
    '\u00A8': '"',  # Umlaut (¨)
    '\u00B4': "'",  # Acute accent (´)
    '\u00B7': ".",  # Middle dot (·)
    '\u00C0': 'A',  # À
    '\u00C1': 'A',  # Á
    '\u00C2': 'A',  # Â
    '\u00C7': 'C',  # Ç
    '\u00C9': 'E',  # É
    '\u00CD': 'I',  # Í
    '\u00CE': 'I',  # Î
    '\u00D1': 'N',  # Ñ
    '\u00D3': 'O',  # Ó
    '\u00D4': 'O',  # Ô
    '\u00D6': 'O',  # Ö
    '\u00D8': 'O',  # Ø
    '\u00DE': 'TH', # Þ
    '\u00DA': 'U',  # Ú
    '\u00DC': 'U',  # Ü
    '\u00DD': 'Y',  # Ý
    '\u00DF': 'ss', # ß
    '\u00E0': 'a',  # à
    '\u00E1': 'a',  # á
    '\u00E2': 'a',  # â
    '\u00E3': 'a',  # ã
    '\u00E4': 'a',  # ä
    '\u00E5': 'a',  # å
    '\u00E6': 'ae', # æ
    '\u00E7': 'c',  # ç
    '\u00E8': 'e',  # è
    '\u00EA': 'e',  # ê
    '\u00EB': 'e',  # ë
    '\u00EC': 'i',  # ì
    '\u00ED': 'i',  # í
    '\u00EE': 'i',  # î
    '\u00EF': 'i',  # ï
    '\u00F0': 'd',  # ð
    '\u00F2': 'o',  # ò
    '\u00F4': 'o',  # ô
    '\u00F5': 'o',  # õ
    '\u00F8': 'o',  # ø
    '\u00F9': 'u',  # ù
    '\u00FA': 'u',  # ú
    '\u00FB': 'u',  # û
    '\u00FC': 'u',  # ü
    '\u00FD': 'y',  # ý
    '\u0101': 'a',  # ā
    '\u0113': 'e',  # ē
    '\u01D4': 'u',  # ǔ
    '\u0244': 'U',  # Ʉ
    '\u0268': 'i',  # ɨ
    '\u0289': 'u',  # ʉ
    '\u02BC': "'",  # ʼ
    '\u02D9': '.',  # ˙
    '\u0304': '-',  # Combining Macron (̄)
    '\u037E': ';',  # Greek Question Mark (;)
    '\u041A': 'K',  # К (Cyrillic)
    '\u0420': 'R',  # Р (Cyrillic)
    '\u0423': 'U',  # У (Cyrillic)
    '\u0430': 'a',  # а (Cyrillic)
    '\u0438': 'i',  # и (Cyrillic)
    '\u043A': 'k',  # к (Cyrillic)
    '\u043C': 'm',  # м (Cyrillic)
    '\u043D': 'n',  # н (Cyrillic)
    '\u043E': 'o',  # о (Cyrillic)
    '\u0440': 'r',  # р (Cyrillic)
    '\u0441': 's',  # с (Cyrillic)
    '\u044B': 'y',  # ы (Cyrillic)
    '\u044F': 'ya', # я (Cyrillic)
    '\u1E5F': 'r',  # ṟ
    '\u200B': '',   # Zero Width Space (​)
    '\u2013': '-',  # En dash (–)
    '\u2014': '-',  # Em dash (—)
    '\u2015': '-',  # Horizontal Bar (―)
    '\u201A': ',',  # Single Low-9 Quotation Mark (‚)
    '\u2022': '*',  # Bullet (•)
    '\u2027': '.',  # Hyphenation Point (‧)
    '\u2039': '<',  # Single Left-Pointing Angle Quotation Mark (‹)
    '\u203A': '>',  # Single Right-Pointing Angle Quotation Mark (›)
    '\u203B': '*',  # Reference Mark (※)
    '\u2192': '->', # Right Arrow (→)
    '\u2215': '/',  # Division Slash (∕)
    '\u2502': '|',  # Box Drawings Light Vertical (│)
    '\u25A1': '[ ]',# White Square (□)
    '\u25C7': '<>', # White Diamond (◇)
    '\u2605': '*',  # Black Star (★)
    '\u3001': ',',  # Japanese Comma (、)
    '\u3002': '.',  # Japanese Full Stop (。)
    '\u300A': '<<', # Double Angle Bracket Left (《)
    '\u300B': '>>', # Double Angle Bracket Right (》)
    '\u300C': '"',  # Left Corner Bracket (「)
    '\u300D': '"',  # Right Corner Bracket (」)
    '\u300E': '"',  # Left White Corner Bracket (『)
    '\u300F': '"',  # Right White Corner Bracket (』)
    '\u3010': '[',  # Left Black Lenticular Bracket (【)
    '\u3011': ']',  # Right Black Lenticular Bracket (】)
    '\u301D': '"',  # Reversed Double Prime Quotation Mark (〝)
    '\u301E': '"',  # Double Prime Quotation Mark (〞)
    '\u3107': 'm',  # ㄇ (Bopomofo)
    '\u318D': '.',  # ㆍ (Hangul)
    '\u4E00': '-',  # 一 (Chinese, treated as a dash)
    '\uFE4B': '-',  # Dashed Overline (﹋)
    '\uFE50': ',',  # Small Comma (﹐)
    '\uFF01': '!',  # Fullwidth Exclamation Mark (！)
    '\uFF02': '"',  # Fullwidth Quotation Mark (＂)
    '\uFF08': '(',  # Fullwidth Left Parenthesis (（)
    '\uFF09': ')',  # Fullwidth Right Parenthesis (）
    '\uFF0C': ',',  # Fullwidth Comma (，)
    '\uFF0D': '-',  # Fullwidth Hyphen-Minus (－)
    '\uFF0E': '.',  # Fullwidth Full Stop (．)
    '\uFF1A': ':',  # Fullwidth Colon (：)
    '\uFF1B': ';',  # Fullwidth Semicolon (；)
    '\uFF1D': '=',  # Fullwidth Equals Sign (＝)
    '\uFF1F': '?',  # Fullwidth Question Mark (？)
    '\uFF2D': 'M',  # Fullwidth Latin Capital Letter M (Ｍ)
    '\uFF2E': 'N',  # Fullwidth Latin Capital Letter N (Ｎ)
    '\uFF2F': 'O',  # Fullwidth Latin Capital Letter O (Ｏ)
    '\uFF37': 'W',  # Fullwidth Latin Capital Letter W (Ｗ)
    '\uFF3F': '_',  # Fullwidth Low Line (＿)
    '\uFF4C': 'l',  # Fullwidth Latin Small Letter L (ｌ)
    '\uFF57': 'w',  # Fullwidth Latin Small Letter W (ｗ)
    '\uFF5E': '~',  # Fullwidth Tilde (～)
}


# Function to replace non-ASCII characters in FORM elements
def fix_non_ascii_chars(xml_file):
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()
        modified = False

        # Iterate over FORM elements
        for element in root.findall('.//FORM') + root.findall('.//TRANSL'):
            text = element.text
            if text:
                # Replace non-ASCII characters using the replacement map
                new_text = ''.join(replacement_map.get(char, char) for char in text)
                if new_text != text:
                    element.text = new_text
                    modified = True

        # Save changes if modifications were made
        if modified:
            tree.write(xml_file, encoding='utf-8', xml_declaration=True)
            print(f"Fixed non-ASCII characters in {xml_file}")

    except Exception as e:
        print(f"Error processing file {xml_file}: {e}")