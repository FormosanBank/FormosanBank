from __future__ import annotations

import os
import unittest
from pathlib import Path

from scripts.review_qc_findings import read_csv, review


ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = Path(os.environ.get("PAIWAN_XML_ROOT", ROOT / "XML")).resolve()
REPORTS_ROOT = Path(os.environ.get("PAIWAN_REPORTS_ROOT", ROOT / "reports")).resolve()


class QCFindingReviewTests(unittest.TestCase):
    def test_every_remaining_finding_has_an_exact_review(self) -> None:
        qc = REPORTS_ROOT / "qc"
        summary = review(
            XML_ROOT,
            read_csv(qc / "xml.csv"),
            read_csv(qc / "text.csv"),
            read_csv(qc / "gloss.csv"),
            read_csv(qc / "scrape.csv"),
            ROOT / "standard_surface_decisions.tsv",
        )
        # One HARD finding is accepted by design: G001 on 078S4W19, whose
        # final -i the source leaves unglossed. review() pins it to that exact
        # location, so any other hard finding fails before reaching here.
        self.assertEqual(summary["hard_findings"], 1)
        self.assertEqual(list(summary["accepted_hard_findings"]), ["G001"])
        self.assertIn("078S4W19", summary["accepted_hard_findings"]["G001"])
        self.assertTrue(summary["ready_to_port"])


if __name__ == "__main__":
    unittest.main()
