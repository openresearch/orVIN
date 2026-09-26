"""Guard the importer against inventing matches while cleaning source templates."""
import unittest

import astra


class AstraImporterTest(unittest.TestCase):
    def test_accepts_position_templates_and_explicit_alternatives_without_repair(self):
        self.assertEqual(("TMB...5E.........",), astra.templates("TMB...5E........."))
        self.assertEqual(("VF1RFD...........", "VF1RFE..........."),
                         astra.templates("VF1RFE........... / VF1RFD..........."))

    def test_rejects_ambiguous_syntax_and_entire_mixed_valid_invalid_rows(self):
        for pattern in ("TMB..............", "WV....1K.........", "VF3LPHNSK", "SCBCC42...........",
                        "WAPB332CO.XE40...", "siehe Bemerkungen", "", "TMB...5E......... / unknown"):
            with self.subTest(pattern=pattern):
                self.assertEqual((), astra.templates(pattern))


if __name__ == "__main__":
    unittest.main()
