import sys, json, re, collections
sys.path.insert(0, '/workspace/Formosan-Robert-Blust-Thao-Dictionary/CodeAndDocs')
from build_review_page import render, E
OUT = "/tmp/claude-1000/-workspace-FormosanBank/0cb3cbf0-0934-4e90-aef3-6d6515ae698f/scratchpad/"
DEV = "/workspace/Formosan-Robert-Blust-Thao-Dictionary/CodeAndDocs/"

RULED = {"blust-dict-p0446-e019", "blust-dict-p0727-e001", "blust-dict-p0848-e005",
         "blust-dict-p0881-e009", "blust-dict-p0924-e006", "blust-dict-p0925-e005",
         "blust-dict-p0996-e003", "blust-dict-p1027-e009"}

data = json.load(open(DEV + "expanded-records.json"))
groups = collections.OrderedDict()
for rec in data["dictionary_examples"]:
    if rec["expansion"]["slash_option"] is None:
        continue
    groups.setdefault(rec["source_record_id"], []).append(rec)

ruled = [k for k in groups if k in RULED]
rest = [k for k in groups if k not in RULED]
step = max(1, len(rest) // (25 - len(ruled)))
sample = sorted(set(ruled + rest[::step][: 25 - len(ruled)]))

def hl(text):
    return E(text).replace("/", '<mark>/</mark>')

items, counts = [], collections.Counter()
for ident in sample:
    members = groups[ident]
    raw = members[0]["source_raw"]
    page = str(members[0]["source_printed_page"])
    group = "maintainer-ruled" if ident in RULED else f"{len(members)} readings"
    counts[group] += 1
    shared = "shared" if len({m["translation"] for m in members}) == 1 else "one each"
    readings = "".join(
        f'<div class="row"><span class="lab n">{E(m["id"].rsplit("-", 1)[1])}</span>'
        f'<span class="thao">{E(m["source"])}</span></div>'
        f'<div class="row"><span class="lab">english</span><span class="eng">{E(m["translation"])}</span></div>'
        for m in members)
    items.append(
        f'<article class="entry" data-id="{E(ident)}" data-group="{E(group)}" '
        f'data-search="{E((raw + " " + members[0]["translation"] + " " + page).lower())}">'
        f'<header><span class="hw">{hl(raw)}</span>'
        f'<span class="tag{" b" if ident in RULED else ""}">{E(group)}</span>'
        f'<span class="pg">p.{page} &middot; {E(ident)}</span>'
        f'<span class="pg">translation {E(shared)}</span></header>'
        f'<div class="row"><span class="lab w">expanded into {len(members)}</span></div>{readings}</article>')

n = render(OUT + "slash-handled.html",
    title="Slash Alternations Already Split",
    eyebrow="Blust 2003 Thao Dictionary · expansion review",
    heading="Twenty-five that the build already splits",
    dek=("<code>expand_source.py</code> turns a slash alternation into one sentence per reading, "
         "sharing the translation unless the parenthetical splits in step. This is a sample of "
         "<b>" + str(len(sample)) + "</b> of the <b>" + str(len(groups)) + "</b> it handles &mdash; "
         "the <b>eight you ruled on</b> in September plus a spread across the book &mdash; so the "
         "scope decisions can be checked for a systematic problem rather than one at a time. "
         "The heading shows what Blust printed; the readings below are what shipped. Flag any where "
         "the split takes shared material to only one side, or splits something that is not an "
         "alternation at all."),
    footer="CodeAndDocs/expanded-records.json &middot; " + str(len(groups)) +
           " slash source records, 374 expanded sentences in XML/Thao",
    verdicts=["correct", "shared material lost", "not an alternation", "needs the page"],
    store="thao-slash-ok",
    groups=[("ALL", len(sample), "")] + [(k, v, "") for k, v in counts.most_common()],
    items=items)
print("slash-handled:", n, "of", len(groups), "groups |", dict(counts))
