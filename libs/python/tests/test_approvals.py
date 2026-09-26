import unittest

from orvin import Context, VinDecoder
from orvin.summary import vin_summary


class TypeApprovalsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.decoder = VinDecoder.bundled()

    def test_seal_candidates_preserve_correlated_engine_options_and_source_rows(self):
        # Synthetic continuation of the LGXC prefix independently identified as
        # BYD SEAL / EKE in CEM's signed September 2025 memorandum, p.1:
        # https://www.cem.es/sites/default/files/2025-10/05_protocolo_taximetro_byd_seal_eke_cam_00_signed_0.pdf
        # The finer template and alternatives below are reviewed ASTRA approval
        # assertions, not independent ground truth for this synthetic vehicle.
        result = self.decoder.decode("LGXCH6AD0S0000001", Context(market="DE"))
        approvals = result["typeApprovals"]
        self.assertEqual("CANDIDATES", approvals["status"])
        rows = {r["approvalId"]: r for r in approvals["candidates"]}
        a, b = rows["ABJ202"], rows["ABJ204"]
        self.assertEqual(("SEAL", "TZ200XYC", "230"),
                         tuple(a["fields"][key] for key in ("type", "engineCode", "powerKw")))
        self.assertEqual(("SEAL", "TZ200XYS", "170"),
                         tuple(b["fields"][key] for key in ("type", "engineCode", "powerKw")))
        self.assertIn("*00639", a["fields"]["euApproval"])
        self.assertTrue(a["fields"]["remarks"])
        self.assertNotIn("remarks", approvals["fields"])
        self.assertEqual(["LGXCH6.D........."], a["matchedPatterns"])
        self.assertGreater(a["sourceRow"], 1)
        self.assertEqual(approvals["sources"][0]["id"], a["sourceId"])
        self.assertEqual("28 Leistung kW", approvals["fields"]["powerKw"]["sourceColumn"])
        self.assertIsNone(result["model"]["value"])
        self.assertIsNone(result["modelYear"]["value"])
        self.assertNotIn("ModelYear", approvals["fields"])
        self.assertNotIn("ProductionYear", approvals["fields"])

    def test_template_positions_are_respected_without_dropping_broader_alternatives(self):
        rows = self.decoder.decode("LGXCH6AB0S0000001")["typeApprovals"]["candidates"]
        ids = {r["approvalId"] for r in rows}
        self.assertIn("ABJ203", ids)
        self.assertNotIn("ABJ202", ids)
        self.assertNotIn("ABJ204", ids)
        unknown = self.decoder.decode("ZZZAAAAAAAAAAAAAA")["typeApprovals"]
        self.assertEqual("NO_MATCH", unknown["status"])
        for vin in ("TMB", "LGXCH6ID0S0000001"):
            invalid = self.decoder.decode(vin)["typeApprovals"]
            self.assertEqual("INVALID_INPUT", invalid["status"])
            self.assertEqual([], invalid["candidates"])

    def test_candidates_never_replace_direct_golf_facts_or_resolve_from_caller_year(self):
        vin = "WVWZZZ1KZ5P000001"
        golf = self.decoder.decode(vin, Context(market="DE"))
        self.assertEqual("Golf", golf["model"]["value"])
        self.assertEqual("2005", golf["modelYear"]["value"])
        self.assertGreater(len(golf["typeApprovals"]["candidates"]), 1)
        self.assertEqual(golf["typeApprovals"], self.decoder.decode(vin, Context(1990, "DE"))["typeApprovals"])
        text = vin_summary(golf)
        self.assertIn("Swiss type-approval candidates:", text)
        self.assertIn("not this vehicle's actual configuration", text)
        self.assertIn("https://opendata.astra.admin.ch/", text)

    def test_returned_candidates_cannot_corrupt_the_cached_dataset(self):
        vin = "LGXCH6AD0S0000001"
        first = self.decoder.decode(vin)["typeApprovals"]
        first["candidates"][0]["fields"]["type"] = "changed"
        first["sources"][0]["title"] = "changed"
        second = self.decoder.decode(vin)["typeApprovals"]
        self.assertNotEqual("changed", second["candidates"][0]["fields"]["type"])
        self.assertNotEqual("changed", second["sources"][0]["title"])


if __name__ == "__main__":
    unittest.main()
