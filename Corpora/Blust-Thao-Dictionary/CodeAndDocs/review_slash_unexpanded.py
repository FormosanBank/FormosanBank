import sys, glob, re, html
sys.path.insert(0, '/workspace/Formosan-Robert-Blust-Thao-Dictionary/CodeAndDocs')
from lxml import etree
from build_review_page import render, E
OUT = "/tmp/claude-1000/-workspace-FormosanBank/0cb3cbf0-0934-4e90-aef3-6d6515ae698f/scratchpad/"
XML = "/workspace/Formosan-Robert-Blust-Thao-Dictionary/XML/"

def load(pattern):
    out = []
    for f in sorted(glob.glob(XML + pattern)):
        for s in etree.parse(f).getroot().findall("S"):
            tr = s.find("TRANSL")
            out.append((s.get("id"), s.get("source"),
                        (s.find('FORM[@kindOf="original"]').text or ""),
                        (tr.text or "") if tr is not None else "",
                        tr.get("notes") if tr is not None else None))
    return out

def hl(text):
    return E(text).replace("/", '<mark>/</mark>')

def naive(form):
    return [p.strip() for p in form.split("/") if p.strip()]

items, groups = [], {"example": 0, "headword form": 0}
rows = [(i, src, fo, en, nt, "example") for i, src, fo, en, nt in load("Thao/*examples*.xml") if "/" in fo]
rows += [(i, src, fo, en, nt, "headword form") for i, src, fo, en, nt in load("Thao/*entries*.xml") if "/" in fo]
rows.sort(key=lambda r: r[0])
for ident, src, form, eng, notes, kind in rows:
    groups[kind] += 1
    parts = naive(form)
    readings = "".join(
        f'<div class="row"><span class="lab n">reading {n}</span>'
        f'<span class="thao">{E(p)}</span></div>'
        for n, p in enumerate(parts, start=1)
    )
    page = re.search(r"p(\d{4})", ident).group(1).lstrip("0")
    items.append(
        f'<article class="entry" data-id="{E(ident)}" data-group="{E(kind)}" '
        f'data-search="{E((form + " " + eng + " " + page).lower())}">'
        f'<header><span class="hw">{hl(form)}</span>'
        f'<span class="tag{"" if kind=="example" else " b"}">{E(kind)}</span>'
        f'<span class="pg">p.{page} &middot; {E(ident)}</span></header>'
        f'<div class="row"><span class="lab">english</span><span class="eng">{E(eng) or "&mdash;"}</span></div>'
        + (f'<div class="row"><span class="lab n">note</span><span class="eng">{E(notes)}</span></div>' if notes else "")
        + f'<div class="row"><span class="lab w">split on / gives</span></div>{readings}'
        f'<div class="row"><span class="pg">{E(src)}</span></div>'
        "</article>"
    )
n = render(OUT + "slash-unexpanded.html",
    title="Unexpanded Slash Alternations",
    eyebrow="Blust 2003 Thao Dictionary · slash scope",
    heading="Three slashes still unresolved",
    dek=("Blust separates acceptable alternatives with a slash. <b>" + str(len(rows)) + "</b> of them are "
         "still unexpanded in the entry build, so those sentences carry the slash into the FORM and take "
         "no word tier. Expanding them needs the <b>scope</b>, and only the page settles it: in "
         "<i>cumay a huqi/huqi a cumay</i> the slash separates two whole phrases, but in "
         "<i>antu/ani yaku tu ma-cakaw, Lujan sa ma-cakaw</i> it separates only the first word and the "
         "rest is shared. Each card shows what a naive split on the slash would give &mdash; where that "
         "is wrong, say what the slash actually ranges over."),
    footer="XML/Thao; the other 104 are expanded, sharing or splitting their English as the scope requires" + str(len(rows)) + " slash-bearing FORMs &middot; NTU scopes a slash to the morpheme; Song-Kanakanavu splits on / ; and ( )",
    verdicts=["naive split is right", "shared material", "not an alternation", "needs the page"],
    store="thao-slash",
    groups=[("ALL", len(rows), "")] + [(k, v, "") for k, v in groups.items() if v],
    items=items,
    resolved_heading='Every slash resolved',
    resolved_note="It opened with <b>107</b> slash-bearing FORMs. The scope resolver settles all but four; those four are curated from the maintainer's own readings.")
print("slash-unexpanded:", n)
