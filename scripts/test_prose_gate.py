"""Tests for prose_gate.py.

Run from the repository root: python3 -m unittest discover -s scripts
PROSE_GATE_PATH swaps in another checker, which is how a mutant test works.

Each case builds a throwaway git repository from a fixture under
scripts/fixtures/prose/, so the gate runs against git ls-files exactly as in CI.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = Path(os.environ.get("PROSE_GATE_PATH", HERE / "prose_gate.py"))
FIXTURES = HERE / "fixtures" / "prose"


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


class ProseGateTest(unittest.TestCase):
    def repo(self, fixture=None):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        git(tmp, "init", "-q")
        if fixture:
            shutil.copytree(FIXTURES / fixture, tmp, dirs_exist_ok=True)
        git(tmp, "add", "-A")
        return tmp

    def run_gate(self, root, *extra):
        return subprocess.run([sys.executable, str(CHECKER), "--root", str(root), *extra],
                              capture_output=True, text=True)

    def test_clean_control_passes(self):
        run = self.run_gate(self.repo("clean"))
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertIn("1 files, 0 failing, 0 blocking, OK", run.stdout)

    def test_blocking_fixture_fails(self):
        run = self.run_gate(self.repo("fail"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("BLOCKING README.md", run.stdout)

    def test_report_mode_exits_zero_but_still_lists(self):
        run = self.run_gate(self.repo("fail"), "--report")
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertIn("BLOCKING README.md", run.stdout)
        self.assertIn("report only", run.stdout)

    def test_empty_file_list_fails_even_in_report_mode(self):
        for extra in ((), ("--report",)):
            run = self.run_gate(self.repo(), *extra)
            self.assertEqual(run.returncode, 1, run.stdout)
            self.assertIn("no files matched", run.stdout)

    def test_untracked_file_is_not_checked(self):
        root = self.repo("clean")
        git(root, "rm", "-q", "--cached", "README.md")
        run = self.run_gate(root)
        self.assertEqual(run.returncode, 1, run.stdout)

    def test_keep_file_beside_the_file_is_applied(self):
        root = self.repo("fail")
        (root / "prose.keep.json").write_text(
            '[{"rule": "bold-label", "all": true, "reason": "test: quoted example"}]')
        git(root, "add", "-A")
        run = self.run_gate(root)
        self.assertEqual(run.returncode, 0, run.stdout)

    def test_unparseable_linter_output_fails(self):
        root = self.repo("clean")
        broken = root / "lint.py"
        broken.write_text("print('nothing useful')\n")
        run = self.run_gate(root, "--lint", str(broken))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("UNPARSEABLE", run.stdout)

    def test_matches_only_published_prose_paths(self):
        root = self.repo("fail")
        (root / "docs").mkdir()
        shutil.copy(FIXTURES / "fail" / "README.md", root / "docs" / "README.md")
        (root / "skills" / "x" / "deep").mkdir(parents=True)
        shutil.copy(FIXTURES / "clean" / "README.md", root / "skills" / "x" / "SKILL.md")
        shutil.copy(FIXTURES / "fail" / "README.md", root / "skills" / "x" / "deep" / "SKILL.md")
        git(root, "add", "-A")
        run = self.run_gate(root, "--report")
        self.assertIn("2 files", run.stdout)
        self.assertNotIn("docs/README.md", run.stdout)
        self.assertNotIn("deep", run.stdout)


if __name__ == "__main__":
    unittest.main()
