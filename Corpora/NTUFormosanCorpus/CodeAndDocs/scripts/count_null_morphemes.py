import xml.etree.ElementTree as ET
import glob
import os

xml_files = glob.glob('Final_XML/**/*.xml', recursive=True)

for xml_file in sorted(xml_files):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    s_hits = []
    w_hits = []
    m_hits = []

    for s in root.iter('S'):
        s_form = s.find('FORM')
        if s_form is not None and s_form.text and '∅' in s_form.text:
            s_hits.append((s.get('id'), s_form.text.strip()))
        for w in s.iter('W'):
            w_form = w.find('FORM')
            if w_form is not None and w_form.text and '∅' in w_form.text:
                w_hits.append((w.get('id'), w_form.text.strip()))
            for m in w.iter('M'):
                m_form = m.find('FORM')
                if m_form is not None and m_form.text and '∅' in m_form.text:
                    m_hits.append((m.get('id'), m_form.text.strip()))

    if s_hits or w_hits or m_hits:
        print(f"\n=== {xml_file} ===")
        print(f"  S-level: {len(s_hits)}")
        print(f"  W-level: {len(w_hits)}")
        print(f"  M-level: {len(m_hits)}")
        if s_hits:
            print("  S-level examples:")
            for sid, text in s_hits[:3]:
                print(f"    {sid}: {text}")
