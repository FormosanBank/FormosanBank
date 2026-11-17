"""Locate each errata correction in the published ePark XML by lesson + sentence/word number (from the AUDIO
urls), falling back to text similarity. usage: match_errata2.py ERRATA_K2_TSV EPARK_XML_DIR DIALECTS_CSV OUT_TSV"""
import csv, re, sys, os, glob, unicodedata, collections
from lxml import etree
from rapidfuzz import fuzz, process
tsv, xmldir, dcsv, out = sys.argv[1:5]
SEC = {'conversation': 'sheng_huo_hui_hua_pian_daily_conversation', 'culture': 'wen_hua_pian_cultural_section',
       'picture_story': 'tu_hua_gu_shi_pian_picture_story', 'read_write': 'yue_du_shu_xie_pian_reading_writing'}
DIAL = {int(r['idx']): r['dialect'] for r in csv.DictReader(open(dcsv))}
CJKSP = re.compile(r'(?<=[　-鿿＀-￯])\s+(?=[　-鿿＀-￯])')
def clean(s): return CJKSP.sub('', unicodedata.normalize('NFKC', s))
def norm(s):
    s = unicodedata.normalize('NFC', s).lower(); s = re.sub(r"[’‘ʼ`´′']", "'", s)
    return re.sub(r"[^\w'^]+", ' ', s).strip()
ZH = {c: i for i, c in enumerate('零一二三四五六七八九十')}
def zhnum(s):
    if s.isdigit(): return int(s)
    if s == '十': return 10
    if '十' in s:
        a, b = s.split('十'); return (ZH.get(a, 1) if a else 1) * 10 + (ZH.get(b, 0) if b else 0)
    return ZH.get(s)
def index_file(fn):
    """(lesson, 's'|'w', n) -> (sid, text) from AUDIO urls."""
    idx, groups, order = {}, {}, []
    for s in etree.parse(fn).iterfind('.//S'):
        f = s.find('FORM[@kindOf="original"]'); a = s.find('AUDIO')
        if f is None or not f.text or a is None: continue
        u = a.get('url', ''); item = (s.get('id'), f.text)
        m = re.search(r'/(\d+)c(\d+)([sw])(\d+)\.mp3$', u)                     # conversation
        if m: idx[(int(m.group(2)), m.group(3), int(m.group(4)))] = item; continue
        m = re.search(r'_data/audio/\d+/\d+_(\d+)_V(\d+)\.mp3$', u)            # culture / read_write vocabulary
        if m: idx[(int(m.group(1)), 'w', int(m.group(2)))] = item; continue
        m = re.search(r'/text/sound/+(\d+)/\d+\.mp3$', u)                      # lesson texts, grouped by textId
        if m:
            t = m.group(1)
            if t not in groups: groups[t] = []; order.append(t)
            groups[t].append(item)
    for L, t in enumerate(order, 1):
        for n, item in enumerate(groups[t], 1): idx[(L, 's', n)] = item
    return idx, len(order)
def lesson_items(idx, L):
    return [v for k, v in idx.items() if k[0] == L]
SPK = re.compile(r"^\s*[A-Z][\w’'\-]{1,15}\s*[:：]\s*")
def flags(c, ours):
    f = []
    a, b = norm(c), norm(ours)
    if a.replace(' ', '') == b.replace(' ', ''): f.append('spacing_only')
    if b and not (0.8 <= len(a) / max(1, len(b)) <= 1.25): f.append('length_change')
    if bool(SPK.match(c)) != bool(SPK.match(ours)): f.append('speaker_label')
    if a and b and a[:1] != b[:1] and (a[1:4] == b[1:4] or b[1:1 + 8] == a[:8] or a[1:1 + 8] == b[:8]): f.append('first_letter')
    return f
cache = {}
def get_index(sec, did):
    if (sec, did) not in cache:
        fn = glob.glob(os.path.join(xmldir, SEC[sec], '*', DIAL[did] + '.xml'))
        if fn:
            idx, nles = index_file(fn[0]); allS = [(s.get('id'), s.find('FORM[@kindOf="original"]').text) for s in etree.parse(fn[0]).iterfind('.//S') if s.find('FORM[@kindOf="original"]') is not None and s.find('FORM[@kindOf="original"]').text]
            cache[(sec, did)] = (os.path.relpath(fn[0], xmldir), idx, nles, allS)
        else: cache[(sec, did)] = ('', {}, 0, [])
    return cache[(sec, did)]
LAT = r"[A-Za-zÀ-ɏɐ-ʯ’'ʼ^]"
def corrections(res, is_word_ctx=False):
    """[(sentence_no or None, corrected_text)] — each 應修訂為/修正為/第N句 segment, with the nearest preceding 第N句."""
    out = []
    for m in re.finditer(r'(?:應?修[訂正]為|改為|改成|更正為|第\s*(\d+)\s*句\s*[:：])\s*[:：]?\s*', res):
        seg = res[m.end():]
        t = re.match(r"\s*((?:" + LAT + r"|[\s:,.?!\-\"“”()…~0-9])+)", seg)
        if not t: continue
        txt = re.sub(r'\s+', ' ', t.group(1)).strip(' ,;')
        txt = re.sub(r'\s*\(?\s*\d+\s*[.)、]?\s*$', '', txt).strip(' ,;(')
        if len(re.findall(r'[A-Za-z]', txt)) < 2 or (len(txt.split()) < 2 and len(re.findall(r'[A-Za-z]', txt)) < 6 and not is_word_ctx): continue
        prev = [int(x) for x in re.findall(r'第\s*(\d+)\s*句', res[:m.end()])]
        out.append((prev[-1] if prev else None, txt))
    if not out:   # bare form like "hani 修正為 heni" handled above; else take the whole Latin run
        t = re.search(r"((?:" + LAT + r")(?:" + LAT + r"|[\s:,.?!\-\"“”()…])+)", res)
        if t and len(re.findall(r'[A-Za-z]', t.group(1))) >= 4: out.append((None, t.group(1).strip()))
    # de-duplicate exact repeats
    seen, uniq = set(), []
    for k in out:
        if k not in seen: seen.add(k); uniq.append(k)
    return uniq
R = list(csv.DictReader(open(tsv), delimiter='\t')); rows = []
for r in R:
    did = int(r['did']); fn, idx, nles, allS = get_index(r['section'], did)
    mat, res = clean(r['material']), clean(r['result'])
    base = dict(section=r['section'], did=did, dialect=DIAL.get(did, '?'), seq=r['seq'], kind2=r['kind2'], material=mat, result=res, file=fn)
    if r['kind2'] in ('audio', 'no_change', 'zh_translation'):
        rows.append({**base, 'cls': 'not_text_edit'}); continue
    Lm = re.search(r'第\s*([0-9一二三四五六七八九十]+)\s*課', mat); L = zhnum(Lm.group(1)) if Lm else None
    is_word = bool(re.search(r'單字|詞彙|單詞', mat)); wn = re.search(r'\((\d+)\)', mat)
    cs = corrections(res, is_word)
    if not cs:
        rows.append({**base, 'cls': 'no_formosan_extracted', 'lesson': L}); continue
    normS = [norm(t) for _, t in allS]
    for sn, c in cs:
        key = (L, 'w', int(wn.group(1))) if is_word and wn else ((L, 's', sn) if L and sn else None)
        loc = idx.get(key) if key else None
        nc = norm(c)
        top = process.extract(nc, normS, scorer=fuzz.ratio, limit=2)
        fz = (allS[top[0][2]], top[0][1]) if top else (('', ''), 0); fz2 = top[1][1] if len(top) > 1 else 0
        how = 'number' if loc else ''
        if not loc and L:
            cand = lesson_items(idx, L)
            if cand:
                rep = clean(r['report']); quotes = [q.strip() for q in re.findall(r"((?:" + LAT + r")(?:" + LAT + r"|[\s:,.?!\-])+)", rep) if len(re.findall(r'[A-Za-z]', q)) >= 6]
                best = None
                for item in cand:
                    sc = max([fuzz.ratio(nc, norm(item[1]))] + [fuzz.ratio(norm(q), norm(item[1])) for q in quotes])
                    if best is None or sc > best[0]: best = (sc, item)
                scores = sorted((max([fuzz.ratio(nc, norm(i[1]))] + [fuzz.ratio(norm(q), norm(i[1])) for q in quotes]) for i in cand), reverse=True)
                if best and best[0] >= 60 and (len(scores) < 2 or scores[0] - scores[1] >= 10): loc = best[1]; how = 'within_lesson'
        proposed = ''
        if loc:
            sim = fuzz.ratio(nc, norm(loc[1])); ours = loc[1]
            al = fuzz.partial_ratio_alignment(c.lower(), ours.lower())
            frag = len(c) < 0.8 * len(ours) and al is not None and al.score >= 80
            if norm(ours) == nc: cls = 'already_correct'; proposed = ours
            elif frag:
                ds, de = al.dest_start, al.dest_end; ds0, de0 = ds, de
                while ds > 0 and ours[ds - 1].isalnum(): ds -= 1
                while de < len(ours) and ours[de].isalnum(): de += 1
                proposed = ours[:ds] + c + ours[de:]
                midword = (ds != ds0) or (de != de0)   # fix's ends fall inside our words: likely a truncated extraction
                cls = 'already_correct' if norm(proposed) == norm(ours) else ('fragment_midword' if midword else 'located_fragment')
            elif sim >= 50:
                proposed = c + (ours[-1] if ours[-1:] in '.?!' and c[-1:] not in '.?!' else '')
                cls = 'trivial_located' if not flags(c, ours) else 'located_flagged'
            else: cls = 'located_but_dissimilar'; proposed = c
            tgt = loc
        else:
            sim = fz[1]; tgt = fz[0]
            if norm(tgt[1]) == nc: cls = 'already_correct'
            elif sim >= 85 and sim - fz2 >= 10: cls = 'trivial_fuzzy' if not flags(c, tgt[1]) else 'fuzzy_flagged'
            elif key and not loc: cls = 'locator_missing_in_xml'
            else: cls = 'not_located'
        rows.append({**base, 'cls': cls, 'lesson': L, 'item': ('word %s' % wn.group(1)) if (is_word and wn) else (('sentence %s' % sn) if sn else ''),
                     'corrected': c, 'target_sid': tgt[0], 'target_text': tgt[1], 'similarity': round(sim, 1), 'proposed': proposed if loc else ((c + (tgt[1][-1] if tgt[1][-1:] in '.?!' and c[-1:] not in '.?!' else '')) if tgt[1] else ''), 'located_by': how or 'fuzzy', 'flags': ','.join(flags(c, tgt[1])) if tgt[1] else ''})
keys = ['section', 'did', 'dialect', 'seq', 'kind2', 'cls', 'located_by', 'flags', 'lesson', 'item', 'corrected', 'target_sid', 'target_text', 'proposed', 'similarity', 'material', 'result', 'file']
with open(out, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=keys, delimiter='\t', extrasaction='ignore'); w.writeheader(); w.writerows(rows)
C = collections.Counter(r['cls'] for r in rows)
print('correction units:', len(rows)); [print(f'  {k:<26}{v:>6}') for k, v in C.most_common()]
for sec in SEC: print(' ', sec, dict(collections.Counter(r['cls'] for r in rows if r['section'] == sec)))
