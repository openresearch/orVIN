from pathlib import Path
import shutil
import tempfile
import unittest

import kba


class KbaImportTest(unittest.TestCase):
    def setUp(self):
        self.row = {"Berichtszeitpunkt": "01.01.2026", "Herstellerschluessel": "0005",
                    "Herstellertext": "Synthetic", "Typschluessel": "AMQ", "Handelsname": None,
                    "Anzahl": None, "ZS_Anzahl": ".", "ObjectId": 1}

    def test_preserves_zeroes_nulls_markers_and_duplicate_type_candidates(self):
        alternative = {**self.row, "ObjectId": 2, "Handelsname": "Alternative"}
        text = kba.normalize([alternative, self.row], "2026-01-01").decode()
        self.assertIn("0005\tAMQ\tSynthetic\t\\N\t\\N\t.\t1\n", text)
        self.assertIn("0005\tAMQ\tSynthetic\tAlternative\t\\N\t.\t2\n", text)
        self.assertEqual(3, len(text.splitlines()))

    def test_incomplete_and_duplicate_downloads_are_rejected(self):
        for rows, ids, count in [([self.row], [1, 2], 2), ([self.row, self.row], [1, 2], 2),
                                  ([self.row], [2], 1), ([], [], 0)]:
            with self.assertRaisesRegex(ValueError, "Incomplete"):
                kba.check_completeness(rows, ids, count)

    def test_rejects_unexpected_shapes_dates_codes_counts_and_delimiters(self):
        for key, value in [("Berichtszeitpunkt", "01.01.2025"), ("Herstellerschluessel", "5"),
                            ("Typschluessel", "ＡMQ"), ("Anzahl", -1), ("Anzahl", True),
                            ("Handelsname", "bad\ttext"), ("Handelsname", "\\N")]:
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                kba.normalize([{**self.row, key: value}], "2026-01-01")
        with self.assertRaisesRegex(ValueError, "object ID"):
            kba.normalize([self.row, self.row], "2026-01-01")

    def test_pinned_snapshot_matches_canonical_table_and_tampering_fails(self):
        self.assertGreater(kba.validate()["recordCount"], 0)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            for name in ("metadata.json", "source.json.gz", "types.tsv"):
                shutil.copyfile(kba.DIRECTORY / name, path / name)
            with (path / "types.tsv").open("ab") as stream:
                stream.write(b"extra row\n")
            with self.assertRaisesRegex(ValueError, "changed KBA"):
                kba.validate(path)


if __name__ == "__main__":
    unittest.main()
