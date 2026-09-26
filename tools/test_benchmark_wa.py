"""Tests for benchmark evidence boundaries, independent of decoder implementation."""
import unittest

import benchmark_wa as benchmark


def source_row(prefix="ABCDEF1234", make="EXAMPLE", model="ONE", year="2024", count="1"):
    return {"vin_1_10": prefix, "make": make, "model": model, "model_year": year, "vehicle_count": count}


def resolution(value=None, status="KNOWN"):
    return {"status": status, "value": value}


def decoded(model="ONE", year="2024", make="EXAMPLE"):
    return {"brand": resolution(make), "model": resolution(model), "modelYear": resolution(year)}


class WaBenchmarkTest(unittest.TestCase):
    def test_conflicting_grouped_labels_are_preserved_and_excluded_per_field(self):
        groups = benchmark.group_rows([source_row(count="4"), source_row(model="TWO", count="6")])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["vehicleCount"], 10)
        result = benchmark.evaluate_group(groups[0], lambda _: decoded(), [])
        weighted = benchmark.summarize([result], weighted=True)
        self.assertEqual(weighted["model"]["sourceConflicts"], 10)
        self.assertIsNone(weighted["model"]["coverage"])
        self.assertEqual(weighted["make"]["known"], 10)
        self.assertEqual(weighted["make"]["exactPrecision"], 1)

    def test_continuation_sensitive_prediction_is_an_abstention(self):
        group = benchmark.group_rows([source_row()])[0]
        result = benchmark.evaluate_group(group, lambda vin: decoded(model="ONE" if vin[10] == "A" else "TWO"), [])
        summary = benchmark.summarize([result])["model"]
        self.assertEqual(summary["known"], 0)
        self.assertEqual(summary["coverage"], 0)
        self.assertIsNone(summary["exactPrecision"])
        self.assertEqual(summary["abstentions"], {"PROBE_DISAGREEMENT": 1})

    def test_one_known_probe_does_not_hide_unknown_others(self):
        self.assertEqual(benchmark.consensus([resolution("ONE"), resolution(status="UNKNOWN")]),
                         ("PROBE_INCOMPLETE", None))
        self.assertEqual(benchmark.consensus([resolution(status="AMBIGUOUS")] * 3), ("AMBIGUOUS", None))

    def test_alias_is_explicit_make_scoped_and_does_not_change_exact_precision(self):
        group = benchmark.group_rows([source_row(model="ONE-E")])[0]
        alias = {"make": "EXAMPLE", "observed": "ONE-E", "decoded": "ONE ELECTRIC", "reason": "Fixture"}
        result = benchmark.evaluate_group(group, lambda _: decoded(model="One Electric"), [alias])
        summary = benchmark.summarize([result])["model"]
        self.assertEqual(summary["exactPrecision"], 0)
        self.assertEqual(summary["aliasPrecision"], 1)
        self.assertFalse(benchmark.accepted_alias("OTHER", "ONE-E", "ONE ELECTRIC", [alias]))
        self.assertNotEqual(benchmark.normalized("ONE-E"), benchmark.normalized("ONE E"))

    def test_weighted_precision_does_not_confuse_unknown_with_incorrect(self):
        groups = benchmark.group_rows([source_row(count="9"), source_row(prefix="ABCDEF1235", count="1"),
                                       source_row(prefix="ABCDEF1236", count="10")])
        def decode(vin):
            result = decoded(model="TWO" if vin[9] == "5" else "ONE")
            if vin[9] == "6":
                result["model"] = resolution(status="UNKNOWN")
            return result
        rows = [benchmark.evaluate_group(group, decode, []) for group in groups]
        summary = benchmark.summarize(rows, weighted=True)["model"]
        self.assertEqual(summary["coverage"], .5)
        self.assertEqual(summary["exactPrecision"], .9)
        self.assertEqual(summary["abstentions"], {"UNKNOWN": 10})

    def test_extended_wmi_is_not_resolved_using_invented_serial(self):
        group = benchmark.group_rows([source_row(prefix="AB9DEF1234")])[0]
        def fail(_):
            self.fail("Decoder must not be called for an unresolved extended WMI")
        result = benchmark.evaluate_group(group, fail, [])
        self.assertEqual(result["fields"]["make"]["status"], "UNSUPPORTED_PREFIX")

    def test_rejects_accidentally_downloaded_identifiers_or_individual_records(self):
        for row in [dict(source_row(), county="Somewhere"), source_row(prefix="ABCDEF1234A000001"),
                    source_row(count="0"), source_row(count=True)]:
            with self.subTest(row=row), self.assertRaises(ValueError):
                benchmark.group_rows([row])


if __name__ == "__main__":
    unittest.main()
