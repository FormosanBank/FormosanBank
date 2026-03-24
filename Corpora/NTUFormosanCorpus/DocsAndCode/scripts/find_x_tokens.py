import xml.etree.ElementTree as ET
import glob
from collections import defaultdict

xml_files = glob.glob('Final_XML/**/*.xml', recursive=True)

# Track hits at each level: (file, element_tag, id, form_text, transl_text, context)
hits = []

for xml_file in sorted(xml_files):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    for s in root.iter('S'):
        # S-level FORM
        s_form = s.find('FORM')
        if s_form is not None and s_form.text:
            import re
            if re.search(r'\bX\b', s_form.text):
                hits.append(('S-FORM', xml_file, s.get('id'), s_form.text.strip(), ''))

        for w in s.iter('W'):
            # W-level FORM
            w_form = w.find('FORM')
            if w_form is not None and w_form.text:
                if re.search(r'\bX\b', w_form.text):
                    hits.append(('W-FORM', xml_file, w.get('id'), w_form.text.strip(), ''))

            # W-level TRANSL
            for transl in w.findall('TRANSL'):
                if transl.text and re.search(r'\bX\b', transl.text):
                    lang = transl.get('{http://www.w3.org/XML/1998/namespace}lang', '')
                    hits.append(('W-TRANSL-' + lang, xml_file, w.get('id'), w_form.text.strip() if w_form is not None and w_form.text else '', transl.text.strip()))

            for m in w.iter('M'):
                # M-level FORM
                m_form = m.find('FORM')
                if m_form is not None and m_form.text:
                    if re.search(r'\bX\b', m_form.text):
                        hits.append(('M-FORM', xml_file, m.get('id'), m_form.text.strip(), ''))

                # M-level TRANSL
                for transl in m.findall('TRANSL'):
                    if transl.text and re.search(r'\bX\b', transl.text):
                        lang = transl.get('{http://www.w3.org/XML/1998/namespace}lang', '')
                        hits.append(('M-TRANSL-' + lang, xml_file, m.get('id'), m_form.text.strip() if m_form is not None and m_form.text else '', transl.text.strip()))

print(f"Total 'X' token hits (word-boundary): {len(hits)}\n")

by_type = defaultdict(list)
for h in hits:
    by_type[h[0]].append(h)

for kind, items in sorted(by_type.items()):
    print(f"--- {kind} ({len(items)}) ---")
    for item in items[:8]:
        tag, f, eid, form, transl = item
        print(f"  [{eid}] form='{form}'  transl='{transl}'  ({f})")
    if len(items) > 8:
        print(f"  ... and {len(items) - 8} more")
    print()
