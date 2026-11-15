#!/usr/bin/env python3
"""Prose gate: runs tell_lint on the repository's published prose.

The files are listed with git ls-files: README.md, every skills/*/SKILL.md
and every checks/*/README.md. Each file is checked with its keep file when
one exists, looked up in this order beside the file: prose.keep.json, then
(for skills) scripts/keep/SKILL.keep.json. The gate decides from the
linter's own summary line, "N findings, M blocking, ...".

Usage: python3 scripts/prose_gate.py [--root DIR] [--report] [--lint PATH]
Exit 0 prints "prose gate: N files, 0 blocking, OK". Exit 1 prints one
line per blocking file, and also when the file list is empty or the
linter's output cannot be parsed. --report prints the totals and always
exits 0, except when the file list is empty.

Blind spot: the linter checks a catalog of phrases and shapes. A green
run shows those are absent, not that the prose reads well.
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_LINT = HERE.parent / "skills" / "humanized-prose-review" / "scripts" / "tell_lint.py"
PATTERNS = ("README.md", "skills/*/SKILL.md", "checks/*/README.md")
SUMMARY = re.compile(r"^(\d+) findings?, (\d+) blocking", re.M)


def list_files(root):
    out = subprocess.run(["git", "-C", str(root), "ls-files"], capture_output=True,
                         text=True, check=True).stdout.splitlines()
    return sorted(f for f in out
                  if any(fnmatch.fnmatchcase(f, p) and f.count("/") == p.count("/")
                         for p in PATTERNS))


def keep_for(root, rel):
    base = (root / rel).parent
    for candidate in (base / "prose.keep.json", base / "scripts" / "keep" / "SKILL.keep.json"):
        if candidate.is_file():
            return candidate
    return None


def check(root, rel, lint):
    cmd = [sys.executable, str(lint), "--report"]
    keep = keep_for(root, rel)
    if keep:
        cmd += ["--keep", str(keep)]
    cmd.append(str(root / rel))
    run = subprocess.run(cmd, capture_output=True, text=True)
    match = SUMMARY.search(run.stdout)
    if not match:
        return None, (run.stdout + run.stderr).strip()
    return int(match.group(2)), run.stdout


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--root", default=str(HERE.parent))
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--lint", default=str(DEFAULT_LINT))
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    files = list_files(root)
    if not files:
        print("prose gate: no files matched README.md, skills/*/SKILL.md, checks/*/README.md")
        return 1
    total = 0
    failed = 0
    for rel in files:
        blocking, text = check(root, rel, Path(args.lint))
        if blocking is None:
            print("UNPARSEABLE %s: %s" % (rel, text.splitlines()[-1] if text else "no output"))
            failed += 1
        elif blocking:
            print("BLOCKING %s: %d" % (rel, blocking))
            total += blocking
            failed += 1
    if failed and not args.report:
        print("prose gate: %d of %d files fail, %d blocking findings" % (failed, len(files), total))
        return 1
    status = "OK" if not failed else "report only"
    print("prose gate: %d files, %d failing, %d blocking, %s" % (len(files), failed, total, status))
    return 0


if __name__ == "__main__":
    sys.exit(main())
