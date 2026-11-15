import json,sys,pathlib,collections
SKIP={'ch-mapping.json','index.json','stem-words.json'}
def load(d):
    out={}
    for p in pathlib.Path(d).glob('*.json'):
        if p.name in SKIP: continue
        e=json.loads(p.read_text(encoding='utf-8'))
        out[p.name]=e
    return out
A=load(sys.argv[1]); B=load(sys.argv[2])
def senses(e): return [(h.get('name',''),df.get('f','')) for h in e.get('h',[]) for df in h.get('d',[])]
C=collections.Counter(); ex=collections.defaultdict(list)
C['files_old']=len(A); C['files_new']=len(B)
for n in sorted(set(B)-set(A)):
    C['headword_added']+=1
    if len(ex['added'])<8: ex['added'].append((B[n]['t'],[f for _,f in senses(B[n])]))
for n in sorted(set(A)-set(B)): C['headword_removed']+=1; ex['removed'].append(A[n]['t'])
for n in sorted(set(A)&set(B)):
    a,b=A[n],B[n]
    if a==b: continue
    C['file_changed']+=1
    if senses(a)==senses(b): C['changed_examples_only_or_s/r/stem']+=1
    else:
        C['definitions_changed']+=1
        if len(ex['defs'])<12: ex['defs'].append((a['t'],senses(a),senses(b)))
for k,v in C.items(): print(f'{v:7d} {k}')
for k,v in ex.items():
    print('\n#',k)
    for x in v: print('  ',x)
