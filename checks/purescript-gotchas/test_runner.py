"""Tests for runner.py, the purescript-gotchas claim checker.

They need no compiler: compiler output is recorded by hand in fixtures/
in the purs --json-errors format. RUNNER_PATH, when set, names the
runner module to test instead of ./runner.py; test_checker_mutant uses it
to show that a broken checker fails this suite.
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
REPO = HERE.parent.parent
FIXTURES = HERE / "fixtures"
RUNNER_PATH = Path(os.environ.get("RUNNER_PATH", HERE / "runner.py"))


def load_runner():
    spec = importlib.util.spec_from_file_location("runner_under_test",
                                                  RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["runner_under_test"] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def outcome(name: str):
    return runner.classify(runner.parse_compiler_output(fixture(name)))


def case(**overrides) -> dict:
    base = {
        "name": "x",
        "claim": "an individually imported name cannot be re-exported",
        "section": "Modules and exports",
        "errors": [{"code": "UnknownExport", "module": "X.Facade",
                    "line": 1,
                    "includes": ["Cannot export unknown type Thing"]}],
        "warnings": [],
    }
    base.update(overrides)
    return base


SKILL_TABLE = runner.versions_table(REPO)
LOCK_OK = {
    "workspace": {"package_set": {"address": {"registry": "82.1.1"}}},
    "packages": {
        "prelude": {"type": "registry", "version": "6.0.3"},
        "quickcheck": {"type": "registry", "version": "8.0.2"},
        "quickcheck-laws": {"type": "registry", "version": "7.0.0"},
        "js-bigints": {"type": "registry", "version": "2.2.1"},
        "bigints": {"type": "registry", "version": "7.0.1"},
    },
}
TOOLS_OK = {"purs": "0.15.17", "spago": "1.0.5"}


class CheckCase(unittest.TestCase):
    def test_expected_error_matches(self):
        self.assertEqual(runner.check_case(case(), outcome(
            "unknown-export.json")), [])

    def test_wrong_code_fails(self):
        wanted = case(errors=[{"code": "UnknownName", "module": "X.Facade",
                               "line": 1}])
        problems = runner.check_case(wanted, outcome("unknown-export.json"))
        self.assertTrue(problems)
        text = "\n".join(problems)
        self.assertIn("case x:", text)
        self.assertIn("UnknownName", text)
        self.assertIn("UnknownExport", text)

    def test_wrong_line_fails(self):
        wanted = case(errors=[{"code": "UnknownExport",
                               "module": "X.Facade", "line": 2}])
        self.assertTrue(runner.check_case(wanted,
                                          outcome("unknown-export.json")))

    def test_wrong_module_fails(self):
        wanted = case(errors=[{"code": "UnknownExport", "module": "X.Other",
                               "line": 1}])
        self.assertTrue(runner.check_case(wanted,
                                          outcome("unknown-export.json")))

    def test_unexpected_success_fails(self):
        problems = runner.check_case(case(), outcome("clean.json"))
        self.assertTrue(problems)
        self.assertIn("UnknownExport", "\n".join(problems))

    def test_unexpected_error_fails(self):
        problems = runner.check_case(case(errors=[]),
                                     outcome("unknown-export.json"))
        self.assertTrue(problems)
        self.assertIn("unexpected error UnknownExport", "\n".join(problems))

    def test_warning_expected_but_absent_fails(self):
        wanted = case(errors=[], warnings=[{"code": "HiddenConstructors",
                                            "module": "X.Percent"}])
        self.assertTrue(runner.check_case(wanted, outcome("clean.json")))
        self.assertEqual(runner.check_case(
            wanted, outcome("hidden-constructors.json")), [])

    def test_unexpected_warning_fails(self):
        problems = runner.check_case(case(errors=[]),
                                     outcome("hidden-constructors.json"))
        self.assertIn("unexpected warning HiddenConstructors",
                      "\n".join(problems))

    def test_wording_changed_is_reported_separately(self):
        wanted = case(errors=[{"code": "UnknownExport", "module": "X.Facade",
                               "line": 1,
                               "includes": ["Cannot re-export Thing"]}])
        problems = runner.check_case(wanted, outcome("unknown-export.json"))
        self.assertEqual(len(problems), 1)
        self.assertIn("wording changed", problems[0])
        self.assertIn("Cannot re-export Thing", problems[0])

    def test_includes_ignore_line_breaks(self):
        wanted = case(errors=[], warnings=[{
            "code": "HiddenConstructors", "module": "X.Percent",
            "includes": ["derived for a type whose constructors"]}])
        self.assertEqual(runner.check_case(
            wanted, outcome("hidden-constructors.json")), [])

    def test_hole_count_is_exact(self):
        hole = {"code": "HoleInferredType", "module": "X.Main"}
        self.assertEqual(runner.check_case(case(errors=[hole, hole]),
                                           outcome("two-holes.json")), [])
        self.assertTrue(runner.check_case(case(errors=[hole]),
                                          outcome("two-holes.json")))
        self.assertTrue(runner.check_case(case(errors=[hole, hole, hole]),
                                          outcome("two-holes.json")))

    def test_unparseable_compiler_output_fails(self):
        with self.assertRaises(runner.CheckError) as raised:
            runner.parse_compiler_output(fixture("not-json.txt"))
        self.assertIn("not JSON", str(raised.exception))

    def test_json_without_errors_key_fails(self):
        with self.assertRaises(runner.CheckError):
            runner.classify(runner.parse_compiler_output('{"warnings": []}'))

    def test_module_taken_from_file_when_compiler_omits_it(self):
        wanted = case(errors=[{"code": "ErrorParsingModule",
                               "module": "X.Parse", "line": 3,
                               "includes": ["Unexpected token ','"]}])
        got = runner.fill_modules(outcome("parse-error.json"), HERE)
        self.assertEqual(runner.check_case(wanted, got), [])
        self.assertTrue(runner.check_case(wanted,
                                          outcome("parse-error.json")))

    def test_status(self):
        self.assertEqual(outcome("clean.json").status, "ok")
        self.assertEqual(outcome("unknown-export.json").status, "error")


class Manifest(unittest.TestCase):
    def make_tree(self, names, dirs):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(root)]))
        (root / "cases").mkdir()
        for name in dirs:
            (root / "cases" / name).mkdir()
            (root / "cases" / name / "Main.purs").write_text("module M where")
        manifest = {"version": 1, "expectedCases": len(names),
                    "cases": [case(name=n) for n in names]}
        (root / "cases.json").write_text(json.dumps(manifest))
        return root

    def test_manifest_inventory_both_ways(self):
        root = self.make_tree(["a"], ["a", "b"])
        with self.assertRaises(runner.CheckError) as raised:
            runner.load_cases(root / "cases.json")
        self.assertIn("b", str(raised.exception))
        root = self.make_tree(["a", "c"], ["a"])
        with self.assertRaises(runner.CheckError) as raised:
            runner.load_cases(root / "cases.json")
        self.assertIn("c", str(raised.exception))

    def test_matching_tree_loads(self):
        root = self.make_tree(["a", "b"], ["a", "b"])
        self.assertEqual([c["name"] for c in runner.load_cases(
            root / "cases.json")], ["a", "b"])

    def test_empty_manifest_fails(self):
        root = self.make_tree([], [])
        with self.assertRaises(runner.CheckError):
            runner.load_cases(root / "cases.json")

    def test_unknown_key_fails(self):
        root = self.make_tree(["a"], ["a"])
        data = json.loads((root / "cases.json").read_text())
        data["cases"][0]["expect"] = "ok"
        (root / "cases.json").write_text(json.dumps(data))
        with self.assertRaises(runner.CheckError) as raised:
            runner.load_cases(root / "cases.json")
        self.assertIn("expect", str(raised.exception))

    def test_duplicate_name_fails(self):
        root = self.make_tree(["a", "a"], ["a"])
        with self.assertRaises(runner.CheckError):
            runner.load_cases(root / "cases.json")

    def test_deleting_a_case_and_its_directory_fails(self):
        """The case count is pinned in cases.json, so removing a case
        with its directory (the inventory still agrees) fails."""
        root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(root)]))
        shutil.copytree(HERE / "cases", root / "cases")
        data = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        gone = data["cases"].pop()
        shutil.rmtree(root / "cases" / gone["name"])
        (root / "cases.json").write_text(json.dumps(data))
        with self.assertRaises(runner.CheckError) as raised:
            runner.load_cases(root / "cases.json")
        self.assertIn("expectedCases", str(raised.exception))

    def test_expected_count_must_be_stated(self):
        root = self.make_tree(["a"], ["a"])
        data = json.loads((root / "cases.json").read_text())
        del data["expectedCases"]
        (root / "cases.json").write_text(json.dumps(data))
        with self.assertRaises(runner.CheckError):
            runner.load_cases(root / "cases.json")

    def test_scan_floor(self):
        cases = runner.load_cases(HERE / "cases.json")
        names = [c["name"] for c in cases]
        self.assertGreaterEqual(len(cases), 32)
        self.assertIn("cycle-point-free", names)
        self.assertIn("bigints-npm", names)

    def test_every_error_case_names_its_module(self):
        for item in runner.load_cases(HERE / "cases.json"):
            for want in item["errors"] + item["warnings"]:
                self.assertIn("module", want, item["name"])


class Versions(unittest.TestCase):
    def test_versions_match_passes(self):
        self.assertEqual(runner.check_versions(SKILL_TABLE, LOCK_OK,
                                               TOOLS_OK), [])

    def test_versions_mismatch_fails(self):
        lock = json.loads(json.dumps(LOCK_OK))
        lock["packages"]["prelude"]["version"] = "6.0.1"
        problems = runner.check_versions(SKILL_TABLE, lock, TOOLS_OK)
        self.assertEqual(len(problems), 1)
        self.assertIn("prelude", problems[0])
        self.assertIn("6.0.1", problems[0])

    def test_package_missing_from_lock_fails(self):
        lock = json.loads(json.dumps(LOCK_OK))
        del lock["packages"]["bigints"]
        self.assertTrue(runner.check_versions(SKILL_TABLE, lock, TOOLS_OK))

    def test_tool_mismatch_fails(self):
        for tool, wrong in (("purs", "0.15.15"), ("spago", "1.0.3")):
            tools = dict(TOOLS_OK, **{tool: wrong})
            problems = runner.check_versions(SKILL_TABLE, LOCK_OK, tools)
            self.assertEqual(len(problems), 1, tool)
            self.assertIn(tool, problems[0])

    def test_package_set_mismatch_fails(self):
        lock = json.loads(json.dumps(LOCK_OK))
        lock["workspace"]["package_set"]["address"]["registry"] = "80.0.0"
        self.assertTrue(runner.check_versions(SKILL_TABLE, lock, TOOLS_OK))

    def test_anchor_mismatch_fails(self):
        anchors = [{"kind": "tool", "check": "checks/purescript-gotchas",
                    "row": "prelude", "version": "6.0.2"}]
        problems = runner.check_versions(SKILL_TABLE, LOCK_OK, TOOLS_OK,
                                         anchors=anchors)
        self.assertTrue(problems)
        self.assertIn("anchors.json", "\n".join(problems))

    def test_real_anchors_agree(self):
        anchors = runner.load_anchor_entries(REPO)
        self.assertGreaterEqual(len(anchors), 8)
        self.assertEqual(runner.check_versions(SKILL_TABLE, LOCK_OK,
                                               TOOLS_OK, anchors=anchors), [])

    def test_table_row_missing_fails(self):
        table = {k: v for k, v in SKILL_TABLE.items() if k != "quickcheck"}
        self.assertTrue(runner.check_versions(table, LOCK_OK, TOOLS_OK))

    def test_committed_lock_agrees(self):
        lock = json.loads((HERE / "spago.lock").read_text(encoding="utf-8"))
        self.assertEqual(runner.check_versions(SKILL_TABLE, lock, TOOLS_OK),
                         [])


class RunAssertions(unittest.TestCase):
    def test_fraction_bands(self):
        good = {"positive/1": 0.25, "positive/1000": 0.26,
                "signed/1": 0.07, "signed/1000": 0.33}
        spec = {"assert": "fraction-bands", "bands": [
            {"keys": ["positive/1", "positive/1000"], "low": 0.22,
             "high": 0.28},
            {"keys": ["signed/1"], "low": 0.03, "high": 0.10},
            {"keys": ["signed/1000"], "low": 0.28, "high": 0.38}]}
        self.assertEqual(runner.check_run_output(spec, good), [])
        for key, value in (("positive/1000", 0.19), ("signed/1", 0.25),
                           ("signed/1000", 0.07)):
            problems = runner.check_run_output(spec, dict(good, **{key: value}))
            self.assertEqual(len(problems), 1, key)
            self.assertIn(key, problems[0])
        missing = {k: v for k, v in good.items() if k != "signed/1"}
        self.assertEqual(len(runner.check_run_output(spec, missing)), 1)

    def test_fraction_bands_empty_fails(self):
        with self.assertRaises(runner.CheckError):
            runner.check_run_output({"assert": "fraction-bands",
                                     "bands": []}, {})
        with self.assertRaises(runner.CheckError):
            runner.check_run_output({"assert": "fraction-bands", "bands": [
                {"keys": [], "low": 0, "high": 1}]}, {})

    def test_unit_interval_sample(self):
        spec = {"assert": "unit-interval-sample", "count": 3}
        self.assertEqual(runner.check_run_output(
            spec, {"count": 3, "min": 0.001, "max": 0.995, "outside": 0}),
            [])
        self.assertTrue(runner.check_run_output(
            spec, {"count": 3, "min": -0.5, "max": 0.995, "outside": 1}))
        self.assertTrue(runner.check_run_output(
            spec, {"count": 3, "min": 0.2, "max": 0.995, "outside": 0}))
        self.assertTrue(runner.check_run_output(
            spec, {"count": 2, "min": 0.001, "max": 0.995, "outside": 0}))

    def test_unknown_assertion_fails(self):
        with self.assertRaises(runner.CheckError):
            runner.check_run_output({"assert": "vibes"}, {})


class WorkflowPaths(unittest.TestCase):
    """The workflow runs when anything the runner reads changes. A
    line-level reading: each repository module the runner imports from
    scripts/ must be listed under both push and pull_request paths.
    Blind spot: files the runner reads by other means (SKILL.md,
    anchors.json) are listed by hand."""

    WORKFLOW = REPO / ".github" / "workflows" / "check-purescript-gotchas.yml"

    def path_lists(self):
        lists, current = {}, None
        for line in self.WORKFLOW.read_text(encoding="utf-8").split("\n"):
            if line in ("  push:", "  pull_request:"):
                current = lists.setdefault(line.strip(" :"), [])
            elif current is not None and line.startswith("      - "):
                current.append(line.strip()[2:].strip('"'))
            elif current is not None and not line.startswith("    "):
                current = None
        return lists

    def test_imported_scripts_trigger_the_workflow(self):
        source = (HERE / "runner.py").read_text(encoding="utf-8")
        modules = re.findall(r"^\s*from (\w+) import", source, re.M)
        local = [f"scripts/{m}.py" for m in modules
                 if (REPO / "scripts" / f"{m}.py").exists()]
        self.assertIn("scripts/anchors_gate.py", local)
        lists = self.path_lists()
        self.assertEqual(set(lists), {"push", "pull_request"})
        for event, paths in lists.items():
            for path in local:
                self.assertIn(path, paths, event)


@unittest.skipIf(os.environ.get("SKIP_MUTANT"), "inside a mutant run")
class CheckerMutant(unittest.TestCase):
    def test_checker_mutant(self):
        source = (HERE / "runner.py").read_text(encoding="utf-8")
        target = 'got.code == want["code"]'
        self.assertEqual(source.count(target), 1)
        work = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(work)]))
        mutant = work / "runner.py"
        mutant.write_text(source.replace(target, "True"), encoding="utf-8")
        env = dict(os.environ, RUNNER_PATH=str(mutant), SKIP_MUTANT="1")
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "test_runner"], cwd=HERE,
            env=env, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0, result.stderr[-2000:])
        self.assertIn("test_wrong_code_fails", result.stderr)


if __name__ == "__main__":
    unittest.main()
