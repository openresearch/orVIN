import re
import unittest

from decoding import pattern_regex


class PatternLanguageTest(unittest.TestCase):
    def test_stars_are_single_characters_and_patterns_are_anchored_prefixes(self):
        expression = re.compile(pattern_regex("A*C|*X"))
        self.assertIsNotNone(expression.match("ABC|TX123456"))
        self.assertIsNone(expression.match("AC|TX123456"))
        self.assertIsNone(expression.match("XABC|TX123456"))

    def test_brackets_ranges_pipe_and_source_special_range(self):
        expression = re.compile(pattern_regex("[A-C][1-A]***|*[AFK]"))
        self.assertIsNotNone(expression.match("BA123|TF000001"))
        self.assertIsNotNone(expression.match("C1123|TK000001"))
        self.assertIsNone(expression.match("BZ123|TF000001"))
        self.assertIsNone(expression.match("BA123XTF000001"))

    def test_numeric_formulas_only_match_numeric_capture_positions(self):
        expression = re.compile(pattern_regex("**##"))
        self.assertIsNotNone(expression.match("AB24C|8A000001"))
        self.assertIsNone(expression.match("AB2XC|8A000001"))
        self.assertIsNone(pattern_regex("[AB]##"))

    def test_like_underscore_and_percent_differ_from_bracket_regex(self):
        self.assertIsNotNone(re.match(pattern_regex("A_C%X"), "ABC12X"))
        self.assertIsNone(re.match(pattern_regex("[A]_C"), "ABC"))
        self.assertIsNotNone(re.match(pattern_regex("[A]_C"), "A_C"))


if __name__ == "__main__":
    unittest.main()
