import glob,re,json,pathlib,collections,sys
sys.path.insert(0,sys.argv[1]+'/draft'); from safolu_headwords import clean,SPECIAL
SP=pathlib.Path(sys.argv[1])
CIRC='①②③④⑤⑥⑦⑧⑨'
norm=lambda s: re.sub(r'[^㐀-鿿A-Za-z\']','',s or '')
blocks=collections.defaultdict(list)
for f in sorted(glob.glob(str(SP/'src/printed/amis-safolu/dict/*.txt'))):
    t=open(f,encoding='utf-8',errors='replace').read().replace('\r','')
    for b in re.split(r'\n\s*\n',t):
        lines=[l for l in b.split('\n') if l.strip()]
        if not lines: continue
        hw=re.split(r'[（(]',lines[0].strip())[0].strip().lower()
        defs=[l.strip() for l in lines[1:] if not l.startswith((' ','\t'))]
        nsense=sum(l.count(c) for l in defs for c in CIRC) or 1
        blocks[hw].append({'file':pathlib.Path(f).name[:2],'defs':defs,'n':nsense})
C=collections.Counter(); ex=collections.defaultdict(list)
d=SP/'src/e7c6976/docs/s'
for p in sorted(d.glob('*.json')):
    if p.name in SPECIAL: continue
    e=json.loads(p.read_text()); H=e['h']
    hs=[[clean(x.get('f','')) for x in h.get('d',[])] for h in H]
    pb=blocks.get(e['t'].lower(),[])
    main=[b for b in pb if b['file'] not in ('23','24')]
    # distinct printed blocks by definition text
    distinct=[]
    for b in pb:
        k=norm(''.join(b['defs']))[:12]
        if k not in [norm(''.join(x['defs']))[:12] for x in distinct]: distinct.append(b)
    if len(H)==1:
        C['1 h']+=1
        if len(distinct)>1: C['1 h, but print has >1 DIFFERENT blocks']+=1; len(ex['1h_multi'])<8 and ex['1h_multi'].append((e['t'],hs,[b['defs'] for b in distinct]))
        continue
    C['>1 h']+=1
    same=[h for h in hs]; identical = all(norm(''.join(h))==norm(''.join(hs[0])) for h in hs)
    if identical: k='>1 h: all h identical (repeat)'
    elif len(distinct)==len(H): k='>1 h: as many distinct printed blocks as h (homophones in print)'
    elif not pb: k='>1 h: headword not found in print'
    elif len(distinct)==1: k='>1 h: print has ONE block'
    else: k=f'>1 h: other ({len(H)} h vs {len(distinct)} distinct blocks)'
    C[k]+=1; len(ex[k])<8 and ex[k].append((e['t'],hs,[(b['file'],b['defs']) for b in pb]))
for k,v in sorted(C.items()): print(f'{v:6d} {k}')
json.dump(ex,open(SP/'draft/homophone_examples.json','w'),ensure_ascii=False)
for k,v in ex.items():
    print('\n#',k)
    for x in v[:5]: print('   ',json.dumps(x,ensure_ascii=False)[:330])
