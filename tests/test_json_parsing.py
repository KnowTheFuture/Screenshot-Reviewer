"""Unit tests for screenshot_enricher._extract_json_block."""

import unittest

from screenshot_enricher import _extract_json_block


class TestJSONParsing(unittest.TestCase):
    def setUp(self):
        self.good = '[{"filename":"a.png","tags_ai":["ok"]}]'
        self.prose = "Sure! Here's what I found:\n" + self.good + "\nHope this helps!"
        self.truncated = '[{"filename":"a.png","tags_ai":["ok"]}'
        self.extra = "Some explanation\n" + self.good + "\n--END--"
        self.invalid = "no json here"

    def test_good_json(self):
        result = _extract_json_block(self.good)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["filename"], "a.png")

    def test_wrapped_in_prose(self):
        result = _extract_json_block(self.prose)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["tags_ai"], ["ok"])

    def test_extra_commentary(self):
        result = _extract_json_block(self.extra)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["filename"], "a.png")

    def test_truncated_returns_fallback(self):
        result = _extract_json_block(self.truncated)
        self.assertEqual(result, {"ask_user": True})

    def test_invalid_returns_fallback(self):
        result = _extract_json_block(self.invalid)
        self.assertEqual(result, {"ask_user": True})


if __name__ == "__main__":
    unittest.main()
