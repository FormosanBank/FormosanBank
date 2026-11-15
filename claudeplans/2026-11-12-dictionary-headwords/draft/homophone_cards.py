import json,re,glob,pathlib,sys,collections,difflib,csv
SP=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(SP/'draft'))
from safolu_headwords import clean,SPECIAL
from build_page_data import safolu_render, S, NOT, uniq   # reuses renderers (re-runs builder; fine)
CIRC='①②③④⑤⑥⑦⑧⑨'
pr=collections.defaultdict(list)
for f in sorted(glob.glob(str(SP/'src/printed/amis-safolu/dict/*.txt'))):
    sec=pathlib.Path(f).name[:2]
    for b in re.split(r'\n\s*\n',open(f,encoding='utf-8',errors='replace').read().replace('\r','')):
        L=[l for l in b.split('\n') if l.strip()]
        if not L or L[0].startswith((' ','\t')): continue
        hw=re.split(r'[（(]',L[0].strip())[0].strip()
        pr[hw.lower()].append((sec,' '.join(l.strip() for l in L[1:] if not l.startswith((' ','\t')))))
def psenses(t):
    t=re.sub(r"(同|參見) ?[A-Za-z'^\- ,、]+。?",'',t).strip()
    parts=[p.strip() for p in re.split('['+CIRC+']',t) if p.strip()]
    return parts or [t]
n=lambda s: re.sub(r'[^㐀-鿿]','',s or '')
E={}
for p in (SP/'src/4cb8/docs/s').glob('*.json'):
    if p.name not in SPECIAL:
        e=json.loads(p.read_text()); E[e['t']]=e
pick=["deko","ngangiw","'edeng","pakayakayay","palalen","misa'atekak","ama","'adawang","na","kayki","kita","'angdisay","'emod","pinawnawan",
      "maamootay","pakafuti'","'atipen","macerar","palafosa","'a'adawangen","'adingo","'acis","'aliwac","micekos","mingihngihay","misacacakan"]
items=[]
for t in pick:
    e=E.get(t)
    if not e: continue
    hs=[[clean(x.get('f','')) for x in h.get('d',[])] for h in e['h']]
    allsenses=[s for h in hs for s in h]
    one=safolu_render(t,allsenses)
    perh=[]; seen=set()
    for h in hs:
        k=re.sub(r'\W','',''.join(h))
        if not k or k in seen: continue
        seen.add(k); r=safolu_render(t,h)
        if r!=NOT: perh+=r+[('','')]
    ents=[(s,d) for s,d in pr.get(t.lower(),[]) if s not in('23','24')] or pr.get(t.lower(),[])
    byp=[]
    for i,(s,d) in enumerate(ents,1):
        r=sorted(((difflib.SequenceMatcher(None,n(''.join(h)),n(d)).ratio(),j) for j,h in enumerate(hs)),reverse=True)
        ok=r and r[0][0]>=0.6 and (len(r)<2 or r[0][0]-r[1][0]>=0.15)
        byp+=[('FORM',f'{t}   [printed entry {i} of {len(ents)}, section {s}' + (']' if ok else '; upstream text not matched: needs a check]'))]+S(t,psenses(d))[1:]+[('','')]
    items.append({'key':t,'source':[f'section {s}: {d[:110]}' for s,d in pr.get(t.lower(),[])],
        'cells':{'print':one if len(ents)<2 else [x for x in byp if x!=('','')],'one':one,'perh':[x for x in perh if x!=('','')]}})
card={"id":"s-homophones","corpus":"Safolu","title":"One word with several senses, or two words spelled alike",
 "count":"882 headwords are printed as 2+ separate entries in one section of the book (plus 36 whose repeated entries are word-for-word identical); 326 of them match the upstream data cleanly, 556 do not",
 "question":"Should words spelled alike but printed as separate entries become separate S blocks?",
 "body":[
  "The printed dictionary (miaoski/amis-safolu dict/*.txt, f512d5b, the text the examples were checked against) marks senses of ONE word with ① ② ③ inside one entry, e.g. 'aca ① 只有 ② 即使…也… ③ 又，再. That signal is reliable: it is the author's own numbering.",
  "Words spelled alike are printed as separate entries, e.g. deko 袖手 / deko 泥蟹. But separate entries are NOT always different words: the book reprints the 680 '-initial entries in its ' section (file 23) and 616 loanwords in an appendix (file 24); it prints some words twice in one section (maamootay 發霉 twice, 'atipen word for word); and the ' section sometimes splits what the main section numbers as ①②: 'adingo is ① 影子 ② 靈魂 in section 01 but two entries in section 23. Telling these apart takes reading the definitions; a shared-wording test fails both ways (pinawnawan 水淹沒的地方 / 涮鍋的地點 share wording but are different words; macerar 山崩 / 倒塌 share none but are one word).",
  "Upstream's converter (generate-json-from-sqlite.rb:30) makes one h per printed entry paragraph and merges every same-spelled entry into one file, so the JSON's h list mixes all three kinds plus parse fragments (micekos has 7 h, some just 'micekosan（cekos）').",
  "For your Blust rulings: \"If the FORM notes both contain the word homograph, they are homophones, keep both\" and \"one word - merge as ver=alt\". Those were about Blust; this card decides Safolu.",
  "In the first option's column the translations shown are the printed text, so you can see the book's entries; the build would publish the matched upstream text. Rows below: chosen to show each kind (homophones first, then one word printed twice, then section-23 splits and parse fragments); 26 of the 882."],
 "options":[
  {"key":"print","label":"Follow the book's entries, check the rest","rec":True,"desc":"Senses ①②③ of one entry → one S. Separate entries in the same main section → separate S. Reprints in sections 23/24 → folded into the matching main entry. The 326 headwords that match cleanly are done automatically; the 556 that do not go on review cards grouped by kind before publishing."},
  {"key":"one","label":"One S per spelling","desc":"As in the draft: all senses of all same-spelled entries in one S. Homophones are merged into one block."},
  {"key":"perh","label":"One S per upstream entry (h)","desc":"Mechanical: 43,626 S, 1,087 headwords split. Separates homophones, but also gives reprints, reworded repeats and parse fragments their own S with the same spelling."}],
 "items":items}
# Fey
rows=list(csv.DictReader(open(SP/'main-ro/Corpora/Virginia_Fey_Dictionary/CodeAndDocs/source/virginia_fey_source.csv',encoding='utf-8')))
ents=[]
for r in rows:
    if r['詞條'].strip(): ents.append([r['詞條'].strip(),[]])
    if ents and (r['英文解釋'].strip() or r['中文解釋'].strip()): ents[-1][1].append((r['英文解釋'].strip(),r['中文解釋'].strip()))
fi=[]
for h,s in ents:
    if h in ("ha","sowal","'adidem","Alapawan","alapawan","Cikor","cikor","'afel"):
        fi.append({'key':h,'source':[f'{a} / {b}' for a,b in s],'cells':{'one':S(h,[b for a,b in s],[a for a,b in s])}})
fcard={"id":"f-homophones","corpus":"Fey","title":"One word with several senses, or two words spelled alike",
 "count":"1,024 of 4,848 headwords have 2+ senses; no headword is repeated (65 capitalised names such as Alapawan sit beside a lower-case alapawan as separate headwords already)",
 "question":"Fey's source gives no structural way to tell homophones from senses. Keep one S per headword?",
 "body":["Both the raw text (upstream h.txt etc.) and the sheet are one block per headword with its sense pairs under it: no numbering, no homograph mark, no repeated headwords. Some entries plainly mix different words, e.g. ha: 'a grammatical particle' / 'a thing used or planned to accomplish a task' / 'a prefix used in the south'. Separating them would be my judgement of meaning, not the source's structure.",
          "Capitalised names are separate headwords in the source (Alapawan vs alapawan) and so become separate S under any option."],
 "options":[
  {"key":"one","label":"One S per headword","rec":True,"desc":"All senses of a headword in one S (senses after the first ver=\"alt\"), as the source groups them."},
  {"key":"review","label":"Review the 1,024 multi-sense headwords","desc":"A review page where each multi-sense headword is marked 'one word' or 'split into separate words' by a person before publishing."}],
 "items":fi}
json.dump([card,fcard],open(SP/'draft/homophone_cards.json','w'),ensure_ascii=False)
print(len(items),len(fi))
for it in items[:2]+items[14:15]+items[23:24]:
    print('##',it['key']); [print('  ',k,v) for k,v in it['cells'].items()]
