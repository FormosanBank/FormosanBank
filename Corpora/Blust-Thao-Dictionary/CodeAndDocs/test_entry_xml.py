"""What the entry XML must be true of, in the shape of test_entries.py.

test_entries.py asserts things about the parse. These assert the same things
survive the pipeline - build -> clean_xml -> standardize -> add_phonology - and
add the ones that only exist once there is XML: tier pairing, id shape, and
that nothing the schema forbids reached the file.
"""

import collections
import re
import unittest
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
XML_DIR = Path(__file__).resolve().parents[1] / "XML" / "Thao"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
THAO_ONLY_LETTERS = re.compile(r"[vxVX]")


def load():
    trees = {}
    for path in sorted(XML_DIR.glob("*.xml")):
        trees[path.name] = etree.parse(str(path)).getroot()
    return trees


class TestEntryXML(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trees = load()
        assert cls.trees, f"no XML under {XML_DIR}"
        cls.entries = {n: r for n, r in cls.trees.items() if "_entries_" in n}
        cls.examples = {n: r for n, r in cls.trees.items() if "_examples_" in n}
        cls.texts = {n: r for n, r in cls.trees.items() if "_text_" in n}
        cls.all_s = [s for r in cls.trees.values() for s in r.findall("S")]
        # The published tree has three families of file. The five interlinear
        # texts come from the other pipeline and carry their own id and locator
        # shape, so the assertions about entry ids and entry locators are over
        # the dictionary's own sentences (maintainer, 2026-09-11).
        cls.dictionary_s = [
            s
            for name, r in cls.trees.items()
            if "_text_" not in name
            for s in r.findall("S")
        ]

    # -- the file is legal at all ---------------------------------------
    def test_both_families_are_present(self):
        self.assertEqual(len(self.entries), 8)
        self.assertEqual(len(self.examples), 8)

    def test_no_control_characters(self):
        for name, root in self.trees.items():
            for element in root.iter():
                for value in [element.text] + list(element.attrib.values()):
                    if value and CONTROL.search(value):
                        self.fail(f"{name}: {element.tag} {value[:40]!r}")

    def test_every_text_carries_the_required_metadata(self):
        for name, root in self.trees.items():
            for attribute in ("id", "citation", "BibTeX_citation", "copyright",
                              "source", "glottocode", "dialect"):
                self.assertTrue(root.get(attribute), f"{name} has no @{attribute}")
            self.assertEqual(root.get(XML_LANG), "ssf", name)
            self.assertEqual(root.get("copyright"), "CC BY-NC 4.0", name)

    # -- ids (POL-037) ---------------------------------------------------
    def test_the_five_interlinear_texts_are_published(self):
        """They come from build_xml.py; without them the corpus loses
        Blust's only running prose - 167 sentences and 2,542 interlinear
        word forms."""
        self.assertEqual(len(self.texts), 5, sorted(self.texts))
        text_s = [s for r in self.texts.values() for s in r.findall('S')]
        self.assertEqual(len(text_s), 167)
        for sentence in text_s:
            self.assertRegex(sentence.get('id'), r'^blust-text-t\d{2}-s\d{3}')

    def test_an_id_names_the_page_the_sentence_is_printed_on(self):
        """Not the page its entry opens on.

        A long entry runs over several pages and every sense and example was
        inheriting the first: 2,436 examples and 1,820 senses carried a page
        they are not printed on. Checked against extract_source.py's own
        attribution, which is independent of this parser: 8,211 of 8,214
        examples matched by text now agree, and the three that do not are short
        sentences the book prints twice.

        The counter is therefore shared across the WHOLE build. An entry that
        opens on p.379 sits in the 0280-0379 file, but a sense of it printed on
        p.380 numbers against p.380 - and a per-file counter restarted there and
        collided with the next file's own p.380 ids.
        """
        for sentence in self.dictionary_s:
            page = int(re.search(r"p(\d{4})", sentence.get("id")).group(1))
            self.assertIn(f"printed p. {page};", sentence.get("source"))

    def test_sentence_ids_are_unique_and_shaped(self):
        seen = collections.Counter(s.get("id") for s in self.dictionary_s)
        duplicated = [i for i, n in seen.items() if n > 1]
        self.assertEqual(duplicated, [], duplicated[:5])
        # -qNN is a Thao question quoted inside an "answer to ..."
        # parenthetical, lifted out as a sentence of its own.
        pattern = re.compile(r"^blust-(entry|ex)-p\d{4}-[se]\d{3}(-q\d{2})?$")
        bad = [i for i in seen if not pattern.match(i)]
        self.assertEqual(bad, [], bad[:5])

    def test_word_ids_extend_their_sentence_id(self):
        for sentence in self.dictionary_s:
            for word in sentence.findall("W"):
                self.assertTrue(
                    word.get("id").startswith(sentence.get("id") + "-w"),
                    word.get("id"),
                )
                for morpheme in word.findall("M"):
                    self.assertTrue(
                        morpheme.get("id").startswith(word.get("id") + "-m"),
                        morpheme.get("id"),
                    )

    # -- tiers -----------------------------------------------------------
    def test_every_sentence_has_both_form_tiers(self):
        for sentence in self.dictionary_s:
            kinds = [f.get("kindOf") for f in sentence.findall("FORM")]
            self.assertIn("original", kinds, sentence.get("id"))
            self.assertIn("standard", kinds, sentence.get("id"))

    def test_no_form_is_empty(self):
        for sentence in self.dictionary_s:
            for form in sentence.iter("FORM"):
                self.assertTrue(
                    (form.text or "").strip(),
                    f"{sentence.get('id')} has an empty FORM",
                )

    def test_phonology_pairs_with_every_form(self):
        # POL-003: PHON is machine-owned and follows FORM one for one.
        for sentence in self.dictionary_s:
            for parent in [sentence] + sentence.findall(".//W") + sentence.findall(".//M"):
                # A ver FORM takes no PHON of its own: PHON has no @ver, so a
                # tier has one and it belongs to the base (POL-028).
                forms = [
                    f.get("kindOf") for f in parent.findall("FORM")
                    if not f.get("ver")
                ]
                phons = [p.get("kindOf") for p in parent.findall("PHON")]
                self.assertEqual(sorted(forms), sorted(phons), sentence.get("id"))

    def test_translations_are_english(self):
        for sentence in self.dictionary_s:
            for translation in sentence.findall("TRANSL"):
                self.assertEqual(translation.get(XML_LANG), "eng", sentence.get("id"))
                self.assertTrue((translation.text or "").strip(), sentence.get("id"))

    # -- the content is what it claims to be (test_entries.py's concerns) --
    NOTATION = re.compile(r"[()/~\[\]]")

    def test_every_sentence_has_one_W_per_word(self):
        """No FORM carries lexicographic notation, so no sentence is skipped.

        309 did, and each shape now has a reading: a bracket inside a word
        becomes a ver="alt" FORM, a bracket standing as its own token becomes
        two readings, a slash becomes one reading each. The last five were the
        maintainer's calls of 2026-09-11 - two citation slashes ruled
        typographical, three records whose readings they gave outright.

        Notation in a W FORM is V121 HARD, so this is the property that keeps
        it out, and V148 (a file with some sentences unsegmented) is gone with
        it.
        """
        for sentence in self.dictionary_s:
            form = sentence.find('FORM[@kindOf="original"]')
            self.assertFalse(
                self.NOTATION.search(form.text), f"{sentence.get('id')}: {form.text!r}"
            )
            self.assertEqual(
                len(sentence.findall("W")),
                len(form.text.split()),
                sentence.get("id"),
            )

    def test_the_morpheme_tier_is_all_or_nothing(self):
        # POL-023 reads the M tier per sentence.
        for sentence in self.dictionary_s:
            words = sentence.findall("W")
            if not words:
                continue
            with_m = [w for w in words if w.findall("M")]
            self.assertIn(len(with_m), (0, len(words)), sentence.get("id"))

    def test_no_structural_marker_leaked_into_a_value(self):
        leak = re.compile(r"\bnotes?\s*:", re.IGNORECASE)
        for sentence in self.dictionary_s:
            for element in list(sentence.iter("FORM")) + list(sentence.iter("TRANSL")):
                self.assertFalse(
                    leak.search(element.text or ""),
                    f"{sentence.get('id')}: {element.text[:50]!r}",
                )

    def test_headwords_do_not_use_letters_thao_lacks(self):
        # `e` and `o` are Thao (names and loanwords); v and x are not.
        offenders = [
            (s.get("id"), s.find('FORM[@kindOf="original"]').text)
            for name, root in self.entries.items() for s in root.findall("S")
            if THAO_ONLY_LETTERS.search(s.find('FORM[@kindOf="original"]').text or "")
        ]
        self.assertEqual(offenders, [], offenders[:5])

    def test_no_new_example_is_a_single_word(self):
        """An example is never one word - a one-word FORM is a truncation.

        There were 49, all truncations: the sentence ran across a printed line
        and only its tail reached the FORM. Reading a Thao run that OPENS an
        indented line as a continuation rather than a new example retired 35 of
        them and took E10 (example with no bold word) from 38 to 0.

        The 14 that remain are real one-word sentences - `cakaw!` "You are
        greedy!", `minu?` "What is it?", `kalhus!` "Go to sleep!" - so the count
        is held, not driven to zero.
        """
        singles = [
            s.get("id") for root in self.examples.values() for s in root.findall("S")
            if len(s.find('FORM[@kindOf="original"]').text.split()) <= 1
        ]
        # 8 now. Six of the fourteen were the same single word published
        # twice: three closed when the dedup began keying the gloss on its
        # words rather than its typesetting (the last was p.415
        # `shan-na-ikahi`, `Wait awhile!` against `wait awhile`), and three
        # more on the maintainer's verdicts in same-form-rulings.json, which
        # folded p.345 `pashi-caycuy`, p.793 `pish-qilha-z` and p.1057
        # `pashi-yakin` into the entries they illustrate.
        self.assertEqual(len(singles), 8, singles[:8])

    def test_every_example_has_a_translation(self):
        # p0835-e006 - `ani yaku ma-min-riqaz atu`, the first defect the
        # maintainer ever reported - is fixed: the book set its English in the
        # definition face, and an indented body line arriving while an example
        # is open and untranslated is now read as that translation.
        #
        # The last one standing was p.887 `tata wa shaba `100\'; tusha wa
        # shaba` / `200`, where Blust sets the first gloss in the Thao face and
        # wraps the second onto its own line. The maintainer read it as two
        # examples, 100 and 200, and curated-readings.json carries that.
        missing = [
            s.get("id") for root in self.examples.values() for s in root.findall("S")
            if not s.findall("TRANSL")
        ]
        self.assertEqual(missing, [])

    def test_a_quoted_question_becomes_its_own_sentence(self):
        """Blust answers a question inside a parenthetical and sets it in Thao:

            I just sowed the rice (answer to Shi-ntua ihu? Where did you go?)

        That is a Thao sentence with a translation sitting inside a note, so it
        is lifted out rather than left as prose. Four in the book; the Thao is
        recognised by its font at parse time, not guessed from the string.

        Three of the four publish. p.303 quotes a question the same page also
        prints as a running example, and the two glosses differ only in a
        capital - `did you take my money?` against `Did you take my money?` -
        so the dedup keeps one. The lift still has to happen for the parse to
        be right; what is asserted here is the outcome, and the survivor is
        blust-ex-p0303-e018.
        """
        quoted = {
            s.get("id"): (
                s.find('FORM[@kindOf="original"]').text,
                s.find("TRANSL").text,
            )
            for root in self.examples.values()
            for s in root.findall("S")
            if re.search(r"-q\d{2}$", s.get("id"))
        }
        self.assertEqual(
            quoted,
            {
                "blust-ex-p0383-e006-q01": (
                    "Shi-ntua ihu?", "Where did you go?"),
                "blust-ex-p0629-e001-q01": (
                    "la-piza m-ihu a azazak", "How many children do you have?"),
                "blust-ex-p0876-e009-q01": (
                    "shi-ntua ihu?", "Where were you?"),
            },
        )
        for identifier in quoted:
            host = identifier.rsplit("-q", 1)[0]
            self.assertIn(host, {s.get("id") for r in self.examples.values()
                                 for s in r.findall("S")})

    def test_every_tier_is_in_the_language_it_claims(self):
        """The cleanliness test, run the same way over both builds.

        Both trees now score zero. The last one standing was printed p.832,
        which fails to leave the sub-entry face so that an English definition is
        set as though it were a Thao form - `masa-rima masay rima use the hand
        for some purpose`. The maintainer ruled it two spellings of one word
        with the alternation slash dropped, and curated-readings.json carries
        that: one S, one English, and `masay rima` as a ver="alt" FORM.
        """
        from language_check import check
        from validate_entries import load_lexicons

        english, thao = load_lexicons()
        counts, hits = check(XML_DIR, english, thao)
        self.assertEqual(
            [(rule, identifier) for rule, identifier, _ in hits], []
        )

    def test_the_provenance_locator_names_the_entry(self):
        for sentence in self.dictionary_s:
            self.assertRegex(sentence.get("source"), r"^printed p\. \d+; entry ")


if __name__ == "__main__":
    unittest.main()


class TestCuratedReadings(unittest.TestCase):
    """A curated reading is a maintainer's ruling the rules cannot derive.

    Two things have to stay true of that list, and neither is obvious from
    reading it: nothing on it is doing nothing, and nothing that came off it
    has been quietly lost. The maintainer's instruction, 2026-09-11:

        If a new rule makes a curated reading unnecessary (because it now
        resolves on its own), then we should stop having it. That makes the
        list shorter, which is good for anyone trying to figure out what
        happens during processing. BUT we should keep the now-superfluous
        decisions around as a kind of regression test.
    """

    @staticmethod
    def _english_by_printed():
        import json
        records = json.loads(
            (HERE / "entry-records.json").read_text(encoding="utf-8"))["entries"]
        english = {}
        for entry in records:
            for sense in entry["senses"]:
                if sense["form"]:
                    english.setdefault(sense["form"], sense["definition"] or "")
                for example in sense["examples"]:
                    english.setdefault(example["thao"], example["english"] or "")
        return english

    def test_no_curated_reading_is_superfluous(self):
        """Every entry in curated-readings.json must change the outcome.

        One that does not is a ruling the rules have caught up with; it belongs
        in settled-readings.json, where it goes on being checked without
        lengthening the list a reader has to hold in their head.
        """
        import build_entry_xml

        english = self._english_by_printed()
        curated = dict(build_entry_xml.CURATED_READINGS)
        idle = []
        for key in curated:
            with_it = build_entry_xml.readings(key, english.get(key, ""))
            build_entry_xml.CURATED_READINGS.pop(key)
            try:
                without = build_entry_xml.readings(key, english.get(key, ""))
            finally:
                build_entry_xml.CURATED_READINGS[key] = curated[key]
            if with_it == without:
                idle.append(key)
        self.assertEqual(
            idle, [],
            "the rules now derive these on their own - move them to "
            "settled-readings.json with a `retired` note: " + repr(idle))

    def test_settled_readings_still_hold(self):
        """A retired curation must still be what the rules produce.

        If one stops matching, the rule that replaced it has regressed: either
        fix the rule or put the curation back.
        """
        import json

        import build_entry_xml

        english = self._english_by_printed()
        settled = json.loads(
            (HERE / "settled-readings.json").read_text(encoding="utf-8"))
        checked = 0
        for key, record in settled.items():
            if key.startswith("_"):
                continue
            self.assertNotIn(
                key, build_entry_xml.CURATED_READINGS,
                f"{key!r} is in both curated-readings.json and "
                "settled-readings.json; it belongs in one")
            expected = [r["thao"] for r in record["readings"]]
            actual = [r[0] for r in
                      build_entry_xml.readings(key, english.get(key, ""))]
            self.assertEqual(
                actual, expected,
                f"the rules no longer reproduce the retired ruling on {key!r}")
            checked += 1
        self.assertGreater(checked, 0)
