"""Extract correction rows from ePark errata PDFs (問題回報修改清冊) into one TSV.
usage: extract_errata.py ERRATA_DIR OUT_TSV"""
import sys, os, re, csv, glob, collections
import pdfplumber
d, out = sys.argv[1], sys.argv[2]
rows = []
for f in sorted(glob.glob(os.path.join(d, '*.pdf'))):
    sec, did = os.path.basename(f)[:-4].rsplit('_', 1)
    cur = None
    with pdfplumber.open(f) as pdf:
        for pno, p in enumerate(pdf.pages, 1):
            for t in p.extract_tables():
                for r in t:
                    c = [(x or '').replace('\n', ' ').strip() for x in r]
                    if len(c) < 6 or c[0].startswith('序號') or 'ＯＯ' in c[1]:
                        continue
                    if c[0] == '' and cur is not None:        # continuation of the previous row onto a new page
                        for k, v in enumerate(c[:7]):
                            if v: cur[k] = (cur[k] + ' ' + v).strip()
                        continue
                    if not re.match(r'^\d+$', c[0]):
                        continue
                    cur = (c + [''] * 7)[:7]
                    rows.append((sec, int(did), f, pno, cur))
def kind(res, ref):
    if re.search(r'無誤|不需修改|無需修改|維持原', res) and '應修訂為' not in res: return 'no_change'
    if re.search(r'中(字|文)翻譯|中譯|漢譯', res): return 'zh_translation'
    if '應修訂為' in res or '修訂為' in res: return 'formosan_or_mixed'
    return 'other'
with open(out, 'w', newline='') as fh:
    w = csv.writer(fh, delimiter='\t')
    w.writerow(['section', 'did', 'dialect', 'seq', 'material', 'report', 'result', 'status', 'handbook_page', 'kind', 'pdf', 'pdf_page'])
    for sec, did, f, pno, c in rows:
        w.writerow([sec, did, c[1], c[0], c[2], c[3], c[4], c[5], c[6], kind(c[4], c[2]), os.path.basename(f), pno])
C = collections.Counter((r[0]) for r in rows)
K = collections.Counter(kind(r[4][4], r[4][2]) for r in rows)
print('files:', len(glob.glob(os.path.join(d, '*.pdf'))), '| rows:', len(rows))
print('by section:', dict(C)); print('by kind:', dict(K))
print('dialects:', len(set((r[0], r[1]) for r in rows)))
