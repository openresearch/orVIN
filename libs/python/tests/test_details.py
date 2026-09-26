import json
from pathlib import Path
import unittest

from orvin import Context, VinDecoder

ROOT = Path(__file__).resolve().parents[3]


class DetailsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decoder = VinDecoder.bundled()

    def test_independently_reviewed_vehicle_examples(self):
        for fixture in json.loads((ROOT / "data/vehicle-fixtures.json").read_text()):
            with self.subTest(fixture=fixture["id"]):
                result = self.decoder.decode(fixture["vin"], Context(market=fixture["market"]))
                self.assertEqual("DECODED", result["details"]["status"])
                for code, expected in fixture["expected"].items():
                    field = result["details"]["fields"][code]
                    self.assertEqual("KNOWN", field["status"], code)
                    self.assertEqual(expected, field["value"], code)
                    self.assertTrue(field["evidence"][0]["sourceUrl"].startswith("https://"))
                self.assertEqual(fixture["expected"].get("ModelYear"), result["modelYear"]["value"])
                self.assertNotIn("ProductionDate", result["details"]["fields"])
                sources = {s["id"]: s for s in result["details"]["sources"]}
                for field in result["details"]["fields"].values():
                    for fact in field["evidence"]:
                        source = sources[fact["sourceId"]]
                        self.assertEqual(source["url"], fact["sourceUrl"])
                        for key in ("publisher", "title", "edition", "section", "retrievedOn", "reuseBasis"):
                            self.assertTrue(source[key], key)

    def test_golf_layout_does_not_apply_to_jetta_other_years_or_unreviewed_plants(self):
        golf = self.decoder.decode("WVWZZZ1KZ5P000001")
        self.assertEqual("Golf", golf["model"]["value"])
        self.assertEqual("2005", golf["modelYear"]["value"])
        self.assertEqual("MOSEL", golf["details"]["fields"]["PlantCity"]["value"])
        self.assertNotIn("EngineModel", golf["details"]["fields"])
        for vin in ("WVWZZZ1KZ6P000001", "WVWZZZ1KZ5A000001", "3VWZZZ1KZ5P000001", "WVWAA71K05P000001"):
            self.assertFalse(any(e["kind"].startswith("OEM_RULE") for f in self.decoder.decode(vin, Context(market="DE"))["details"]["fields"].values() for e in f["evidence"]))
        self.assertEqual("CONTEXT_CONFLICT", self.decoder.decode("WVWZZZ1KZ5P000001", Context(2006))["details"]["status"])

    def test_foreign_market_never_promotes_us_rules_to_established_facts(self):
        vin = "1HGCM82603A000000"
        result = self.decoder.decode(vin)
        self.assertEqual("NEEDS_CONTEXT", result["model"]["status"])
        self.assertEqual(["Accord"], result["model"]["possibilities"])
        self.assertIsNone(result["model"]["value"])
        german = self.decoder.decode(vin, Context(market="DE"))
        self.assertEqual("NEEDS_CONTEXT", german["details"]["status"])
        self.assertEqual(["Accord"], german["model"]["possibilities"])
        self.assertIsNone(german["model"]["value"])
        self.assertEqual("HONDA", german["brand"]["value"])

    def test_year_cycles_keep_missing_alternative_and_explicit_year_resolves_it(self):
        vin = "5UPAA2420AA000001"  # Synthetic trailer; code A means 1980 or 2010.
        result = self.decoder.decode(vin, Context(market="US"))
        self.assertEqual([1980, 2010], [a["modelYear"] for a in result["details"]["alternatives"]])
        self.assertEqual({}, result["details"]["alternatives"][0]["fields"])
        self.assertEqual("UNKNOWN", result["modelYear"]["status"])
        self.assertEqual(["2010"], result["modelYear"]["possibilities"])
        resolved = self.decoder.decode(vin, Context(2010, "US"))
        self.assertEqual("2010", resolved["modelYear"]["value"])
        self.assertEqual("24", resolved["details"]["fields"]["TrailerLength"]["value"])
        conflict = self.decoder.decode(vin, Context(2011, "US"))
        self.assertEqual("CONTEXT_CONFLICT", conflict["details"]["status"])
        self.assertEqual({}, conflict["details"]["fields"])

    def test_numeric_capture_and_bracket_plant_pattern_have_traceable_evidence(self):
        numeric = self.decoder.decode("5VLAA24208A000001", Context(2008, "US"))["details"]["fields"]
        self.assertEqual("2", numeric["Axles"]["value"])
        self.assertEqual("24", numeric["TrailerLength"]["value"])
        self.assertEqual("NUMERIC_PATTERN", numeric["Axles"]["evidence"][0]["kind"])
        bmw = self.decoder.decode("5UXWX7C50BA000000", Context(market="US"))["details"]["fields"]
        self.assertEqual("*****|*[AFK]", bmw["PlantCity"]["evidence"][0]["keys"])
        honda = self.decoder.decode("1HGCM82603A000000", Context(market="US"))["details"]["fields"]
        self.assertEqual("UNIT_CONVERSION", honda["DisplacementL"]["evidence"][0]["kind"])

    def test_model_resolves_shared_make_without_destroying_wmi_evidence(self):
        result = self.decoder.decode("1C4RJFBG0FC000000", Context(market="US"))
        self.assertEqual("JEEP", result["brand"]["value"])
        self.assertEqual("Grand Cherokee", result["model"]["value"])
        self.assertEqual(7, len(result["candidates"]))

    def test_european_rules_do_not_extend_to_unreviewed_years_plants_or_configurations(self):
        for vin in ("XP7YGAEK0RB000001", "XP7YGAEK0TC000001", "XP7YGAEZ0TB000001", "XP7YGAEK0TB000000"):
            with self.subTest(vin=vin):
                result = self.decoder.decode(vin, Context(market="DE"))
                self.assertTrue(all(code.startswith("ManufacturerDirectory")
                                    for code in result["details"]["fields"]))
        berlin = self.decoder.decode("XP7YGAEK0TB000001")
        self.assertEqual("Model Y", berlin["model"]["value"])
        self.assertIsNone(berlin["modelYear"]["value"])
        self.assertEqual("2026", berlin["details"]["fields"]["ProductionYear"]["value"])

    def test_invalid_input_and_mutations_never_produce_or_corrupt_rich_facts(self):
        for vin in ("", "1HG", "1HGCM826I3A000000", "1HGCM82603A00000😀"):
            result = self.decoder.decode(vin, Context(market="US"))
            self.assertEqual("INVALID_INPUT", result["details"]["status"])
            self.assertEqual({}, result["details"]["fields"])
        result = self.decoder.decode("1HGCM82603A000000", Context(market="US"))
        alternative = next(a for a in result["details"]["alternatives"] if "Model" in a["fields"])
        alternative["fields"]["Model"][0]["value"] = "changed"
        result["details"]["sources"][0]["title"] = "changed"
        self.assertEqual("Accord", self.decoder.decode("1HGCM82603A000000", Context(market="US"))["model"]["value"])
        self.assertNotEqual("changed", self.decoder.decode("1HGCM82603A000000", Context(market="US"))["details"]["sources"][0]["title"])


if __name__ == "__main__":
    unittest.main()
