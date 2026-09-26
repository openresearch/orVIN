"""Regression checks for automatic refresh boundaries, independent of live sources."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import publish_refresh
import refresh_data


class StructuredRefreshTest(unittest.TestCase):
    def test_discovery_chooses_latest_documented_plain_archive(self):
        html = ('plain backup file "vPICList_lite_2025_09.plain.zip" updated on 09/19/2025 '
                'plain backup file "vPICList_lite_2025_10.plain.zip" updated on 10/18/2025')
        self.assertEqual(("vPICList_lite_2025_10.plain.zip", "2025_10", "2025-10-18"),
                         refresh_data.latest_nhtsa(html))
        for invalid in ("<html>Unavailable</html>",
                        'plain backup file "vPICList_lite_2099_01.plain.zip" updated on 01/01/2099'):
            with self.assertRaises(ValueError):
                refresh_data.latest_nhtsa(invalid)

    def test_empty_truncated_or_disproportionate_data_stops_refresh(self):
        for old, new in ((1000, 0), (1000, 900), (1000, 1600)):
            with self.subTest(old=old, new=new), self.assertRaises(ValueError):
                refresh_data.count_guard("rows", old, new)
        refresh_data.count_guard("rows", 1000, 1020)
        refresh_data.exclusion_guard("patterns", 50, 1000, 52, 1000)
        with self.assertRaises(ValueError):
            refresh_data.exclusion_guard("patterns", 50, 1000, 70, 1000)

    def test_sql_data_changes_are_allowed_but_schema_and_functions_are_not(self):
        def archive(path, columns="id, name", body="SELECT 1", value="1\tfirst"):
            with zipfile.ZipFile(path, "w") as zipped:
                zipped.writestr("vPICList_lite_2025_09.sql",
                    f"CREATE FUNCTION vpic.example() RETURNS integer\nAS $$\n{body}\n$$;\n"
                    f"COPY vpic.make ({columns}) FROM stdin;\n{value}\n\\.\n")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "test.zip"
            archive(path)
            before = refresh_data.sql_contract(path)
            archive(path, value="1\tupdated\n2\tadded")
            self.assertEqual(before, refresh_data.sql_contract(path))
            archive(path, columns="id, renamed")
            self.assertNotEqual(before, refresh_data.sql_contract(path))
            archive(path, body="SELECT 2")
            self.assertNotEqual(before, refresh_data.sql_contract(path))
            with zipfile.ZipFile(path, "w") as zipped:
                zipped.writestr("unexpected.sql", "SELECT 1")
            with self.assertRaises(ValueError):
                refresh_data.sql_contract(path)

    def test_referenced_historical_source_is_retained_once(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(refresh_data, "ROOT", Path(tmp)):
            root = Path(tmp)
            for name in ("identity/fixtures.json", "vehicle-fixtures.json", "astra/review.json", "snapshots/metadata.json"):
                p = root / "data" / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('[{"sourceRefs":["old-edition"]}]' if name == "vehicle-fixtures.json" else "[]")
            archive = root / "data/old.zip"
            archive.write_bytes(b"historical evidence")
            source = {"id": "old-edition", "url": "https://example.test/source"}
            self.assertTrue(refresh_data.preserve_referenced_source(source, archive))
            self.assertTrue(refresh_data.preserve_referenced_source(source, archive))
            history = json.loads((root / "data/snapshots/metadata.json").read_text())
            self.assertEqual(1, len(history))
            self.assertEqual("old.zip", history[0]["snapshot"])
            self.assertEqual(64, len(history[0]["sha256"]))
            self.assertFalse(refresh_data.preserve_referenced_source({"id": "uncited"}, archive))

    def test_publication_cannot_edit_curated_rules_or_test_expectations(self):
        publish_refresh.check_paths(["data/kba/types.tsv", "data/identity/index.tsv", "tools/source-pins.json"])
        for path in ("data/europe/tesla-model-y.json", "data/astra/review.json", "data/identity/fixtures.json",
                     "tools/astra.py", ".github/workflows/release.yml", "libs/python/orvin/answer.py"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                publish_refresh.check_paths(["data/kba/types.tsv", path])
        self.assertEqual("v0.10.1", publish_refresh.next_tag(["v0.9.9", "v0.10.0", "v0.11.0-rc1"]))
