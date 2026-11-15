"""Build the dialect-location report page (round 1, with responses) from rows.py + counts + the list TSV."""
import csv, html, json, re, sys, collections, importlib.util
from pathlib import Path

HERE = Path(__file__).parent
SP = HERE.parent
spec = importlib.util.spec_from_file_location("rows", HERE / "rows.py"); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)

counts = {}
for line in (SP / "published_dialect_counts.txt").read_text().splitlines():
    if line.startswith("--- dialect-labelled files outside"): break
    m = re.match(r"\s*(\d+)\s+(\S+)\s+(\S+)\s+(\S+)$", line)
    if m: counts[(m.group(2), m.group(3), m.group(4))] = int(m.group(1))
assert len(counts) == 57, len(counts)

# coverage: every corpus x label exactly once across cards, not-found items, not-listed
seen = collections.Counter()
for r in R.ROWS: seen.update(r["keys"])
for it in R.NOTFOUND_ITEMS: seen.update(it["keys"])
for k, _ in R.NOTLISTED: seen[k] += 1
bad = ([k for k in counts if seen[k] == 0], [k for k in seen if k not in counts], [k for k, v in seen.items() if v > 1])
if any(bad): sys.exit(f"COVERAGE FAIL missing/extra/dup = {bad}")

listrows = list(csv.DictReader(open(SP / "dialect_locations.tsv"), delimiter="\t"))
E = html.escape
VERDICT = collections.OrderedDict([
  ("nomatch", ("Doesn’t match", "bad")), ("partial", ("Partly matches", "warn")),
  ("village", ("Matches: village or community named", "ok")), ("township", ("Matches: township only", "ok2")),
  ("county", ("Only the county is known", "mid")), ("unplaced", ("Places named, but I can’t place them on the list", "mid")),
  ("notfound", ("No location found", "none")), ("notlisted", ("Language not in the list", "none")),
])
LINK = {"source": "source’s own words", "roman": "my reading of a romanized name",
        "outside": "my outside knowledge of a place", "secondhand": "our own summary of a source I couldn’t see"}

def units_of(v):
    if v == "notfound": return [k for it in R.NOTFOUND_ITEMS for k in it["keys"]]
    if v == "notlisted": return [k for k, _ in R.NOTLISTED]
    return [k for r in R.ROWS if r["verdict"] == v for k in r["keys"]]
def label(k): return f"{k[1]} · {k[2]}"

tally_rows, tot_u, tot_f = [], 0, 0
for v, (name, cls) in VERDICT.items():
    us = units_of(v); f = sum(counts[k] for k in us); tot_u += len(us); tot_f += f
    tally_rows.append(f'<tr><td><span class="pill {cls}">{E(name)}</span></td><td class="n">{len(us)}</td><td class="n">{f:,}</td><td>{E(", ".join(sorted({k[0] for k in us})))}</td></tr>')
assert tot_u == 57 and tot_f == sum(counts.values())

ITEMS = {}  # id -> list of question keys (for the page's tally)
def respond(iid, questions):
    ITEMS[iid] = [q["key"] for q in questions]
    qs = []
    for q in questions:
        opts = "".join(
            f'<button type="button" class="opt" data-item="{E(iid)}" data-q="{E(q["key"])}" data-opt="{E(k)}" aria-pressed="false">'
            f'<span class="ol">{E(lbl)}</span><span class="od">{E(eff)}</span></button>' for k, lbl, eff in q["options"])
        qs.append(f'<fieldset class="q"><legend>{E(q["prompt"])}</legend><div class="opts">{opts}</div></fieldset>')
    return (f'<div class="respond" data-item="{E(iid)}"><div class="rhead"><h4>Your response</h4><span class="saved" data-saved="{E(iid)}"></span></div>'
            + "".join(qs) +
            f'<label class="note"><span>Note (optional)</span><textarea id="note-{E(iid)}" data-note="{E(iid)}" rows="2" placeholder="Anything I should know, or the wording you want"></textarea></label></div>')

def proposed(text):
    return f'<div class="proposed"><h4>README text I would propose (not added)</h4><p>{E(text)}</p></div>' if text else ""

def card(r):
    name, cls = VERDICT[r["verdict"]]
    files = sum(counts[k] for k in r["keys"]); corpora = sorted({k[0] for k in r["keys"]})
    chips = "".join(f'<span class="chip">{E(LINK[l])}</span>' for l in r["link"])
    ev = "".join(f'<li><q>{E(q)}</q><span class="where">{E(w)}</span></li>' for q, w in r["evidence"])
    return f'''
<article class="card {cls} item" id="{E(r["id"])}" data-item="{E(r["id"])}">
  <header><span class="pill {cls}">{E(name)}</span><h3>{E(r["title"])}</h3>
    <p class="meta"><b>{E(" / ".join(corpora))}</b> · {E(", ".join(label(k) for k in r["keys"]))} · {files:,} published file{"s" if files != 1 else ""}{" · linked to the list by: " + chips if chips else ""}</p></header>
  <div class="cols">
    <section><h4>What the source says</h4><ul class="ev">{ev}</ul><p class="small"><b>Places named:</b> {E(r["places"])}</p></section>
    <section><h4>What the list says</h4><p>{E(r["listsays"])}</p><h4>What the README says now</h4><p>{E(r["readme"])}</p></section>
  </div>
  <p class="caveat"><b>Caveats:</b> {E(r["caveat"])}</p>
  {proposed(r.get("add",""))}
  {respond(r["id"], r["questions"])}
</article>'''

def nfcard(it):
    rows = "".join(f'<tr><td><b>{E(k[0])}</b><br><span class="small">{E(label(k))} · {counts[k]:,} file{"s" if counts[k]!=1 else ""}</span></td><td>{E(why)}</td><td>{E(where)}</td></tr>' for k, why, where in it["why"])
    return f'''
<article class="card none item" id="{E(it["id"])}" data-item="{E(it["id"])}">
  <header><span class="pill none">No location found</span><h3>{E(it["title"])}</h3></header>
  <div class="tablewrap"><table><thead><tr><th>Corpus · label</th><th>What I found</th><th>Where it would be</th></tr></thead><tbody>{rows}</tbody></table></div>
  {proposed(it.get("add",""))}
  {respond(it["id"], it["questions"])}
</article>'''

sections = []
for v in ["nomatch", "partial", "village", "township", "county", "unplaced"]:
    rs = [r for r in R.ROWS if r["verdict"] == v]
    if rs:
        n = len(units_of(v))
        sections.append(f'<h2 id="{v}">{E(VERDICT[v][0])} <span class="count">{n} label{"s" if n != 1 else ""}</span></h2>' + "".join(card(r) for r in rs))

noticed = "".join(f'''
<article class="card mid item" id="{E(it["id"])}" data-item="{E(it["id"])}"><header><h3>{E(it["title"])}</h3></header>{respond(it["id"], it["questions"])}</article>''' for it in R.NOTICED_ITEMS)
ITEMS["general"] = []  # note-only item; not counted in the tally
nl = "".join(f'<tr><td><b>{E(k[0])}</b></td><td>{E(label(k))}</td><td class="n">{counts[k]}</td><td>{E(lang)}</td></tr>' for k, lang in R.NOTLISTED)
listtable = "".join(f'<tr><td>{E(r["language"])}</td><td>{E(r["dialect"])}</td><td>{E(r["county"])}</td><td>{E(r["township"])}</td><td>{E(r["villages"])}</td><td class="n">{r["pdf_page"]}</td></tr>' for r in listrows)

page = (HERE / "template.html").read_text()
for key, val in {
    "{{TALLY}}": "".join(tally_rows), "{{TOT_FILES}}": f"{tot_f:,}", "{{SECTIONS}}": "".join(sections),
    "{{NOTFOUND_ITEMS}}": "".join(nfcard(it) for it in R.NOTFOUND_ITEMS), "{{NOTFOUND_N}}": str(len(units_of("notfound"))),
    "{{NOTICED_ITEMS}}": noticed, "{{NOTLISTED}}": nl, "{{LISTTABLE}}": listtable, "{{LIST_N}}": str(len(listrows)),
    "{{ITEMS_JSON}}": json.dumps({k: v for k, v in ITEMS.items() if v}, ensure_ascii=False),
    "{{N_ITEMS}}": str(sum(1 for v in ITEMS.values() if v)),
}.items():
    assert key in page, key
    page = page.replace(key, val)
assert not re.findall(r"\{\{[A-Z_]+\}\}", page)
out = HERE / "dialect-locations.html"; out.write_text(page)
print("wrote", out, len(page), "bytes;", sum(1 for v in ITEMS.values() if v), "answerable items;", tot_u, "labels;", tot_f, "files")
