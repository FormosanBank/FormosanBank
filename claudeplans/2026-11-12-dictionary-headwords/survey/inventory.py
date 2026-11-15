import json,sys,collections,pathlib
d=pathlib.Path(sys.argv[1]); SKIP={'ch-mapping.json','index.json','stem-words.json'}
C=collections.Counter(); ex=collections.defaultdict(list); nh=collections.Counter()
for p in sorted(d.glob('*.json')):
    if p.name in SKIP: continue
    e=json.loads(p.read_text(encoding='utf-8')); C['entries']+=1
    nh[len(e.get('h',[]))]+=1
    for k,v in e.items():
        C['entry.'+k]+=1
        if k!='h' and len(ex['entry.'+k])<5: ex['entry.'+k].append((e['t'],v))
    for h in e.get('h',[]):
        for k,v in h.items():
            C['h.'+k]+=1
            if k!='d' and len(ex['h.'+k])<5: ex['h.'+k].append((e['t'],v))
        for df in h.get('d',[]):
            C['definitions']+=1
            for k,v in df.items():
                C['d.'+k]+=1
                if k not in('f','e') and len(ex['d.'+k])<6: ex['d.'+k].append((e['t'],df.get('f'),v))
            if not df.get('e'): C['d.without_examples']+=1
            if not df.get('f'): C['d.empty_or_missing_f']+=1
for k,v in sorted(C.items()): print(f'{v:7d} {k}')
print('heteronyms per entry:',dict(nh))
for k,v in ex.items():
    print('\n#',k)
    for x in v: print('   ',x)
