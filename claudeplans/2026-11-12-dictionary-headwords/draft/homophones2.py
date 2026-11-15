import glob,re,json,pathlib,collections,sys
SP=pathlib.Path(sys.argv[1])
blocks=collections.defaultdict(list)
for f in sorted(glob.glob(str(SP/'src/printed/amis-safolu/dict/*.txt'))):
    sec=pathlib.Path(f).name[:2]
    t=open(f,encoding='utf-8',errors='replace').read().replace('\r','')
    for b in re.split(r'\n\s*\n',t):
        lines=[l for l in b.split('\n') if l.strip()]
        if not lines or lines[0].startswith((' ','\t')): continue
        hw=re.split(r'[（(]',lines[0].strip())[0].strip()
        defs=' '.join(l.strip() for l in lines[1:] if not l.startswith((' ','\t')))
        blocks[hw.lower()].append((sec,hw,defs))
C=collections.Counter(); groups=[]
for hw,bs in blocks.items():
    per=collections.Counter(s for s,_,_ in bs)
    secs=set(per)
    mx=max(per.values())
    C['printed headwords']+=1
    if mx>1:
        C['>=2 entries in one section (homophones by the rule)']+=1
        same=[s for s,n in per.items() if n>1][0]
        texts=[d for s,_,d in bs if s==same]
        if len(set(re.sub(r'\W','',x) for x in texts))==1: C['   ...but the entries are word-for-word identical']+=1; k='identical'
        else: k='differ'
        groups.append((hw,k,[(s,h,d[:70]) for s,h,d in bs]))
    if len(secs)>1: C['printed in >1 section']+=1
    if len(secs)>1 and mx==1: C['   ...only as reprints (1 entry per section)']+=1
    if any(h!=bs[0][1] for _,h,_ in bs): C['entries differ only in capitalisation']+=1
for k,v in C.items(): print(f'{v:6d} {k}')
print('section counts:',collections.Counter(s for bs in blocks.values() for s,_,_ in bs).most_common())
json.dump(groups,open(SP/'draft/homophone_groups.json','w'),ensure_ascii=False)
import random; random.seed(3)
for g in [x for x in groups if x[1]=='differ'][:4]+random.sample([x for x in groups if x[1]=='differ'],12)+[x for x in groups if x[1]=='identical'][:4]:
    print(json.dumps(g,ensure_ascii=False)[:300])
