"""Builds throwaway upstream git repositories for test_detect_drift.py.

Each Upstream is a real git repository in a temporary directory, with a
fixed author, committer and clock so that commit IDs repeat from run to
run. Tests hand its path to FixtureSources in place of a network clone.
Nothing here touches the network or the user's git configuration.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Upstream",
    "GIT_AUTHOR_EMAIL": "upstream@example.invalid",
    "GIT_COMMITTER_NAME": "Upstream",
    "GIT_COMMITTER_EMAIL": "upstream@example.invalid",
}


class Upstream:
    def __init__(self, path: Path):
        self.path = path
        self.clock = 1700000000
        path.mkdir(parents=True)
        self.git("init", "-q", "-b", "main")

    def git(self, *args: str) -> str:
        env = {**os.environ, **ENV}
        when = f"{self.clock} +0000"
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = when
        done = subprocess.run(["git", "-C", str(self.path), *args], env=env,
                              capture_output=True, text=True, check=True)
        return done.stdout.strip()

    def commit(self, message: str, files: dict) -> str:
        """Write (text) or delete (None) each file, commit, return the SHA."""
        for rel, text in files.items():
            target = self.path / rel
            if text is None:
                self.git("rm", "-q", rel)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
            self.git("add", rel)
        self.clock += 60
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")

    def tree(self, rev: str, path: str) -> str:
        return self.git("rev-parse", f"{rev}:{path}")

    def branch(self, name: str, rev: str) -> None:
        self.git("branch", "-f", name, rev)

    def reset_hard(self, rev: str) -> None:
        """Rewrite main to rev, as a force-push would."""
        self.git("reset", "-q", "--hard", rev)
