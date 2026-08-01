#!/usr/bin/env python3

import unittest

from normalize_standard_forms import normalize_standard


class NormalizeStandardTests(unittest.TestCase):
    def test_removes_bunun_morpheme_boundaries(self) -> None:
        value, _ = normalize_standard("Ma-aq tu siduq a ni-i tu papia ka?")
        self.assertEqual(value, "Maaq tu siduq a nii tu papia ka?")

    def test_selects_attached_lexical_alternative(self) -> None:
        value, _ = normalize_standard("ya asa ka neyciyo/niciyo?")
        self.assertEqual(value, "ya asa ka neyciyo?")

    def test_selects_spaced_lexical_alternative(self) -> None:
        value, _ = normalize_standard("Smkuxul meuyas / matas patas ka hiya.")
        self.assertEqual(value, "Smkuxul meuyas patas ka hiya.")

    def test_selects_complete_clause_alternatives(self) -> None:
        value, _ = normalize_standard(
            "Mtilux karac saya hu? / Mcilux karac saya haw? "
            "Uxay, msekuy saya. / Haray, mskuy ba saya."
        )
        self.assertEqual(
            value, "Mtilux karac saya hu? Uxay, msekuy saya."
        )

    def test_parenthetical_teaching_alternative_is_removed(self) -> None:
        value, _ = normalize_standard(
            "tanek kamo! kaminan kong! (maran kong! / kokay mo sinsi)"
        )
        self.assertEqual(value, "tanek kamo! kaminan kong!")

    def test_explicit_template_surface_wins(self) -> None:
        value, reasons = normalize_standard("tam+人名", template_surface="tam")
        self.assertEqual(value, "tam")
        self.assertEqual(reasons, ("grammar-template",))

    def test_complete_parenthetical_song_line_is_unwrapped(self) -> None:
        value, _ = normalize_standard(
            "(homayap 'ita:o Siboe, yata:ow Siboe i boe:oe)",
            unwrap_outer_parentheses=True,
        )
        self.assertEqual(value, "homayap 'ita:o Siboe, yata:ow Siboe i boe:oe")

    def test_unmatched_source_parenthesis_is_removed(self) -> None:
        value, _ = normalize_standard("kaadihay (")
        self.assertEqual(value, "kaadihay")


if __name__ == "__main__":
    unittest.main()
