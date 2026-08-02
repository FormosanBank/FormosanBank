#!/usr/bin/env python3

import unittest

from normalize_standard_forms import normalize_standard


class NormalizeStandardTests(unittest.TestCase):
    def test_preserves_ambiguous_bunun_hyphens(self) -> None:
        value, _ = normalize_standard(
            "Maza na-ia hai, nii tu ha-iap mas itu Isbubukun tu halinga."
        )
        self.assertEqual(
            value, "Maza na-ia hai, nii tu ha-iap mas itu Isbubukun tu halinga."
        )

    def test_preserves_hyphens_in_proper_names(self) -> None:
        source = "cimʉrʉ na Tai-uan ia, Tanungu'incu mastaan maringʉcai."
        value, _ = normalize_standard(source)
        self.assertEqual(value, source)

    def test_selects_first_equals_alternative(self) -> None:
        value, _ = normalize_standard(
            "ata tu kmaanasapunuqi! = ata tu kmasapunuqi!",
            sentence_id="Thao_1332",
        )
        self.assertEqual(value, "ata tu kmaanasapunuqi!")

    def test_selects_lexical_slash_alternatives(self) -> None:
        value, _ = normalize_standard(
            "msr'ux sami/myan tay/te 'zil.", sentence_id="Atayal_4629"
        )
        self.assertEqual(value, "msr'ux sami tay 'zil.")

    def test_selects_discontinuous_slash_alternatives(self) -> None:
        value, _ = normalize_standard(
            "iyat ta' / ta zngyun gaga' / gaga ta' nanak.",
            sentence_id="Atayal_5144",
        )
        self.assertEqual(value, "iyat ta' zngyun gaga' ta' nanak.")

    def test_removes_parenthetical_and_editor_notes(self) -> None:
        value, _ = normalize_standard(
            "ti mulitan(女子名) a galju ni kina tjai rungrung(男子名)."
        )
        self.assertEqual(value, "ti mulitan a galju ni kina tjai rungrung.")

    def test_preserves_atayal_schwa_notation(self) -> None:
        value, _ = normalize_standard("m_yan phpah kinbetunux i Hana'.")
        self.assertEqual(value, "m_yan phpah kinbetunux i Hana'.")

    def test_repairs_numeric_parenthetical_from_translation(self) -> None:
        value, reasons = normalize_standard(
            "u miasikay i satakalaway a luma' (101) ci Panay.",
            sentence_id="Sakizaya_2511",
        )
        self.assertEqual(
            value, "u miasikay i satakalaway a luma' 101 ci Panay."
        )
        self.assertEqual(reasons, ("reviewed-source-repair",))

    def test_repairs_saaroa_extraction_artifact(self) -> None:
        value, _ = normalize_standard(
            "u數詞u paapuhla ualuia laihla upatu.",
            sentence_id="Saaroa_1716",
        )
        self.assertEqual(value, "ʉnʉmʉ paapuhla ualuia laihla upatu.")


if __name__ == "__main__":
    unittest.main()
