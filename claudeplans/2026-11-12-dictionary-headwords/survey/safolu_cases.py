import json,sys,pathlib,re,collections
d=pathlib.Path(sys.argv[1]); SKIP={'ch-mapping.json','index.json','stem-words.json'}
CJK=re.compile(r'[㐀-鿿]')
def clean(f): return f.replace('`','').replace('~','').strip()
XREF=re.compile(r'^(同|參見|參閱|參看|詳見|見|即)\s*')
C=collections.Counter(); ex=collections.defaultdict(list)
def add(k,x):
    C[k]+=1
    if len(ex[k])<10: ex[k].append(x)
for p in sorted(d.glob('*.json')):
    if p.name in SKIP: continue
    e=json.loads(p.read_text(encoding='utf-8')); t=e['t']
    if t.startswith('-') or t.endswith('-'): add('affix headword (leading/trailing -)',t)
    if ' ' in t.strip(): C['multi-word headword']+=1
    live=0
    for h in e['h']:
        nm=h.get('name')
        if nm and nm!=t: add('heteronym with a different name form',(t,nm))
        for df in h.get('d',[]):
            f=clean(df.get('f',''))
            if not f: C['empty sense']+=1; continue
            body=XREF.sub('',f)
            if XREF.match(f) and not CJK.search(body): add('sense = cross-reference only',(t,df['f'])); continue
            stripped=re.sub(r'〔[^〕]*〕|\[[^\]]*\]','',f).strip(' 。.')
            if not stripped: add('sense = label only (〔…〕)',(t,df['f'])); continue
            if not CJK.search(f): add('sense with no Chinese at all',(t,df['f'])); 
            if XREF.match(f): add('sense starts 同/參見 but has more Chinese',(t,df['f']))
            if re.search(r'[A-Za-z]{2,}',f): add('sense contains Amis/Latin words',(t,df['f']))
            live+=1
    if live==0: add('headword with NO usable sense',(t,[x.get('f') for h in e['h'] for x in h.get('d',[])]))
for k,v in C.items(): print(f'{v:6d} {k}')
for k,v in ex.items():
    print('\n#',k)
    for x in v: print('   ',x)
