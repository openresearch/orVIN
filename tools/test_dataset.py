"""Guards against accepting contradictory, unsourced or corrupt contributions."""
import copy
import tempfile
import unittest
from pathlib import Path

from jsonschema import ValidationError
from dataset import ROOT, read_json, render, validate, validate_fixtures


class DatasetValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data = read_json(ROOT / "data/dataset.json")
        # Exercise validation defects on a small reviewed subset; the build
        # separately reconstructs every imported row from the complete archive.
        ids = [f["assignmentId"] for f in read_json(ROOT / "data/fixtures.json")]
        assignments = {a["id"]: a for a in data["assignments"]}
        data["assignments"] = [assignments[key] for key in ids]
        used = {a["manufacturerId"] for a in data["assignments"]}
        data["manufacturers"] = [m for m in data["manufacturers"] if m["id"] in used]
        cls.reviewed_data = data

    def setUp(self):
        self.data = copy.deepcopy(self.reviewed_data)

    def test_missing_provenance_invalid_identifiers_and_unknown_fields_fail(self):
        for field, value in [("sourceRefs", []), ("wmi", "IOQ"), ("wmi", "1234"), ("plant", "guess")]:
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                data["assignments"][0][field] = value
                with self.assertRaises(ValidationError):
                    validate(data)

    def test_unknown_source_or_manufacturer_reference_fails(self):
        for field, value, message in [("sourceRefs", ["missing"], "unknown source"),
                                      ("manufacturerId", "missing", "unknown manufacturer")]:
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                data["assignments"][0][field] = value
                with self.assertRaisesRegex(ValueError, message):
                    validate(data)

    def test_duplicate_ids_and_overlapping_duplicate_assignments_fail(self):
        duplicate = copy.deepcopy(self.data["assignments"][0])
        duplicate["notes"] = "A different record reusing the same stable ID."
        self.data["assignments"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "Duplicate assignment id"):
            validate(self.data)
        duplicate["id"] = "another-id"
        with self.assertRaisesRegex(ValueError, "Duplicate overlapping"):
            validate(self.data)

    def test_conflicts_require_explicit_shared_ambiguity_and_a_reason(self):
        first = self.data["assignments"][0]
        alternative = copy.deepcopy(first)
        alternative.update(id="alternative", manufacturerId=self.data["manufacturers"][1]["id"])
        self.data["assignments"].append(alternative)
        with self.assertRaisesRegex(ValueError, "Unexplained conflicting"):
            validate(self.data)
        for item in [first, alternative]:
            item.update(ambiguityGroup="reviewed-conflict", ambiguityReason="Two source records disagree.")
        validate(self.data)
        del alternative["ambiguityReason"]
        with self.assertRaises(ValidationError):
            validate(self.data)

    def test_disjoint_years_or_markets_are_not_conflicts_but_boundaries_overlap(self):
        first = self.data["assignments"][0]
        second = copy.deepcopy(first)
        second.update(id="later", manufacturerId=self.data["manufacturers"][1]["id"])
        self.data["assignments"].append(second)
        first["constraints"] = {"toModelYear": 2000}
        second["constraints"] = {"fromModelYear": 2001}
        validate(self.data)
        second["constraints"] = {"fromModelYear": 2000}
        with self.assertRaisesRegex(ValueError, "Unexplained conflicting"):
            validate(self.data)
        first["constraints"] = {"markets": ["US"]}
        second["constraints"] = {"markets": ["DE"]}
        validate(self.data)

    def test_reversed_years_and_prefix_fallback_fail(self):
        first = self.data["assignments"][0]
        first["constraints"] = {"fromModelYear": 2001, "toModelYear": 2000}
        with self.assertRaisesRegex(ValueError, "reversed"):
            validate(self.data)
        first["constraints"] = {}
        extra = copy.deepcopy(first)
        extra.update(id="extended", wmi=first["wmi"] + "123")
        self.data["assignments"].append(extra)
        with self.assertRaisesRegex(ValueError, "prefix collision"):
            validate(self.data)

    def test_snapshot_tampering_and_missing_reuse_information_fail(self):
        self.data["sources"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "changed snapshot"):
            validate(self.data)
        del self.data["sources"][0]["reuse"]
        with self.assertRaises(ValidationError):
            validate(self.data)

    def test_json_duplicate_keys_and_unescaped_tsv_controls_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"name": "first", "name": "last"}')
            with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
                read_json(path)
        self.data["assignments"][0]["notes"] = "text\tinjected record"
        with self.assertRaises(ValidationError):
            validate(self.data)

    def test_every_assignment_requires_a_behavior_fixture(self):
        fixtures = read_json(ROOT / "data/fixtures.json")
        with self.assertRaisesRegex(ValueError, "without behavior fixtures"):
            validate_fixtures(fixtures[1:], self.data)

    def test_compilation_has_stable_order_and_preserves_unicode(self):
        self.data["manufacturers"][0]["name"] = "Synthetic Österreich"
        expected = render(self.data, "digest")
        self.data["assignments"].reverse()
        self.data["manufacturers"].reverse()
        self.data["sources"].reverse()
        self.assertEqual(expected, render(self.data, "digest"))
        self.assertIn("Synthetic Österreich", expected)


if __name__ == "__main__":
    unittest.main()
