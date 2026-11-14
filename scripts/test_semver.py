"""Tests for semver.py, from SemVer 2.0.0 (semver.org) sections 2, 9-11.

Run from the repository root: python3 -m unittest discover -s scripts
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import semver  # noqa: E402


class Precedence(unittest.TestCase):
    def assert_ascending(self, versions):
        for lower, higher in zip(versions, versions[1:]):
            with self.subTest(lower=lower, higher=higher):
                self.assertLess(semver.parse(lower), semver.parse(higher))
                self.assertGreater(semver.parse(higher), semver.parse(lower))
                self.assertNotEqual(semver.parse(lower),
                                    semver.parse(higher))

    def test_spec_section_11_prerelease_chain(self):
        self.assert_ascending([
            "1.0.0-alpha", "1.0.0-alpha.1", "1.0.0-alpha.beta",
            "1.0.0-beta", "1.0.0-beta.2", "1.0.0-beta.11", "1.0.0-rc.1",
            "1.0.0"])

    def test_spec_section_11_numeric_fields(self):
        self.assert_ascending(["1.0.0", "2.0.0", "2.1.0", "2.1.1"])
        self.assert_ascending(["1.9.0", "1.10.0", "1.11.0"])

    def test_build_metadata_ignored_for_precedence(self):
        self.assertEqual(semver.parse("1.0.0+build.1"),
                         semver.parse("1.0.0+build.2"))
        self.assertEqual(semver.parse("1.0.0-alpha+001"),
                         semver.parse("1.0.0-alpha"))

    def test_prerelease_flag(self):
        self.assertTrue(semver.parse("4.2.0-beta.1").is_prerelease)
        self.assertFalse(semver.parse("4.2.0+meta").is_prerelease)


class Parse(unittest.TestCase):
    def test_invalid_strings_raise(self):
        for text in ["v1", "1", "1.0", "v1.0.0", "01.0.0", "1.0.0-01",
                     "1.0.0-", "1.0.0+", "", " 1.0.0", "1.0.0-a..b"]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                semver.parse(text)

    def test_valid_strings_parse(self):
        version = semver.parse("1.2.3-rc.1+exp.sha.5114f85")
        self.assertEqual((version.major, version.minor, version.patch),
                         (1, 2, 3))
        self.assertEqual(version.prerelease, ("rc", "1"))


class LatestStable(unittest.TestCase):
    def test_prerelease_ignored_by_default(self):
        self.assertEqual(
            semver.latest_stable(["4.1.1", "4.2.0-beta.1"], False), "4.1.1")

    def test_prerelease_allowed(self):
        self.assertEqual(
            semver.latest_stable(["4.2.0-beta.1", "4.2.0-beta.2"], True),
            "4.2.0-beta.2")

    def test_numeric_not_lexical(self):
        self.assertEqual(
            semver.latest_stable(["9.0.0", "82.1.1", "81.0.0"], False),
            "82.1.1")

    def test_none_when_nothing_qualifies(self):
        self.assertIsNone(semver.latest_stable([], False))
        self.assertIsNone(semver.latest_stable(["1.0.0-rc.1"], False))

    def test_unparseable_entries_skipped(self):
        self.assertEqual(semver.latest_stable(["latest", "1.0.0"], False),
                         "1.0.0")


if __name__ == "__main__":
    unittest.main()
