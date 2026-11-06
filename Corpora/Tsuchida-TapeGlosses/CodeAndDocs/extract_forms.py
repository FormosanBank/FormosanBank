#!/usr/bin/env python3
"""Pull transcribed forms and Japanese glosses out of the Tsuchida collection's
tape catalogue (the two audio tabs of the project's public Google Sheet).

Input : the sheet's tabs as TSV, in --tsv-dir
        the reviewed decisions, --audit (source/audited_glosses.tsv)
Output: one TSV of extracted forms, --out

The content-summary cells mix four gloss patterns with free prose, so every row
carries the pattern that matched and a flag when the "gloss" looks like
recording metadata rather than a meaning. See source-decisions.md.
"""
import argparse, csv, re, collections

CJK = '　-〿぀-ヿ㐀-䶿一-鿿＀-￯'
HAS_CJK = re.compile(f'[{CJK}]')
BRACKET = re.compile(r'\[([^\[\]]{1,120})\]')
TIME = re.compile(r"(\d+m\d+s|\d+'\d+\"?)$")
CORNER_BEFORE = re.compile(f'(?:(\\d+)\\s*)?[「『]([^」』]{{1,80}})[」』]\\s*$')
CJK_BEFORE = re.compile(f'([{CJK}][^\\[\\]]{{0,30}}?)\\s*$')
CJK_AFTER = re.compile(f'^([{CJK}][{CJK}A-Za-z]{{0,30}})')
META = re.compile(r'音声|話者|調査|対応|繰り返|入り混|会話|歌と|最後|途中|以下|不明|finish|END|TOP')
# A "gloss" naming a genre describes a recording, not a word's meaning: these
# rows are the opening words of a song or narrative, not lexical entries.
# 歌 alone is a genre label ("song"), but 歌う is the ordinary verb "to sing",
# which is a lexeme. Everything else matching this pattern was checked
# against all 572 glosses and is genuinely a genre or recording label.
GENRE = re.compile(r'歌(?!う)|唄|テキスト|話$|話\)|モノローグ|声|ハーモニー|掛け声|語り')
ENDS_ELLIPSIS = re.compile(r'(\.\.\.|…)\s*$')
TIMEISH = re.compile(r"\d+m\d+s|\d+['~:]|~")

# tab, filename, language col, dialect col, summary col, notebook col, pages col, duration col
TABS = [
    ("cassette",  "TSFC音源リスト-カセットテープリスト.tsv", 3, 5, 11, 14, 15, 20),
    ("open_reel", "TSFC音源リスト-6mmテープリスト.tsv",      3, 6,  8, 11, 12, 20),
]

def balanced_paren(s):
    if not s or s[0] not in '(（':
        return None
    depth = 0
    for i, ch in enumerate(s):
        if ch in '(（':
            depth += 1
        elif ch in ')）':
            depth -= 1
            if depth == 0:
                return s[1:i]
    return None

def tape_no(aid):
    m = re.match(r'TSFC-Audio[AB]-(\d+)[AB]$', aid)
    return m.group(1) if m else ''

# Patterns where the source itself bracketed the form and parenthesised its
# gloss -- "[rangen wo(a) lobangbang](flying-fish cooking)". That layout is an
# explicit form-and-meaning pair, so a multi-word form in it is a phrasal
# lexeme, not the opening line of a song. The word-count heuristic must not
# fire on these; it exists only for unmarked prose.
EXPLICIT_PAIR = ('paren_after',)

def record_type(form, gloss, pattern=''):
    """lexeme = a form with a meaning; incipit = the first words of a recorded
    song or narrative, where the 'gloss' is a genre label."""
    if ENDS_ELLIPSIS.search(form):
        return 'incipit'
    if len(form.split()) >= 3 and pattern not in EXPLICIT_PAIR:
        return 'incipit'
    if gloss and GENRE.search(gloss):
        return 'incipit'
    return 'lexeme'


def unbalanced_close(gloss):
    """True if the gloss has more closing than opening parentheses.

    A gloss like '深い),' or '日本語再開) 一人' ends with a parenthesis that
    opened earlier in the cell, outside what was captured -- so the capture
    ran past a boundary and the gloss is a fragment, or belongs to a
    different form. Measured 2026-11-06: 8 published rows, every one of them
    either mis-paired or polluted. Catches short glosses the length test
    below misses (Saaroa 'pasamoŋga' <- '深い),' is 4 characters).
    """
    return (gloss.count(')') + gloss.count('）')) > (gloss.count('(') + gloss.count('（'))


def flag(gloss, pattern):
    if not gloss:
        return ''
    if META.search(gloss):
        return 'metadata_phrase'
    if TIMEISH.search(gloss):
        return 'contains_timecode'
    if unbalanced_close(gloss):
        return 'unbalanced_paren_gloss'
    # The threshold was > 14 characters. Lowered to > 5 on 2026-11-06 after
    # auditing every published bare_before row with a gloss of 6 or more
    # characters against its source cell: of 19, about 10 were wrong --
    # section headings ('人, 親族名詞' "person, kinship nouns"), the
    # interviewer's own question ('頭は何ていうんですか？頭'), and glosses
    # captured across an ellipsis run so they belong to an earlier form
    # ('背中, 腰...おび'). The 4-5 character band was audited too and is
    # clean (20 of 21 correct: 'ろうそく' "candle", 'ハンノキ' "alder",
    # '腦っている' "rotten"), so the break is at 6.
    #
    # This excludes about 8 correct records along with the bad ones. That is
    # the intended trade: a wrong gloss is worse than a missing one, and
    # every excluded row stays in extracted_forms.tsv with its reason.
    if pattern == 'bare_before' and len(gloss) > 5:
        return 'long_bare_before'
    return ''

def apply_audit(rows, path):
    """Overlay the reviewed decisions in audited_glosses.tsv onto the automatic
    extraction.

    The automatic rules are a candidate generator: they find bracketed forms and
    guess which neighbouring text is the gloss. Every candidate was then read
    against its own source cell by hand, and the cases the rules got wrong are
    recorded in that file -- either a corrected gloss, a corrected gloss
    language, a corrected language for the segment of tape, or an exclusion with
    the reason. See source-decisions.md.

    A decision whose key no longer matches exactly one extracted row is a hard
    error, not a warning: it means the sheet changed under the audit and the
    decision can no longer be trusted to land on the row it was made about.
    """
    audit = list(csv.DictReader(open(path, encoding='utf-8'), delimiter='\t'))
    index = collections.defaultdict(list)
    for r in rows:
        index[(r['tape_side_id'], r['form'], r['gloss_ja'])].append(r)
    applied = collections.Counter()
    for a in audit:
        hit = index.get((a['tape_side_id'], a['form'], a['extracted_gloss']), [])
        # TSFC-AudioA-8A elicits the same word twice, in two sections of the
        # tape, with the same gloss both times, so side + form + gloss does not
        # identify a single row there. The optional gloss_pattern column breaks
        # that tie; it is blank on every other decision.
        if a.get('gloss_pattern'):
            hit = [r for r in hit if r['gloss_pattern'] == a['gloss_pattern']]
        if len(hit) != 1:
            raise SystemExit(
                f"audit decision matches {len(hit)} rows, expected 1: "
                f"{a['tape_side_id']} / {a['form']!r} / {a['extracted_gloss']!r}"
                + (f" / {a['gloss_pattern']}" if a.get('gloss_pattern') else ''))
        r = hit[0]
        r['audit_action'], r['audit_note'] = a['action'], a['note']
        if a['action'] == 'exclude':
            r['gloss_flag'] = 'audited_excluded'
        elif a['action'] == 'publish':
            r['gloss_ja'] = a['gloss']
            r['gloss_lang'] = a['gloss_lang'] or 'jpn'
            r['language_audited'] = a['language_audited']
            r['gloss_flag'] = ''
            # Every publish decision is a word with a meaning. One of them
            # (Amis 'fongoh') had been typed 'incipit' only because the
            # metadata text swept into its gloss contained 音声 ("audio"),
            # which the genre test reads as the label 声.
            r['record_type'] = 'lexeme'
        else:
            raise SystemExit(f"unknown audit action {a['action']!r}")
        applied[a['action']] += 1
    return applied


def extract(tsv_dir):
    out, st = [], collections.Counter()
    for tab, fn, lc, dc, sc, nc, pc, uc in TABS:
        rows = list(csv.reader(open(f'{tsv_dir}/{fn}'), delimiter='\t'))
        def g(r, i):
            return r[i].strip().replace('\\n', ' ') if len(r) > i else ''
        cur = lang = dial = None
        for r in [x for x in rows[1:] if g(x, 0)]:
            t = tape_no(g(r, 0))
            # language and dialect are stated once per tape, on its A side
            if t != cur:
                cur, lang, dial = t, g(r, lc), g(r, dc)
            else:
                if g(r, lc): lang = g(r, lc)
                if g(r, dc): dial = g(r, dc)
            desc = g(r, sc)
            if not desc:
                continue
            st['rows_with_summary'] += 1
            got = 0
            for m in BRACKET.finditer(desc):
                form = m.group(1).strip()
                if not form or TIME.fullmatch(form):
                    continue
                if HAS_CJK.search(form):
                    st['skipped_cjk_bracket'] += 1
                    continue
                head, tail = desc[:m.start()], desc[m.end():]
                gloss = item = pattern = ''
                p = balanced_paren(tail)
                if p:
                    gloss, pattern = p.strip(), 'paren_after'
                else:
                    a = CJK_AFTER.match(tail)
                    if a:
                        gloss, pattern = a.group(1).strip(), 'bare_after'
                        nxt = balanced_paren(tail[a.end():])
                        if nxt:
                            gloss += f'({nxt.strip()})'
                if not gloss:
                    c = CORNER_BEFORE.search(head)
                    if c:
                        item, gloss, pattern = (c.group(1) or ''), c.group(2).strip(), 'corner_before'
                    else:
                        b = CJK_BEFORE.search(head)
                        if b and not b.group(1).endswith(('：', ':', '」', '』')):
                            gloss, pattern = b.group(1).strip(), 'bare_before'
                out.append({
                    'tape_side_id': g(r, 0), 'tape_kind': tab, 'tape_no': t,
                    'language_as_catalogued': lang or '',
                    'dialect_as_catalogued': dial or '',
                    'form': form, 'gloss_ja': gloss,
                    'gloss_pattern': pattern, 'gloss_flag': flag(gloss, pattern),
                    # Japanese unless the audit says otherwise: three tape
                    # sides were surveyed in English.
                    'gloss_lang': 'jpn',
                    # Set only where the audit found a segment of tape to be in
                    # a different language from the one the catalogue names for
                    # the side; language_as_catalogued stays as the sheet has it.
                    'language_audited': '', 'audit_action': '', 'audit_note': '',
                    'questionnaire_item_no': item,
                    'record_type': record_type(form, gloss, pattern),
                    'notebook_xref': g(r, nc), 'notebook_pages': g(r, pc),
                    'side_duration': g(r, uc), 'source_summary': desc,
                })
                got += 1
            if got:
                st['rows_yielding_forms'] += 1
    return out, st

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--tsv-dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--audit', required=True,
                    help='reviewed decisions, source/audited_glosses.tsv')
    a = ap.parse_args()
    rows, st = extract(a.tsv_dir)
    applied = apply_audit(rows, a.audit)
    with open(a.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter='\t')
        w.writeheader(); w.writerows(rows)
    clean = [r for r in rows if r['gloss_ja'] and not r['gloss_flag']]
    lex = [r for r in clean if r['record_type'] == 'lexeme']
    inc = [r for r in rows if r['record_type'] == 'incipit']
    print(f'{len(rows)} forms -> {a.out}')
    print(f'  audited decisions applied: '
          + ', '.join(f'{v} {k}' for k, v in sorted(applied.items())))
    for k, v in sorted(st.items()):
        print(f'  {k}: {v}')
    print(f'  with a gloss and no flag: {len(clean)}')
    print(f'    of those, lexemes : {len(lex)}')
    print(f'    of those, incipits: {len(clean) - len(lex)}')
    print(f'  incipits overall (any flag state): {len(inc)}')
    print('  lexemes by language + dialect:')
    for (l, d), n in collections.Counter((r['language_as_catalogued'], r['dialect_as_catalogued']) for r in lex).most_common():
        print(f'    {n:4d}  {l}{" / " + d if d else ""}')
