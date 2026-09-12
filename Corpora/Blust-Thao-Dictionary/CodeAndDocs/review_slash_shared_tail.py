"""Printed slashes where material AFTER the slash is still shared by both readings.

The maintainer's question was: which slashes do NOT separate two whole
sentences - where is there content after the slash that both readings should
carry? resolve_scope answers it directly, because the frame it finds is the
claim: a non-empty `suffix` says something after the slash is shared.

This page is generated from what the BUILD does, not from the resolver alone,
so an item disappears once a rule or a ruling settles it. RULED lists the
verdicts already given, with the words they were given in; those cards are gone
whatever the build now does with them.
"""
import sys, collections, json
sys.path.insert(0, '/workspace/Formosan-Robert-Blust-Thao-Dictionary/CodeAndDocs')
sys.path.insert(0, '/workspace/wt-thao-qc')
from QC.utilities.slash_alternatives import resolve_scope
from QC.utilities.parentheticals import take_notes
from build_review_page import render, E, card_id
import build_entry_xml as B

OUT = "/tmp/claude-1000/-workspace-FormosanBank/0cb3cbf0-0934-4e90-aef3-6d6515ae698f/scratchpad/"
HERE = "/workspace/Formosan-Robert-Blust-Thao-Dictionary/CodeAndDocs/"
THAO = frozenset({"tu", "sa", "a", "ya", "wa"})

#: Verdicts already given on this page, keyed by its card id (2026-09-11).
RULED = {
    "anun__296": "something else - already ruled on the reordering page",
    "apiq__299": "shared tail is right",
    "biskaw__324": "slash splits the whole thing",
    "cakaw__338": "shared tail is right",
    "capu__341": "something else - the alternation is the whole verb phrase",
    "dahda(h)__352": "shared tail is right",
    "hadana__393": "shared tail is right",
    "kaligkin__439": "shared tail is right",
    "kan__446": "shared tail is right",
    "kuza__504": "shared tail is right",
    "lhckiz__530": "shared tail is right",
    "lhilhi__535": "shared tail is right",
    "naur__636": "shared tail is right",
    "patatara__694": "shared tail is right (low-confidence list)",
    "pitu__726": "shared tail is right",
    "qusaz__815": "slash splits the whole thing (uncertain)",
    "raput__822": "shared tail is right",
    "rima__832": "slash splits the whole thing - two spellings, ver=alt",
    "ruqit__848": "shared tail is right",
    "ruru__849": "shared tail is right",
    "shkash__923": "keep the frame - ruled on the reordering page, and on the\n                    uncertain list",
    "shlaup__925": "shared tail is right",
    "tima__990": "shared tail is right",
    "tiuz__996": "shared tail is right",
    "tmaza__999": "shared tail is right",
    "tusha__1026": "shared tail is right",
    "tusi__1022": "slash splits the whole thing - the frame fused the two forms",
    "untal__1040": "shared tail is right",
}

items, kinds = [], collections.Counter()
opened = 0
for entry in json.load(open(HERE + "entry-records.json"))["entries"]:
    page = entry["printed_page"]
    for sense in entry["senses"]:
        printed = []
        if sense["form"] and "/" in sense["form"]:
            printed.append((sense["form"], sense["definition"] or "", "headword form"))
        printed += [(x["thao"], x["english"] or "", "example")
                    for x in sense["examples"] if "/" in (x["thao"] or "")]
        for form, english, kind in printed:
            spoken, _notes = take_notes(form, english, never_pairs=THAO)
            scope = resolve_scope(form, translation=spoken or None)
            if not (scope.suffix.strip() and scope.confidence != "low"
                    and len(scope.options) >= 2):
                continue
            opened += 1
            built = [r[0] for r in B.readings(form, english)]
            naive = [piece.strip() for piece in form.split("/") if piece.strip()]
            # The card goes when the build no longer shares a tail: either it
            # took the slash at face value, or the record became one sentence
            # with a ver="alt" spelling, which shares nothing.
            flagged = B.repeats_an_alternant(form, scope.alternants, built)
            # The card goes when the build no longer shares a tail: either it
            # took the slash at face value, or the record became one sentence
            # with a ver="alt" spelling, which shares nothing. A reading that
            # repeats an alternating word stays, whatever else is true of it -
            # that is the "worth someone looking at" signal.
            if (built == naive or len(built) < 2) and not flagged:
                continue
            if flagged:
                kind = "repeats a word"
            ident = card_id(entry["headword"], page)
            if ident in {card_id(k) for k in RULED}:
                continue
            kinds[kind] += 1
            rows = "".join(
                f'<div class="row"><span class="lab">reading {n}</span>'
                f'<span class="thao">{E(o)}</span></div>'
                for n, o in enumerate(built, start=1))
            items.append(
                f'<article class="entry" data-id="{E(entry["headword"])}__{page}__slashtail" '
                f'data-db-id="{E(card_id(ident, "slashtail"))}" '
                f'data-group="{E(kind)}" '
                f'data-search="{E((form + " " + english + " " + str(page)).lower())}">'
                f'<header><span class="hw">{E(form).replace("/", "<mark>/</mark>")}</span>'
                f'<span class="tag">{E(kind)}</span>'
                f'<span class="pg">p.{page} &middot; {E(entry["headword"])} &middot; '
                f'{E(scope.confidence)} confidence</span></header>'
                f'<div class="row"><span class="lab">english</span>'
                f'<span class="eng">{E(english) or "&mdash;"}</span></div>'
                + (f'<div class="row"><span class="lab">shared before</span>'
                   f'<span class="thao">{E(scope.prefix)}</span></div>'
                   if scope.prefix.strip() else "")
                + "".join(f'<div class="row"><span class="lab n">alternant {n}</span>'
                          f'<span class="thao">{E(a)}</span></div>'
                          for n, a in enumerate(scope.alternants, start=1))
                + f'<div class="row"><span class="lab w">SHARED AFTER</span>'
                  f'<span class="thao">{E(scope.suffix)}</span></div>'
                + rows + "</article>")

n = render(
    OUT + "slash-shared-tail.html",
    title="Shared After The Slash",
    eyebrow="Blust 2003 Thao Dictionary · slash scope",
    heading=("One slash left" if len(items) == 1 else f"{len(items)} slashes left"),
    dek=(f"This page opened with <b>43</b> printed slashes where the resolver found "
         f"material after the slash that both readings should carry. <b>{len(RULED)} have "
         "been ruled</b>, and the rulings settled on the test a reader applies first: "
         "<b>are the two sides of the slash the same words in a different order?</b> If "
         "they are, the compiler is showing two word orders, there is no frame, and the "
         "slash is taken at face value. Measured as shared words over the <i>longer</i> "
         "side &mdash; over the shorter side a four-word alternant hanging off a "
         "sixteen-word sentence scores 0.75 and nothing is being reordered &mdash; the "
         "ruled cases put the highest &lsquo;keep&rsquo; at 0.40 and the lowest "
         "reordering at 0.50, so the line sits in a real gap. A second rule catches a "
         "reading that has lost its own printed half, which means the frame fused the two "
         "forms rather than sharing a tail. Four readings neither rule can derive are "
         "curated from the maintainer's own analysis. A reading that repeats a word the "
         "slash is alternating no longer decides anything &mdash; it is a reason to look, "
         "and any such card is tagged <i>repeats a word</i> here."),
    footer="resolve_scope(printed, translation=spoken) vs build_entry_xml.readings() "
           "&middot; a card disappears when a ruling or a rule settles it",
    verdicts=["shared tail is right", "slash splits the whole thing", "something else",
              "needs the page"],
    store="thao-slash-tail",
    groups=[("ALL", len(items), "")] + [(k, v, "") for k, v in kinds.items()],
    items=items,
    resolved_heading="Every shared tail resolved",
    resolved_note=("It opened with <b>43</b> printed slashes claiming shared material "
                   f"after them. {len(RULED)} were ruled; two rules derived from those rulings "
                   "settle the rest."))
print(f"slash-shared-tail: {n} open (of {opened} claiming a tail, {len(RULED)} ruled)")
