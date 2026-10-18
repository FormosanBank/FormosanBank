import sys, glob, re
sys.path.insert(0, '/workspace/Formosan-Robert-Blust-Thao-Dictionary/CodeAndDocs')
from lxml import etree
from build_review_page import render, E
OUT = "/tmp/claude-1000/-workspace-FormosanBank/0cb3cbf0-0934-4e90-aef3-6d6515ae698f/scratchpad/"
XML = "/workspace/Formosan-Robert-Blust-Thao-Dictionary/XML/"
NOT = re.compile(r"[()/~\[\]]")

def kind(form):
    if "/" in form and "(" in form: return "both"
    if "/" in form: return "alternation /"
    if "(" in form: return "optional ( )"
    return "other"

def hl(text):
    out = E(text)
    for ch in "()/~[]":
        out = out.replace(ch, f"<mark>{ch}</mark>")
    return out

rows = []
for f in sorted(glob.glob(XML + "Thao/*entries*.xml")):
    for s in etree.parse(f).getroot().findall("S"):
        form = s.find('FORM[@kindOf="original"]').text or ""
        if not NOT.search(form): continue
        tr = s.find("TRANSL")
        rows.append((s.get("id"), s.get("source"), form,
                     (tr.text or "") if tr is not None else "",
                     tr.get("notes") if tr is not None else None,
                     (s.find('FORM[@kindOf="original"]').get("notes"))))
rows.sort(key=lambda r: r[0])
groups, items = {}, []
for ident, src, form, eng, tnotes, fnotes in rows:
    k = kind(form); groups[k] = groups.get(k, 0) + 1
    page = re.search(r"p(\d{4})", ident).group(1).lstrip("0")
    parts = [p.strip() for p in form.split("/") if p.strip()] if "/" in form else []
    readings = "".join(
        f'<div class="row"><span class="lab n">reading {n}</span><span class="thao">{E(p)}</span></div>'
        for n, p in enumerate(parts, start=1))
    optional = ""
    if "(" in form:
        out_r = re.sub(r"\s*\([^()]*\)", "", form).strip()
        in_r = form.replace("(", "").replace(")", "")
        optional = (f'<div class="row"><span class="lab n">without</span><span class="thao">{E(out_r)}</span></div>'
                    f'<div class="row"><span class="lab n">with</span><span class="thao">{E(in_r)}</span></div>')
    items.append(
        f'<article class="entry" data-id="{E(ident)}" data-group="{E(k)}" '
        f'data-search="{E((form + " " + eng + " " + page).lower())}">'
        f'<header><span class="hw">{hl(form)}</span>'
        f'<span class="tag b">{E(k)}</span>'
        f'<span class="pg">p.{page} &middot; {E(ident)}</span></header>'
        f'<div class="row"><span class="lab">definition</span><span class="eng">{E(eng) or "&mdash;"}</span></div>'
        + (f'<div class="row"><span class="lab n">form note</span><span class="eng">{E(fnotes)}</span></div>' if fnotes else "")
        + (f'<div class="row"><span class="lab n">transl note</span><span class="eng">{E(tnotes)}</span></div>' if tnotes else "")
        + f'<div class="row"><span class="lab w">expanding would give</span></div>{readings}{optional}'
        f'<div class="row"><span class="pg">{E(src)}</span></div></article>')
n = render(OUT + "notation-forms.html",
    title="Headword Forms With Notation",
    eyebrow="Blust 2003 Thao Dictionary · lexicographic notation",
    heading="Two slashes that are not alternations",
    dek=("A headword form carrying lexicographic notation cannot be split into words without "
         "carrying the parenthesis or slash into a <code>W</code> FORM, which is "
         "<code>V121</code>&nbsp;HARD. So these <b>" + str(len(rows)) + "</b> sentences currently take "
         "<b>no word tier</b> at all (<code>V148</code>, SOFT) until the notation is expanded the way "
         "<code>expand_source.py</code> already expands the example sentences. Each card shows what "
         "expansion would give. The question per item is whether that reading is right &mdash; "
         "<i>(kay) p&ndash;acay</i> is plainly optional material, but <i>bizu(h)</i> may be one word "
         "spelt two ways rather than two forms."),
    footer="XML/Thao &middot; " + str(len(rows)) + " of the 309 sentences with no word tier; the other 272 are example sentences",
    verdicts=["strip the slashes", "keep as printed", "needs the page"],
    store="thao-notation",
    groups=[("ALL", len(rows), "")] + sorted(((k, v, "") for k, v in groups.items()), key=lambda g: -g[1]),
    items=items,
    resolved_heading='Every headword form resolved',
    resolved_note='It opened with <b>37</b> headword forms carrying lexicographic notation. A bracket attached to a word became a <code>ver="alt"</code> FORM, a bracketed particle stopped pairing with the English beside it, a slash in the definition split with the form, and the last two slashes were ruled typographical.')
print("notation-forms:", n, groups)
