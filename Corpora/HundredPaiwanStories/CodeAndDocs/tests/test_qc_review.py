from __future__ import annotations

import os
import unittest
from pathlib import Path

from scripts.review_qc_findings import read_csv, review


ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = Path(os.environ.get("PAIWAN_XML_ROOT", ROOT / "XML")).resolve()
REPORTS_ROOT = Path(os.environ.get("PAIWAN_REPORTS_ROOT", ROOT / "reports")).resolve()


def finding(rule_id: str, severity: str, location: str = "S=001S1") -> dict[str, str]:
    return {
        "file": "XML/PaiwanCh2_001.xml",
        "line": "",
        "severity": severity,
        "rule_id": rule_id,
        "title": "invented_for_test",
        "location": location,
        "language": "",
        "character": "",
        "count": "1",
        "message": "",
    }


class QCFindingReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        qc = REPORTS_ROOT / "qc"
        cls.rows = {
            name: read_csv(qc / f"{name}.csv")
            for name in ("xml", "text", "gloss", "scrape")
        }

    def run_review(self, **extra: list[dict[str, str]]) -> dict[str, object]:
        rows = {name: [*found, *extra.get(name, [])] for name, found in self.rows.items()}
        return review(
            XML_ROOT,
            rows["xml"],
            rows["text"],
            rows["gloss"],
            rows["scrape"],
            ROOT / "standard_surface_decisions.tsv",
        )

    def test_unreviewed_soft_rule_is_reported_not_failed(self) -> None:
        summary = self.run_review(text=[finding("V999", "SOFT")])
        self.assertEqual(summary["unreviewed_findings"]["V999"]["count"], 1)
        self.assertTrue(summary["ready_to_port"])

    def test_unreviewed_hard_rule_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "unreviewed HARD findings"):
            self.run_review(xml=[finding("V999", "HARD")])

    def test_reviewed_rule_above_its_reviewed_count_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "more findings than reviewed"):
            self.run_review(gloss=[finding("V064", "SOFT", "M=001S1W1M0")])

    def test_every_remaining_finding_has_an_exact_review(self) -> None:
        summary = self.run_review()
        # One HARD finding is accepted by design: G001 on 078S4W19, whose
        # final -i the source leaves unglossed. review() pins it to that exact
        # location, so any other hard finding fails before reaching here.
        self.assertEqual(summary["hard_findings"], 1)
        self.assertEqual(list(summary["accepted_hard_findings"]), ["G001"])
        self.assertIn("078S4W19", summary["accepted_hard_findings"]["G001"])
        self.assertTrue(summary["ready_to_port"])


if __name__ == "__main__":
    unittest.main()
