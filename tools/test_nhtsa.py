"""Source import regressions: COPY semantics, joins, ambiguity and exclusions."""
import copy
import io
from pathlib import Path
import tempfile
import unittest

import nhtsa


class NhtsaImportTest(unittest.TestCase):
    def tables(self):
        # Independent miniature COPY source, including a NULL legacy makeid.
        source = (
            "COPY vpic.manufacturer (id, name) FROM stdin;\n1\tSynthetic Österreich\n\\.\n"
            "COPY vpic.make (id, name) FROM stdin;\n10\tBrand A\n11\tBrand B\n\\.\n"
            "COPY vpic.vehicletype (id, name) FROM stdin;\n2\tPassenger Car\n\\.\n"
            "COPY vpic.wmi (id, wmi, manufacturerid, makeid, vehicletypeid, publicavailabilitydate, noncompliant) FROM stdin;\n"
            "100\tABC\t1\t\\N\t2\t2020-01-01 00:00:00\t\\N\n\\.\n"
            "COPY vpic.wmi_make (wmiid, makeid) FROM stdin;\n100\t10\n100\t11\n\\.\n"
            "COPY vpic.pattern (id, keys) FROM stdin;\n7\t**A|B\n8\t[C-D]*\n\\.\n"
        )
        return nhtsa.read_tables(io.StringIO(source))

    def test_copy_null_literal_slashes_controls_and_utf8_bytes(self):
        self.assertIsNone(nhtsa.copy_value(r"\N"))
        self.assertEqual(r"\N", nhtsa.copy_value(r"\\N"))
        self.assertEqual("Österreich\tline\nnext\\end", nhtsa.copy_value(r"Österreich\tline\nnext\\end"))
        self.assertEqual("ä/ä", nhtsa.copy_value(r"\303\244/\xc3\xa4"))
        tables, inventory = self.tables()
        self.assertIsNone(tables["wmi"][0]["makeid"])
        self.assertNotIn("pattern", tables)
        self.assertEqual({"columns": ["id", "keys"], "rowCount": 2}, inventory["pattern"])

    def test_authoritative_many_to_many_join_does_not_choose_first_brand(self):
        tables, _ = self.tables()
        mfrs, assignments, exclusions = nhtsa.project(tables)
        self.assertEqual([], exclusions)
        self.assertEqual("Synthetic Österreich", mfrs[0]["name"])
        self.assertEqual({"BRAND A", "BRAND B"}, {a["brand"] for a in assignments})
        self.assertEqual({"nhtsa-wmi-abc"}, {a["ambiguityGroup"] for a in assignments})
        self.assertTrue(all(a["constraints"] == {} for a in assignments))
        self.assertNotIn("country", mfrs[0])
        tables["wmi_make"][0]["makeid"] = "999"
        with self.assertRaisesRegex(ValueError, "Unresolved wmi_make"):
            nhtsa.project(tables)

    def test_exclusions_are_explicit_and_noncompliance_remains_visible(self):
        tables, _ = self.tables()
        tables["wmi"][0]["noncompliant"] = "t"
        for key, value, reason in [("wmi", "ABO", "Invalid VIN alphabet"),
                                    ("publicavailabilitydate", None, "No public-availability"),
                                    ("publicavailabilitydate", "2099-01-01 00:00:00", "after snapshot")]:
            with self.subTest(reason=reason):
                altered = copy.deepcopy(tables)
                altered["wmi"][0][key] = value
                _, assignments, exclusions = nhtsa.project(altered)
                self.assertEqual([], assignments)
                self.assertEqual("100", exclusions[0]["wmiId"])
                self.assertIn(reason, exclusions[0]["reasons"][0])
        _, assignments, _ = nhtsa.project(tables)
        self.assertIn("noncompliant", assignments[0]["notes"])

    def test_truncated_bad_width_or_duplicate_copy_fails(self):
        for source in ("COPY vpic.wmi (id) FROM stdin;\n1\n",
                       "COPY vpic.wmi (id, wmi) FROM stdin;\n1\n\\.\n",
                       "COPY vpic.wmi (id) FROM stdin;\n\\.\nCOPY vpic.wmi (id) FROM stdin;\n\\.\n"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                nhtsa.read_tables(io.StringIO(source))

    def test_wrong_archive_is_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "wrong.zip"
            archive.write_bytes(b"not the reviewed source")
            with self.assertRaisesRegex(ValueError, "SHA-256 pin"):
                nhtsa.derive(archive)


if __name__ == "__main__":
    unittest.main()
