import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from orvin import Context, HsnTsnLookup, VinDecoder

ROOT = Path(__file__).resolve().parents[3]


class VinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decoder = VinDecoder.bundled()

    def test_all_sourced_wmi_fixtures(self):
        for fixture in json.loads((ROOT / "data/fixtures.json").read_text()):
            with self.subTest(fixture=fixture["assignmentId"]):
                result = self.decoder.decode(fixture["vin"])
                self.assertEqual("RECOGNIZED", result["status"])
                self.assertEqual("MODERN_FORMAT", result["structure"])
                self.assertEqual(fixture["manufacturerId"], result["manufacturer"]["value"]["id"])
                self.assertEqual(fixture["brand"], result["brand"]["value"])
                self.assertEqual(fixture["category"], result["category"]["value"])
                self.assertEqual(fixture["wmi"], result["candidates"][0]["wmi"])

    def test_normalization_structure_and_lookup_are_independent(self):
        result = self.decoder.decode("  1hgaaaaaaaaaaaaaa  ")
        self.assertEqual("  1hgaaaaaaaaaaaaaa  ", result["supplied"])
        self.assertEqual("1HGAAAAAAAAAAAAAA", result["normalized"])
        self.assertEqual("RECOGNIZED", result["status"])
        for vin in ("1HGIAAAAAAAAAAAAA", "1HGAAAA AAAAAAAAA", "1HGAAAAAAAAAAAAAſ"):
            self.assertEqual("INVALID_CHARACTERS", self.decoder.decode(vin)["structure"])
            self.assertEqual("RECOGNIZED", self.decoder.decode(vin)["status"])
        self.assertEqual("UNSUPPORTED_FORMAT", self.decoder.decode("\t1HGAAAAAAAAAAAAAA")["status"])
        self.assertEqual("UNKNOWN", self.decoder.decode("ZZZAAAAAAAAAAAAAA")["status"])
        self.assertEqual("NEEDS_CONTEXT", result["assemblyCountry"]["status"])
        self.assertIsNone(result["assemblyCountry"]["value"])
        self.assertIsNone(result["manufacturerCountry"]["value"])

    def test_extended_wmi_does_not_fall_back_or_use_wrong_positions(self):
        for vin in ("1H9AAAAAAAAZZZAAA", "1H9333AAAAAAAAAAA"):
            self.assertEqual("UNKNOWN", self.decoder.decode(vin)["status"])
        for vin in ("", "1H9333", "CHASSIS-1962"):
            self.assertEqual("UNSUPPORTED_FORMAT", self.decoder.decode(vin)["status"])

    def synthetic(self, assignments):
        data = json.loads((ROOT / "data/dataset.json").read_text())
        data["assignments"] = assignments
        return VinDecoder(data, "synthetic-test")

    def test_constraints_use_only_explicit_context_and_inclusive_bounds(self):
        a = json.loads((ROOT / "data/dataset.json").read_text())["assignments"][0]
        a["constraints"] = {"markets": ["US"], "fromModelYear": 2000, "toModelYear": 2005}
        decoder = self.synthetic([a])
        vin = a["wmi"] + "AAAAAAAAAAAAAA"
        self.assertEqual("NEEDS_CONTEXT", decoder.decode(vin)["status"])
        self.assertEqual("NEEDS_CONTEXT", decoder.decode(vin, Context(model_year=2005))["manufacturer"]["status"])
        for year in (2000, 2005):
            self.assertEqual("RECOGNIZED", decoder.decode(vin, Context(year, "US"))["status"])
        for context in (Context(1999, "US"), Context(2006, "US"), Context(2005, "DE")):
            self.assertEqual("UNKNOWN", decoder.decode(vin, context)["status"])

    def test_ambiguity_and_partial_evidence_do_not_pick_first(self):
        a = json.loads((ROOT / "data/dataset.json").read_text())["assignments"][0]
        b = copy.deepcopy(a)
        b.update(id="alternative", brand="Other brand")
        vin = a["wmi"] + "AAAAAAAAAAAAAA"
        result = self.synthetic([a, b]).decode(vin)
        self.assertEqual("AMBIGUOUS", result["status"])
        self.assertEqual("KNOWN", result["manufacturer"]["status"])
        self.assertEqual("AMBIGUOUS", result["brand"]["status"])
        self.assertIsNone(result["brand"]["value"])
        del b["brand"]
        result = self.synthetic([a, b]).decode(vin)
        self.assertEqual("UNKNOWN", result["brand"]["status"])
        self.assertEqual([a["brand"]], result["brand"]["possibilities"])

    def test_bulk_multiple_brands_preserve_known_manufacturer_and_unknown_brand(self):
        result = self.decoder.decode("1C4AAAAAAAAAAAAAA")
        self.assertEqual("AMBIGUOUS", result["status"])
        self.assertEqual("KNOWN", result["manufacturer"]["status"])
        self.assertEqual("nhtsa-manufacturer-994", result["manufacturer"]["value"]["id"])
        self.assertIsNone(result["brand"]["value"])
        self.assertEqual({"DODGE", "CHRYSLER", "VOLKSWAGEN", "JEEP", "FIAT", "RAM", "LANCIA"},
                         set(result["brand"]["possibilities"]))
        # This neighbor was absent from the seed, but exists in the bulk source.
        result = self.decoder.decode("1H9AAAAAAAA334AAA")
        self.assertEqual("nhtsa-manufacturer-12983", result["manufacturer"]["value"]["id"])
        self.assertEqual("1H9334", result["candidates"][0]["wmi"])

    def test_returned_data_cannot_modify_cached_library_state(self):
        result = self.decoder.decode("1HGAAAAAAAAAAAAAA")
        result["candidates"][0]["manufacturer"]["name"] = "changed"
        self.decoder.dataset["version"] = "changed"
        fresh = self.decoder.decode("1HGAAAAAAAAAAAAAA")
        self.assertEqual("AMERICAN HONDA MOTOR CO., INC.", fresh["manufacturer"]["value"]["name"])
        self.assertNotEqual("changed", fresh["dataset"]["version"])

    def test_wrong_argument_types_and_invalid_context_raise(self):
        with self.assertRaises(TypeError):
            self.decoder.decode(None)
        for kwargs in ({"model_year": True}, {"model_year": 1885}, {"market": "us"}):
            with self.assertRaises(ValueError):
                Context(**kwargs)


class HsnTsnTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lookup = HsnTsnLookup.bundled()

    def test_reviewed_source_fixtures_and_reference_date(self):
        fixtures = json.loads((ROOT / "data/kba/fixtures.json").read_text())
        for expected in fixtures:
            with self.subTest(hsn=expected["hsn"], tsn=expected["tsn"]):
                result = self.lookup.lookup(expected["hsn"], expected["tsn"])
                self.assertEqual("RECOGNIZED", result["status"])
                # These independently reviewed identities survive statistical refreshes.
                # Counts, object IDs and reference dates belong to each source snapshot;
                # full offline reconstruction verifies them against that snapshot.
                for field in ("hsn", "tsn", "manufacturer", "tradeName"):
                    self.assertEqual(expected[field], result["value"][field])
                self.assertRegex(result["dataset"]["referenceDate"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertEqual("dl-de/by-2-0", result["dataset"]["source"]["license"])

    def test_leading_zeroes_ascii_only_normalization_and_strict_tsn(self):
        result = self.lookup.lookup(" 0005 ", "amq")
        self.assertEqual(" 0005 ", result["suppliedHsn"])
        self.assertEqual("0005", result["normalizedHsn"])
        self.assertEqual("AMQ", result["normalizedTsn"])
        self.assertEqual("RECOGNIZED", result["status"])
        for hsn, tsn, status in [("5", "AMQ", "INVALID_HSN"), ("0005", "AMQ12345", "INVALID_TSN"),
                                  ("０００５", "AMQ", "INVALID_HSN"), ("0005", "aſq", "INVALID_TSN"),
                                  ("0005", "\tAMQ", "INVALID_TSN"), ("", "", "INVALID_HSN_AND_TSN")]:
            result = self.lookup.lookup(hsn, tsn)
            self.assertEqual("INVALID_INPUT", result["status"])
            self.assertEqual(status, result["inputStatus"])
            self.assertIsNone(result["value"])
        with self.assertRaises(TypeError):
            self.lookup.lookup(5, "AMQ")

    def test_absent_codes_remain_unknown_not_invalid(self):
        result = self.lookup.lookup("9999", "ZZZ")
        self.assertEqual("UNKNOWN", result["status"])
        self.assertEqual("VALID", result["inputStatus"])
        self.assertEqual([], result["candidates"])

    def test_duplicate_keys_preserve_all_candidates_and_unknown_count_markers(self):
        first = {"hsn": "0005", "tsn": "AMQ", "manufacturer": "Synthetic", "tradeName": None,
                 "registeredCount": None, "countMarker": ".", "sourceObjectId": 1}
        second = {**first, "tradeName": "Alternative", "sourceObjectId": 2}
        lookup = HsnTsnLookup(self.lookup.dataset, [first, second])
        result = lookup.lookup("0005", "AMQ")
        self.assertEqual("AMBIGUOUS", result["status"])
        self.assertIsNone(result["value"])
        self.assertEqual([first, second], result["candidates"])
        result["candidates"].clear()
        first["countMarker"] = "changed"
        self.assertEqual(".", lookup.lookup("0005", "AMQ")["candidates"][0]["countMarker"])


class ScriptTest(unittest.TestCase):
    def run_script(self, name, *args, **kwargs):
        return subprocess.run([str(ROOT / name), *args], cwd="/", capture_output=True, text=True, **kwargs)

    def test_scripts_print_library_json_from_an_unrelated_working_directory(self):
        for script, args, expected in [("vin.sh", ["1HGAAAAAAAAAAAAAA"], VinDecoder.bundled().decode_vehicle("1HGAAAAAAAAAAAAAA").short()),
                                       ("hsntsn.sh", ["0005", "amq"], HsnTsnLookup.bundled().lookup_vehicle("0005", "amq").short())]:
            result = self.run_script(script, *args, "--json")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("", result.stderr)
            self.assertEqual(expected, json.loads(result.stdout))

    def test_exit_codes_help_missing_python_and_json_escaping(self):
        invalid = self.run_script("hsntsn.sh", "5", "AMQ", "--json")
        self.assertEqual(2, invalid.returncode)
        self.assertEqual("INVALID_HSN", json.loads(invalid.stdout)["inputStatus"])
        self.assertEqual(0, self.run_script("hsntsn.sh", "9999", "ZZZ").returncode)
        self.assertEqual(2, self.run_script("vin.sh").returncode)
        self.assertEqual(0, self.run_script("vin.sh", "--help").returncode)
        strange = 'quote"\t\\\n'
        self.assertEqual(strange, json.loads(self.run_script("vin.sh", strange, "--json", "--long").stdout)["details"]["input"]["supplied"])
        missing = self.run_script("vin.sh", "anything", env={**os.environ, "ORVIN_PYTHON": "/nonexistent/python"})
        self.assertEqual(1, missing.returncode)
        self.assertIn("Python 3.10+", missing.stderr)

    def test_path_with_spaces_and_no_java_or_build_tools(self):
        import shutil
        import sys
        with tempfile.TemporaryDirectory(prefix="orvin path ") as directory:
            path = Path(directory)
            # Only the commands actually required by the scripts are available on PATH.
            (path / "python3").symlink_to(sys.executable)
            (path / "dirname").symlink_to(shutil.which("dirname"))
            (path / "repo link").symlink_to(ROOT, target_is_directory=True)
            result = subprocess.run([str(path / "repo link/hsntsn.sh"), "0005", "AMQ"], cwd="/",
                                    env={**os.environ, "PATH": directory, "ORVIN_PYTHON": "python3"},
                                    capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            answer = json.loads(result.stdout)
            self.assertEqual("0005", answer["hsn"])
            self.assertEqual("BMW", answer["vehicle"]["make"])

    def test_default_json_deduplicates_credits_and_distinguishes_invalid_input(self):
        answer = json.loads(self.run_script("vin.sh", "WVWAAAAAAAAAAAAAA").stdout)
        self.assertEqual("VW", answer["vehicle"]["make"])
        self.assertEqual("SUPPORTED_FORMAT", answer["inputStatus"])
        ids = [source["id"] for source in answer["sources"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertNotIn("candidates", answer)
        unknown = self.run_script("hsntsn.sh", "9999", "ZZZ")
        self.assertEqual(0, unknown.returncode)
        self.assertEqual("SUPPORTED_FORMAT", json.loads(unknown.stdout)["inputStatus"])
        self.assertTrue(all(v is None for v in json.loads(unknown.stdout)["vehicle"].values()))
        invalid = self.run_script("hsntsn.sh", "5", "AMQ")
        self.assertEqual(2, invalid.returncode)
        self.assertEqual("INVALID_HSN", json.loads(invalid.stdout)["inputStatus"])
        controls = self.run_script("vin.sh", "WVW\n\x1b[31m")
        self.assertEqual(2, controls.returncode)
        self.assertEqual("WVW\n\x1b[31M", json.loads(controls.stdout)["vin"])
        self.assertNotIn("\x1b", controls.stdout)

    def test_summaries_preserve_ambiguity_and_statistical_unknowns(self):
        from orvin.summary import hsntsn_summary, vin_summary
        first = {"hsn": "0005", "tsn": "AMQ", "manufacturer": "Synthetic A", "tradeName": None,
                 "registeredCount": None, "countMarker": ".", "sourceObjectId": 1}
        second = {**first, "manufacturer": "Synthetic B", "sourceObjectId": 2}
        result = HsnTsnLookup(HsnTsnLookup.bundled().dataset, [first, second]).lookup("0005", "AMQ")
        text = hsntsn_summary(result)
        self.assertIn("Status: Ambiguous (2 matches)", text)
        self.assertIn("Candidate 1:", text)
        self.assertIn("Candidate 2:", text)
        self.assertIn("Manufacturer: Synthetic A", text)
        self.assertIn("Manufacturer: Synthetic B", text)
        self.assertIn("Registered vehicles: Unknown", text)
        self.assertIn("Statistical marker: .", text)
        data = json.loads((ROOT / "data/dataset.json").read_text())
        a = data["assignments"][0]
        a["brand"] = "Synthetic A"
        b = {**a, "id": "alternative", "brand": "Synthetic B"}
        data["assignments"] = [a, b]
        decoder = VinDecoder(data, "synthetic")
        text = vin_summary(decoder.decode(a["wmi"] + "AAAAAAAAAAAAAA"))
        self.assertIn("Brand: Ambiguous (possible: Synthetic B; Synthetic A)", text)
        data["assignments"] = [a]
        a["constraints"] = {"markets": ["US"]}
        text = vin_summary(VinDecoder(data, "synthetic").decode(a["wmi"] + "AAAAAAAAAAAAAA"))
        self.assertIn("Status: Needs context", text)
        self.assertIn("Brand: Needs context (possible: Synthetic A)", text)


if __name__ == "__main__":
    unittest.main()
