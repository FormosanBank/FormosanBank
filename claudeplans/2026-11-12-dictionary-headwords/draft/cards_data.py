import json,re,csv,pathlib,collections,sys
sys.path.insert(0,sys.argv[1]+'/draft')
from safolu_headwords import clean, classify, SPECIAL
SP=pathlib.Path(sys.argv[1])
A=SP/'src/e7c6976/docs/s'; B=SP/'src/4cb8/docs/s'
def load(d): return {p.name:json.loads(p.read_text(encoding='utf-8')) for p in d.glob('*.json') if p.name not in SPECIAL}
EA,EB=load(A),load(B)
def senses(e): return [clean(df.get('f','')) for h in e.get('h',[]) for df in h.get('d',[])]
out={}
# S1 version
chg=[]; 
for n in sorted(set(EA)&set(EB)):
    a,b=senses(EA[n]),senses(EB[n])
    if a!=b: chg.append({'hw':EA[n]['t'],'old':a,'new':b})
out['s_pin_changed']=chg
out['s_pin_added']=[{'hw':EB[n]['t'],'senses':senses(EB[n])} for n in sorted(set(EB)-set(EA))]
# per-sense categories at pin B
cat=collections.defaultdict(list)
CJK=re.compile(r'[㐀-鿿]')
for n in sorted(EB):
    e=EB[n]; ss=senses(e)
    for s in ss:
        k=classify(s)
        others=[x for x in ss if x!=s and classify(x)=='ok']
        if k in('xref','label','nochinese'): cat[k].append({'hw':e['t'],'sense':s,'other':others})
        if k=='ok':
            m=re.match(r"^([A-Za-z'^ ,.!?\-]+?)[.!?]?\s*([㐀-鿿].*)$",s)
            if m and len(m.group(1).split())>=3: cat['embedded'].append({'hw':e['t'],'sense':s,'amis':m.group(1).strip(),'zho':m.group(2).strip(),'other':others})
            if re.search(r'[：:]\s*$',s): cat['heading'].append({'hw':e['t'],'sense':s,'all':ss})
            if re.search(r'[〔〈][^〕〉]*借詞[〕〉]',s): cat['borrow'].append({'hw':e['t'],'sense':s})
    t=e['t']
    if t.startswith('-') or t.endswith('-') or '…' in t: cat['affix'].append({'hw':t,'senses':ss})
    if e.get('stem') or e.get('tag'): cat['stemtag'].append({'hw':t,'stem':e.get('stem',''),'tag':e.get('tag','')})
    sr=[(k,clean(w)) for h in e['h'] for df in h.get('d',[]) for k in ('s','r') for w in (df.get(k) or [])]
    if sr: cat['synrel'].append({'hw':t,'s':[w for k,w in sr if k=='s'],'r':[w for k,w in sr if k=='r']})
for k,v in cat.items(): out['s_'+k]=v
# Fey
rows=list(csv.DictReader(open(SP/'main-ro/Corpora/Virginia_Fey_Dictionary/CodeAndDocs/source/virginia_fey_source.csv',encoding='utf-8')))
ents=[]
for line,r in enumerate(rows,2):
    h=r['詞條'].strip()
    if h: ents.append({'hw':h,'line':line,'senses':[],'see':[]})
    if not ents: continue
    e,z=r['英文解釋'].strip(),r['中文解釋'].strip()
    if e or z: ents[-1]['senses'].append([e,z])
    if r['參見'].strip(): ents[-1]['see'].append(r['參見'].strip())
XE=re.compile(r"^(refer to|see)\s+\S+\.?$",re.I); XZ=re.compile(r"^(詳見|參見|參看|參閱|見)\s*[A-Za-z'^ ,\-]+[。.]?$")
out['f_xref']=[x for x in ents if any(XE.match(e) or XZ.match(z) for e,z in x['senses'])]
out['f_fixme']=[x for x in ents if any('FIXME' in z or 'FIXME' in e for e,z in x['senses'])]
out['f_affix']=[x for x in ents if x['hw'].startswith('-') or x['hw'].endswith('-')]
out['f_see']=[x for x in ents if x['see']]
out['f_split']=[x for x in ents if any('*' in e or re.search('[，、]',z) for e,z in x['senses'])]
out['f_all_count']=len(ents)
json.dump(out,open(SP/'draft/cards.json','w'),ensure_ascii=False)
for k,v in out.items(): print(k, len(v) if isinstance(v,list) else v)
