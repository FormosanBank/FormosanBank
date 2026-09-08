"""
fix_colon_quote.py

In every <FORM kindOf="standard"> element of amis_glosbe.xml,
replaces the sequence `: "` with `, "`.
"""

from lxml import etree
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
xml_file = os.path.join(dir_path, "../../Final_XML/amis_glosbe.xml")

tree = etree.parse(xml_file)
count = 0

for form in tree.getroot().findall('.//FORM[@kindOf="standard"]'):
    if form.text and ': "' in form.text:
        form.text = form.text.replace(': "', ', "')
        count += 1

tree.write(xml_file, pretty_print=True, encoding="utf-8", xml_declaration=True)
print(f"Modified {count} elements.")
