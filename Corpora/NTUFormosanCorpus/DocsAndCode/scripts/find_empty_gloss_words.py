import os
import json
import csv

def find_empty_gloss_words(grammar_dir, output_csv):
    header = ["language", "file_name", "Sentence_id", "Formosan", "En", "Ch"]
    rows = []
    for lang in os.listdir(grammar_dir):
        lang_dir = os.path.join(grammar_dir, lang)
        if not os.path.isdir(lang_dir):
            continue
        for fname in os.listdir(lang_dir):
            if not fname.endswith('.json'):
                continue
            fpath = os.path.join(lang_dir, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for entry in data.get('glosses', []):
                sid, s = entry[0], entry[1]
                for w in s.get('gloss', []):
                    # w is [form, zh, en] or [form, en, zh] depending on language, but grammar is always [form, zh, en]
                    form = w[0] if len(w) > 0 else ''
                    zh = w[1] if len(w) > 1 else ''
                    en = w[2] if len(w) > 2 else ''
                    if (not zh or zh == '_') and (not en or en == '_'):
                        rows.append([lang, fname, sid, form, en, zh])
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {output_csv}")

if __name__ == "__main__":
    grammar_dir = "grammar"
    output_csv = "empty_gloss_words.csv"
    find_empty_gloss_words(grammar_dir, output_csv)
