"""The 13 printed slashes whose expansion repeats material.

Every one of these is a slash between two alternants that say the same thing
in a different word order, so there is no shared frame to splice - but the
resolver found one, and the reading it built contains a word twice:

    printed   ruza pia-biskaw/pia-biskaw sa ruza
    reading   ruza pia-biskaw ruza

The one exception in the set is p.924, where the slash really does separate
two words inside a shared frame and the repeated `cicu` is the sentence's own.
A repeated token is therefore a detector, not a decision, which is why these
come to the maintainer rather than to a rule.
"""
import sys, glob, re, collections
sys.path.insert(0, '/workspace/Formosan-Robert-Blust-Thao-Dictionary/CodeAndDocs')
from lxml import etree
from build_review_page import render, E

OUT = "/tmp/claude-1000/-workspace-FormosanBank/0cb3cbf0-0934-4e90-aef3-6d6515ae698f/scratchpad/"
XML = "/workspace/Formosan-Robert-Blust-Thao-Dictionary/XML/"
READING = re.compile(r"reading (\d+) of (\d+) of '(.*)'$")

by_source = collections.OrderedDict()
for path in sorted(glob.glob(XML + "Thao/*examples*.xml")):
    for s in etree.parse(path).getroot().findall("S"):
        match = READING.search(s.get("source") or "")
        if not match or "/" not in match.group(3):
            continue
        form = (s.find('FORM[@kindOf="original"]').text or "").strip()
        transl = s.find("TRANSL")
        by_source.setdefault(match.group(3), []).append(
            (s.get("id"), int(match.group(1)), form,
             (transl.text or "") if transl is not None else "",
             transl.get("notes") if transl is not None else None))

def repeats(form):
    counts = collections.Counter(form.split())
    return sorted(t for t, n in counts.items() if n > 1 and len(t) > 2)

items = []
for printed, readings in by_source.items():
    if not any(repeats(form) for _id, _n, form, _e, _nt in readings):
        continue
    ident = readings[0][0]
    page = re.search(r"p(\d{4})", ident).group(1).lstrip("0")
    printed_parts = [p.strip() for p in printed.split("/") if p.strip()]
    built = "".join(
        f'<div class="row"><span class="lab{" w" if repeats(form) else ""}">reading {n}</span>'
        f'<span class="thao">{E(form)}</span>'
        + (f'<span class="lab n">repeats {E(", ".join(repeats(form)))}</span>' if repeats(form) else "")
        + "</div>"
        for _id, n, form, _e, _nt in sorted(readings, key=lambda r: r[1]))
    naive = "".join(
        f'<div class="row"><span class="lab">split on / gives</span>'
        f'<span class="thao">{E(p)}</span></div>'
        for p in printed_parts)
    english = readings[0][3]
    notes = readings[0][4]
    items.append(
        f'<article class="entry" data-id="{E(ident)}" data-group="example" '
        f'data-search="{E((printed + " " + english + " " + page).lower())}">'
        f'<header><span class="hw">{E(printed).replace("/", "<mark>/</mark>")}</span>'
        f'<span class="tag">printed</span>'
        f'<span class="pg">p.{page} &middot; {E(ident)}</span></header>'
        f'<div class="row"><span class="lab">english</span><span class="eng">{E(english) or "&mdash;"}</span></div>'
        + (f'<div class="row"><span class="lab n">note</span><span class="eng">{E(notes)}</span></div>' if notes else "")
        + f'<div class="row"><span class="lab w">the build produced</span></div>{built}'
        + naive
        + "</article>")

n = render(
    OUT + "slash-reorderings.html",
    title="Slashes That Reorder",
    eyebrow="Blust 2003 Thao Dictionary · slash scope",
    heading="Thirteen slashes whose expansion says a word twice",
    dek=("Blust separates acceptable alternatives with a slash, and the scope "
         "resolver expands one by finding what the two alternants share and "
         "splicing the rest between. That is right when the slash separates two "
         "words inside one frame. It is wrong when the alternants are the same "
         "sentence in a different word order, because then there is no frame - "
         "and the reading it builds contains a word twice. <b>Printed "
         "<i>ruza pia-biskaw/pia-biskaw sa ruza</i> came out "
         "<i>ruza pia-biskaw ruza</i>.</b> These are the "
         f"<b>{len(items)}</b> printed sources where some reading repeats a word. "
         "One of them, p.924, is not a defect: there the slash really does "
         "separate two words in a shared frame and the sentence says "
         "<i>cicu</i> twice on its own. So a repeated word is a detector, not a "
         "decision, and each of these needs a call. Each card shows what the "
         "build produced and what a plain split at the slash would give."),
    footer="XML/Thao &middot; 8,624 example sentences, 93 of them from a printed slash",
    verdicts=["split at the slash", "the build is right", "something else", "needs the page"],
    store="thao-slash-reorder",
    groups=[("ALL", len(items), "")],
    items=items,
    resolved_heading="Every reordering resolved",
    resolved_note="It opened with 13 printed sources whose expansion repeated a word.")
print("slash-reorderings:", n)
