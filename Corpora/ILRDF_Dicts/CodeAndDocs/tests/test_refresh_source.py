import gzip
import unittest

from refresh_source import deterministic_gzip, deterministic_json


class DeterministicSnapshotTests(unittest.TestCase):
    def test_json_and_gzip_are_byte_stable(self):
        payload = {"z": "族語", "a": [2, 1]}
        raw = deterministic_json(payload)
        first = deterministic_gzip(raw)
        second = deterministic_gzip(raw)
        self.assertEqual(first, second)
        self.assertEqual(gzip.decompress(first), raw)
        self.assertEqual(raw.decode("utf-8"), '{"a":[2,1],"z":"族語"}\n')


if __name__ == "__main__":
    unittest.main()
