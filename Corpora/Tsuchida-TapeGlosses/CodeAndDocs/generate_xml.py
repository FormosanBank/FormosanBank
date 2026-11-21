#!/usr/bin/env python3
"""Build FormosanBank XML from the forms extracted by extract_forms.py.

Only clean form-gloss pairs in Formosan languages are published: a row needs a
gloss and an empty gloss_flag. Everything else stays in
source/extracted_forms.tsv for review. See source-decisions.md for why.

Two columns here come from the hand audit recorded in source/audited_glosses.tsv
rather than from the catalogue: gloss_lang, because three tape sides were
surveyed in English rather than Japanese, and language_audited, because two
sides contain a stretch of a language other than the one the catalogue names
for the side. language_as_catalogued is never overwritten, and every S says
both what the catalogue called the side and what the audit concluded.

One file per (language, dialect-as-catalogued) so that the catalogue's own
dialect labels never get silently merged.
"""
import argparse, csv, collections, os, re
from xml.sax.saxutils import escape, quoteattr

# catalogue's language string -> (ISO 639-3, FormosanBank language name)
LANG = {
    'Kavalan':    ('ckv', 'Kavalan'),
    'Saaroa':     ('sxr', 'Saaroa'),
    'Tsou':       ('tsu', 'Tsou'),
    'Yami':       ('tao', 'Yami'),
    'Saisiyat':   ('xsy', 'Saisiyat'),
    'Kanakanabu': ('xnb', 'Kanakanavu'),
    'Rukai':      ('dru', 'Rukai'),
    'Mantauran':  ('dru', 'Rukai'),
    'Atayal':     ('tay', 'Atayal'),
    'Tayal':      ('tay', 'Atayal'),
    'Sedeq':      ('trv', 'Seediq'),
    'Bunun':      ('bnn', 'Bunun'),
    'Amis':       ('ami', 'Amis'),
    'Ami':        ('ami', 'Amis'),
}
# Languages with no dialect rows in dialects.csv take the language name as the
# dialect value, the convention every single-dialect language follows.
SINGLE_DIALECT = {'Kavalan', 'Saaroa', 'Saisiyat', 'Kanakanavu', 'Tsou', 'Yami'}
# The only catalogue dialect label that maps to a dialects.csv row without a
# judgement call: dialects.csv lists Rukai/Wanshan with OtherNames "Mantauran".
DIALECT_MAP = {('Rukai', 'Mantauran-as-language'): 'Wanshan'}

CITATION = ('土田滋台湾原住民語資料 [Tsuchida Shigeru Taiwan Indigenous Language '
            'Materials], 2023. Digital collection managed by the Information '
            'Resources Center, Research Institute for Languages and Cultures of '
            'Asia and Africa, Tokyo University of Foreign Studies. '
            'https://formosa.aa-ken.jp')
BIBTEX = ('@misc{TsuchidaFormosanMaterials2023,'
          'title={土田滋台湾原住民語資料 [Tsuchida Shigeru Taiwan Indigenous Language Materials]},'
          'year={2023},'
          'howpublished={Digital collection managed by the Information Resources Center, '
          'Research Institute for Languages and Cultures of Asia and Africa, '
          'Tokyo University of Foreign Studies},'
          'url={https://formosa.aa-ken.jp}}')
COPYRIGHT = 'CC BY 4.0'
SOURCE = ('Audio catalogue (TSFC音源リスト) of the Tsuchida collection, '
          'content-summary column; see CodeAndDocs/source-decisions.md')


def slug(s):
    return re.sub(r'[^A-Za-z0-9]+', '', s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--forms', required=True)
    ap.add_argument('--xml-dir', required=True)
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.forms), delimiter='\t'))
    # Only lexemes: a row classified 'incipit' is the opening words of a
    # recorded song or narrative and its "gloss" is a genre label, not a
    # meaning, so publishing it in a wordlist would misrepresent both.
    # The language a row is filed under: what the audit concluded for that
    # stretch of tape if it looked at it, otherwise what the catalogue says.
    def lang_of(r):
        return r['language_audited'] or r['language_as_catalogued']

    clean = [r for r in rows
             if r['gloss_ja'] and not r['gloss_flag']
             and r['record_type'] == 'lexeme'
             and lang_of(r) in LANG]

    # Group on the FormosanBank language, not the catalogue's string: "Ami"
    # and "Amis" (and "Tayal" and "Atayal") are the same language spelled two
    # ways in the sheet, and keying on the raw string made two groups write to
    # one filename, so the second silently overwrote the first.
    groups = collections.defaultdict(list)
    for r in clean:
        cl = lang_of(r)
        _, fb = LANG[cl]
        # Mantauran is a Rukai dialect given in the language column; keep it
        # apart from Rukai rows that name no dialect.
        if cl == 'Mantauran':
            dial = 'Mantauran'
        elif r['language_audited']:
            # The catalogue's dialect names a dialect of the side's catalogued
            # language, so it says nothing about this stretch of tape.
            dial = ''
        else:
            dial = r['dialect_as_catalogued']
        groups[(fb, dial)].append(r)

    written = []
    for (fb_lang, cat_dial), items in sorted(groups.items()):
        iso = LANG[lang_of(items[0])][0]
        if cat_dial == 'Mantauran':
            dialect = DIALECT_MAP[('Rukai', 'Mantauran-as-language')]
        elif fb_lang in SINGLE_DIALECT:
            dialect = fb_lang
        else:
            dialect = 'unknown'

        tag = 'Tsuchida_TapeGlosses_' + slug(fb_lang)
        if cat_dial:
            tag += '_' + slug(cat_dial)
        outdir = os.path.join(a.xml_dir, fb_lang)
        os.makedirs(outdir, exist_ok=True)
        path = os.path.join(outdir, tag + '.xml')

        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append(
            f'<TEXT id={quoteattr(tag.upper())} '
            f'citation={quoteattr(CITATION)} '
            f'BibTeX_citation={quoteattr(BIBTEX)} '
            f'copyright={quoteattr(COPYRIGHT)} '
            f'xml:lang="{iso}" dialect={quoteattr(dialect)} '
            f'source={quoteattr(SOURCE)}>')

        seq = collections.Counter()
        for r in items:
            side = r['tape_side_id']
            seq[side] += 1
            sid = f'{tag}_{side}_{seq[side]:03d}'
            prov = [f'tape side {side}',
                    f'catalogued as "{r["language_as_catalogued"]}"']
            if cat_dial and cat_dial != 'Mantauran':
                prov.append(f'catalogued dialect "{cat_dial}"')
            if r['language_audited']:
                prov.append(f'filed under {r["language_audited"]} on audit, '
                            f'not the catalogued language: {r["audit_note"]}')
            elif r['audit_note']:
                prov.append(f'gloss corrected on audit: {r["audit_note"]}')
            if r['notebook_xref']:
                nb = r['notebook_xref']
                if r['notebook_pages']:
                    nb += f' ({r["notebook_pages"]})'
                prov.append(f'notebook {nb}')
            if r['questionnaire_item_no']:
                prov.append(f'basic-vocabulary item {r["questionnaire_item_no"]}')
            # A cell may list two forms against one Japanese gloss, separated
            # by a comma or a tilde. These are distinct lexemes sharing a gloss
            # (Kavalan "bi, bugas" for 米), not spelling variants of one form,
            # so each gets its own S rather than a POL-028 ver="alt" FORM --
            # which V150 alternate_FORM_low_overlap correctly rejected.
            parts = [p.strip() for p in re.split(r'\s*[,~]\s*', r['form']) if p.strip()]
            note = list(prov)
            if len(parts) > 1:
                note.append(f'source cell listed these together as "{r["form"]}"')
            for k, part in enumerate(parts):
                pid = sid if len(parts) == 1 else f'{sid}{chr(ord("a") + k)}'
                lines.append(f'  <S id={quoteattr(pid)} source={quoteattr("; ".join(note))}>')
                lines.append(f'    <FORM kindOf="original">{escape(part)}</FORM>')
                # No kindOf="standard" FORM. Maintainer's ruling, 2026-11-06:
                # "No standard until we've decided how to standardize." A copy
                # of the original would assert that Tsuchida's phonetic
                # notation is already the standard orthography, which it is
                # not. V014 count_missing_standard_form is SOFT and will
                # report every S; that is the intended, visible consequence.
                lines.append(f'    <PHON kindOf="original">{escape(part)}</PHON>')
                # Not always Japanese: three sides were surveyed in English and
                # their glosses are English, which the audit records per row.
                lines.append(f'    <TRANSL xml:lang="{r["gloss_lang"] or "jpn"}">'
                             f'{escape(r["gloss_ja"])}</TRANSL>')
                lines.append('  </S>')
        lines.append('</TEXT>')
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        # Count the S elements actually emitted, not the number of source rows:
        # a shared-gloss cell yields more than one S, so the two numbers differ
        # and reporting rows under the heading "S" overstates nothing but
        # misnames what it counts. Both are printed, and the S count is checked
        # against what is on disk below.
        n_s = sum(1 for ln in lines if ln.lstrip().startswith('<S id='))
        written.append((path, fb_lang, iso, dialect, cat_dial, len(items), n_s))

    tot_rows = sum(w[5] for w in written)
    tot_s = sum(w[6] for w in written)
    print(f'{len(written)} files, {tot_rows} source rows -> {tot_s} S elements\n')
    print(f'{"file":62s} {"lang":10s} {"iso":4s} {"dialect":9s} {"catalogued":12s} {"rows":>5s} {"S":>4s}')
    for p, l, i, d, cd, nr, ns in written:
        print(f'{os.path.relpath(p, a.xml_dir):62s} {l:10s} {i:4s} {d:9s} {cd or "-":12s} {nr:5d} {ns:4d}')

    # Verify against the files themselves. A filename collision once silently
    # destroyed six records while the summary still printed the full total, so
    # the reported figure is re-read from disk rather than trusted.
    on_disk = 0
    for w in written:
        with open(w[0], encoding='utf-8') as f:
            on_disk += sum(1 for ln in f if ln.lstrip().startswith('<S id='))
    assert on_disk == tot_s, f'reported {tot_s} S but {on_disk} on disk'
    print(f'\nverified on disk: {len(written)} files, {on_disk} S elements')
    skipped = collections.Counter()
    for r in rows:
        if r not in clean:
            if lang_of(r) not in LANG:
                skipped['non-Formosan language'] += 1
            elif not r['gloss_ja']:
                skipped['no gloss'] += 1
            elif r['gloss_flag']:
                skipped['gloss flagged: ' + r['gloss_flag']] += 1
            else:
                skipped['incipit, not a lexeme'] += 1
    print('\nnot published:')
    for k, v in skipped.most_common():
        print(f'  {v:4d}  {k}')


if __name__ == '__main__':
    main()
