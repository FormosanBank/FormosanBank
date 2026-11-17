"""Second-pass classification of extracted errata rows. usage: classify_errata.py IN_TSV OUT_TSV"""
import csv, re, sys, collections
inp, out = sys.argv[1], sys.argv[2]
R = list(csv.DictReader(open(inp), delimiter='\t'))
import unicodedata
CJKSP = re.compile(r'(?<=[　-鿿＀-￯])\s+(?=[　-鿿＀-￯])')
def clean(s):  # NFKC folds Kangxi-radical lookalikes (⽣→生, ⽂→文); drop PDF line-break spaces between CJK chars
    return CJKSP.sub('', unicodedata.normalize('NFKC', s))
def kind(r):
    res, rep, mat = clean(r['result']), clean(r['report']), clean(r['material'])
    fix = re.search(r'應?修[訂正]為|改為|改成|更正為', res) or re.search(r'第\s*\d+\s*句\s*[:：]?\s*[A-Za-z’\']', res) or re.search(r'標題', res)
    if re.search(r'無誤|不需修[改正訂]|無需修[改正訂]|維持原|不予修[改正訂]|不修[改正訂]', res) and not fix: return 'no_change'
    if re.search(r'音檔|錄音|重錄|發音', res) and not re.search(r'[A-Za-z]{3,}[^。]*[.?!]', res.split('音檔')[0] if '音檔' in res else ''):
        if re.search(r'音檔[^。；;]*(錯誤|有誤|不一致|重錄)|重新錄製|重錄', res): return 'audio'
    if re.search(r'中(字|文)翻譯|中譯|漢譯|翻譯|華文|中文', res) and not re.search(r'族語', res[:20]): return 'zh_translation'
    if re.search(r'單字|詞彙|單詞', mat): return 'vocabulary'
    if fix and re.search(r'[A-Za-z]{2,}', res): return 'formosan_text'
    if fix: return 'other_fix'
    return 'unclassified'
for r in R: r['kind2'] = kind(r)
with open(out, 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=list(R[0].keys()), delimiter='\t'); w.writeheader(); w.writerows(R)
print('rows', len(R), '| dialect-section lists with rows', len(set((r['section'], r['did']) for r in R)))
secs = sorted(set(r['section'] for r in R)); kinds = ['formosan_text', 'vocabulary', 'zh_translation', 'audio', 'no_change', 'other_fix', 'unclassified']
C = collections.Counter((r['section'], r['kind2']) for r in R)
print(f'{"section":<15}' + ''.join(f'{k:>15}' for k in kinds) + f'{"total":>8}')
for s in secs: print(f'{s:<15}' + ''.join(f'{C[(s,k)]:>15}' for k in kinds) + f'{sum(C[(s,k)] for k in kinds):>8}')
print(f'{"ALL":<15}' + ''.join(f'{sum(C[(s,k)] for s in secs):>15}' for k in kinds) + f'{len(R):>8}')
