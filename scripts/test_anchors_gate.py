"""Tests for anchors_gate.py, following the gate-integrity standard block.

Run from the repository root: python3 -m unittest discover -s scripts
ANCHORS_GATE_PATH swaps in another checker, which is how the mutant test works.

Every must-fail case starts from scripts/fixtures/gate/pass-minimal, applies
an optional setup and then one defect. The case mutant applies the setup
alone and requires exit 0, so each case fails for its own defect.
"""
from __future__ import annotations

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
REPO = HERE.parent
CHECKER = Path(os.environ.get("ANCHORS_GATE_PATH", HERE / "anchors_gate.py"))
PASS_MINIMAL = HERE / "fixtures" / "gate" / "pass-minimal"
PINNED = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1"


def load_checker():
    spec = importlib.util.spec_from_file_location("anchors_gate", CHECKER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["anchors_gate"] = module
    spec.loader.exec_module(module)
    return module


gate = load_checker()


def run_cli(root):
    return subprocess.run(
        [sys.executable, "-I", str(CHECKER), "--root", str(root)],
        capture_output=True, text=True)


def findings(result):
    """Parse 'CODE subject: message' lines into (code, subject) pairs."""
    pairs = []
    for line in result.stdout.splitlines():
        match = re.match(r"^([A-Z_]+) (\S+): ", line)
        if match:
            pairs.append((match.group(1), match.group(2)))
    return pairs


# Edits applied to a copy of pass-minimal.

def write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace(root, rel, old, new):
    path = root / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {rel}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def append(root, rel, text):
    path = root / rel
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


def edit_anchors(root, change):
    path = root / "anchors.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def anchor(data, anchor_id):
    return next(a for a in data["anchors"] if a["id"] == anchor_id)


VERSIONS_SECTION = (
    "\n## Versions\n\n| Tool or package | Version |\n|---|---|\n"
    "| gizmo | 1.0.0 |\n")
FORKY_NOTICE = "skills/forky/NOTICE.md"
INSTALLED = {
    "id": "installed/elsewhere", "skill": "elsewhere", "kind": "installed",
    "repo": "someone/skills", "path": "skills/elsewhere",
    "folderHash": "76a98a285cb0434f3d39e1a873823556330e398b"}


def add_installed(root):
    edit_anchors(root, lambda d: d["anchors"].append(dict(INSTALLED)))


def rename_installed_to_local(root):
    edit_anchors(root, lambda d: anchor(d, "installed/elsewhere").update(
        skill="plain"))


def empty_everything(root):
    for child in (root / "skills").iterdir():
        shutil.rmtree(child)
    edit_anchors(root, lambda d: d.update(anchors=[], declined=[]))


def fence_versions_table(root):
    replace(root, "skills/tooly/SKILL.md", "| Tool or package",
            "```\n| Tool or package")
    replace(root, "skills/tooly/SKILL.md", "(a remark) |\n",
            "(a remark) |\n```\n")


# name: (setup or None, defect, expected code, expected subject)
CASES = {
    "skill_without_entry": (
        None, lambda r: write(r, "skills/new/SKILL.md", "# New\n"),
        "UNREGISTERED", "new"),
    "none_on_skill_with_versions": (
        None, lambda r: append(r, "skills/plain/SKILL.md", VERSIONS_SECTION),
        "NONE_FORBIDDEN", "plain"),
    "none_on_skill_with_notice": (
        None, lambda r: shutil.copy(r / FORKY_NOTICE,
                                    r / "skills/plain/NOTICE.md"),
        "NONE_FORBIDDEN", "plain"),
    "none_on_skill_with_third_party_row": (
        None, lambda r: replace(
            r, "THIRD_PARTY.md", "\nProse after",
            "| plain | obra/superpowers `plain` @ `2ce8aa1` | MIT |\n"
            "\nProse after"),
        "NONE_FORBIDDEN", "plain"),
    "tool_check_missing": (
        None, lambda r: (r / "checks/x/run.sh").unlink(),
        "CHECK_MISSING", "tooly"),
    "tool_check_not_executable": (
        None, lambda r: (r / "checks/x/run.sh").chmod(0o644),
        "CHECK_MISSING", "tooly"),
    "versions_value_mismatch": (
        None, lambda r: replace(r, "skills/tooly/SKILL.md",
                                "| widget | 4.1.1", "| widget | 4.1.2"),
        "VERSIONS_MISMATCH", "tooly"),
    "versions_row_without_anchor": (
        None, lambda r: replace(r, "skills/tooly/SKILL.md",
                                "(a remark) |\n",
                                "(a remark) |\n| gadget | 1.0.0 |\n"),
        "VERSIONS_UNANCHORED", "tooly"),
    "versions_table_in_fence_does_not_satisfy": (
        None, fence_versions_table, "VERSIONS_MISMATCH", "tooly"),
    "notice_commit_mismatch": (
        None, lambda r: replace(r, FORKY_NOTICE, "`2ce8aa1`", "`2ce8aa2`"),
        "NOTICE_MISMATCH", "forky"),
    "notice_release_mismatch": (
        None, lambda r: replace(r, FORKY_NOTICE, "(v7.0.1)", "(v7.0.2)"),
        "NOTICE_MISMATCH", "forky"),
    "notice_upstream_name_mismatch": (
        None, lambda r: replace(r, FORKY_NOTICE, "`original`", "`renamed`"),
        "NOTICE_MISMATCH", "forky"),
    "notice_unparseable": (
        None, lambda r: replace(
            r, FORKY_NOTICE, "This skill is a modified version of `original` "
            "from", "This skill was adapted from"),
        "NOTICE_UNPARSEABLE", "forky"),
    "notice_without_entry": (
        None, lambda r: shutil.copy(r / FORKY_NOTICE,
                                    r / "skills/tooly/NOTICE.md"),
        "NOTICE_MISMATCH", "tooly"),
    "notice_missing_for_fork": (
        None, lambda r: (r / FORKY_NOTICE).unlink(),
        "NOTICE_MISMATCH", "forky"),
    "vendored_notice_version_mismatch": (
        None, lambda r: replace(r, "skills/vendy/NOTICE.md",
                                "version 1.2.3", "version 1.2.4"),
        "NOTICE_MISMATCH", "vendy"),
    "vendored_local_file_missing": (
        None, lambda r: (r / "skills/vendy/references/up-1.2.3.md").unlink(),
        "SCHEMA", "vendy"),
    "third_party_mismatch": (
        None, lambda r: replace(r, "THIRD_PARTY.md", "`2ce8aa1`", "`2ce8aa9`"),
        "THIRD_PARTY_MISMATCH", "forky"),
    "third_party_vendored_version_mismatch": (
        None, lambda r: replace(r, "THIRD_PARTY.md", "someone/upstream 1.2.3",
                                "someone/upstream 1.2.4"),
        "THIRD_PARTY_MISMATCH", "vendy"),
    "third_party_row_without_entry": (
        None, lambda r: replace(
            r, "THIRD_PARTY.md", "\nProse after",
            "| ghost | obra/superpowers `ghost` @ `2ce8aa1` | MIT |\n"
            "\nProse after"),
        "THIRD_PARTY_MISMATCH", "ghost"),
    "third_party_row_missing": (
        None, lambda r: replace(
            r, "THIRD_PARTY.md",
            "| forky | obra/superpowers `original` @ `2ce8aa1` (a remark) "
            "| MIT, (c) 2025 Someone |\n", ""),
        "THIRD_PARTY_MISMATCH", "forky"),
    "unknown_key": (
        None, lambda r: edit_anchors(
            r, lambda d: anchor(d, "tooly/widget").update(colour="red")),
        "SCHEMA", "tooly/widget"),
    "duplicate_id": (
        None, lambda r: edit_anchors(
            r, lambda d: d["anchors"].append(dict(anchor(d, "plain")))),
        "DUPLICATE_ID", "plain"),
    "short_commit_in_anchors": (
        None, lambda r: edit_anchors(
            r, lambda d: anchor(d, "forky").update(commit="2ce8aa1")),
        "SCHEMA", "forky"),
    "installed_named_like_local_skill": (
        add_installed, rename_installed_to_local,
        "SCHEMA", "installed/elsewhere"),
    "no_such_skill": (
        None, lambda r: edit_anchors(r, lambda d: d["anchors"].append(
            {"id": "ghost", "skill": "ghost", "kind": "none",
             "reason": "Gone."})),
        "NO_SUCH_SKILL", "ghost"),
    "declined_names_unknown_anchor": (
        None, lambda r: edit_anchors(r, lambda d: d["declined"].append(
            {"anchor": "nobody", "to": "1.0.0", "reason": "No."})),
        "SCHEMA", "declined"),
    "directory_without_skill_md": (
        None, lambda r: write(r, "skills/stray/README.md", "# Stray\n"),
        "NOT_A_SKILL_DIR", "stray"),
    "stray_file_under_skills": (
        None, lambda r: write(r, "skills/notes.txt", "notes\n"),
        "NOT_A_SKILL_DIR", "notes.txt"),
    "unpinned_action": (
        None, lambda r: replace(r, ".github/workflows/ci.yml", PINNED,
                                "actions/checkout@v5"),
        "UNPINNED_ACTION", ".github/workflows/ci.yml"),
    "unpinned_action_quoted": (
        None, lambda r: replace(r, ".github/workflows/ci.yml", PINNED,
                                "'actions/checkout@main'"),
        "UNPINNED_ACTION", ".github/workflows/ci.yml"),
    "unparseable_anchors": (
        None, lambda r: write(r, "anchors.json", "{not json"),
        "SCHEMA", "anchors.json"),
    "empty_skills_dir": (
        None, empty_everything, "SCHEMA", "skills"),
}


class Fixtures(unittest.TestCase):
    """Block items 1, 2, 3 and 8: named failures, each with its case mutant."""

    def setUp(self):
        self.room = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.room)

    def fresh(self, name):
        root = self.room / name
        shutil.copytree(PASS_MINIMAL, root)
        return root

    def test_pass_minimal(self):
        result = run_cli(self.fresh("pass"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("anchors gate: 4 skills, 4 anchors, OK", result.stdout)

    def test_every_case_fails_for_its_own_defect(self):
        for name, (setup, defect, code, subject) in CASES.items():
            with self.subTest(case=name):
                root = self.fresh(name)
                if setup:
                    setup(root)
                control = run_cli(root)
                self.assertEqual(
                    control.returncode, 0,
                    f"case mutant {name} should pass:\n{control.stdout}"
                    f"{control.stderr}")
                defect(root)
                result = run_cli(root)
                self.assertEqual(result.returncode, 1,
                                 result.stdout + result.stderr)
                self.assertIn((code, subject), findings(result),
                              result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_empty_skills_message(self):
        root = self.fresh("empty")
        empty_everything(root)
        result = run_cli(root)
        self.assertIn("SCHEMA skills: no skills found", result.stdout)


class Headings(unittest.TestCase):
    """Block items 5 and 6: spelling probes, near misses, fences."""

    SPELLINGS = ["## Versions", "##  Versions ", "## Versions ##",
                 "   ## Versions", "## Versions #####"]
    NEAR_MISSES = ["## Versioning the Block", "### Versions", "#Versions",
                   "# Versions", "## Versions and history",
                   "    ## Versions", "<!-- ## Versions -->"]

    def test_spelling_probes_count_once(self):
        for spelling in self.SPELLINGS:
            with self.subTest(spelling=spelling):
                text = f"# T\n\n{spelling}\n\nText.\n"
                self.assertEqual(gate.versions_heading_count(text), 1)

    def test_near_misses_count_zero(self):
        for near in self.NEAR_MISSES:
            with self.subTest(near=near):
                text = f"# T\n\n{near}\n\nText.\n"
                self.assertEqual(gate.versions_heading_count(text), 0)

    def test_fenced_headings_count_zero(self):
        for fence in ["```", "~~~", "````", "```markdown"]:
            with self.subTest(fence=fence):
                close = fence.rstrip("markdown") or fence
                text = f"# T\n\n{fence}\n## Versions\n{close}\n"
                self.assertEqual(gate.versions_heading_count(text), 0)

    def test_fence_closed_only_by_its_own_kind(self):
        text = "```\n~~~\n## Versions\n```\n## Versions\n"
        self.assertEqual(gate.versions_heading_count(text), 1)

    def test_unterminated_fence_hides_the_rest(self):
        text = "```\n## Versions\n"
        self.assertEqual(gate.versions_heading_count(text), 0)

    def test_spellings_trip_the_gate(self):
        for spelling in self.SPELLINGS:
            with self.subTest(spelling=spelling), \
                    tempfile.TemporaryDirectory() as room:
                root = Path(room) / "r"
                shutil.copytree(PASS_MINIMAL, root)
                append(root, "skills/plain/SKILL.md",
                       f"\n{spelling}\n\nText.\n")
                result = run_cli(root)
                self.assertIn(("NONE_FORBIDDEN", "plain"), findings(result))

    def test_versions_in_code_fence_ignored(self):
        self.assert_plain_suffix_passes(
            "\n```markdown\n## Versions\n\n| a | 1 |\n```\n")

    def test_near_miss_heading_ignored(self):
        self.assert_plain_suffix_passes("\n## Versioning the Block\n\nText.\n")

    def assert_plain_suffix_passes(self, suffix):
        with tempfile.TemporaryDirectory() as room:
            root = Path(room) / "r"
            shutil.copytree(PASS_MINIMAL, root)
            append(root, "skills/plain/SKILL.md", suffix)
            result = run_cli(root)
            self.assertEqual(result.returncode, 0,
                             result.stdout + result.stderr)


class Parsers(unittest.TestCase):

    def test_versions_table_rows(self):
        text = (PASS_MINIMAL / "skills/tooly/SKILL.md").read_text()
        self.assertEqual(gate.parse_versions_table(text),
                         {"widget": "4.1.1 (a remark)"})

    def test_no_versions_section_is_none(self):
        text = (PASS_MINIMAL / "skills/plain/SKILL.md").read_text()
        self.assertIsNone(gate.parse_versions_table(text))

    def test_versions_table_stops_at_next_section(self):
        text = ("## Versions\n\n| T | V |\n|---|---|\n| a | 1 |\n\n"
                "## Next\n\n| T | V |\n|---|---|\n| b | 2 |\n")
        self.assertEqual(gate.parse_versions_table(text), {"a": "1"})

    def test_fork_notice_facts(self):
        text = (PASS_MINIMAL / "skills/forky/NOTICE.md").read_text()
        facts = gate.parse_notice(text, "fork")
        self.assertEqual(
            (facts.name, facts.repo, facts.commit, facts.release),
            ("original", "obra/superpowers", "2ce8aa1", "v7.0.1"))

    def test_vendored_notice_facts(self):
        text = (PASS_MINIMAL / "skills/vendy/NOTICE.md").read_text()
        facts = gate.parse_notice(text, "vendored")
        self.assertEqual(
            (facts.local, facts.name, facts.repo, facts.version),
            ("references/up-1.2.3.md", "SKILL.md", "someone/upstream",
             "1.2.3"))

    def test_link_text_and_url_must_agree(self):
        text = (PASS_MINIMAL / "skills/forky/NOTICE.md").read_text().replace(
            "https://github.com/obra/superpowers",
            "https://github.com/evil/superpowers")
        with self.assertRaises(gate.GateError) as caught:
            gate.parse_notice(text, "fork")
        self.assertEqual(caught.exception.code, "NOTICE_UNPARSEABLE")

    def test_third_party_rows(self):
        text = (PASS_MINIMAL / "THIRD_PARTY.md").read_text()
        rows = gate.parse_third_party(text)
        self.assertEqual(sorted(rows), ["forky", "vendy"])
        self.assertEqual(rows["forky"].commit, "2ce8aa1")
        self.assertEqual(rows["forky"].name, "original")
        self.assertEqual(rows["vendy"].version, "1.2.3")

    def test_workflow_pins(self):
        self.assertEqual(gate.check_workflow_pins(PASS_MINIMAL), [])


class LiveRepository(unittest.TestCase):
    """Block item 4: scan floor with named members, on the real repository."""

    def test_live_repo_scan_floor(self):
        result = run_cli(REPO)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        match = re.search(r"anchors gate: (\d+) skills, (\d+) anchors, OK",
                          result.stdout)
        self.assertIsNotNone(match, result.stdout)
        self.assertGreaterEqual(int(match.group(1)), 31)
        anchors = gate.load_anchors(REPO / "anchors.json")
        local = [a for a in anchors.anchors if a["kind"] != "installed"]
        self.assertGreaterEqual(len(local), 31)
        kinds = {a["id"]: a["kind"] for a in anchors.anchors}
        self.assertEqual(kinds["test-first"], "fork")
        self.assertEqual(kinds["humanized-prose-review"], "vendored")
        table = gate.parse_versions_table(
            (REPO / "skills/purescript-gotchas/SKILL.md").read_text())
        self.assertEqual(len(table), 9)
        self.assertIn("registry package set", table)


class CheckerMutant(unittest.TestCase):
    """Block item 7: a broken checker must fail this suite."""

    MUTANTS = [
        ("allows none everywhere", "if forbidden_reasons:", "if False:"),
        ("ignores fences", "fence = opening_fence(line)", "fence = None"),
        ("skips stray entries", "if not (entry / \"SKILL.md\").is_file():",
         "if False:"),
        ("ignores executable bit", "os.access(run, os.X_OK)", "True"),
        ("ignores release", "facts.release != entry[\"release\"]", "False"),
    ]

    @unittest.skipIf("ANCHORS_GATE_PATH" in os.environ,
                     "already running a mutant")
    def test_each_mutant_fails_the_suite(self):
        source = (HERE / "anchors_gate.py").read_text(encoding="utf-8")
        for name, old, new in self.MUTANTS:
            with self.subTest(mutant=name), \
                    tempfile.TemporaryDirectory() as room:
                self.assertIn(old, source)
                broken = Path(room) / "anchors_gate.py"
                broken.write_text(source.replace(old, new), encoding="utf-8")
                done = subprocess.run(
                    [sys.executable, "-m", "unittest", "test_anchors_gate"],
                    cwd=HERE, capture_output=True, text=True,
                    env={**os.environ, "ANCHORS_GATE_PATH": str(broken)})
                self.assertNotEqual(done.returncode, 0, name)


if __name__ == "__main__":
    unittest.main()
