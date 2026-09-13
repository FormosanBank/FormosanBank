"""The published-id ledger replaces source-drift auditing.

Zero-source-drift was the wrong invariant: reproducibility is checked by
diffing a rebuild against the published tree, and a refresh after an upstream
change *should* change the text. What must hold is that ids never change
silently. They may be deleted (an item is suppressed) or added (new upstream
items, or a split), but always declared.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_xml import audit_ids, load_ledger, render_ledger  # noqa: E402

G1 = "11111111-1111-4111-8111-111111111111"
G2 = "22222222-2222-4222-8222-222222222222"
G3 = "33333333-3333-4333-8333-333333333333"

LEDGER = f"""id,source_guids,status,note
Amis_{G1},{G1},active,
Amis_{G2},{G2} {G3},active,merged under two headwords
Amis_{G3},{G3},suppressed,lesson number not a translation
"""


def _ledger(tmp: Path, text: str = LEDGER) -> dict:
    path = tmp / "published_ids.csv"
    path.write_text(text, encoding="utf-8")
    return load_ledger(path)


class TestLedgerLoading(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).resolve().parent / "_tmp_ledger"
        self.tmp.mkdir(exist_ok=True)

    def tearDown(self):
        for f in self.tmp.glob("*"):
            f.unlink()
        self.tmp.rmdir()

    def test_guids_parse_as_a_set(self):
        rows = _ledger(self.tmp)
        self.assertEqual(rows[f"Amis_{G2}"].source_guids, {G2, G3})

    def test_status_round_trips(self):
        rows = _ledger(self.tmp)
        self.assertEqual(rows[f"Amis_{G3}"].status, "suppressed")

    def test_render_is_stable_and_reloadable(self):
        rows = _ledger(self.tmp)
        reloaded = load_ledger_text(render_ledger(rows))
        self.assertEqual(
            {k: (v.source_guids, v.status) for k, v in rows.items()},
            {k: (v.source_guids, v.status) for k, v in reloaded.items()},
        )


def load_ledger_text(text: str) -> dict:
    import io
    from generate_xml import _parse_ledger
    return _parse_ledger(io.StringIO(text))


class TestAuditIds(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(__file__).resolve().parent / "_tmp_ledger2"
        self.tmp.mkdir(exist_ok=True)
        self.rows = _ledger(self.tmp)

    def tearDown(self):
        for f in self.tmp.glob("*"):
            f.unlink()
        self.tmp.rmdir()

    def test_clean_run_has_no_errors(self):
        xml_ids = {f"Amis_{G1}", f"Amis_{G2}"}
        extracted = {f"Amis_{G1}": {G1}, f"Amis_{G2}": {G2, G3}}
        self.assertEqual(audit_ids(self.rows, xml_ids, extracted), [])

    def test_active_id_missing_from_xml_fails(self):
        xml_ids = {f"Amis_{G1}"}
        extracted = {f"Amis_{G1}": {G1}, f"Amis_{G2}": {G2, G3}}
        errors = audit_ids(self.rows, xml_ids, extracted)
        self.assertTrue(any("silently deleted" in e for e in errors), errors)

    def test_suppressed_id_absent_from_xml_is_fine(self):
        xml_ids = {f"Amis_{G1}", f"Amis_{G2}"}
        extracted = {f"Amis_{G1}": {G1}, f"Amis_{G2}": {G2, G3}}
        errors = audit_ids(self.rows, xml_ids, extracted)
        self.assertFalse(any(G3 in e and "silently deleted" in e for e in errors))

    def test_undeclared_xml_id_fails(self):
        new = "44444444-4444-4444-8444-444444444444"
        xml_ids = {f"Amis_{G1}", f"Amis_{G2}", f"Amis_{new}"}
        extracted = {f"Amis_{G1}": {G1}, f"Amis_{G2}": {G2, G3}}
        errors = audit_ids(self.rows, xml_ids, extracted)
        self.assertTrue(any("not in the ledger" in e for e in errors), errors)

    def test_reassigned_guids_fail(self):
        """The check nothing else catches: an id now points at other material."""
        xml_ids = {f"Amis_{G1}", f"Amis_{G2}"}
        extracted = {f"Amis_{G1}": {G1}, f"Amis_{G2}": {G2}}  # G3 dropped out
        errors = audit_ids(self.rows, xml_ids, extracted)
        self.assertTrue(any("source GUIDs changed" in e for e in errors), errors)

    def test_split_child_inherits_the_parent_row(self):
        text = (
            LEDGER.replace(
                f"Amis_{G1},{G1},active,\n", f"Amis_{G1},{G1},split-parent,\n")
            + f"Amis_{G1}_a,{G1},active,split from a numbered record\n"
            + f"Amis_{G1}_b,{G1},active,split from a numbered record\n"
        )
        rows = _ledger(self.tmp, text)
        xml_ids = {f"Amis_{G1}_a", f"Amis_{G1}_b", f"Amis_{G2}"}
        extracted = {f"Amis_{G1}": {G1}, f"Amis_{G2}": {G2, G3}}
        self.assertEqual(audit_ids(rows, xml_ids, extracted), [])


class TestGenerateWritesSourceTiersOnly(unittest.TestCase):
    def test_no_restore_source_mode(self):
        import generate_xml
        self.assertEqual(generate_xml.MODES, ("generate", "audit", "ledger"))
        self.assertFalse(hasattr(generate_xml, "_restore_processed"))

    def test_build_tree_emits_no_derived_tiers(self):
        import generate_xml
        from ilrdf_source import Sentence
        s = Sentence(original="Form.", language="Amis")
        s.source_ids.add(G1)
        s.translations.append(("zho", "翻譯。"))
        root = generate_xml._build_tree("Amis", [s], "2026-08-21")
        for sentence in root.findall("S"):
            self.assertEqual(
                [f.get("kindOf") for f in sentence.findall("FORM")], ["original"])
            self.assertIsNone(sentence.find("PHON"))


if __name__ == "__main__":
    unittest.main()
