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
        self.assertGreaterEqual(len(rules), 80)
        self.assertIn("not-just", [r["id"] for r in rules])
        self.assertIn("buried-instruction", [r["id"] for r in rules])
        self.assertIn("container-hold", [r["id"] for r in rules])

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


class CodeRules(unittest.TestCase):
    """A "code" rule reads inline code spans; fenced code stays masked."""

    def test_code_rule_sees_a_span_that_other_rules_cannot(self):
        self.assertEqual(ids(lint.scan("`src/a` holds the types.")), ["container-hold"])

    def test_code_rule_ignores_fenced_code(self):
        text = "Run this now.\n\n```\n`src/a` holds the types.\n```\n\nThen stop."
        self.assertEqual(ids(lint.scan(text)), [])


class ObservedExamples(unittest.TestCase):
    """Converted register entries: the verbatim example fails, the rewrite passes."""

    CASES = [
        ("container-hold",
         "- `src/runtime`, `src/program`, `src/facade`: will hold the Effect shell,"
         " the wiring and the CLI. They hold no code.",
         "`src/runtime`, `src/program` and `src/facade` are empty. The Effect shell"
         " will go in `src/runtime`, the wiring in `src/program` and the CLI in"
         " `src/facade`."),
        ("status-contrast", "Planned, not built.",
         "Only the Domain types, the decoders and the pacing function have code so"
         " far. The rest of this page describes the design."),
        ("status-heading", "## Event log (planned)\n\nThe log is append-only.",
         "## Event log\n\nThe log is append-only."),
        ("status-bold-repeat",
         "- **Built:** the decoders.\n- **Planned:** the CLI.",
         "The decoders have code. The CLI is still a design."),
        ("buried-instruction",
         "For sequence diagrams of a tranche and of a launch attempt, the hold\n"
         "states, a plain-words account of pacing, and what exists today, read\n"
         "docs/how-it-works.md. Each src/ layer has a README linked from there.",
         "Read docs/how-it-works.md next. It has diagrams of one batch of work"
         " and of how foreman decides to start an agent, explains how pacing"
         " works, and lists what exists today. Each source directory has its own"
         " README, linked from that page."),
    ]

    def test_example_fails_and_rewrite_passes(self):
        for rule, bad, good in self.CASES:
            with self.subTest(rule=rule):
                self.assertIn(rule, [f["rule"] for f in lint.scan(bad)["blocking"]])
                self.assertEqual(ids(lint.scan(good)), [])

    NOTES = [
        ("hedged-intent",
         "Row polymorphism is the intended bridge to TypeScript's structural\n"
         "flexibility",
         "Waxwing uses row polymorphism to give TypeScript programmers the\n"
         "flexibility they expect from structural types."),
        ("would-chain",
         "Planned inference would collect the row from the operations a\n"
         "function calls. Construction requirements and failures would be\n"
         "accounted for where a service is constructed. Adding a service or\n"
         "error family would no longer require copying its name through every\n"
         "caller. Explicit signatures would still limit what a function is\n"
         "allowed to do.",
         "We plan to have the compiler work out a function's requirements for\n"
         "you. It will look at the services and operations the function uses\n"
         "and add them to the function's type, in the part of the type called\n"
         "its row. If you write a function's type yourself, the compiler still\n"
         "checks the body against it."),
        ("passive-vague-verb",
         "Construction requirements and failures would be accounted for where a\n"
         "service is constructed.",
         "When code constructs a service, the compiler will add that service's\n"
         "own requirements and possible errors to the constructing code's type."),
        ("staged-claim",
         "The hypothesis is that these features can make dependencies and\n"
         "errors compose without a new environment type, error union or\n"
         "transformer stack for every combination.",
         "We expect inferred rows to let you call functions that need\n"
         "different services, or that fail in different ways, without writing\n"
         "any glue types to combine them."),
        ("vague-influence",
         "Koka, Unison and Effekt inform the effect system's lineage.",
         "Koka, Unison and Effekt are research languages whose type checkers\n"
         "track side effects."),
        ("deserves",
         "Dependencies, expected failures, external interaction, state and\n"
         "divergence deserve precise descriptions instead of one catch-all IO.",
         "A function's type will list five kinds of effect. Haskell gives all\n"
         "five the single type `IO`."),
        ("gerund-pair", "the type itself lists the printing and the throwing.",
         "The `<console,exn>` part says that the function may print and may\n"
         "throw."),
        ("headless-summary",
         "whether it changes state, and whether it might run forever, instead\n"
         "of putting all of that under one IO type as Haskell does.",
         "whether it changes state, and whether it might run forever.\n"
         "Haskell gives all five the single type `IO`."),
        ("touch-change", "It won't touch your verbatim examples.",
         "The agent will not edit any entry's Example field, which quotes the\n"
         "original text exactly."),
        ("contrast-density",
         "Fix the file, rather than editing the file under it, and"
         " cross-reference instead of duplicating.",
         "Cross-reference the existing entry."),
        ("unreasoned-preference",
         "a note when the phrase repeats within a short span. That beats\n"
         "blocking every single use.",
         "It will not block a single use, because one phrase of that kind is\n"
         "often the clearest way to state a choice."),
    ]

    def test_noted_example_is_found_without_blocking_and_rewrite_passes(self):
        for rule, bad, good in self.NOTES:
            with self.subTest(rule=rule):
                result = lint.scan(bad)
                self.assertIn(rule, ids(result))
                self.assertNotIn(rule, [f["rule"] for f in result["blocking"]])
                self.assertNotIn(rule, ids(lint.scan(good)))

    def test_domain_noun_hold_is_not_the_tell(self):
        text = ("Foreman creates a hold when a step fails. `foreman release` clears"
                " that hold, and `src/domain/hold.ts` defines it.")
        self.assertNotIn("container-hold", ids(lint.scan(text)))


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

    def test_a_note_never_blocks_and_is_not_company(self):
        result = lint.scan("The cache is valuable. All of this is in the README.")
        self.assertEqual(sorted(ids(result)), ["ai-word", "headless-summary"])
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
        humanizer = (refs / "humanizer-4.0.0.md").read_text(encoding="utf-8")
        additional = (refs / "additional-tells.md").read_text(encoding="utf-8")
        cls.researched = (refs / "researched-tells.md").read_text(encoding="utf-8")
        cls.sections = set()
        cls.sections |= {"§" + n for n in re.findall(r"^### (\d+)\.", humanizer, re.M)}
        cls.sections |= set(re.findall(r"^### (A\d+)\.", additional, re.M))
        cls.r_sections = set(re.findall(r"^### (R\d+)\.", cls.researched, re.M))
        cls.sections |= cls.r_sections
        cls.observed = (refs / "observed-tells.md").read_text(encoding="utf-8")
        cls.o_sections = set(re.findall(r"^### (O\d+)\.", cls.observed, re.M))
        cls.sections |= cls.o_sections

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


class ObservedRegister(unittest.TestCase):
    """The register's fields are present and its statuses agree with the rules."""

    FIELDS = ("Observed", "Example", "Why", "Rewrite", "Mechanizable", "Status",
              "Checklist")

    @classmethod
    def setUpClass(cls):
        text = (SKILL / "references" / "observed-tells.md").read_text(encoding="utf-8")
        text = re.split(r"^## ", text, flags=re.M)[0]
        cls.entries = {}
        for block in re.split(r"^### ", text, flags=re.M)[1:]:
            match = re.match(r"(O\d+)\.", block)
            if match:
                cls.entries[match.group(1)] = block

    def test_register_inventory_floor(self):
        self.assertGreaterEqual(len(self.entries), 49)
        self.assertIn("O2", self.entries)

    def test_every_entry_has_every_field_in_order(self):
        for name, block in self.entries.items():
            with self.subTest(entry=name):
                places = [block.find("**%s:**" % field) for field in self.FIELDS]
                self.assertNotIn(-1, places)
                self.assertEqual(places, sorted(places))
                self.assertRegex(block, r"\*\*Observed:\*\* \d{4}-\d{2}-\d{2}")
                self.assertRegex(block, r"\*\*Mechanizable:\*\* (?:yes|partly|no)\b")

    def status(self, block):
        line = block.split("**Status:**", 1)[1].split("**Checklist:**", 1)[0]
        return " ".join(line.split())

    def test_status_is_open_judgment_only_or_converted(self):
        for name, block in self.entries.items():
            with self.subTest(entry=name):
                self.assertRegex(self.status(block),
                                 r"^(?:open|judgment-only|converted to `[a-z-]+`"
                                 r"(?:, `[a-z-]+`)*)$")

    def test_converted_status_and_rule_refs_agree_both_ways(self):
        rules = lint.load_rules()
        for name, block in self.entries.items():
            with self.subTest(entry=name):
                listed = set(re.findall(r"`([a-z-]+)`", self.status(block)))
                refs = {r["id"] for r in rules if r["ref"] == name}
                self.assertEqual(listed, refs)


class RegisterRewrites(unittest.TestCase):
    """The register's Rewrite blocks must not show the tells it records.

    Each block is scanned with its blockquote markers and double quotes
    removed, so the rewrite is read as prose. It fails on any blocking
    finding and on any finding of a rule converted from the register.
    scripts/keep/observed-rewrites.keep.json lists the fragments that must
    stay verbatim (a rewrite that quotes a phrase it discusses), each with
    its entry and a reason; an unused keep entry is an error.
    """

    KEEP = HERE / "keep" / "observed-rewrites.keep.json"

    @classmethod
    def setUpClass(cls):
        text = (SKILL / "references" / "observed-tells.md").read_text(encoding="utf-8")
        entries, worked = re.split(r"^## Worked example\b.*$", text, flags=re.M)
        cls.rewrites = {}
        body = worked.split("\nRewrite:\n", 1)[1]
        cls.rewrites["worked-example"] = re.sub(r"^> ?", "", body, flags=re.M).replace('"', "")
        for block in re.split(r"^### ", entries, flags=re.M)[1:]:
            match = re.match(r"(O\d+)\.", block)
            if match:
                body = block.split("**Rewrite:**", 1)[1].split("**Mechanizable:**", 1)[0]
                body = re.sub(r"^> ?", "", body, flags=re.M).replace('"', "")
                cls.rewrites[match.group(1)] = body
        cls.keep = json.loads(cls.KEEP.read_text(encoding="utf-8"))

    def test_every_entry_has_a_rewrite_to_scan(self):
        self.assertGreaterEqual(len(self.rewrites), 50)
        self.assertIn("worked-example", self.rewrites)
        for name, body in self.rewrites.items():
            with self.subTest(entry=name):
                self.assertRegex(body, r"\w")

    def test_keep_entries_name_real_entries_and_give_reasons(self):
        for entry in self.keep:
            with self.subTest(entry=entry):
                self.assertIn(entry["entry"], self.rewrites)
                self.assertTrue(entry.get("reason"))

    def test_no_rewrite_blocks_or_shows_a_register_tell(self):
        for name, body in self.rewrites.items():
            with self.subTest(entry=name):
                keep = [{k: v for k, v in e.items() if k != "entry"}
                        for e in self.keep if e["entry"] == name]
                result = lint.scan(body, keep=keep)
                self.assertEqual([(f["rule"], f["text"]) for f in result["blocking"]], [])
                own = [(f["rule"], f["text"]) for f in result["findings"]
                       if f["ref"].startswith("O")]
                self.assertEqual(own, [])

    def test_a_planted_tell_in_a_rewrite_fails(self):
        result = lint.scan("Foreman will start the agent. It won't touch the log.")
        self.assertIn("touch-change", ids(result))


class CheckerMutant(unittest.TestCase):
    """Block item 7: a broken checker must fail this suite."""

    MUTANTS = [
        ("scans nothing", "for rule in rules:", "for rule in []:"),
        ("never blocks", "if finding[\"tier\"] == \"strong\"", "if False"),
        ("skips masking", "masked = mask(text, plain)", "masked = text"),
        ("hides code spans", "spans_visible = mask(text, plain, spans=False)",
         "spans_visible = masked"),
        ("code rules read raw text", "spans_visible = mask(text, plain, spans=False)",
         "spans_visible = text"),
        ("notes block like weak tells",
         'live = [f for f in findings if not f["quoted"] and f["tier"] != "note"]',
         'live = [f for f in findings if not f["quoted"]]'),
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
