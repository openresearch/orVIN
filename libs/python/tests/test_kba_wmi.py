"""Public results must expose sourced directory facts without inventing vehicle facts."""
import json
from pathlib import Path
import unittest

from orvin import Context, VinDecoder

ROOT = Path(__file__).resolve().parents[3]
SOURCE = "kba-sv31-2026-01-15"


class ManufacturerDirectoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decoder = VinDecoder.bundled()

    def test_reviewed_pdf_facts_apply_in_any_market_and_keep_row_lineage(self):
        fixtures = json.loads((ROOT / "data/kba-wmi/fixtures.json").read_text())
        for fixture in fixtures:
            for market in ("AT", "DE", "US", "JP"):
                with self.subTest(fixture=fixture["id"], market=market):
                    raw = self.decoder.decode(fixture["vin"], Context(market=market))
                    for code, expected in fixture["expected"].items():
                        field = raw["details"]["fields"][code]
                        self.assertEqual(sorted(expected), sorted(field["possibilities"]))
                        self.assertEqual("AMBIGUOUS" if len(expected) > 1 else "KNOWN", field["status"])
                        for fact in field["evidence"]:
                            self.assertEqual(SOURCE, fact["sourceId"])
                            self.assertIn("PDF page", fact["keys"])
                    facts = [f for a in raw["details"]["alternatives"] for code, fs in a["fields"].items()
                             if not code.startswith("ManufacturerDirectory") for f in fs]
                    self.assertFalse(any(f["sourceId"] == SOURCE for f in facts))

    def test_credits_survive_long_output_and_no_retail_make_or_plant_is_guessed(self):
        answer = self.decoder.decode_vehicle("WAKAAAAAAAAAAAAAA", Context(market="AT"))
        short, long = answer.short(), answer.long()
        self.assertEqual(short, {k: v for k, v in long.items() if k != "details"})
        self.assertIsNone(short["vehicle"]["make"])
        self.assertIsNone(short["vehicle"]["model"])
        self.assertIsNone(short["vehicle"]["modelYear"])
        specification = long["details"]["specifications"]
        self.assertEqual("Kempten", specification["ManufacturerDirectoryLocation"]["value"])
        self.assertNotIn("PlantCity", specification)
        credit, = [s for s in long["details"]["provenance"]["additionalSources"] if s["id"] == SOURCE]
        self.assertEqual("LicenseRef-KBA-SV31-Attribution", credit["license"])
        self.assertEqual("https://www.kba.de/SharedDocs/Downloads/DE/SV/sv31_pdf.pdf?__blob=publicationFile&v=3#page=151", credit["termsUrl"])
        self.assertIn("26. September 2026", credit["modifications"])
        self.assertIn("eigene Darstellung", credit["modifications"])

    def test_extended_near_miss_and_golf_primary_answer_remain_correct(self):
        wrong = self.decoder.decode("W09A53AAAAAAAAAAA", Context(market="AT"))
        facts = [f for a in wrong["details"]["alternatives"] for fs in a["fields"].values() for f in fs]
        self.assertFalse(any(f["ruleId"] == "sv31-p006-r001" for f in facts))
        golf = self.decoder.decode_vehicle("WVWZZZ1KZ5P000001", Context(market="AT")).long()
        self.assertEqual(("VW", "Golf", 2005), tuple(golf["vehicle"][k] for k in ("make", "model", "modelYear")))
        self.assertNotIn("ManufacturerDirectoryHSN", golf["details"]["specifications"])
        rows = [a for a in golf["details"]["alternatives"] if "ManufacturerDirectoryHSN" in a["fields"]]
        self.assertEqual(4, len(rows))

    def test_1ca_preference_is_traceable_without_relabeling_or_combining_kba_facts(self):
        for market in ("AT", "DE", "US", "JP"):
            with self.subTest(market=market):
                answer = self.decoder.decode_vehicle("1CAAAAAAAAAAAAAAA", Context(market=market))
                short, long = answer.short(), answer.long()
                self.assertEqual("Cobra Industries", short["vehicle"]["make"])
                self.assertEqual("cobra~20industries", short["vehicle"]["makeId"])
                evidence = long["details"]["evidence"]
                decision_facts = [evidence[e]["record"] for e in long["details"]["decisions"]["make"]["evidenceIds"]]
                preference, = [f for f in decision_facts if f.get("kind") == "SOURCE_PREFERENCE"]
                self.assertEqual("kba-sv31-1ca-prefer-nhtsa", preference["ruleId"])
                self.assertTrue(preference["sourceId"].startswith("nhtsa-vpic-"))
                self.assertIn("sv31-p034-r078", preference["keys"])
                self.assertIn("not proof that KBA is wrong", preference["keys"])
                self.assertTrue(any(s["id"] == preference["sourceId"] for s in short["sources"]))
                spec = long["details"]["specifications"]
                self.assertEqual("DAIMLERCHRYSLER CORP (DODGE/BUS)", spec["ManufacturerDirectoryName"]["value"])
                self.assertEqual("1004", spec["ManufacturerDirectoryHSN"]["value"])
                for alternative in long["details"]["alternatives"]:
                    self.assertFalse({"Make", "ManufacturerDirectoryHSN"} <= alternative["fields"].keys())
        other = self.decoder.decode("1C3AAAAAAAAAAAAAA", Context(market="AT"))
        self.assertNotEqual("COBRA INDUSTRIES", other["brand"]["value"])
        self.assertFalse(any(f["kind"] == "SOURCE_PREFERENCE"
                             for field in other["details"]["fields"].values() for f in field["evidence"]))


if __name__ == "__main__":
    unittest.main()
