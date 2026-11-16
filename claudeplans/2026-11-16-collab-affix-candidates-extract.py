import pathlib, re, json, collections, sys
import xml.etree.ElementTree as ET
XL='{http://www.w3.org/XML/1998/namespace}lang'
ISO={'ami':'Amis','tay':'Atayal','bnn':'Bunun','xnb':'Kanakanavu','ckv':'Kavalan','pwn':'Paiwan',
     'pyu':'Puyuma','dru':'Rukai','sxr':'Saaroa','xsy':'Saisiyat','szy':'Sakizaya','ssf':'Thao',
     'tsu':'Tsou','tao':'Yami'}
EXCL_LANGS={'Paiwan','Amis','Atayal','Yami'}
VOICE={'AV','PV','LV','OV','ACT','UV','UV1','UV2'}
EXCL_GLOSS={'IMP','STAT','NEG','CAUS','IRR','COS','CMPR','REFL','RECP','INVOL','DUR','MULT',
            'CFACT','IPFV','FUT','HORT','OPT','SBJV'}|VOICE
SPLIT=re.compile(r'[.\-=:<>\[\]()\s／/+~]+')
def atoms(t): return [a for a in SPLIT.split(t or '') if a]
def is_caps(a): return bool(re.search(r'[A-Z]',a)) and not re.search(r'[a-z]',a)
def lang_of(root):
    iso=root.get(XL) or ''
    if iso=='trv': return 'Truku' if root.get('dialect')=='Truku' else 'Seediq'
    return ISO.get(iso,iso)
def std(el, pref):
    # chosen standard gloss: eng standard if corpus has eng, else zho standard
    for lg in pref:
        for t in el.findall('TRANSL'):
            if t.get('kindOf')=='standard' and t.get(XL)==lg:
                return (t.text or '')+''.join(c.tail or '' for c in t)
    return ''
def transl_of(s):
    for lg in ('eng','zho'):
        for t in s.findall('TRANSL'):
            if t.get(XL)==lg and t.get('kindOf') is None:
                return t.text or ''
    for t in s.findall('TRANSL'):
        return t.text or ''
    return ''

corpora=[p.stem for p in pathlib.Path('Glossing/ConversionTables').glob('*.tsv') if not p.name.endswith('.rules.tsv')]
# per (lang, corpus): occurrences
tok=collections.defaultdict(collections.Counter)         # (lang,corpus,gloss)->count
forms=collections.defaultdict(collections.Counter)       # (lang,gloss)->form counts
srcs=collections.defaultdict(collections.Counter)        # (lang,gloss)->corpus counts
cooc=collections.defaultdict(set)                        # (lang,corpus,gloss)->set of co-occurring atoms
pairs=collections.defaultdict(set)                       # (lang,corpus,gloss)-> set of co-occurring NON-CAPS atoms
examples=collections.defaultdict(list)                   # (lang,gloss)->examples
caps_flag={}
for corpus in corpora:
    base=pathlib.Path('Corpora',corpus)
    if not base.exists(): continue
    files=list(base.rglob('*.xml'))
    # corpus tier preference
    has_eng=False
    for p in files[:40]:
        try: r=ET.parse(p).getroot()
        except Exception: continue
        for t in r.iter('TRANSL'):
            if t.get('kindOf')=='standard' and t.get(XL)=='eng': has_eng=True; break
        if has_eng: break
    pref=('eng','zho') if has_eng else ('zho','eng')
    for p in files:
        try: root=ET.parse(p).getroot()
        except Exception: continue
        lang=lang_of(root)
        if lang in EXCL_LANGS or not lang: continue
        for s in root.iter('S'):
            for w in s.findall('W'):
                ms=w.findall('M')
                units=[]   # (atoms, form) per gloss-bearing unit
                if ms:
                    for m in ms:
                        g=std(m,pref)
                        if g.strip():
                            f=next((x.text for x in m.findall('FORM') if x.text),'')
                            units.append((atoms(g),f))
                else:
                    g=std(w,pref)
                    if g.strip():
                        f=next((x.text for x in w.findall('FORM') if x.text),'')
                        units.append((atoms(g),f))
                allat=set(a for u,_ in units for a in u)
                if not (allat & VOICE): continue   # not a verb token
                wf=next((x.text for x in w.findall('FORM') if x.text),'')
                wg=std(w,pref) or ' '.join('-'.join(u) for u,_ in units)
                for u,f in units:
                    for a in set(u):
                        key=(lang,corpus,a)
                        tok[key][a]+=1
                        cooc[key] |= (allat-{a})
                        pairs[key] |= set(x for x in allat-{a} if not is_caps(x) and re.search(r'[a-zA-Z一-鿿]',x))
                        forms[(lang,a)][f or wf]+=1
                        srcs[(lang,a)][corpus]+=1
                        caps_flag[a]=is_caps(a)
                        if len(examples[(lang,a)])<12:
                            sf=next((x.text for x in s.findall('FORM') if x.get('kindOf')=='original' and x.text),'') or next((x.text for x in s.findall('FORM') if x.text),'')
                            examples[(lang,a)].append({'corpus':corpus,'s':(sf or '')[:110],'w':wf,'wg':wg[:60],'t':(transl_of(s) or '')[:110]})
# qualification
# diversity per (lang,corpus,gloss) for non-caps
div={k: len(cooc[k]) for k in cooc}
cand=collections.defaultdict(dict)
for (lang,corpus,a) in tok:
    if a in EXCL_GLOSS: continue
    if not re.search(r'[a-zA-Z一-鿿]',a): continue
    ok=False
    if caps_flag.get(a): ok=True
    else:
        # lowercase/lexical: qualifies if it co-occurs (same word) with another non-caps gloss of LOWER diversity
        mydiv=div.get((lang,corpus,a),0)
        for h in pairs.get((lang,corpus,a),()):
            if div.get((lang,corpus,h),0) < mydiv: ok=True; break
    if ok:
        cand[lang][a]=cand[lang].get(a,0)+sum(tok[(lang,corpus,a)].values())
out={}
for lang in sorted(cand):
    rows=[]
    for a,n in sorted(cand[lang].items(), key=lambda kv:-kv[1]):
        rows.append({'gloss':a,'caps':bool(caps_flag.get(a)),'n':n,
            'forms':forms[(lang,a)].most_common(8),
            'sources':srcs[(lang,a)].most_common(),
            'examples':examples[(lang,a)][:3]})
    out[lang]=rows
json.dump(out,open('/tmp/claude-1000/-workspace-FormosanBank/60537d4b-20d6-4615-9fc1-97174a4ba4aa/scratchpad/collab_candidates.json','w'),ensure_ascii=False,indent=1)
for lang in out: print(lang, len(out[lang]), 'candidates;', 'top:', ', '.join(r['gloss'] for r in out[lang][:8]))
