import json,sys,collections,pathlib,re,random
d=pathlib.Path(sys.argv[1]); SKIP={'ch-mapping.json','index.json','stem-words.json'}
C=collections.Counter(); ex=collections.defaultdict(list)
pats={'backtick_link':r'`[^~]*~','latin_word':r'[A-Za-z\']{2,}','lenticular〔〕':r'〔[^〕]*〕','paren_full（）':r'（[^）]*）','paren_ascii()':r'\([^)]*\)','square[]':r'\[[^\]]*\]','FFFx_marker':r'[￹￺￻]','no_final_。':r'[^。！？」]$','starts 同/見/參':r'^(同|見|參|即)','contains 同/見':r'(同|見|參見)`'}
random.seed(1)
for p in sorted(d.glob('*.json')):
    if p.name in SKIP: continue
    e=json.loads(p.read_text(encoding='utf-8'))
    for h in e.get('h',[]):
        for df in h.get('d',[]):
            f=df.get('f','')
            if not f: continue
            C['nonempty f']+=1
            for k,pt in pats.items():
                if re.search(pt,f):
                    C[k]+=1
                    if len(ex[k])<6: ex[k].append((e['t'],f))
br=collections.Counter()
for p in sorted(d.glob('*.json')):
    if p.name in SKIP: continue
    e=json.loads(p.read_text(encoding='utf-8'))
    for h in e.get('h',[]):
        for df in h.get('d',[]):
            for m in re.findall(r'〔[^〕]*〕',df.get('f','')): br[m]+=1
for k,v in sorted(C.items()): print(f'{v:7d} {k}')
print('\n〔〕 labels:',br.most_common(25))
for k,v in ex.items():
    print('\n#',k)
    for x in v: print('   ',x)
