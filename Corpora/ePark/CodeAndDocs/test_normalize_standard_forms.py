#!/usr/bin/env python3

import unittest

from normalize_standard_forms import normalize_standard


class NormalizeStandardTests(unittest.TestCase):
    def test_preserves_ambiguous_bunun_hyphens(self) -> None:
        value, _ = normalize_standard("Ma-aq tu siduq a ni-i tu papia ka?")
        self.assertEqual(value, "Ma-aq tu siduq a ni-i tu papia ka?")

    def test_preserves_thao_loanword_hyphens(self) -> None:
        value, _ = normalize_standard("tian-sii")
        self.assertEqual(value, "tian-sii")

    def test_preserves_orthographic_underscore(self) -> None:
        value, _ = normalize_standard("n_gyut m_yan ling_wa")
        self.assertEqual(value, "n_gyut m_yan ling_wa")

    def test_preserves_numeric_slashes(self) -> None:
        value, _ = normalize_standard("lalu: Ciwas ryax: 2013/05/23")
        self.assertEqual(value, "lalu: Ciwas ryax: 2013/05/23")

    def test_preserves_attached_lexical_alternative(self) -> None:
        value, _ = normalize_standard("ya asa ka neyciyo/niciyo?")
        self.assertEqual(value, "ya asa ka neyciyo/niciyo?")

    def test_preserves_spaced_lexical_alternative(self) -> None:
        value, _ = normalize_standard("Smkuxul meuyas / matas patas ka hiya.")
        self.assertEqual(value, "Smkuxul meuyas / matas patas ka hiya.")

    def test_substantive_parenthetical_is_preserved(self) -> None:
        source = "sahuy linnglung (mmemung myulung na)"
        value, _ = normalize_standard(source)
        self.assertEqual(value, source)

    def test_short_parenthetical_is_preserved_without_review(self) -> None:
        source = "sira pipia (piya) so kataotao"
        value, _ = normalize_standard(source)
        self.assertEqual(value, source)

    def test_code_switched_cjk_is_preserved(self) -> None:
        source = "anini sa pararid sa i 文化健康站 no niyaro' cingra"
        value, _ = normalize_standard(source)
        self.assertEqual(value, source)

    def test_explicit_template_surface_wins(self) -> None:
        value, reasons = normalize_standard("tam+人名", template_surface="tam")
        self.assertEqual(value, "tam")
        self.assertEqual(reasons, ("grammar-template",))

    def test_splits_reviewed_puyuma_en_dash_boundary(self) -> None:
        value, reasons = normalize_standard(
            "na palribak–a trakubakuban.", split_puyuma_en_dash=True
        )
        self.assertEqual(value, "na palribak a trakubakuban.")
        self.assertEqual(reasons, ("Puyuma-en-dash-word-boundary",))

    def test_unmatched_source_parenthesis_is_preserved_without_review(self) -> None:
        value, _ = normalize_standard("kaadihay (")
        self.assertEqual(value, "kaadihay (")


if __name__ == "__main__":
    unittest.main()
