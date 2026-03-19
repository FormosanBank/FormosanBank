#!/usr/bin/env python3
"""
Update FormosanBank corpus markdown files with statistics tables from CSV files.

Usage:
    python update_corpus_stats.py

The script reads CSV files from the `statistics/` folder and inserts (or replaces)
a Corpus Statistics section as the second section of each corresponding markdown file
in `en-us/the-bank-architecture/corpora/`.
"""

import csv
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT  = Path(__file__).parent
STATS_DIR  = REPO_ROOT / 'statistics'
CORPORA_DIR = REPO_ROOT / 'en-us' / 'the-bank-architecture' / 'corpora'

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Languages that have no dialect subdivisions
NO_DIALECT_LANGS = {'ckv', 'ssf', 'sxr', 'szy', 'tao', 'tsu', 'xnb', 'xsy'}

# Dialects that are culturally/politically treated as independent languages.
# Maps (csv_lang_code, csv_dialect_name) → display name used as a language-level column.
PROMOTE_DIALECT_AS_LANG = {
    ('trv', 'Truku'): 'Truku',
}

# Human-readable names for each ISO language code
LANG_NAMES = {
    'ami': 'Amis',
    'bnn': 'Bunun',
    'ckv': 'Kavalan',
    'dru': 'Rukai',
    'pwn': 'Paiwan',
    'pyu': 'Puyuma',
    'ssf': 'Thao',
    'sxr': 'Saaroa',
    'szy': 'Sakizaya',
    'tao': 'Yami',
    'tay': 'Atayal',
    'trv': 'Seediq',
    'tsu': 'Tsou',
    'xnb': 'Kanakanabu',
    'xsy': 'Saisiyat',
}

# HTML markers so the section can be cleanly replaced on subsequent runs
STATS_START = '<!-- CORPUS STATS START -->'
STATS_END   = '<!-- CORPUS STATS END -->'

# Mapping: CSV filename  →  MD filename (None = no matching MD yet)
CSV_TO_MD = {
    'ePark_corpora_stats.csv':                  'epark.md',
    'FormosanBankGitBook_corpora_stats.csv':    'FormosanBankGitBook.md',
    'Glosbe_corpora_stats.csv':                 'Glosbe.md',
    'HundredPaiwanStories_corpora_stats.csv':   'HundredPaiwanTexts.md',
    'ILRDF_Dicts_corpora_stats.csv':            'ilrdf-dictionaries.md',
    'MontgomeryTexts_corpora_stats.csv':        'MontgomeryTexts.md',
    'NTU_Paiwan_ASR_corpora_stats.csv':         'ntu-paiwan-asr.md',
    'Paiwan_Stories_corpora_stats.csv':         'paiwan-stories.md',
    'Presidential_Apologies_corpora_stats.csv': 'presidential-apologies.md',
    'RauDong_corpora_stats.csv':                'RauDong.md',
    'SEALS33_corpora_stats.csv':                'SEALS33.md',
    'Virginia_Fey_Dictionary_corpora_stats.csv':'virginia-feys-amis-dictionary.md',
    'WakelinTexts_1958_Yami_corpora_stats.csv': None,   # no matching MD yet
    'Whitehorn_Collection_corpora_stats.csv':   'Whitehorn-Collection.md',
    'Wikipedias_corpora_stats.csv':             'wikipedias.md',
}

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_count(value) -> str:
    """Format an integer with thousands separators, e.g. 58782 → '58,782'."""
    try:
        n = int(float(value))
    except (ValueError, TypeError):
        return '—'
    return f'{n:,}'


def fmt_audio(seconds) -> str:
    """Convert seconds to hours, e.g. 48071.9 → '13.4h'. Zero → '0'."""
    try:
        s = float(seconds)
    except (ValueError, TypeError):
        return '—'
    if s == 0:
        return '0'
    return f'{s / 3600:.1f}h'


def fmt_pct(proportion) -> str:
    """Format a 0–1 proportion as a percentage, e.g. 0.85 → '85%'."""
    try:
        p = float(proportion)
    except (ValueError, TypeError):
        return '—'
    return f'{p * 100:.0f}%'


# ---------------------------------------------------------------------------
# Row handling
# ---------------------------------------------------------------------------

def col_header(lang: str, dialect: str) -> str:
    """
    Return the column header for a language/dialect combination.

    Rules:
      - Empty language            → 'Unknown'
      - No-dialect language       → just the ISO code (e.g. 'ckv')
      - Multi-dialect + dialect   → 'lang<br>Dialect'
      - Multi-dialect + no dialect→ 'lang<br>UK'  (UK = unknown)
    """
    lang    = lang.strip()
    dialect = dialect.strip()
    if not lang:
        return 'Unknown'
    if (lang, dialect) in PROMOTE_DIALECT_AS_LANG:
        return PROMOTE_DIALECT_AS_LANG[(lang, dialect)]
    display = LANG_NAMES.get(lang, lang)
    if lang in NO_DIALECT_LANGS:
        return display
    if dialect:
        return f'{display}<br>{dialect}'
    return f'{display}<br>UK'


def row_has_data(row: dict) -> bool:
    """Return True if at least one displayed numeric field is non-zero."""
    fields = ('word_count', 'audio_time', 'eng_transl_count',
              'zho_transl_count', 'segmented_sentences')
    try:
        return any(float(row.get(f) or 0) != 0 for f in fields)
    except (ValueError, TypeError):
        return True


def sort_key(row: dict):
    """Sort key: language alphabetically (empty → last), then dialect."""
    lang    = row.get('language', '').strip() or '\xff'
    dialect = row.get('dialect',  '').strip() or ''
    return (lang, dialect)


def prepare_rows(raw_rows: list[dict]) -> list[dict]:
    """Filter meaningless rows and sort."""
    kept = [r for r in raw_rows if row_has_data(r)]
    return sorted(kept, key=sort_key)


# ---------------------------------------------------------------------------
# Table building
# ---------------------------------------------------------------------------

# Non-breaking space for indented sub-rows inside a markdown table cell
INDENT = '&nbsp;&nbsp;&nbsp;&nbsp;'

# Row definitions: (display label, CSV field or None, formatter)
ROW_DEFS = [
    ('Word count',                        'word_count',           fmt_count),
    ('Audio length',                      'audio_time',           fmt_audio),
    ('Translated sentences',              None,                   None),          # header row
    (f'{INDENT}English',                  'eng_transl_count',     fmt_count),
    (f'{INDENT}Mandarin',                 'zho_transl_count',     fmt_count),
    ('Morphologically segmented',         'segmented_sentences',  fmt_count),
    ('Proportion glossed',                'glossed_proportion',   fmt_pct),
]


def build_table(rows: list[dict]) -> str:
    """Return a markdown table string for the given (already sorted/filtered) rows."""
    headers = [col_header(r.get('language', ''), r.get('dialect', '')) for r in rows]

    # Header row + separator
    header_line = '| | ' + ' | '.join(headers) + ' |'
    sep_line    = '| --- | ' + ' | '.join(['---'] * len(headers)) + ' |'

    data_lines = []
    for label, field, formatter in ROW_DEFS:
        if field is None:
            # Parent label row – all data cells are empty
            cells = [''] * len(rows)
        else:
            cells = [formatter(r.get(field, 0)) for r in rows]
        data_lines.append('| ' + label + ' | ' + ' | '.join(cells) + ' |')

    return '\n'.join([header_line, sep_line] + data_lines)


def build_stats_section(rows: list[dict], heading: str) -> str:
    """
    Return the full stats section (including HTML markers) ready for insertion.
    The section ends with a *** divider so the next section is visually separated.
    """
    table = build_table(rows)
    return (
        f'{STATS_START}\n'
        f'{heading} Corpus Statistics\n\n'
        f'{table}\n\n'
        f'***\n\n'
        f'{STATS_END}'
    )


# ---------------------------------------------------------------------------
# Markdown manipulation
# ---------------------------------------------------------------------------

def detect_section_heading_level(content: str) -> str:
    """
    Return the markdown heading prefix (e.g. '###') used for top-level sections
    (i.e. the first sub-heading below the document title).
    Falls back to '###'.
    """
    m = re.search(r'^(#{2,4})\s', content, re.MULTILINE)
    return m.group(1) if m else '###'


# Matches a *** divider line (possibly surrounded by spaces/tabs, but NOT newlines
# within the *** itself, so we stay within a single line).
_SEP_RE = re.compile(r'\n[ \t]*\*\*\*[ \t]*\n')


def find_insert_position(content: str) -> int:
    """
    Find the character index at which to insert the stats section.

    Strategy (in order):
      1. After the FIRST *** separator (makes stats the 2nd section).
      2. Before the SECOND heading of the same level as the first section heading
         (for files that don't use *** separators).
      3. End of file as a last resort.
    """
    # -- Option 1: use *** separator -------------------------------------------
    m = _SEP_RE.search(content)
    if m:
        return m.end()   # character right after the '\n' that closes the ***

    # -- Option 2: before 2nd heading of same level as 1st section heading ------
    section_level = detect_section_heading_level(content)
    # Pattern matches headings at the same level (e.g. '### ' or '## ')
    section_re = re.compile(
        r'^' + re.escape(section_level) + r'[^#]',
        re.MULTILINE
    )
    matches = list(section_re.finditer(content))
    if len(matches) >= 2:
        return matches[1].start()

    # -- Option 3: before 2nd heading of ANY level (e.g. files with only # headings) --
    any_heading_re = re.compile(r'^#{1,6}\s', re.MULTILINE)
    all_headings = list(any_heading_re.finditer(content))
    if len(all_headings) >= 2:
        return all_headings[1].start()

    # -- Option 4: end of file --------------------------------------------------
    return len(content)


def update_md(md_path: Path, rows: list[dict]) -> None:
    """Read the markdown file, insert/replace the stats section, and write it back."""
    content = md_path.read_text(encoding='utf-8')

    # Always strip any existing stats section first so we can reinsert at the
    # correct position (handles both fresh runs and position corrections).
    if STATS_START in content:
        strip_re = re.compile(
            r'\n?' + re.escape(STATS_START) + r'.*?' + re.escape(STATS_END) + r'\n?',
            re.DOTALL,
        )
        content = strip_re.sub('', content)
        # Collapse runs of 3+ blank lines left by the removal
        content = re.sub(r'\n{3,}', '\n\n', content)

    heading = detect_section_heading_level(content)
    section = build_stats_section(rows, heading)
    pos     = find_insert_position(content)

    new_content = content[:pos] + '\n' + section + '\n\n' + content[pos:]

    md_path.write_text(new_content, encoding='utf-8')
    print(f'  ✓  Updated {md_path.name}')


# ---------------------------------------------------------------------------
# README aggregation
# ---------------------------------------------------------------------------

# Normalise variant/legacy language codes to canonical ISO codes
LANG_NORMALISE = {
    'amis': 'ami',
}


def _empty_stats() -> dict:
    return {
        'word_count':          0,
        'audio_time':          0.0,
        'eng_transl_count':    0,
        'zho_transl_count':    0,
        'segmented_sentences': 0,
        'glossed_segments':    0.0,   # sum of seg_sentences × glossed_proportion
    }


def _accumulate(bucket: dict, row: dict) -> None:
    try:
        bucket['word_count']          += int(float(row.get('word_count')          or 0))
        bucket['audio_time']          += float(row.get('audio_time')              or 0)
        bucket['eng_transl_count']    += int(float(row.get('eng_transl_count')    or 0))
        bucket['zho_transl_count']    += int(float(row.get('zho_transl_count')    or 0))
        seg                            = int(float(row.get('segmented_sentences') or 0))
        gp                             = float(row.get('glossed_proportion')      or 0)
        bucket['segmented_sentences'] += seg
        bucket['glossed_segments']    += seg * gp
    except (ValueError, TypeError):
        pass


def _aggregate_csvs() -> tuple[dict, dict]:
    """
    Read every CSV and return two aggregation dicts:
      lang_stats  : { lang_code → stats }
      dial_stats  : { (lang_code, dialect_label) → stats }   multi-dialect langs only
    """
    from collections import defaultdict
    lang_stats: dict[str, dict] = defaultdict(_empty_stats)
    dial_stats: dict[tuple, dict] = defaultdict(_empty_stats)

    for csv_path in sorted(STATS_DIR.glob('*.csv')):
        with csv_path.open(encoding='utf-8') as fh:
            for row in csv.DictReader(fh):
                lang = LANG_NORMALISE.get(
                    row.get('language', '').strip(),
                    row.get('language', '').strip()
                )
                if not lang:
                    continue

                dialect = row.get('dialect', '').strip()

                # Check if this dialect is promoted to a language in its own right
                if (lang, dialect) in PROMOTE_DIALECT_AS_LANG:
                    promoted = PROMOTE_DIALECT_AS_LANG[(lang, dialect)]
                    _accumulate(lang_stats[promoted], row)
                    # Don't add to dial_stats — it's a language, not a dialect
                else:
                    _accumulate(lang_stats[lang], row)
                    # Dialect breakdown only for multi-dialect languages
                    if lang not in NO_DIALECT_LANGS:
                        label = dialect if dialect else 'UK'
                        _accumulate(dial_stats[(lang, label)], row)

    return dict(lang_stats), dict(dial_stats)


def _make_table_from_buckets(keys: list, buckets: dict, header_fn) -> str:
    """Generic table builder given an ordered list of bucket keys."""
    headers   = [header_fn(k) for k in keys]
    header_line = '| | ' + ' | '.join(headers) + ' |'
    sep_line    = '| --- | ' + ' | '.join(['---'] * len(keys)) + ' |'

    def glossed(k):
        seg = buckets[k]['segmented_sentences']
        gs  = buckets[k]['glossed_segments']
        return '0%' if seg == 0 else fmt_pct(gs / seg)

    def col(k, field, fmt):
        return fmt(buckets[k][field])

    data_lines = [
        '| Word count | '                + ' | '.join(col(k, 'word_count',          fmt_count) for k in keys) + ' |',
        '| Audio length | '              + ' | '.join(col(k, 'audio_time',          fmt_audio) for k in keys) + ' |',
        '| Translated sentences | '      + ' | '.join('' for _ in keys)                                       + ' |',
        f'| {INDENT}English | '          + ' | '.join(col(k, 'eng_transl_count',    fmt_count) for k in keys) + ' |',
        f'| {INDENT}Mandarin | '         + ' | '.join(col(k, 'zho_transl_count',    fmt_count) for k in keys) + ' |',
        '| Morphologically segmented | ' + ' | '.join(col(k, 'segmented_sentences', fmt_count) for k in keys) + ' |',
        '| Proportion glossed | '        + ' | '.join(glossed(k)                               for k in keys) + ' |',
    ]
    return '\n'.join([header_line, sep_line] + data_lines)


def build_readme_tables() -> tuple[str, str]:
    """Return (language-level table, dialect-level table) markdown strings."""
    lang_stats, dial_stats = _aggregate_csvs()

    # --- Language-level table (columns = ISO codes, no dialect) ---
    lang_keys = sorted(lang_stats)
    lang_table = _make_table_from_buckets(
        lang_keys, lang_stats,
        header_fn=lambda k: LANG_NAMES.get(k, k)
    )

    # --- Dialect-level table (columns = Language<br>Dialect, multi-dialect langs only) ---
    dial_keys = sorted(dial_stats, key=lambda t: (t[0], t[1]))
    dial_table = _make_table_from_buckets(
        dial_keys, dial_stats,
        header_fn=lambda t: f'{LANG_NAMES.get(t[0], t[0])}<br>{t[1]}'
    )

    return lang_table, dial_table


def update_readme() -> None:
    readme_path = CORPORA_DIR / 'README.md'
    content     = readme_path.read_text(encoding='utf-8')

    # Strip any existing stats section
    if STATS_START in content:
        strip_re = re.compile(
            r'\n?' + re.escape(STATS_START) + r'.*?' + re.escape(STATS_END) + r'\n?',
            re.DOTALL,
        )
        content = strip_re.sub('', content)
        content = re.sub(r'\n{3,}', '\n\n', content)

    lang_table, dial_table = build_readme_tables()
    section = (
        f'{STATS_START}\n'
        f'### Corpus Statistics\n\n'
        f'#### By language\n\n'
        f'{lang_table}\n\n'
        f'#### By dialect\n\n'
        f'{dial_table}\n\n'
        f'***\n\n'
        f'{STATS_END}'
    )

    pos         = find_insert_position(content)
    new_content = content[:pos] + '\n' + section + '\n\n' + content[pos:]
    readme_path.write_text(new_content, encoding='utf-8')
    print('  ✓  Updated README.md\n')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print('Updating corpus markdown files with statistics…\n')

    for csv_name, md_name in CSV_TO_MD.items():
        print(f'Processing {csv_name} …')

        if md_name is None:
            print('  ⚠  No matching MD file – skipped.\n')
            continue

        csv_path = STATS_DIR  / csv_name
        md_path  = CORPORA_DIR / md_name

        if not csv_path.exists():
            print(f'  ✗  CSV not found: {csv_path}\n')
            continue
        if not md_path.exists():
            print(f'  ✗  MD not found:  {md_path}\n')
            continue

        with csv_path.open(encoding='utf-8') as fh:
            raw_rows = list(csv.DictReader(fh))

        rows = prepare_rows(raw_rows)
        if not rows:
            print('  ⚠  All rows were filtered out (no data) – skipped.\n')
            continue

        update_md(md_path, rows)
        print()

    print('Updating README.md with aggregate statistics…\n')
    update_readme()

    print('Done!')


if __name__ == '__main__':
    main()
