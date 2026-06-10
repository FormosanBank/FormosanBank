"""Compare validation_results_4.csv (pre-fix baseline) against the current
validation_results.csv. Report what was fixed, what regressed, and a count summary."""
import csv, os

os.chdir('/Users/jkhartshorne/Documents/Projects/Formosan/Formosan-NTU')

def load(path):
    with open(path) as f:
        return list(csv.DictReader(f))

rows_old = load('validation_results_4.csv')
rows_new = load('validation_results.csv')

old = {(r['filename'], r['s_id']): r for r in rows_old}
new = {(r['filename'], r['s_id']): r for r in rows_new}

fixed     = sorted(old.keys() - new.keys())
regressed = sorted(new.keys() - old.keys())

print(f"v4 (baseline): {len(rows_old):4d} rows")
print(f"current:       {len(rows_new):4d} rows")
print(f"fixed:         {len(fixed):4d}")
print(f"regressed:     {len(regressed):4d}")
print()

if regressed:
    print("=== REGRESSIONS (in current but not v4) ===")
    for k in regressed:
        print(" ", new[k])
    print()

print("=== FIXED (in v4 but not current) ===")
# Group by file for readability
by_file = {}
for fn, sid in fixed:
    by_file.setdefault(fn, []).append(sid)
for fn in sorted(by_file):
    print(f"  {fn}")
    for sid in sorted(by_file[fn]):
        print(f"    {sid}")

import xml.etree.ElementTree as ET
import json, os

os.chdir('/Users/jkhartshorne/Documents/Projects/Formosan/Formosan-NTU')

NEW_ERRORS = [
    ('Final_XML/Grammar/Sakizaya/Sakizaya.xml',        '04_S_11'),
    ('Final_XML/Grammar/Sakizaya/Sakizaya.xml',        '08_S_15'),
    ('Final_XML/Grammar/Seediq/Seediq.xml',            '13_S_24'),
    ('Final_XML/Grammar/Seediq/Seediq.xml',            '13_S_27'),
    ('Final_XML/Sentences/Kanakanavu/Kanakanavu.xml',  '3_S_238'),
    ('Final_XML/Sentences/Kanakanavu/Kanakanavu.xml',  '3_S_311'),
    ('Final_XML/Sentences/Kanakanavu/Kanakanavu.xml',  '4_S_168'),
    ('Final_XML/Sentences/Rukai/Rukai.xml',            '20200528-FW-Jimmy_S_11'),
    ('Final_XML/Sentences/Rukai/Rukai.xml',            '20200528-FW-Jimmy_S_7'),
    ('Final_XML/Sentences/Rukai/Rukai.xml',            '20200528-FW-Ryan_S_19'),
    ('Final_XML/Sentences/Rukai/Rukai.xml',            '20200529-FW-Ryan_S_18'),
    ('Final_XML/Sentences/Rukai/Rukai.xml',            '20200530-FW-Lixing-1_S_19'),
    ('Final_XML/Sentences/Rukai/Rukai.xml',            '20200530-FW-Ryan_S_35'),
    ('Final_XML/Stories/Kanakanavu/Kanakanavu_kkvNr-puratu_Muu.xml', 'kkvNr-puratu_Muu_S_80'),
    ('Final_XML/Stories/Saisiyat/Saisiyat_SaiNr-holiday_kalaeh a _oemaw.xml', 'SaiNr-holiday_kalaeh a _oemaw_S_25'),
    ('Final_XML/Stories/Saisiyat/Saisiyat_SaiNr-holiday_kalaeh a _oemaw.xml', 'SaiNr-holiday_kalaeh a _oemaw_S_27'),
    ('Final_XML/Stories/Saisiyat/Saisiyat_SaiNr-kathethel_parain a _oemaw.xml', 'SaiNr-kathethel_parain a _oemaw_S_11'),
]

_trees = {}
def get_tree(path):
    if path not in _trees:
        _trees[path] = ET.parse(path)
    return _trees[path]

for xml_path, s_id in NEW_ERRORS:
    tree = get_tree(xml_path)
    root = tree.getroot()

    s_elem = root.find(f'.//S[@id="{s_id}"]')
    if s_elem is None:
        print(f'  !! {s_id} not found in {xml_path}')
        continue

    form_elem = s_elem.find('FORM')
    form_text = form_elem.text if form_elem is not None else ''
    form_notes = form_elem.get('notes', '') if form_elem is not None else ''
    words_in_form = form_text.split() if form_text else []

    w_elems = s_elem.findall('W')
    w_forms = [w.find('FORM').text if w.find('FORM') is not None else '' for w in w_elems]

    print(f'=== {xml_path}  {s_id} ===')
    print(f'  FORM ({len(words_in_form)} tokens): {form_text!r}')
    if form_notes:
        print(f'  notes: {form_notes!r}')
    print(f'  W count: {len(w_elems)}')
    print(f'  W FORMs: {w_forms}')
    zh = s_elem.find('TRANSL[@lang="zh"]')
    en = s_elem.find('TRANSL[@lang="en"]')
    print(f'  zh: {zh.text if zh is not None else ""}')
    print(f'  en: {en.text if en is not None else ""}')
    print()

# Now inspect source JSON for the one anomalous case: 20200530-FW-Ryan_S_35
print('=== SOURCE JSON: Rukai sentence 20200530-FW-Ryan S_35 ===')
rukai_dir = 'sentence/Rukai_Vedai'
for fname in sorted(os.listdir(rukai_dir)):
    if '20200530-FW-Ryan' not in fname:
        continue
    fpath = os.path.join(rukai_dir, fname)
    with open(fpath) as fh:
        data = json.load(fh)
    for entry in data['glosses']:
        if str(entry[0]) == '35':
            print(f'  File: {fname}')
            print(json.dumps(entry[1], ensure_ascii=False, indent=2))
            break
