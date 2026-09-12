"""Sentences that share a spelling but not a meaning.

After the dedup, what is left is 171 groups where two (twice, three) published
sentences have the same FORM and different TRANSL. The shared remover no longer
touches them - it requires the gloss to match - and
validate_duplicate_sentences reports them SOFT. Each is one of two things and
only a reader can say which:

  homophones            two words that happen to be spelt alike, like Blust's
                        `a` the future marker and `a` the linking particle.
                        Both entries stay.
  one word, two glosses the same word glossed twice in different words, or with
                        two senses the book prints separately. One S, the second
                        gloss becoming a ver="alt" TRANSL (POL-025).
"""
import sys, glob, json, collections
from pathlib import Path
sys.path.insert(0, '/workspace/Formosan-Robert-Blust-Thao-Dictionary/CodeAndDocs')
from lxml import etree
from build_review_page import render, E, card_id

OUT = "/tmp/claude-1000/-workspace-FormosanBank/0cb3cbf0-0934-4e90-aef3-6d6515ae698f/scratchpad/"
XML = "/workspace/Formosan-Robert-Blust-Thao-Dictionary/XML/Thao/"
XL = "{http://www.w3.org/XML/1998/namespace}lang"

#: Every verdict the maintainer has given, keyed by the group's FORM.
#: apply_same_form_rulings.py is what acts on these; the page reads the same
#: file so a ruled group stops being a question the moment it is recorded.
RULINGS = json.loads(
    (Path(__file__).resolve().parent / "same-form-rulings.json")
    .read_text(encoding="utf-8")
)
RULED = {r["form"]: r["action"] for r in RULINGS["rulings"]}


def both_marked_homograph(members) -> bool:
    """Blust subscripted BOTH, so they are two words (maintainer, 2026-09-11).

    "If the FORM notes both contain the word 'homograph', they are homophones,
    keep both." The `both` is what does the work: where only one member carries
    the note, the note is about that entry's ROOT being a homograph and says
    nothing about this pair - `kawi a filhaq` "leaf of a tree" against "leaves
    of a tree" is one word glossed twice, not two words. 50 groups qualify, 9
    have the note on one side only and stay open.
    """
    return all("Homograph" in notes_of(s) for _kind, s in members)

groups = collections.defaultdict(list)
for path in sorted(glob.glob(XML + "*.xml")):
    kind = ("entry" if "_entries_" in path
            else "example" if "_examples_" in path else "text")
    for s in etree.parse(path).getroot().findall("S"):
        form = s.find('FORM[@kindOf="standard"]')
        if form is None or not (form.text or "").strip():
            form = s.find('FORM[@kindOf="original"]')
        key = " ".join((form.text or "").split())
        if key:
            groups[key].append((kind, s))

def notes_of(s):
    out = []
    for f in s.findall("FORM"):
        if f.get("notes"):
            out.append(f.get("notes"))
    return " | ".join(out)

items, kinds = [], collections.Counter()
settled_by_pattern = 0
for key, members in sorted(groups.items()):
    if len(members) < 2:
        continue
    glosses = {" ".join((t.text or "").split())
               for _k, s in members for t in s.findall("TRANSL")}
    if len(glosses) < 2:
        continue
    if key in RULED:
        continue
    if both_marked_homograph(members):
        settled_by_pattern += 1
        continue
    # A homograph subscript in the book is the strongest single clue, so say so.
    # Only ONE side is subscripted here: `both` already left the page. A
    # one-sided note is about that entry's root, not about this pair.
    marked = any("Homograph" in notes_of(s) for _k, s in members)
    group = ("one side subscripted" if marked
             else "example" if all(k == "example" for k, _s in members)
             else "entry")
    kinds[group] += 1
    rows = []
    for kind, s in members:
        transl = s.findall("TRANSL")
        rows.append(
            f'<div class="row"><span class="lab n">{E(kind)}</span>'
            f'<span class="pg">{E(s.get("id"))}</span></div>'
            + "".join(
                f'<div class="row"><span class="lab">gloss</span>'
                f'<span class="eng">{E(" ".join((t.text or "").split()))}</span></div>'
                for t in transl)
            + (f'<div class="row"><span class="lab n">form notes</span>'
               f'<span class="eng">{E(notes_of(s))}</span></div>'
               if notes_of(s) else "")
            + f'<div class="row"><span class="pg">{E(s.get("source"))}</span></div>')
    items.append(
        f'<article class="entry" data-id="{E(members[0][1].get("id"))}__sameform" '
        f'data-db-id="{E(ident)}" data-group="{E(group)}" '
        f'data-search="{E((key + " " + " ".join(glosses)).lower())}">'
        f'<header><span class="hw">{E(key)}</span>'
        f'<span class="tag{"" if group == "entry" else " b"}">{E(group)}</span>'
        f'<span class="pg">{len(members)} sentences &middot; '
        f'{len(glosses)} glosses</span></header>'
        + "<hr style='border:0;border-top:1px solid var(--rule);margin:9px 0'>".join(rows)
        + "</article>")

n = render(
    OUT + "same-form-other-gloss.html",
    title="One Spelling, Two Meanings",
    eyebrow="Blust 2003 Thao Dictionary · after the dedup",
    heading=f"{len(items)} spellings with more than one meaning",
    dek=(f"The dictionary dedups: where two published sentences had the same "
         "FORM <i>and</i> the same gloss, one was removed. What was left was 171 "
         "groups sharing a spelling but not a meaning, and two patterns from the "
         "maintainer have closed most of them.<br><br>"
         "<b>Both sides subscripted &rarr; two words.</b> Where Blust printed a "
         "homograph subscript on <i>both</i> members they are homophones and "
         "both stay &mdash; <b>50 groups</b>, settled without a card. The "
         "<i>both</i> is what does the work: a note on one side only is about "
         "that entry's root, and says nothing about the pair.<br><br>"
         "<b>A grammatical label is not a definition.</b> <i>\u201c(PF) by "
         "oneself\u201d</i> had the label inside the gloss, so the same word "
         "read two ways. Blust sets the label in its own face, but a compound "
         "one - <code>[AFc; PFc]</code>, <code>[F; atemporal]</code> - can "
         "arrive in the definition face, and on printed p.291 even the simple "
         "ones do; <code>clean_xml</code> then turned the square brackets round. "
         "<b>24 definitions</b> fixed, and 6 of these groups closed with them."
         "<br><br>What is left is what neither pattern reaches."),
    footer="XML/Thao after step 6b &middot; 16,540 S &middot; "
           "the groups are all size 2 but two, which have three",
    verdicts=["homophones - keep both", "one word - merge as ver=alt",
              "something else", "needs the page"],
    store="thao-same-form",
    groups=[("ALL", len(items), "")] + [(k, v, "") for k, v in kinds.items()],
    items=items,
    resolved_heading="Every spelling resolved",
    resolved_note="It opened with 171 groups sharing a spelling but not a meaning.")
print(f"same-form-other-gloss: {n} groups  {dict(kinds)}")
