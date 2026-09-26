"""Protect the PDF import's identifier, integrity and non-inference boundaries."""
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest

import kba_wmi


class KbaWmiImportTest(unittest.TestCase):
    def test_extended_identifier_matches_positions_12_to_14_without_prefix_fallback(self):
        row = {"page": 6, "row": 1, "label": "A+A HAHN", "hsn": "1031", "part1": "W09",
               "part2": "A53", "name": "A+A HAHN GMBH", "location": "NEUMÜNSTER"}
        rule, = kba_wmi.rules([row])
        self.assertIsNotNone(re.fullmatch(rule["pattern"], "W09AAAAAAAAA53001"))
        self.assertIsNone(re.fullmatch(rule["pattern"], "W09A53AAAAAAAAAAA"))
        self.assertIsNone(re.fullmatch(rule["pattern"], "W09AAAAAAAAA54001"))
        for column in ("part1", "part2"):
            changed = {**row, column: "WBI"}
            self.assertEqual([], list(kba_wmi.rules([changed])))

    def test_missing_cells_are_not_filled_or_reinterpreted_as_brand_plant_or_vehicle_hsn(self):
        row = {"page": 140, "row": 55, "label": "VOLKSWAGEN-VW (RA)", "hsn": "0600",
               "part1": "8AX", "part2": "", "name": "", "location": ""}
        rule, = kba_wmi.rules([row])
        self.assertEqual({"ManufacturerDirectoryLabel", "ManufacturerDirectoryHSN"},
                         {claim["code"] for claim in rule["claims"]})
        self.assertIn("PDF page 140, table row 55", rule["claims"][0]["keys"])
        self.assertEqual([], rule["markets"])
        self.assertNotIn("modelYear", rule)

    def test_source_tampering_and_unreviewed_pdf_fail_before_import(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name)
            (directory / "changed.pdf").write_bytes(b"unreviewed edition")
            with self.assertRaisesRegex(ValueError, "reviewed edition"):
                kba_wmi.extract_pdf(directory / "changed.pdf")
            metadata = json.loads((kba_wmi.DIRECTORY / "metadata.json").read_bytes())
            (directory / "metadata.json").write_text(json.dumps(metadata))
            (directory / metadata["snapshot"]).write_bytes(b"tampered table")
            with self.assertRaisesRegex(ValueError, "snapshot digest"):
                kba_wmi.load(directory)

    def test_comparison_retains_conflicts_missing_identifiers_and_invalid_printed_values(self):
        base = {"page": 6, "row": 1, "hsn": "0001", "part1": "ABC", "part2": "",
                "label": "Company A", "name": "Company A", "location": "City"}
        other = {**base, "row": 2, "name": "Company B", "hsn": "0002"}
        report = kba_wmi.comparison([base, other, {**base, "row": 3, "part1": "WBI"},
                                     {**base, "row": 4, "part1": ""}],
                {"manufacturers": [{"id": "m", "name": "Company C"}],
                 "assignments": [{"wmi": "ABC", "manufacturerId": "m"}]})
        self.assertEqual(1, report["counts"]["repeatedWmis"])
        self.assertEqual(["Company A", "Company B"], report["differingManufacturerLabels"][0]["kbaNames"])
        self.assertEqual("WBI", report["excludedRows"][0]["printedIdentifier"])
        self.assertEqual(["sv31-p006-r004"], report["rowsWithoutWmi"])
        changed = copy.deepcopy(base)
        changed["row"] = 2
        with self.assertRaisesRegex(ValueError, "locator"):
            kba_wmi.validate_rows([changed])

    def test_preference_requires_the_reviewed_kba_row_and_unchanged_nhtsa_identity(self):
        rows, metadata = kba_wmi.load()
        nhtsa = json.loads((kba_wmi.ROOT / "data/dataset.json").read_bytes())
        # Independent reviewed records: KBA PDF 34/78, NHTSA WMI 4873 / make 4657.
        rule, = kba_wmi.preference_rules(rows, metadata, nhtsa)
        self.assertEqual("COBRA INDUSTRIES", rule["claims"][0]["value"])
        self.assertEqual({"Make"}, {claim["code"] for claim in rule["claims"]})
        self.assertEqual("DAIMLERCHRYSLER CORP (DODGE/BUS)",
                         next(r for r in rows if r["page"] == 34 and r["row"] == 78)["name"])
        changed_rows = copy.deepcopy(rows)
        next(r for r in changed_rows if r["page"] == 34 and r["row"] == 78)["part1"] = "1C3"
        with self.assertRaisesRegex(ValueError, "KBA preference scope changed"):
            list(kba_wmi.preference_rules(changed_rows, metadata, nhtsa))
        for field, value in (("brand", "DODGE"), ("constraints", {"markets": ["US"]})):
            with self.subTest(field=field):
                changed = copy.deepcopy(nhtsa)
                next(a for a in changed["assignments"] if a["id"] == "wmi-1ca")[field] = value
                with self.assertRaisesRegex(ValueError, "NHTSA preference assignment changed"):
                    list(kba_wmi.preference_rules(rows, metadata, changed))
        changed = copy.deepcopy(nhtsa)
        assignment = next(a for a in changed["assignments"] if a["id"] == "wmi-1ca")
        changed["assignments"].append({**assignment, "id": "competing-1ca"})
        with self.assertRaisesRegex(ValueError, "NHTSA preference assignment changed"):
            list(kba_wmi.preference_rules(rows, metadata, changed))
        # An unchanged assignment may move to a new structured source edition;
        # the compiled fact must cite that actual edition, not the old review.
        changed = copy.deepcopy(nhtsa)
        old_source = changed["sources"][0]["id"]
        changed["sources"][0]["id"] = "nhtsa-vpic-test-edition"
        for item in changed["assignments"]:
            item["sourceRefs"] = ["nhtsa-vpic-test-edition" if sid == old_source else sid for sid in item["sourceRefs"]]
        rule, = kba_wmi.preference_rules(rows, metadata, changed)
        self.assertEqual("nhtsa-vpic-test-edition", rule["claims"][0]["sourceId"])


if __name__ == "__main__":
    unittest.main()
