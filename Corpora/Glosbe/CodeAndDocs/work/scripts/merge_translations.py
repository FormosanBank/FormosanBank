"""
merge_translations.py

Combines amis_glosbe.xml (Simplified Chinese, zh-Hans) with
amis_glosbe-traditional.xml (Traditional Chinese, zh-Hant) by appending
a <TRANSL xml:lang="zh-Hant"> element to each <S> in the main file.

Updates amis_glosbe.xml in place.
"""

from lxml import etree
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
base_dir = os.path.join(dir_path, "../../Final_XML")

simplified_file  = os.path.join(base_dir, "amis_glosbe.xml")
traditional_file = os.path.join(base_dir, "amis_glosbe-traditional.xml")
output_file      = os.path.join(base_dir, "amis_glosbe.xml")

# Parse both files
simp_tree = etree.parse(simplified_file)
trad_tree = etree.parse(traditional_file)

# Build a lookup: S id -> zh-Hant TRANSL element
trad_transl = {}
for s in trad_tree.getroot().findall(".//S"):
    sid = s.get("id")
    transl = s.find('TRANSL[@{http://www.w3.org/XML/1998/namespace}lang="zh-Hant"]')
    if transl is not None:
        trad_transl[sid] = transl

# Append zh-Hant TRANSL to each S in the simplified tree
matched = 0
missing = 0
for s in simp_tree.getroot().findall(".//S"):
    sid = s.get("id")
    if sid in trad_transl:
        s.append(trad_transl[sid])
        matched += 1
    else:
        print(f"  WARNING: no Traditional translation found for {sid}")
        missing += 1

print(f"Matched: {matched}, Missing: {missing}")

simp_tree.write(output_file, pretty_print=True, encoding="utf-8", xml_declaration=True)
print(f"Written to: {output_file}")
