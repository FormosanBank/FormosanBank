"""Write the standard gloss tier from a conversion table + rules file.

For every W/M-level TRANSL gloss in the target XML:
  * stamps ``kindOf="original"`` where the attribute is absent (the bare
    forms are legal; stamping is the maintainer's g5 decision), and
  * adds a sibling ``TRANSL kindOf="standard"`` in the same ``xml:lang``,
    whose text is the gloss with every CONVERT atom mapped to its standard
    (honoring per-language ``language_overrides``), KEEP and UNDECIDED atoms
    copied as-is, separators and infix angle-brackets preserved.

A gloss the rules cannot segment (it contains characters the rules mark
INVESTIGATE/RESIDUE, e.g. parentheses) is copied verbatim and listed in the
residue report. ``NOTE-PARENS <regex>`` (maintainer 2026-11-15) marks
clarifier chunks that are removed from the standard text and stored on the
standard TRANSL's ``notes`` attribute. LGR Rule 7 parentheses are handled by
``RULE7-PARENS`` / ``RULE7-PARENS-SPACED`` (below). Other parens remain
residue. Elements that already carry a standard TRANSL for that
language are left exactly as they are (preexisting hand-made standards are
never overwritten). Originals are never modified beyond the kindOf stamp
(POL-036/POL-062). S-level TRANSLs are never touched (V151).

Leipzig Rule 7 for voice (maintainer, 2026-11-15, unvoiced-verbs audit: Rule 7 "see(AV)", "All 12,001 with a
lexical gloss; the 3,684 on affixes/auxiliaries stay as they are"):
  * a gloss piece group that fuses ONE voice code (AV/PV/LV/OV) with a lexical gloss by periods (Rule 4,
    ``AV.see``) is written ``see(AV)``; groups whose other pieces are all codes (affixes, auxiliaries:
    ``AUX.AV``, ``PV.IMP``) stay as they are. A piece is lexical when it is not a code of the table.
  * a rules file may declare ``RULE7-PARENS``: parentheses attached to a gloss and holding only codes
    (``die(AV)``, ``打（AF）``) are then a Rule 7 category, converted, and no longer residue; all other
    parentheses stay residue (maintainer, 2026-11-11: "parens/brackets shouldn't be in glosses").
    ``RULE7-PARENS-SPACED`` also accepts whitespace between the gloss and such parentheses and drops it
    (``go (AV)`` -> ``go(AV)``); it is per corpus because prose glosses define codes the same way
    (Yedda ``conjunction (CONJ)``). It replaces the former KEEP-PARENS (maintainer, 2026-11-17: "Bracket
    fold: Approved.").
  * a rules file may declare ``INFIX-GLOSS-BRACKETS``: in a word-level gloss, the gloss of each morpheme
    whose original FORM is an infix written ``-X-`` (POL-014) is put in angle brackets, LGR Rule 9:
    ``AV-talk`` -> ``<AV>talk`` for r-em-eŋaw (maintainer, 2026-11-17: "All this should go into our
    pending PR").
  * ``<gloss>&=<stem>  CONTEXT-ADD→<V>`` rules add a voice the source leaves unglossed: on a word whose
    form (lower case, = clitics removed) is <stem> and which carries no voice code at all, the morpheme
    whose original gloss is exactly <gloss> gets ``(<V>)`` in every standard tier.
A rules file may also declare ``<exact gloss>  WHOLE-GLOSS→<CODE>``: a gloss (or gloss segment) that is exactly
``<exact gloss>`` (after stripping outer whitespace) becomes ``<CODE>`` (maintainer, 2026-11-16, unvoiced-verbs audit
whole_gloss_rule_r8: "Yes"), e.g. Yedda ``ligature (LIG)`` -> LNK, HPS ``(name)`` -> PN. The pattern is literal text,
not a regular expression, and nothing but an exact match converts.
A rules file may declare ``<form>@<Language>  TWIN-VOICE``: on a morpheme of that language whose original FORM is
<form> (affix marks removed), when one gloss language's new standard only repeats the form (``<m>``) and the other
language's standard is a voice code and nothing else (``<AV>``), the voice code replaces the self-gloss (maintainer,
2026-11-17: "If a verb has an affix that is self-glossed in one language but glossed as a voice marker in the other
language AND its form is one that often appears voice-glossed, replace the self-gloss with the voice gloss.").
``--redo-changed`` re-derives EXISTING standard glosses: one is replaced only if it is exactly what this tool
produced before these rules (so hand-made standards stay untouched) and the new rules change it.

Dry-run by default; ``--write`` modifies the XML in place. Run:

  python QC/glossing/apply_gloss_standard.py --corpus NTUFormosanCorpus [--write]
  python QC/glossing/apply_gloss_standard.py --path <XML dir> --table T.tsv --rules R.tsv [--write]
"""
from __future__ import annotations

import argparse
import collections
import csv
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

XMLLANG = "{http://www.w3.org/XML/1998/namespace}lang"
GLOSS_LANGS = {"eng", "zho"}
ISO_TO_LANGUAGE = {
    "ami": "Amis", "tay": "Atayal", "bnn": "Bunun", "xnb": "Kanakanavu",
    "ckv": "Kavalan", "pwn": "Paiwan", "pyu": "Puyuma", "dru": "Rukai",
    "sxr": "Saaroa", "xsy": "Saisiyat", "szy": "Sakizaya", "ssf": "Thao",
    "tsu": "Tsou", "tao": "Yami",
}


VOICES = ("AV", "PV", "LV", "OV")
LEXICAL = re.compile(r"[a-z\u3400-\u9fff]")
RULE7_GROUP = re.compile(r"(?<=\S)[(（]([^()（）]+)[)）]")
RULE7_GROUP_SPACED = re.compile(r"\s*[(（]([^()（）]+)[)）]")
INFIX_FORM = re.compile(r"-[^-=\s]+-")
CHUNK_SPLIT = re.compile(r"([-=<>\s]+)")


def rule7_voice(text: str, table: "Table") -> str:
    """Rule 4 -> Rule 7 for voice: in each period-joined group, one voice code fused with a lexical gloss
    (AV.see, say.AV, AV.FUT.go) becomes see(AV) / say(AV) / FUT.go(AV). Groups with no lexical piece
    (AUX.AV, PV.IMP) and groups already holding parentheses are left alone."""
    out = []
    for chunk in CHUNK_SPLIT.split(text):
        pieces = chunk.split(".")
        if len(pieces) > 1 and "(" not in chunk and ")" not in chunk:
            v = [p for p in pieces if p in VOICES]
            lex = [p for p in pieces if p not in VOICES and p not in table.codes and LEXICAL.search(p)]
            if len(v) == 1 and lex:
                chunk = ".".join(p for p in pieces if p not in VOICES) + f"({v[0]})"
        out.append(chunk)
    return "".join(out)


def bracket_infixes(text: str, infix_glosses) -> str:
    """LGR Rule 9 on a word gloss: each infix morpheme's gloss g, written ``g-`` at the start or after a
    boundary (- = >), becomes ``<g>``: AV-talk -> <AV>talk, AV-PRF-meet -> <AV><PRF>meet."""
    for g in infix_glosses:
        text = re.sub(r"(^|(?<=[-=>]))" + re.escape(g) + r"-", "<" + g.replace("\\", "\\\\") + ">", text, count=1)
    return text


def add_voice(text: str, voice: str) -> str:
    return text if text.endswith(")") else f"{text}({voice})"


def language_of(root: ET.Element) -> str:
    iso = root.get(XMLLANG) or ""
    if iso == "trv":  # trv is Seediq-or-Truku; the dialect attribute decides
        return "Truku" if root.get("dialect") == "Truku" else "Seediq"
    return ISO_TO_LANGUAGE.get(iso, iso)


class Table:
    def __init__(self, path: pathlib.Path):
        self.map: dict[str, tuple[str, str, dict[str, str]]] = {}
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                code = row["source_code"]
                overrides = {}
                for part in re.findall(r"(\S+?)→(\S+)", row.get("language_overrides") or ""):
                    overrides[part[0]] = part[1]
                self.map[code] = (row["status"], row.get("standard") or "", overrides)
        # every code the table knows (source codes, standards, override targets): what is NOT here is lexical.
        # A KEEP row with an empty standard is a lexical gloss that has a row only for its per-language
        # overrides (NTU become/變成/變/state: "lexical gloss elsewhere", Bunun→COS), so it stays lexical.
        lexical_rows = {c for c, (t, s, _o) in self.map.items() if t == "KEEP" and not s}
        self.codes = (set(self.map) - lexical_rows) | {s for _t, s, _o in self.map.values() if s} \
            | {x for _t, _s, o in self.map.values() for x in o.values()}

    def standard_for(self, atom: str, language: str) -> str:
        entry = self.map.get(atom)
        if entry is None:
            return atom                      # unknown atom: copied as-is
        status, standard, overrides = entry
        if language in overrides:
            return overrides[language]
        if status == "CONVERT" and standard:
            return standard
        return atom                          # KEEP and UNDECIDED copy


AFFIX_MARKS = "-=<>⟨⟩"


def form_core(form: str) -> str:
    """A morpheme form with affix punctuation removed (also word-internally:
    a source may write an infixed prefix as s-i), lowercased."""
    return re.sub(f"[{re.escape(AFFIX_MARKS)} ]", "", form).lower()


def context_matches(pattern: str, context_forms) -> bool:
    """Does a context-rule form pattern match the word?

    context_forms holds the cores of the word's segmented morpheme FORMs plus,
    marked "~"-prefixed, the whole word's own form — so that an unsegmented
    word (Yedda) can satisfy an affix pattern by its shape: "-an" matches a
    morpheme an or a word ending in an; "si-" a morpheme si or a word starting
    with si; a bare pattern only an exact morpheme.
    """
    if pattern == "+bound":
        # Reserved pattern: the word is morphologically complex (>= 2 M
        # children) — maintainer q_cmpr 2026-11-16 ("only when tja is bound")
        return "#multi" in context_forms
    core = form_core(pattern)
    if not core:
        return False
    for f in context_forms:
        if f.startswith("~"):
            word = f[1:]
            if pattern.startswith("-") and word.endswith(core):
                return True
            if pattern.endswith("-") and word.startswith(core):
                return True
        elif f == core:
            return True
    return False


class Rules:
    """Separator, residue and context-rule behavior from the corpus's .rules.tsv."""

    def __init__(self, path: pathlib.Path):
        self.separators: list[str] = []
        self.keep_brackets = False
        self.residue_chars = ""
        note_parens: list[str] = []
        # (atom, form core, target), in file order: "UV&-an / CONTEXT-CONVERT→LV"
        # means an atom UV on a word one of whose morphemes is -an becomes LV.
        # An atom with context rules but no matching form is kept as-is (the
        # rules file states that fallback, e.g. "UV&⟨in⟩-only / KEEP-UV").
        self.context_rules: list[tuple[str, str, str]] = []
        self.rule7_parens = False
        self.rule7_spaced = False
        self.infix_gloss_brackets = False
        self.add_rules: dict[tuple[str, str], str] = {}     # (word stem, morpheme gloss) -> voice
        self.whole_gloss: dict[str, str] = {}               # exact whole gloss -> standard
        self.twin_voice: set[tuple[str, str]] = set()      # (form core, language) for TWIN-VOICE
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                repl = row["replacement"]
                pat = row["pattern"]
                add = re.fullmatch(r"CONTEXT-ADD→(\S+)", repl)
                if add and "&=" in pat:
                    gloss, stem = pat.rsplit("&=", 1)
                    self.add_rules[(stem.strip().lower(), gloss.strip())] = add.group(1)
                    continue
                whole = re.fullmatch(r"WHOLE-GLOSS→(\S+)", repl)
                if whole:
                    self.whole_gloss[pat.strip()] = whole.group(1)
                    continue
                if repl == "RULE7-PARENS":
                    self.rule7_parens = True
                    continue
                if repl == "RULE7-PARENS-SPACED":
                    self.rule7_parens = self.rule7_spaced = True
                    continue
                if repl == "TWIN-VOICE" and "@" in pat:
                    form, lang = pat.rsplit("@", 1)
                    self.twin_voice.add((form_core(form.strip()), lang.strip()))
                    continue
                if repl == "INFIX-GLOSS-BRACKETS":
                    self.infix_gloss_brackets = True
                    continue
                ctx = re.fullmatch(r"CONTEXT-CONVERT→(\S+)", repl)
                if ctx and "&" in pat:
                    atom, form = pat.split("&", 1)
                    self.context_rules.append((atom, form.strip(), ctx.group(1)))
                elif "&" in pat:
                    continue                    # documented fallback (KEEP-*)
                elif repl in ("KEEP-SEPARATOR", "INFIX-BREAK"):
                    self.separators.append(pat)
                elif repl == "KEEP-BRACKETS":
                    self.keep_brackets = True
                elif repl == "NOTE-PARENS":
                    note_parens.append(pat)
                elif repl in ("INVESTIGATE", "RESIDUE") and pat not in ("…",):
                    self.residue_chars += pat.strip("[]")
        # Clarifier chunks (moved to the standard TRANSL's notes attribute);
        # whitespace before the chunk is consumed; recognized before the
        # residue check.
        self.note_parens_re = re.compile(
            r"\s*(" + "|".join(note_parens) + r")") if note_parens else None
        self.context_atoms = {a for a, _f, _t in self.context_rules}
        sep = "|".join(self.separators) or r"\."
        self.split_re = re.compile(f"({sep})")
        self.residue_re = re.compile(f"[{re.escape(self.residue_chars)}]") \
            if self.residue_chars else None


def convert_gloss(gloss: str, table: Table, rules: Rules, language: str,
                  context_forms: frozenset = frozenset(), new: bool = True):
    """Returns (standard_text, is_residue, note). context_forms are the cores
    of the word's morpheme FORMs, for the rules file's context rules. ``note``
    holds any NOTE-PARENS chunks removed from the text (empty otherwise).
    new=False reproduces the behavior before the 2026-11-15 voice Rule 7 rules
    (RULE7-PARENS, the Rule 4 -> Rule 7 voice restyle; used by --redo-changed).

    Order: an exact WHOLE-GLOSS match; NOTE-PARENS chunks moved to the note;
    RULE7-PARENS code-only groups after a gloss (masked; with -SPACED, also
    after whitespace, which is dropped); the residue check on what is left;
    conversion; the voice restyle."""
    if gloss.strip() in rules.whole_gloss:
        return rules.whole_gloss[gloss.strip()], False, ""
    original = gloss
    note = ""
    if rules.note_parens_re and rules.note_parens_re.search(gloss):
        note = " ".join(m.group(1)
                        for m in rules.note_parens_re.finditer(gloss))
        gloss = rules.note_parens_re.sub("", gloss)
    groups: list[str] = []
    if new and rules.rule7_parens:
        def keep(m):
            if not m.string[:m.start()].strip():
                return m.group(0)             # nothing before it: not attached to a gloss
            inner = [a for a in re.split(r"[.\s]+", m.group(1)) if a]
            if inner and all(a in table.codes for a in inner):
                groups.append(".".join(table.standard_for(a, language) for a in inner))
                return f"\uE000{len(groups) - 1}\uE001"
            return m.group(0)
        gloss = (RULE7_GROUP_SPACED if rules.rule7_spaced else RULE7_GROUP).sub(keep, gloss)

    def std_atom(atom: str) -> str:
        if atom in rules.context_atoms:
            for rule_atom, pattern, target in rules.context_rules:
                if rule_atom == atom and context_matches(pattern, context_forms):
                    return target
            # No diagnostic form: fall through to the table (maintainer card
            # Q5, 2026-11-15). A table row with an empty standard still keeps
            # the atom, which preserves the documented Yedda UV fallback.
        return table.standard_for(atom, language)

    def convert_flat(text: str) -> str:
        out = []
        for part in (re.split(r"(<[^<>]+>)", text)
                     if rules.keep_brackets else [text]):
            if part.startswith("<") and part.endswith(">") and rules.keep_brackets:
                inner = part[1:-1]
                pieces = [std_atom(a) if i % 2 == 0 and a else a
                          for i, a in enumerate(rules.split_re.split(inner))]
                out.append("<" + "".join(pieces) + ">")
            else:
                pieces = [std_atom(a) if i % 2 == 0 and a else a
                          for i, a in enumerate(rules.split_re.split(part))]
                out.append("".join(pieces))
        return "".join(out)

    if rules.residue_re and rules.residue_re.search(gloss):
        return original, True, ""
    text = convert_flat(gloss).strip()
    for i, g in enumerate(groups):
        text = text.replace(f"\uE000{i}\uE001", f"({g})")
    if new:
        text = rule7_voice(text, table)
    return text, False, note


def _word_has_voice(elements, table, rules, language, context) -> bool:
    """Does any original gloss of the word (W or its M) carry a voice code once converted (old rules)?"""
    for el in elements:
        for t in el.findall("TRANSL"):
            if t.get("kindOf") == "standard" or t.get(XMLLANG) not in GLOSS_LANGS:
                continue
            text = "".join(t.itertext()).strip()
            if not text:
                continue
            conv, _res, _note = convert_gloss(text, table, rules, language, context, new=False)
            if any(p in VOICES for p in re.split(r"[.\-=<>\s/()（）]+", conv)):
                return True
    return False


def process_file(path: pathlib.Path, table: Table, rules: Rules, write: bool,
                 stats: collections.Counter, residue: collections.Counter, redo: bool = False):
    tree = ET.parse(path)
    root = tree.getroot()
    language = language_of(root)
    changed = False
    for word in root.iter("W"):
        morphs = word.findall("M")
        if rules.context_rules:
            cores = {form_core(f.text) for m in morphs
                     for f in m.findall("FORM") if f.text}
            if len(morphs) >= 2:
                cores.add("#multi")   # for the reserved "+bound" pattern
            if not morphs:
                # unsegmented word: its own shape may satisfy affix patterns
                cores |= {"~" + form_core(f.text)
                          for f in word.findall("FORM") if f.text}
            context = frozenset(cores)
        else:
            context = frozenset()
        to_add = {}
        if rules.add_rules:
            wf = next((f.text for f in word.findall("FORM") if f.get("kindOf") in (None, "original") and f.text),
                      None) or next((f.text for f in word.findall("FORM") if f.text), "") or ""
            stem = wf.strip().lower().split("=")[0]
            if any(k[0] == stem for k in rules.add_rules) and \
                    not _word_has_voice([word] + morphs, table, rules, language, context):
                for m in morphs:
                    for t in m.findall("TRANSL"):
                        v = rules.add_rules.get((stem, "".join(t.itertext()).strip()))
                        if v and t.get("kindOf") != "standard":
                            to_add[id(m)] = v
        infixes: dict[str, list[str]] = {}
        if rules.infix_gloss_brackets:
            # glosses of the word's infix morphemes (original FORM -X-, POL-014), per gloss language
            for m in morphs:
                form = next((f.text for f in m.findall("FORM")
                             if f.get("kindOf") in (None, "original") and f.text), "") or ""
                if INFIX_FORM.fullmatch(form.strip()):
                    for t in m.findall("TRANSL"):
                        text = "".join(t.itertext()).strip()
                        if t.get("kindOf") != "standard" and t.get(XMLLANG) in GLOSS_LANGS and text:
                            infixes.setdefault(t.get(XMLLANG), []).append(
                                convert_gloss(text, table, rules, language, context)[0])
        for parent in [word] + morphs:
            before = {id(t) for t in parent.findall("TRANSL") if t.get("kindOf") == "standard"}
            changed |= _process_element(parent, table, rules, write, stats,
                                        residue, language, context, redo=redo,
                                        voice_to_add=to_add.get(id(parent)),
                                        infixes=infixes if parent is word else None)
            if rules.twin_voice and parent is not word:
                changed |= _twin_voice(parent, rules, language, before, stats)
    if write and changed:
        tree.write(path, encoding="UTF-8", xml_declaration=True)
    return changed


def _twin_voice(m, rules, language, before, stats) -> bool:
    """TWIN-VOICE: a newly written standard gloss that only repeats the morpheme's form takes the voice code of
    the other gloss language's standard, if that is a voice code and nothing else."""
    form = next((f.text for f in m.findall("FORM") if f.get("kindOf") in (None, "original") and f.text), "") or ""
    fc = form_core(form.strip())
    if (fc, language) not in rules.twin_voice:
        return False
    std = {t.get(XMLLANG): t for t in m.findall("TRANSL")
           if t.get("kindOf") == "standard" and t.get(XMLLANG) in GLOSS_LANGS and not t.get("ver")}
    changed = False
    for lang, t in std.items():
        if id(t) in before or len(t) or form_core((t.text or "").strip()) != fc:
            continue
        for other_lang, o in std.items():
            atoms = [a for a in re.split(r"[.\-=<>\s()（）]+", o.text or "") if a]
            if other_lang != lang and atoms and all(a in VOICES for a in atoms):
                t.text = o.text
                stats["twin_voice"] += 1
                changed = True
                break
    return changed


def _process_element(parent, table, rules, write, stats, residue, language,
                 context, redo: bool = False, voice_to_add: str | None = None,
                 infixes: dict | None = None) -> bool:
    changed = False
    existing_standard = {(t.get(XMLLANG), t.get("ver"))
                         for t in parent.findall("TRANSL")
                         if t.get("kindOf") == "standard"}
    for transl in list(parent.findall("TRANSL")):
        kind = transl.get("kindOf")
        lang = transl.get(XMLLANG)
        ver = transl.get("ver")
        # A gloss may hold child elements (POL-021 <UNCLEAR/>); its text then
        # lives in transl.text AND the children's tails. Convert each text
        # segment, keep the children in place.
        segments = [("text", transl.text or "")] + \
                   [(child, child.tail or "") for child in transl]
        has_content = any(s.strip() for _, s in segments)
        if kind == "standard" or lang not in GLOSS_LANGS or not has_content:
            continue
        if kind is None and not ver:
            # ver= variants stay unstamped: V022 forbids two same-lang
            # kindOf="original" TRANSLs and is not ver-aware
            transl.set("kindOf", "original")   # g5 stamp
            stats["stamped"] += 1
            changed = True
        full = "".join(s for _, s in segments).strip()
        if (lang, ver) in existing_standard:
            std = next((t for t in parent.findall("TRANSL") if t.get("kindOf") == "standard"
                        and t.get(XMLLANG) == lang and t.get("ver") == ver), None)
            if not redo or std is None:
                stats["preexisting_standard_kept"] += 1
                continue
            if len(std) or len(transl):               # <UNCLEAR/> children: not re-derived
                stats["redo_skipped_children"] += 1
                continue
            old, _r, _n = convert_gloss(full, table, rules, language, context, new=False)
            new_text, res, new_note = convert_gloss(full, table, rules, language, context, new=True)
            if infixes and infixes.get(lang) and not res:
                new_text = bracket_infixes(new_text, infixes[lang])
            if voice_to_add and not res:
                new_text = add_voice(new_text, voice_to_add)
                stats["voice_added"] += 1
            cur = (std.text or "").strip()
            if cur != old.strip():
                stats["handmade_standard_kept"] += 1
            elif new_text != cur:
                std.text = new_text
                if new_note:
                    std.set("notes", new_note)
                stats["redone"] += 1
                changed = True
            else:
                stats["preexisting_standard_kept"] += 1
            continue
        converted_segments = []
        any_res = False
        note_parts = []
        for where, seg in segments:
            if seg.strip():
                std_seg, is_res, seg_note = convert_gloss(
                    seg.strip(), table, rules, language, context)
                any_res = any_res or is_res
                if seg_note:
                    note_parts.append(seg_note)
            else:
                std_seg = seg
            converted_segments.append((where, std_seg))
        if any_res:   # any residue segment: the whole gloss copies verbatim
            converted_segments = segments
            stats["residue"] += 1
            residue[full[:60]] += 1
        elif "".join(s for _, s in converted_segments) != "".join(
                s for _, s in segments):
            stats["converted"] += 1
        else:
            stats["copied"] += 1
        if infixes and infixes.get(lang) and not any_res and len(converted_segments) == 1:
            converted_segments = [("text", bracket_infixes(converted_segments[0][1], infixes[lang]))]
            stats["infix_bracketed"] += 1
        if voice_to_add and not any_res and len(converted_segments) == 1:
            converted_segments = [("text", add_voice(converted_segments[0][1], voice_to_add))]
            stats["voice_added"] += 1
        new = ET.Element("TRANSL")
        new.set(XMLLANG, lang)
        new.set("kindOf", "standard")
        if ver:
            # V085: same-lang standards are discriminated by ver
            new.set("ver", ver)
        if note_parts and not any_res:
            # NOTE-PARENS chunks removed from the text live on the notes attr
            new.set("notes", " ".join(note_parts))
        new.text = converted_segments[0][1]
        for (child, _), (_w, std_tail) in zip(segments[1:],
                                              converted_segments[1:]):
            copy = ET.Element(child.tag, dict(child.attrib))
            copy.tail = std_tail
            new.append(copy)
        new.tail = transl.tail
        idx = list(parent).index(transl)
        parent.insert(idx + 1, new)
        existing_standard.add((lang, ver))
        changed = True
        stats["standard_added"] += 1
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", help="corpus name under Corpora/ (uses the "
                    "repo's Glossing/ConversionTables/<corpus>[.rules].tsv)")
    ap.add_argument("--corpora_path", default="Corpora")
    ap.add_argument("--path", help="explicit XML file/dir (with --table/--rules)")
    ap.add_argument("--table")
    ap.add_argument("--rules")
    ap.add_argument("--redo-changed", action="store_true",
                    help="re-derive existing tool-made standard glosses that the Rule 7 rules change")
    ap.add_argument("--write", action="store_true",
                    help="modify XML in place (default: dry run)")
    args = ap.parse_args()

    repo = pathlib.Path(__file__).resolve().parents[2]
    if args.corpus:
        xml_root = pathlib.Path(args.corpora_path) / args.corpus / "XML"
        table_p = repo / "Glossing" / "ConversionTables" / f"{args.corpus}.tsv"
        rules_p = repo / "Glossing" / "ConversionTables" / f"{args.corpus}.rules.tsv"
    else:
        if not (args.path and args.table and args.rules):
            ap.error("need --corpus, or --path with --table and --rules")
        xml_root, table_p, rules_p = (pathlib.Path(args.path),
                                      pathlib.Path(args.table),
                                      pathlib.Path(args.rules))
    table, rules = Table(table_p), Rules(rules_p)
    files = ([xml_root] if xml_root.is_file()
             else sorted(xml_root.rglob("*.xml")))
    stats: collections.Counter = collections.Counter()
    residue: collections.Counter = collections.Counter()
    nfiles = 0
    for f in files:
        try:
            process_file(f, table, rules, args.write, stats, residue, redo=args.redo_changed)
            nfiles += 1
        except ET.ParseError as err:
            print(f"PARSE ERROR {f}: {err}", file=sys.stderr)
    mode = "WROTE" if args.write else "DRY RUN"
    print(f"{mode}: {nfiles} files | " +
          " ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    if residue:
        print(f"residue ({sum(residue.values())} glosses copied verbatim; "
              "top 10):")
        for g, n in residue.most_common(10):
            print(f"  {g!r} ×{n}")


if __name__ == "__main__":
    main()
