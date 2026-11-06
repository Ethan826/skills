"""Tests for tell_lint.py, following the gate-integrity standard block.

Run from the skill folder: python3 -m unittest discover -s scripts
TELL_LINT_PATH swaps in another checker, which is how the mutant test works.
"""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
CHECKER = Path(os.environ.get("TELL_LINT_PATH", HERE / "tell_lint.py"))
RULES = HERE / "tell_rules.json"


def load_checker():
    spec = importlib.util.spec_from_file_location("tell_lint", CHECKER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["tell_lint"] = module
    spec.loader.exec_module(module)
    return module


lint = load_checker()


def run_cli(*args, stdin=None):
    return subprocess.run(
        [sys.executable, "-I", str(CHECKER), *args],
        input=stdin, capture_output=True, text=True)


def ids(result):
    return [f["rule"] for f in result["findings"]]


class RuleProbes(unittest.TestCase):
    """Block item 5: every rule proves its own spelling and its near miss."""

    def test_rule_inventory_floor_and_named_member(self):
        rules = lint.load_rules()
        self.assertGreaterEqual(len(rules), 64)
        self.assertIn("not-just", [r["id"] for r in rules])

    def test_every_rule_catches_its_probe_exactly_once(self):
        for rule in lint.load_rules():
            self.assertTrue(rule["probes"])
            for probe in rule["probes"]:
                with self.subTest(rule=rule["id"], probe=probe):
                    result = lint.scan(probe, plain=rule.get("plain", False))
                    self.assertEqual(ids(result).count(rule["id"]), 1)

    def test_every_near_miss_finds_nothing_for_its_rule(self):
        for rule in lint.load_rules():
            self.assertTrue(rule["near_misses"])
            for probe in rule["near_misses"]:
                with self.subTest(rule=rule["id"], probe=probe):
                    result = lint.scan(probe, plain=rule.get("plain", False))
                    self.assertEqual(ids(result).count(rule["id"]), 0)

    def test_rule_ids_are_unique(self):
        names = [r["id"] for r in lint.load_rules()]
        self.assertEqual(len(names), len(set(names)))


class Masking(unittest.TestCase):
    """Block item 6: code, URLs and front matter neither trigger nor satisfy."""

    def test_inline_code_is_not_scanned(self):
        self.assertEqual(ids(lint.scan("Call `delve` with one argument today.")), [])

    def test_fenced_code_is_not_scanned(self):
        text = "Run this command now.\n\n```\nlet's dive in\n```\n\nThen stop it."
        self.assertEqual(ids(lint.scan(text)), [])

    def test_url_is_not_scanned(self):
        text = "See https://example.com/delve/tapestry for the full list."
        self.assertEqual(ids(lint.scan(text)), [])

    def test_front_matter_is_not_scanned(self):
        text = "---\ntitle: delve\n---\n\nThe body has ordinary words in it."
        self.assertEqual(ids(lint.scan(text)), [])

    def test_masking_keeps_offsets_so_lines_stay_true(self):
        text = "```\ncode\n```\n\nWe delve here."
        self.assertEqual(lint.scan(text)["findings"][0]["line"], 5)

    def test_residue_rules_still_read_inside_urls(self):
        text = "See https://example.com/a?utm_source=chatgpt.com for it."
        self.assertEqual(ids(lint.scan(text)), ["url-residue"])

    def test_a_hit_inside_double_quotes_is_listed_but_does_not_block(self):
        result = lint.scan('The author wrote "let\'s dive in" as a joke.')
        self.assertEqual(ids(result), ["staged-opener"])
        self.assertTrue(result["findings"][0]["quoted"])
        self.assertEqual(result["blocking"], [])

    def test_a_hit_inside_a_blockquote_does_not_block(self):
        result = lint.scan("> Let's dive in, the source said.\n\nPlain text here.")
        self.assertEqual(result["blocking"], [])


class Tiers(unittest.TestCase):
    def test_one_strong_hit_blocks(self):
        result = lint.scan("Here's the thing about caching in this service.")
        self.assertEqual([f["rule"] for f in result["blocking"]], ["staged-opener"])

    def test_one_weak_hit_alone_does_not_block(self):
        result = lint.scan("The cache is a valuable part of this service.")
        self.assertEqual(ids(result), ["ai-word"])
        self.assertEqual(result["blocking"], [])

    def test_two_distinct_weak_rules_in_one_paragraph_block(self):
        result = lint.scan("The cache is valuable. It can be argued that it helps.")
        self.assertEqual(sorted(f["rule"] for f in result["blocking"]),
                         ["ai-word", "waffle"])

    def test_the_same_weak_rule_twice_is_not_company(self):
        result = lint.scan("A valuable cache and a robust queue sit here.")
        self.assertEqual(result["blocking"], [])

    def test_weak_rules_in_separate_paragraphs_are_not_company(self):
        text = "The cache is valuable.\n\nIt can be argued that it helps."
        self.assertEqual(lint.scan(text)["blocking"], [])


class Isbn(unittest.TestCase):
    def test_bad_checksum_is_flagged(self):
        self.assertEqual(ids(lint.scan("See ISBN 978-0-306-40615-8 for this.")),
                         ["isbn-checksum"])

    def test_good_isbn13_and_isbn10_pass(self):
        text = "See ISBN 978-0-306-40615-7 and ISBN 0-306-40615-2 for this."
        self.assertEqual(ids(lint.scan(text)), [])


class PlainMode(unittest.TestCase):
    def test_markdown_syntax_is_a_tell_only_in_plain_text(self):
        text = "The **enzyme** breaks starch down in the mouth."
        self.assertEqual(ids(lint.scan(text)), [])
        self.assertEqual(ids(lint.scan(text, plain=True)), ["markdown-leak"])

    def test_plain_mode_does_not_mask_backticks(self):
        self.assertIn("ai-word", ids(lint.scan("We `delve` here.", plain=True)))


class KeepList(unittest.TestCase):
    """Block section 4: reviewed and pinned, an unused entry fails."""

    def test_entry_clears_its_finding_and_stays_visible(self):
        keep = [{"rule": "staged-opener", "text": "Here's the thing", "count": 1,
                 "reason": "the author's voice"}]
        result = lint.scan("Here's the thing about caching.", keep=keep)
        self.assertEqual(result["blocking"], [])
        self.assertEqual(result["kept"][0]["rule"], "staged-opener")

    def test_entry_that_matches_nothing_is_an_error(self):
        keep = [{"rule": "staged-opener", "text": "Here's the thing", "count": 1,
                 "reason": "voice"}]
        with self.assertRaisesRegex(lint.LintError, "keep entry matches nothing"):
            lint.scan("Ordinary words about caching.", keep=keep)

    def test_a_new_use_beyond_the_pinned_count_still_blocks(self):
        keep = [{"rule": "staged-opener", "text": "Here's the thing", "count": 1,
                 "reason": "voice"}]
        text = "Here's the thing about caching. Here's the thing about queues."
        self.assertEqual(len(lint.scan(text, keep=keep)["blocking"]), 1)

    def test_entry_without_a_reason_is_an_error(self):
        keep = [{"rule": "staged-opener", "text": "Here's the thing", "count": 1}]
        with self.assertRaisesRegex(lint.LintError, "keep entry needs"):
            lint.scan("Here's the thing about caching.", keep=keep)

    def test_whole_rule_entry_covers_a_voice_sample(self):
        keep = [{"rule": "dash", "all": True, "reason": "sample uses dashes"}]
        result = lint.scan("The plan — such as it is — works.", keep=keep)
        self.assertEqual(result["blocking"], [])
        self.assertEqual(len(result["kept"]), 2)


class Metrics(unittest.TestCase):
    def test_counts_prose_words_only(self):
        result = lint.scan("One two three.\n\n```\nfour five\n```\n")
        self.assertEqual(result["metrics"]["words"], 3)

    def test_reports_sentence_spread_and_participle_rate(self):
        text = "Short one here. This sentence is quite a lot longer, adding words."
        metrics = lint.scan(text)["metrics"]
        self.assertEqual(metrics["sentences"], 2)
        self.assertGreater(metrics["sentence_length_stdev"], 0)
        self.assertGreater(metrics["participial_per_1000_words"], 0)


class Cli(unittest.TestCase):
    """Block items 1, 2, 3 and 9: named messages and both modes."""

    def write(self, data, suffix=".md"):
        handle = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        handle.write(data)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_clean_text_exits_zero(self):
        done = run_cli(self.write(b"The cache holds recent rows for a minute."))
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_planted_tell_exits_one_and_names_the_rule(self):
        done = run_cli(self.write(b"Let's dive in to caching."))
        self.assertEqual(done.returncode, 1)
        self.assertIn("staged-opener", done.stdout)

    def test_report_mode_exits_zero_on_the_same_tell(self):
        done = run_cli("--report", self.write(b"Let's dive in to caching."))
        self.assertEqual(done.returncode, 0)
        self.assertIn("staged-opener", done.stdout)

    def test_missing_file_fails_with_a_named_message(self):
        done = run_cli("/no/such/file.md")
        self.assertEqual(done.returncode, 2)
        self.assertIn("cannot read", done.stderr)

    def test_binary_input_fails_with_a_named_message(self):
        done = run_cli(self.write(b"\xff\xfe\x00bad"))
        self.assertEqual(done.returncode, 2)
        self.assertIn("not UTF-8", done.stderr)

    def test_empty_input_fails(self):
        done = run_cli(self.write(b"   \n"))
        self.assertEqual(done.returncode, 2)
        self.assertIn("no prose", done.stderr)

    def test_code_only_input_fails_because_nothing_was_scanned(self):
        done = run_cli(self.write(b"```\ncode\n```\n"))
        self.assertEqual(done.returncode, 2)
        self.assertIn("no prose", done.stderr)

    def test_stdin_is_read_with_a_dash(self):
        done = run_cli("-", stdin="Let's dive in to caching.")
        self.assertEqual(done.returncode, 1)

    def test_json_output_parses(self):
        done = run_cli("--json", self.write(b"Let's dive in to caching."))
        self.assertEqual(json.loads(done.stdout)["blocking"][0]["rule"], "staged-opener")

    def test_broken_rules_file_fails(self):
        done = run_cli("--rules", self.write(b"[{\"id\": \"x\"}]", ".json"),
                       self.write(b"Words."))
        self.assertEqual(done.returncode, 2)
        self.assertIn("rule", done.stderr)

    def test_invalid_rule_regex_fails(self):
        rule = {"id": "x", "tier": "weak", "ref": "R1", "pattern": "(",
                "probes": ["a"], "near_misses": ["b"]}
        done = run_cli("--rules", self.write(json.dumps([rule]).encode(), ".json"),
                       self.write(b"Words."))
        self.assertEqual(done.returncode, 2)
        self.assertIn("rule x", done.stderr)

    def test_empty_rules_file_fails(self):
        done = run_cli("--rules", self.write(b"[]", ".json"), self.write(b"Words."))
        self.assertEqual(done.returncode, 2)
        self.assertIn("no rules", done.stderr)


class CatalogContract(unittest.TestCase):
    """Rules and catalogs agree in both directions."""

    @classmethod
    def setUpClass(cls):
        refs = SKILL / "references"
        humanizer = (refs / "humanizer-3.1.0.md").read_text(encoding="utf-8")
        additional = (refs / "additional-tells.md").read_text(encoding="utf-8")
        cls.researched = (refs / "researched-tells.md").read_text(encoding="utf-8")
        cls.sections = set()
        cls.sections |= {"§" + n for n in re.findall(r"^### (\d+)\.", humanizer, re.M)}
        cls.sections |= set(re.findall(r"^### (A\d+)\.", additional, re.M))
        cls.r_sections = set(re.findall(r"^### (R\d+)\.", cls.researched, re.M))
        cls.sections |= cls.r_sections

    def test_catalog_inventory_is_not_empty(self):
        self.assertGreaterEqual(len(self.sections), 40)
        self.assertIn("R1", self.sections)

    def test_every_rule_refers_to_a_real_catalog_section(self):
        for rule in lint.load_rules():
            with self.subTest(rule=rule["id"]):
                self.assertIn(rule["ref"], self.sections)

    def test_every_researched_tell_has_a_rule_or_says_it_has_none(self):
        covered = {r["ref"] for r in lint.load_rules()}
        blocks = re.split(r"^### ", self.researched, flags=re.M)[1:]
        self.assertGreaterEqual(len(blocks), 15)
        for block in blocks:
            name = block.split(".", 1)[0]
            with self.subTest(section=name):
                self.assertIn("**Lint:**", block)
                says_none = "**Lint:** none" in block
                self.assertNotEqual(name in covered, says_none)


class CheckerMutant(unittest.TestCase):
    """Block item 7: a broken checker must fail this suite."""

    MUTANTS = [
        ("scans nothing", "for rule in rules:", "for rule in []:"),
        ("never blocks", "if finding[\"tier\"] == \"strong\"", "if False"),
        ("skips masking", "masked = mask(text, plain)", "masked = text"),
    ]

    @unittest.skipIf("TELL_LINT_PATH" in os.environ, "already running a mutant")
    def test_each_mutant_fails_the_suite(self):
        source = (HERE / "tell_lint.py").read_text(encoding="utf-8")
        for name, old, new in self.MUTANTS:
            with self.subTest(mutant=name), tempfile.TemporaryDirectory() as room:
                self.assertIn(old, source)
                broken = Path(room) / "tell_lint.py"
                broken.write_text(source.replace(old, new), encoding="utf-8")
                shutil.copy(RULES, room)
                done = subprocess.run(
                    [sys.executable, "-m", "unittest", "test_tell_lint"],
                    cwd=HERE, capture_output=True, text=True,
                    env={**os.environ, "TELL_LINT_PATH": str(broken)})
                self.assertNotEqual(done.returncode, 0)
                self.assertRegex(done.stderr, r"FAILED \(")


if __name__ == "__main__":
    unittest.main()
