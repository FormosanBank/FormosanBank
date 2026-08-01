#!/usr/bin/env python3

import unittest

from normalize_standard_forms import normalize_standard


class NormalizeStandardTests(unittest.TestCase):
    def test_removes_bunun_morpheme_boundaries(self) -> None:
        value, _ = normalize_standard(
            "Maza na-ia hai, nii tu ha-iap mas itu Isbubukun tu halinga."
        )
        self.assertEqual(
            value, "Maza naia hai, nii tu haiap mas itu Isbubukun tu halinga."
        )

    def test_selects_first_equals_alternative(self) -> None:
        value, _ = normalize_standard(
            "ata tu kmaanasapunuqi! = ata tu kmasapunuqi!"
        )
        self.assertEqual(value, "ata tu kmaanasapunuqi!")

    def test_selects_lexical_slash_alternatives(self) -> None:
        value, _ = normalize_standard("msr'ux sami/myan tay/te 'zil.")
        self.assertEqual(value, "msr'ux sami tay 'zil.")

    def test_selects_discontinuous_slash_alternatives(self) -> None:
        value, _ = normalize_standard(
            "iyat ta' / ta zngyun gaga' / gaga ta' nanak."
        )
        self.assertEqual(value, "iyat ta' zngyun gaga' ta' nanak.")

    def test_removes_parenthetical_and_editor_notes(self) -> None:
        value, _ = normalize_standard(
            "ti mulitan(女子名) a galju ni kina tjai rungrung(男子名)."
        )
        self.assertEqual(value, "ti mulitan a galju ni kina tjai rungrung.")

    def test_removes_atayal_infix_placeholder(self) -> None:
        value, _ = normalize_standard("m_yan phpah kinbetunux i Hana'.")
        self.assertEqual(value, "myan phpah kinbetunux i Hana'.")


if __name__ == "__main__":
    unittest.main()
