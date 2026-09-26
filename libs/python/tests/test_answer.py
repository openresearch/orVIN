"""Consumer contracts for normalized answers and the real command-line entry point."""
import json
import copy
from pathlib import Path
import subprocess
import unittest

from orvin import Context, HsnTsnLookup, VinDecoder
from orvin.answer import vin_answer

ROOT = Path(__file__).resolve().parents[3]


class CommandContractTest(unittest.TestCase):
    def test_json_is_the_normalized_short_answer(self):
        completed = subprocess.run([str(ROOT / "vin.sh"), "WVWZZZ1KZ5P000001", "--json"],
                                   text=True, capture_output=True, check=True)
        answer = json.loads(completed.stdout)
        self.assertEqual(answer.get("vehicle"), {"makeId": "vw", "make": "VW", "modelId": "vw:golf", "model": "Golf",
                                                "modelYear": 2005, "productionYear": None})
        self.assertNotIn("details", answer)
        self.assertNotIn("candidates", answer)
        self.assertLess(len(completed.stdout), 15000)
        self.assertTrue(answer["sources"])


    def test_flags_choose_the_same_library_projection(self):
        for script, args in (("vin.sh", ["WVWZZZ1KZ5P000001"]), ("hsntsn.sh", ["0603", "BMT"])):
            short = None
            for flags in ([], ["--json"], ["--json=short"]):
                result = subprocess.run([str(ROOT / script), *args, *flags], capture_output=True, text=True, check=True)
                parsed = json.loads(result.stdout)
                if short is None:
                    short = parsed
                self.assertEqual(short, parsed)
            long = None
            for flags in (["--long"], ["--json", "--long"], ["--long", "--json"], ["--json=long"]):
                parsed = json.loads(subprocess.run([str(ROOT / script), *args, *flags], capture_output=True, text=True, check=True).stdout)
                if long is None:
                    long = parsed
                self.assertEqual(long, parsed)
                self.assertEqual(short, {k: v for k, v in parsed.items() if k != "details"})
            error = subprocess.run([str(ROOT / script), *args, "--json=short", "--long"], capture_output=True, text=True)
            self.assertEqual(2, error.returncode)
            self.assertEqual("", error.stdout)


class AnswerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decoder = VinDecoder.bundled()

    def test_owner_authorized_golf_and_attribution(self):
        fixture = json.loads((ROOT / "data/identity/fixtures.json").read_text())[0]
        self.assertEqual("User-contributed Golf 5 from Austria.", fixture["source"]["attribution"])
        self.assertTrue(fixture["source"]["permission"])
        answer = self.decoder.decode_vehicle(fixture["vin"], Context(market="AT"))
        self.assertEqual(fixture["expected"], answer.vehicle)
        self.assertEqual("RESOLVED", answer.short()["fieldStatus"]["model"])
        self.assertEqual("UNKNOWN", answer.short()["fieldStatus"]["productionYear"])
        sources = {s["id"]: s for s in answer.short()["sources"]}
        self.assertTrue(set(fixture["ruleSourceRefs"]) <= sources.keys())
        self.assertFalse(any("astra" in sid or "kba" in sid for sid in sources))
        for source in sources.values():
            self.assertTrue(source["url"])
            self.assertTrue(source["reuseBasis"])
            self.assertTrue(source["modifications"])

    def test_contributed_vehicles_never_resolve_to_a_conflicting_identity(self):
        fixtures = json.loads((ROOT / "data/identity/fixtures.json").read_text())
        contributed = [f for f in fixtures if "reportedExpectations" in f]
        self.assertTrue(contributed)
        for fixture in contributed:
            with self.subTest(fixture=fixture["id"]):
                self.assertTrue(fixture["source"]["permission"])
                answer = self.decoder.decode_vehicle(fixture["vin"]).vehicle
                for field, value in fixture["expected"].items():
                    self.assertEqual(value, answer[field])
                for field, value in fixture["reportedExpectations"].items():
                    if answer[field] is not None:
                        self.assertEqual(value, answer[field])

    def test_long_is_lossless_extension_with_resolvable_references(self):
        answer = self.decoder.decode_vehicle("WVWZZZ1KZ5P000001")
        short, long = answer.short(), answer.long()
        details = long.pop("details")
        self.assertEqual(short, long)
        approvals = [e for e in details["evidence"].values() if e["kind"] == "TYPE_APPROVAL"]
        raw = self.decoder.decode("WVWZZZ1KZ5P000001")
        self.assertGreater(len(approvals), 0)
        self.assertEqual(len(raw["typeApprovals"]["candidates"]), len(approvals))
        self.assertTrue(any("remarks" in e["record"]["fields"] for e in approvals))
        sources = {s["id"] for s in short["sources"] + details["provenance"]["additionalSources"]}
        for evidence in details["evidence"].values():
            self.assertTrue(set(evidence["sourceIds"]) <= sources)
        for decision in details["decisions"].values():
            self.assertTrue(set(decision["evidenceIds"]) <= details["evidence"].keys())
            self.assertTrue(set(decision["normalizationRuleIds"]) <= details["provenance"]["normalizationRules"].keys())
        short["vehicle"]["make"] = "modified"
        self.assertEqual("VW", answer.short()["vehicle"]["make"])

    def test_context_conflict_preserves_rule_evidence_and_never_falls_back(self):
        answer = self.decoder.decode_vehicle("WVWZZZ1KZ5P000001", Context(2006, "AT"))
        short, long = answer.short(), answer.long()
        self.assertEqual("CONFLICT", short["fieldStatus"]["modelYear"])
        self.assertIsNone(short["vehicle"]["modelYear"])
        self.assertIsNone(short["vehicle"]["model"])
        self.assertTrue(long["details"]["decisions"]["modelYear"]["evidenceIds"])
        self.assertIn("vw-vin-chart-2005", {s["id"] for s in short["sources"]})

    def test_production_year_and_provided_model_year_are_distinct(self):
        answer = self.decoder.decode_vehicle("XP7YGAEK0TB000001", Context(market="DE")).short()
        self.assertEqual("Model Y", answer["vehicle"]["model"])
        self.assertEqual(2026, answer["vehicle"]["productionYear"])
        self.assertIsNone(answer["vehicle"]["modelYear"])
        provided = self.decoder.decode_vehicle("WVWZZZ1KZ5P000001", Context(2005, "AT")).short()
        self.assertEqual("PROVIDED", provided["fieldStatus"]["modelYear"])

    def test_us_market_assumptions_and_competing_catalogue_identity(self):
        raw = self.decoder.decode("1HGCM82603A000000")
        short = vin_answer(raw).short()
        self.assertEqual("Honda", short["vehicle"]["make"])
        self.assertEqual("Accord", short["vehicle"]["model"])
        self.assertEqual("RESOLVED", short["fieldStatus"]["make"])
        self.assertEqual("SUGGESTED", short["fieldStatus"]["model"])
        self.assertEqual("US_MARKET_ASSUMED", short["assumptions"][0]["code"])
        # Synthetic conflicting approval; verifies policy without inventing a real registration.
        approval = copy.deepcopy(self.decoder.decode("WVWZZZ1KZ5P000001")["typeApprovals"])
        approval["candidates"] = [{"approvalId": "synthetic-civic", "sourceId": approval["sources"][0]["id"],
            "sourceRow": 1, "vinPattern": "1HG..............", "matchedPatterns": ["1HG.............."],
            "fields": {"make": "HONDA", "type": "Civic"}}]
        raw["typeApprovals"] = approval
        conflicting = vin_answer(raw).short()
        self.assertEqual("AMBIGUOUS", conflicting["fieldStatus"]["model"])
        self.assertIsNone(conflicting["vehicle"]["model"])
        self.assertIsNone(conflicting["vehicle"]["modelYear"])

    def test_partial_foreign_year_cycle_does_not_erase_established_wmi_make(self):
        result = VinDecoder.bundled().decode_vehicle("1H9AAAAAAAA333AAA", Context(market="NZ")).short()
        self.assertEqual("Hombilt Trailers", result["vehicle"]["make"])
        self.assertEqual("RESOLVED", result["fieldStatus"]["make"])
        self.assertIsNone(result["vehicle"]["modelYear"])

    def test_invalid_input_has_no_manufacturer_guess(self):
        answer = self.decoder.decode_vehicle("WVWZZZ1KZ5P00000I").short()
        self.assertEqual("INVALID_CHARACTERS", answer["inputStatus"])
        self.assertTrue(all(value is None for value in answer["vehicle"].values()))
        self.assertEqual([], answer["sources"])

    def test_kba_short_keeps_required_credit_and_never_uses_reference_year(self):
        answer = HsnTsnLookup.bundled().lookup_vehicle("0603", "bmt").short()
        self.assertEqual("0603", answer["hsn"])
        self.assertEqual("BMT", answer["tsn"])
        self.assertEqual("VW", answer["vehicle"]["make"])
        self.assertEqual("Golf Sportsvan", answer["vehicle"]["model"])
        self.assertIsNone(answer["vehicle"]["modelYear"])
        source = next(s for s in answer["sources"] if s["id"].startswith("kba-"))
        self.assertEqual("dl-de/by-2-0", source["license"])
        self.assertEqual("https://www.govdata.de/dl-de/by-2-0", source["termsUrl"])
        self.assertIn("Normalized output labels", source["modifications"])
        absent = HsnTsnLookup.bundled().lookup_vehicle("9999", "ZZZ").short()
        self.assertIsNone(absent["vehicle"]["make"])
        self.assertEqual("dl-de/by-2-0", absent["sources"][0]["license"])
        self.assertIn("/fieldStatus/make", absent["sources"][0]["fields"])


if __name__ == "__main__":
    unittest.main()
