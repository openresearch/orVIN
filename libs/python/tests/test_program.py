"""Synthetic rule programs test policy, not real-world vehicle assertions."""
import copy
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

from orvin import Context, VinDecoder
from orvin.details import RichDecoder
from orvin.lookup import _data_directory
from orvin.program import rules, manifest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
from compile_dataset import rule_rows, FORMAT, CAPABILITIES


class ProgramTest(unittest.TestCase):
    VIN = "ZZZAAAAAAAAAAAAAA"

    def decoder(self, inputs):
        # Compile new rules using existing operations, with no engine modifications.
        content = ("\n".join(rule_rows(inputs, {"test-only"}, {"Make", "Model", "ModelYear"})) + "\n").encode()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "rules.tsv").write_bytes(content)
            (path / "manifest.tsv").write_text(f"V\t{FORMAT}\t{CAPABILITIES}\nF\trules.tsv\t{hashlib.sha256(content).hexdigest()}\n")
            compiled = rules(path)
        rich = RichDecoder(_data_directory() / "decoding")
        rich.literal_rules = compiled
        rich.sources["test-only"] = {"id": "test-only", "url": "https://example.invalid/test-only", "title": "Synthetic policy test", "publisher": "ORvin tests"}
        decoder = VinDecoder({"version": "test", "sources": [], "manufacturers": [], "assignments": []}, "test")
        decoder._rich = rich
        return decoder

    def rule(self, name, market, model="Accord", year=None):
        fields = {"Make": "HONDA", "Model": model}
        if year:
            fields["ModelYear"] = str(year)
        return {"id": name, "pattern": self.VIN, "markets": [market] if market else [], "marketScope": market or "GLOBAL",
                "stage": "synthetic-policy-test", **({"modelYear": year} if year else {}),
                "claims": [{"code": code, "value": value, "sourceId": "test-only", "kind": "TEST_ONLY",
                            "ruleId": name, "keys": "Synthetic; not a real vehicle assertion"} for code, value in fields.items()]}

    def test_any_source_market_can_suggest_and_applicable_override_wins(self):
        decoder = self.decoder([self.rule("japan", "JP"), self.rule("brazil", "BR", "Civic")])
        local = decoder.decode_vehicle(self.VIN, Context(market="BR")).short()
        self.assertEqual("Civic", local["vehicle"]["model"])
        self.assertEqual("RESOLVED", local["fieldStatus"]["model"])
        self.assertEqual([], local["assumptions"])
        # Different conditional answers never become a majority-vote guess.
        abroad = decoder.decode_vehicle(self.VIN, Context(market="ZA")).short()
        self.assertEqual("AMBIGUOUS", abroad["fieldStatus"]["model"])
        self.assertIsNone(abroad["vehicle"]["model"])
        single = self.decoder([self.rule("japan", "JP")]).decode_vehicle(self.VIN, Context(market="NZ")).short()
        self.assertEqual("SUGGESTED", single["fieldStatus"]["model"])
        self.assertEqual(["JP"], single["assumptions"][0]["sourceMarkets"])
        self.assertEqual("NZ", single["assumptions"][0]["requestedMarket"])

    def test_order_duplicates_and_conflicts_do_not_choose_a_winner(self):
        a, b = self.rule("a", None), self.rule("b", None, "Civic")
        duplicated = copy.deepcopy(a)
        duplicated["claims"] *= 3
        answers = [self.decoder(ruleset).decode_vehicle(self.VIN).short() for ruleset in ([a, b], [b, a], [duplicated, b])]
        self.assertEqual(answers[0], answers[1])
        self.assertEqual(answers[0], answers[2])
        self.assertEqual("AMBIGUOUS", answers[0]["fieldStatus"]["model"])
        conflict = self.decoder([self.rule("local", "BR", year=2005), self.rule("foreign", "JP", "Civic", 2006)])
        answer = conflict.decode_vehicle(self.VIN, Context(2006, "BR")).short()
        self.assertEqual("CONFLICT", answer["fieldStatus"]["model"])
        self.assertIsNone(answer["vehicle"]["model"])

    def test_unsupported_program_and_unknown_sources_fail_closed(self):
        invalid = self.rule("bad", "JP")
        invalid["claims"][0]["sourceId"] = "missing"
        with self.assertRaisesRegex(ValueError, "Unknown claim source"):
            self.decoder([invalid])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "manifest.tsv").write_text("V\torvin-runtime-999\tarbitrary-code\n")
            with self.assertRaisesRegex(RuntimeError, "Unsupported"):
                manifest(path)


if __name__ == "__main__":
    unittest.main()
