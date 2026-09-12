#!/usr/bin/env python3
"""Check that the parsed dictionary says what it is supposed to say.

Two kinds of check, because two kinds of thing go wrong.

**Content.** Every field has a language it is supposed to be in, and nothing was
verifying that. A definition set in the wrong face, a column boundary off by a
few points, an entry that ran past its end - each of those puts English where
Thao belongs or the reverse, and each was silent. The discriminators are
deliberately crude and one-sided: a token counts as evidence only if it is
unambiguous in one language and absent from the other, and a field is only
reported when the evidence is lopsided. `but` is a Thao word; `a` and `sa` are
words in both; those carry no weight here.

**Structure.** The schema's invariants, per format (maintainer, 2026-09-10):
format A's headword is a free word whose own definition is the unnumbered first
sense, and derived forms run 2, 3, 4 ...; format B's headword is a bound root
with no sense of its own, so its numbering starts at 2.

**Consumption.** How much of the printed page ended up in a record, and where
the rest went. Silence about the remainder is what let a whole page go missing.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_entries import merge_accent_overlays  # noqa: E402
from extract_source import DICTIONARY_PAGES, SOURCE_PATH, normalized_rows  # noqa: E402
from pdf_text import join_spans  # noqa: E402

REFERENCE = Path(__file__).resolve().parent / "reference"


def _load_list(name):
    path = REFERENCE / name
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def load_lexicons():
    """The two word lists, both external to this book.

    Deriving them from the dictionary was circular: a list of English words
    taken from the definitions cannot fail a test that the definitions are
    English. So English comes from the `wordfreq` package's top-1000 and Thao
    from FormosanBank's ILRDF_Dicts corpus - a different corpus compiled by
    different people. The five words that occur in both (`am as but day la`)
    are removed from each, so neither can be evidence for the other.

    Hyphens go before comparison, here and on the book's text: Blust segments
    morphemes and ILRDF does not, so `ma-thuaw` and `mathuaw` have to meet.
    """
    english = _load_list("english-top1000.txt")
    thao = _load_list("thao-ilrdf.txt")
    assert not (english & thao), sorted(english & thao)
    return english, thao


# Letters Blust's Thao does not use. `e` is NOT one of them: Blust describes
# /e/ and /o/, and they turn up in names and loanwords - Sage, Wane, iseg,
# tai'eg were the whole of E01 and all four are correct as printed
# (maintainer, 2026-09-10).
NON_THAO_LETTERS = re.compile(r"[vxVX]")
# The marker of a NOTE section belongs to the structure, not to the note text.
NOTE_LEAK = re.compile(r"\bnotes?\s*:", re.IGNORECASE)

ENGLISH_ONLY: set = set()
THAO_ONLY: set = set()


#: What each rule means, in one place. build_worklist_page.py imports this:
#: a second, hand-kept copy drifted and left the worklist labelling E03
#: with its old meaning (maintainer, 2026-09-11).
RULE_TITLES = {
        "E01": "headword uses a non-Thao letter", "E02": "definition reads as Thao",
        "E03": "sense form has a definition or a second form run into it", "E04": "example.thao reads as English",
        "E05": "example.english reads as Thao", "E06": "translation with no Thao",
        "E07": "Thao with no translation", "E08": "note reads as Thao",
        "S01": "entry with no headword", "S02": "entry with no senses",
        "S03": "sense with no definition",
        "S06": "free word whose first sense is numbered",
        "S07": "sense numbers have a gap / wrong start",
        "S08": "one sense number used twice",
        "S09": "a run of unnumbered senses - a missed entry boundary",
        "E10": "example with no bold word",
        "E11": "Thao form with no letter or digit",
        "L01": "structural marker left in the text",
    }


Finding = collections.namedtuple("Finding", "rule entry page field detail")


def _tokens(text, drop_capitalised=False):
    """Words, hyphens removed - see load_lexicons.

    A capitalised token is a proper name - Kilash, Ali, Musa, PAN, Thao - and
    belongs to both languages equally, so it is no evidence for either. Left in,
    it made "Kilash finds Ali disgusting" read as 60% Thao.
    """
    if drop_capitalised:
        text = " ".join(w for w in text.split() if not w[:1].isupper())
    return [
        t.strip(".,;:?!`'\"()[]").replace("-", "").replace("\u2013", "").lower()
        for t in (text or "").split()
    ]


def _english_score(text):
    toks = [t for t in _tokens(text, drop_capitalised=True) if t]
    if not toks:
        return 0.0, 0.0, 0
    e = sum(1 for t in toks if t in ENGLISH_ONLY)
    h = sum(1 for t in toks if t in THAO_ONLY)
    return e / len(toks), h / len(toks), len(toks)


def check_leaks(entries):
    """No structural marker may survive into a value.

    "NOTE:" opens a note; by the time the note is a string the marker has been
    consumed, so finding one anywhere in the JSON means a marker was read as
    content - in the note itself, or worse, in a definition or an example.
    """
    out = []
    for e in entries:
        for field, value in (("headword", e["headword"]),
                             ("etymology", e["etymology"] or "")):
            if NOTE_LEAK.search(value or ""):
                out.append(Finding("L01", e["headword"], e["printed_page"], field,
                                   f"structural marker in the text: {value[:60]!r}"))
        for s in e["senses"]:
            fields = [("definition", s["definition"]), ("form", s["form"])]
            fields += [(f"note {i}", n) for i, n in enumerate(s["notes"])]
            for ex in s["examples"]:
                fields += [("example.thao", ex["thao"]),
                           ("example.english", ex["english"])]
            for field, value in fields:
                if NOTE_LEAK.search(value or ""):
                    out.append(Finding("L01", e["headword"], e["printed_page"],
                                       field,
                                       f"structural marker in the text: {value[:60]!r}"))
    return out


def check_content(entries):
    """Every field in the language it is supposed to be in."""
    out = []
    for e in entries:
        head, page = e["headword"], e["printed_page"]
        if NON_THAO_LETTERS.search(e["headword"] or ""):
            out.append(Finding("E01", head, page, "headword",
                               f"{e['headword']!r} uses a letter Thao does not"))
        # Deliberately NOT a rule: "the headword is an English word". Thao's
        # syllable shapes guarantee collisions with short English ones - an,
        # can, fun, law, man, May, run, say and uk are all real Thao headwords -
        # and a single word carries no evidence either way. E01, the letter
        # inventory, is the check that works on one word.
        for s in e["senses"]:
            eng, tha, n = _english_score(s["definition"])
            # A MAJORITY has to be attested Thao. The English list is the top
            # 1,000 words, so an ordinary definition built of uncommon ones -
            # "creeper (generic); types: binbin, marumiz, quay, qula",
            # "banana: Musa sapientum (Linn.)" - scores eng = 0, and any trace
            # of Thao then beat it. Citing Thao terms inside a definition is
            # normal and not a finding (maintainer, 2026-09-10).
            if n >= 4 and tha >= 0.5:
                out.append(Finding("E02", head, page, "definition",
                                   f"reads as Thao, not English: {s['definition'][:60]!r}"))
            # E03 used to be the letter test, which caught the three forms
            # below only because the English that ran into them contains `e`.
            # With `e` admitted, the signals have to be the real ones: the book
            # occasionally fails to leave the sub-entry face, so a definition
            # runs into a form ("masa-rima masay rima use the hand for some
            # purpose"), or two head phrases are set as one ("filhaq a rima
            # rima a filhaq finger") - which repeats a word (maintainer,
            # 2026-09-10).
            form = s["form"] or ""
            # A form with no letter or digit is not a word: printed p. 1031
            # leaves a bare `~`, Blust's repetition glyph, standing where a
            # headword belongs. add_phonology then emits an empty PHON, which
            # is V073 HARD, so this has to be caught before the XML is built.
            thao_side = (form or head or "").strip()
            if thao_side and not any(c.isalnum() for c in thao_side):
                out.append(Finding("E11", head, page, "sense form",
                                   f"{thao_side!r} has no letter or digit - not a word"))
            form_tokens = [w for w in _tokens(form) if w]
            english_in_form = sum(1 for w in form_tokens if w in ENGLISH_ONLY)
            # A printed slash IS the boundary - "cumay a huqi/huqi a cumay"
            # is Blust setting both word orders correctly, and belongs to the
            # slash-alternative tooling, not here. And a form repeated whole
            # ("pakish pakish", "paqi paqi") is reduplication, not two forms.
            reduplicated = len(set(form_tokens)) == 1
            repeated = [] if ("/" in form or reduplicated) else [
                w for w, c in collections.Counter(form_tokens).items()
                if c > 1 and len(w) > 2
            ]
            if form != head and english_in_form >= 3:
                out.append(Finding("E03", head, page, "sense form",
                                   f"{form!r} has a definition run into it"))
            elif form != head and repeated:
                out.append(Finding("E03", head, page, "sense form",
                                   f"{form!r} repeats {repeated[0]!r} - two forms set as one"))
            elif NON_THAO_LETTERS.search(form) and form != head:
                out.append(Finding("E03", head, page, "sense form",
                                   f"{form!r} uses a letter Thao does not"))
            for ex in s["examples"]:
                eng, tha, n = _english_score(ex["thao"])
                if n >= 4 and eng > tha and eng >= 0.2:
                    out.append(Finding("E04", head, page, "example.thao",
                                       f"reads as English: {ex['thao'][:60]!r}"))
                eng, tha, n = _english_score(ex["english"])
                if n >= 4 and tha >= 0.5:
                    out.append(Finding("E05", head, page, "example.english",
                                       f"reads as Thao: {ex['english'][:60]!r}"))
                if not ex["thao"]:
                    out.append(Finding("E06", head, page, "example",
                                       f"translation with no Thao: {ex['english'][:60]!r}"))
                if not ex["english"]:
                    out.append(Finding("E07", head, page, "example",
                                       f"Thao with no translation: {ex['thao'][:60]!r}"))
                if ex["thao"] and not ex.get("exemplifies"):
                    out.append(Finding("E10", head, page, "example",
                                       "no bold word: the example illustrates nothing"))
            for note in s["notes"]:
                eng, tha, n = _english_score(note)
                if n >= 6 and tha >= 0.5:
                    out.append(Finding("E08", head, page, "note",
                                       f"reads as Thao: {note[:60]!r}"))
    return out


def check_structure(entries):
    """The schema's invariants, per format."""
    out = []
    for e in entries:
        head, page, fmt = e["headword"], e["printed_page"], e["format"]
        senses = e["senses"]
        if not head:
            out.append(Finding("S01", head, page, "entry", "no headword"))
        if not senses:
            out.append(Finding("S02", head, page, "entry", "no senses"))
            continue
        for index, s in enumerate(senses):
            # A bound-root header defines nothing - that is what makes it one -
            # and Blust sometimes prints an example straight under it. That
            # sense has no definition on purpose (maintainer, 2026-09-11:
            # "puqnur does not have a sense listed. It DOES have an example
            # sentence with definition").
            if fmt == "B" and index == 0 and s["number"] is None:
                continue
            if not s["definition"]:
                out.append(Finding("S03", head, page, f"sense {s['number']}",
                                   f"{s['form']!r} has no definition"))
        # A long run of sub-entries the book never numbered is not a printing
        # slip; it is an entry boundary that was missed, and everything after it
        # was absorbed into this entry.
        run = 0
        worst = 0
        for sense in senses:
            run = 0 if sense["number"] is not None else run + 1
            worst = max(worst, run)
        if worst > 3:
            out.append(Finding("S09", head, page, "entry",
                               f"{worst} consecutive senses the book never numbered "
                               "- probably a missed entry boundary"))
        numbered = [s["number"] for s in senses if s["number"] is not None]
        # S04 ("bound root with its own sense") and S05 ("bound root with no
        # derived forms") are RETIRED (maintainer, 2026-09-11). Both asked
        # whether a bound-root header looked like a bound root, and every one of
        # the 24 entries they ever raised was ruled a fact about the book, not
        # about the parse: "this is parsed correctly" (kashamuan, manadu,
        # tishqaudia, Lhqapamumu, Lhqatafatu, Rariku) or "there are no derived
        # forms in the book" (ituiza). The ruling that settles both is that a
        # header WITH a definition is not a bound root at all, whatever the bars
        # around it say, and publishes like any other entry - which makes it a
        # publication decision in build_entry_xml.py, not a finding here.
        if fmt != "B":
            if senses[0]["number"] is not None:
                out.append(Finding("S06", head, page, "entry",
                                   f"a free word whose first sense is numbered "
                                   f"{senses[0]['number']}"))
        # A number may repeat across lettered sub-senses (afu has 1a, 1b, 1c),
        # so the invariant is over the DISTINCT numbers in order.
        distinct = sorted(set(numbered))
        if distinct and distinct != list(range(distinct[0], distinct[0] + len(distinct))):
            out.append(Finding("S07", head, page, "entry",
                               f"sense numbers {numbered[:12]} have a gap"))
        elif distinct and distinct[0] not in (1, 2):
            out.append(Finding("S07", head, page, "entry",
                               f"sense numbering starts at {distinct[0]}"))
        # A number repeated with no distinguishing letter is two senses that
        # were run together, or one that was split.
        letters = collections.Counter(
            (s["number"], s.get("subsense")) for s in senses if s["number"] is not None
        )
        repeated = [k for k, n in letters.items() if n > 1]
        if repeated:
            out.append(Finding("S08", head, page, "entry",
                               f"sense {repeated[0][0]} appears "
                               f"{letters[repeated[0]]} times with the same label"))
    return out


def consumption(document, consumed, skipped):
    total = 0
    for pdf_page in DICTIONARY_PAGES:
        for row in normalized_rows(document, pdf_page):
            if 95.0 < row.y0 < 680.0:
                # The parser folds a free-standing acute onto its vowel before
                # reading anything, so the printed side has to be measured the
                # same way - otherwise every merged accent reads as a character
                # the parser lost.
                total += sum(
                    len(join_spans([s])) for s in merge_accent_overlays(list(row.spans))
                )
    return total


def load_rulings(path: Path) -> dict[tuple[str, str, str], str]:
    """(rule, headword, page) -> where the ruling is applied."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        (r["rule"], r["headword"], str(r["page"])): r["handled"]
        for r in data.get("rulings", [])
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", type=Path,
                    default=Path(__file__).resolve().parent / "entry-records.json")
    ap.add_argument("--tsv", type=Path, help="write every finding as TSV")
    ap.add_argument("--baseline", type=Path,
                    default=Path(__file__).resolve().parent / "entry-baseline.json",
                    help="the committed result this run is compared against")
    ap.add_argument("--accept", action="store_true",
                    help="rewrite the baseline from this run")
    ap.add_argument("--rulings", type=Path,
                    default=Path(__file__).resolve().parent / "entry-rulings.json",
                    help="findings the maintainer has already ruled on")
    args = ap.parse_args()

    data = json.loads(args.records.read_text(encoding="utf-8"))
    entries, stats = data["entries"], data["statistics"]
    global ENGLISH_ONLY, THAO_ONLY
    ENGLISH_ONLY, THAO_ONLY = load_lexicons()
    print("=== lexicons, both external to this book ===")
    print(f"  English: wordfreq top-1000            : {len(ENGLISH_ONLY):,}")
    print(f"  Thao:    FormosanBank ILRDF_Dicts     : {len(THAO_ONLY):,}")
    print("  overlap between them                  : 0 (removed from both)\n")
    findings = (check_leaks(entries) + check_content(entries)
                + check_structure(entries))

    # A finding the maintainer has ruled on is not a question any more. The
    # ruling is recorded with the words it was given in, and the record still
    # says what the page says - what changes is where the corpus is built.
    # Without this the worklist kept handing back pages already answered.
    ruled = load_rulings(args.rulings)
    answered = [f for f in findings if (f.rule, f.entry, str(f.page)) in ruled]
    findings = [f for f in findings if (f.rule, f.entry, str(f.page)) not in ruled]

    document = fitz.open(SOURCE_PATH)
    printed = consumption(document, stats["characters_consumed"],
                          stats["characters_skipped"])
    kept = stats["characters_consumed"]
    print("=== consumption ===")
    print(f"  characters printed in the dictionary body : {printed:,}")
    print(f"  characters that reached a record          : {kept:,}  ({kept/printed*100:.1f}%)")
    print(f"  characters skipped, by reason             : {stats['characters_skipped']}")
    print(f"  unaccounted                               : {printed-kept-sum(stats['characters_skipped'].values()):,}")

    print("\n=== findings ===")
    by_rule = collections.Counter(f.rule for f in findings)
    titles = RULE_TITLES
    for rule, n in sorted(by_rule.items()):
        print(f"  {rule}  {n:6d}  {titles.get(rule,'')}")
    print(f"  {'':4}  {len(findings):6d}  total over {len(entries):,} entries")

    if answered:
        print(f"\n=== ruled, and so not asked again ({len(answered)}) ===")
        for finding in sorted(answered, key=lambda f: (f.rule, f.page)):
            handled = ruled[(finding.rule, finding.entry, str(finding.page))]
            print(f"  {finding.rule}  {finding.entry} p.{finding.page}  -> {handled}")

    # A committed baseline is what makes a change legible: without it, a
    # refactor that quietly loses 200 examples looks exactly like one that does
    # not. Every number the run produces goes in, not just the finding counts.
    current = {
        "entries": len(entries),
        "format_A": sum(1 for e in entries if e["format"] == "A"),
        "format_B": sum(1 for e in entries if e["format"] == "B"),
        "senses": sum(len(e["senses"]) for e in entries),
        "examples": sum(len(s["examples"]) for e in entries for s in e["senses"]),
        "notes": sum(len(s["notes"]) for e in entries for s in e["senses"]),
        "characters_consumed": kept,
        "characters_printed": printed,
        "findings": dict(sorted(by_rule.items())),
        "entries_with_findings": len({(f.entry, f.page) for f in findings}),
        "keys": sorted(f"{f.rule}\t{f.entry}\t{f.page}" for f in findings),
    }
    if args.accept:
        args.baseline.write_text(
            json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nbaseline rewritten: {args.baseline}")
    elif args.baseline.exists():
        was = json.loads(args.baseline.read_text(encoding="utf-8"))
        moved = [
            (k, was.get(k), current.get(k))
            for k in current
            if k not in ("keys", "findings") and was.get(k) != current.get(k)
        ]
        appeared = sorted(set(current["keys"]) - set(was.get("keys", [])))
        gone = sorted(set(was.get("keys", [])) - set(current["keys"]))
        print("\n=== against the committed baseline ===")
        if not moved and not appeared and not gone:
            print("  no change")
        for k, a, b in moved:
            if k == "findings":
                continue
            print(f"  {k}: {a} -> {b}")
        for k in sorted(set(was.get("findings", {})) | set(current["findings"])):
            a, b = was.get("findings", {}).get(k, 0), current["findings"].get(k, 0)
            if a != b:
                print(f"  {k}: {a} -> {b}")
        if appeared:
            print(f"  NEW findings ({len(appeared)}):")
            for k in appeared[:15]:
                print(f"     {k}")
        if gone:
            print(f"  fixed ({len(gone)}):")
            for k in gone[:15]:
                print(f"     {k}")
        if moved or appeared or gone:
            print("  (run with --accept once the change is understood and wanted)")
    else:
        print("\n=== no baseline yet; run with --accept to write one ===")

    if args.tsv:
        with args.tsv.open("w", encoding="utf-8") as fh:
            fh.write("rule\theadword\tprinted_page\tfield\tdetail\n")
            for f in sorted(findings, key=lambda x: (x.rule, x.page)):
                fh.write(f"{f.rule}\t{f.entry}\t{f.page}\t{f.field}\t{f.detail}\n")
        print(f"\nwrote {args.tsv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
