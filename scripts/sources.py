"""Where drift detection gets upstream facts: the network or fixtures.

Sources is the interface detect_drift.py consumes. NetworkSources reads
the real registries and clones with git; FixtureSources reads recorded
or synthetic documents from a directory and hands out local git
repositories. Both run every response through the same parse_* functions,
so the tests exercise the parsing the scheduled run uses.

Any failure to reach or read a source raises SourceError. Detection does
not catch it: a run that cannot see an upstream must fail, not report
"no drift".

Endpoints (confirmed 2026-11-14 against the live services):
- npm: GET https://registry.npmjs.org/<package> with the abbreviated
  "application/vnd.npm.install-v1+json" document; versions are the keys
  of "versions".
- GitHub releases: GET /repos/<owner>/<repo>/releases?per_page=100,
  following Link rel="next".
- Package sets: the purescript/registry repository keeps one file per
  set under package-sets/ (its README). The listing uses the git trees
  API, GET /repos/purescript/registry/git/trees/main:package-sets,
  because the contents API stops at 1,000 entries (526 sets today). A
  truncated listing is an error.
- PureScript packages: metadata/<package>.json in purescript/registry,
  read from raw.githubusercontent.com; versions are the keys of
  "published" ("unpublished" ones do not count).
- Clones: git clone --filter=blob:none --bare (blob-less, not shallow,
  so every anchor in history is present; plan D11).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import NamedTuple, Optional

try:
    from typing import Protocol
except ImportError:  # pragma: no cover - Python < 3.8
    Protocol = object

USER_AGENT = "skills-drift-check"
TIMEOUT_SECONDS = 60


class SourceError(Exception):
    """An upstream could not be reached or its response not understood."""


class Release(NamedTuple):
    tag: str
    prerelease: bool
    draft: bool
    url: Optional[str]  # None when the release has no html_url


class Sources(Protocol):
    def clone(self, repo: str) -> Path: ...
    def npm_versions(self, package: str) -> list: ...
    def github_releases(self, repo: str) -> list: ...
    def package_sets(self) -> list: ...
    def purescript_package_versions(self, package: str) -> list: ...


# Which Sources method answers each tool ecosystem in anchors.json.
ECOSYSTEM_READERS = {
    "npm": "npm_versions",
    "github-release": "github_releases",
    "purescript-package-set": "package_sets",
    "purescript-package": "purescript_package_versions",
}


# ----------------------------------------------------------------- parsers

def _require(condition: bool, what: str) -> None:
    if not condition:
        raise SourceError(f"unexpected response shape: {what}")


def parse_npm(document) -> list:
    _require(isinstance(document, dict) and
             isinstance(document.get("versions"), dict), "npm versions")
    return list(document["versions"])


def parse_releases(document) -> list:
    _require(isinstance(document, list), "releases list")
    releases = []
    for entry in document:
        _require(isinstance(entry, dict) and
                 isinstance(entry.get("tag_name"), str), "release entry")
        releases.append(Release(entry["tag_name"], bool(entry["prerelease"]),
                                bool(entry["draft"]),
                                entry.get("html_url") or None))
    return releases


def parse_package_sets(document) -> list:
    _require(isinstance(document, dict) and
             isinstance(document.get("tree"), list), "git tree")
    if document.get("truncated"):
        raise SourceError("package-sets listing is truncated")
    return [entry["path"][:-len(".json")] for entry in document["tree"]
            if entry.get("type") == "blob" and
            entry["path"].endswith(".json")]


def parse_package_metadata(document) -> list:
    _require(isinstance(document, dict) and
             isinstance(document.get("published"), dict),
             "registry metadata")
    return list(document["published"])


def _file_name(name: str) -> str:
    return name.replace("/", "__")


# ---------------------------------------------------------------- fixtures

class FixtureSources:
    """Reads documents under fixture_dir; repos maps owner/name to a path.

    Layout: npm/<package>.json, github-releases/<owner>__<repo>.json (all
    pages as one list), package-sets.json, purescript-package/<name>.json,
    with "/" in a name written as "__". A missing file or repository is a
    SourceError, as an unreachable service would be.
    """

    def __init__(self, fixture_dir: Path, repos: dict):
        self.fixture_dir = Path(fixture_dir)
        self.repos = dict(repos)

    def _load(self, rel: str):
        path = self.fixture_dir / rel
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise SourceError(f"fixture {rel}: {error}")

    def clone(self, repo: str) -> Path:
        if repo not in self.repos:
            raise SourceError(f"no fixture repository for {repo}")
        return Path(self.repos[repo])

    def npm_versions(self, package: str) -> list:
        return parse_npm(self._load(f"npm/{_file_name(package)}.json"))

    def github_releases(self, repo: str) -> list:
        return parse_releases(
            self._load(f"github-releases/{_file_name(repo)}.json"))

    def package_sets(self) -> list:
        return parse_package_sets(self._load("package-sets.json"))

    def purescript_package_versions(self, package: str) -> list:
        return parse_package_metadata(
            self._load(f"purescript-package/{_file_name(package)}.json"))


# ----------------------------------------------------------------- network

NEXT_LINK = re.compile(r'<([^>]+)>;\s*rel="next"')


class NetworkSources:
    """The live registries and GitHub. Read-only.

    token, when given, is sent to the GitHub API as a bearer token (the
    workflow's GITHUB_TOKEN raises the rate limit); it is never sent to
    npm or used for cloning, since every upstream here is public.
    Clones go under workdir, which the caller owns and deletes.
    """

    def __init__(self, token: Optional[str], workdir: Path,
                 npm_base: str = "https://registry.npmjs.org",
                 api_base: str = "https://api.github.com",
                 raw_base: str = "https://raw.githubusercontent.com",
                 git_base: str = "https://github.com"):
        self.token = token
        self.workdir = Path(workdir)
        self.npm_base = npm_base
        self.api_base = api_base
        self.raw_base = raw_base
        self.git_base = git_base
        self._clones = {}
        self._cache = {}

    def _get(self, url: str, accept: str, github: bool):
        headers = {"User-Agent": USER_AGENT, "Accept": accept}
        if github and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request,
                                        timeout=TIMEOUT_SECONDS) as reply:
                body = reply.read()
                link = reply.headers.get("Link") or ""
        except (urllib.error.URLError, OSError) as error:
            raise SourceError(f"GET {url}: {error}")
        try:
            return json.loads(body.decode("utf-8")), link
        except (UnicodeDecodeError, ValueError) as error:
            raise SourceError(f"GET {url}: not JSON: {error}")

    def _cached(self, key, fetch):
        if key not in self._cache:
            self._cache[key] = fetch()
        return self._cache[key]

    def clone(self, repo: str) -> Path:
        if repo not in self._clones:
            target = self.workdir / f"{_file_name(repo)}.git"
            self.workdir.mkdir(parents=True, exist_ok=True)
            done = subprocess.run(
                ["git", "clone", "--quiet", "--filter=blob:none", "--bare",
                 f"{self.git_base}/{repo}.git", str(target)],
                capture_output=True, text=True,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
            if done.returncode != 0:
                raise SourceError(f"git clone {repo}: {done.stderr.strip()}")
            self._clones[repo] = target
        return self._clones[repo]

    def npm_versions(self, package: str) -> list:
        url = f"{self.npm_base}/{urllib.parse.quote(package, safe='@')}"
        return self._cached(("npm", package), lambda: parse_npm(self._get(
            url, "application/vnd.npm.install-v1+json", False)[0]))

    def github_releases(self, repo: str) -> list:
        def fetch():
            url = f"{self.api_base}/repos/{repo}/releases?per_page=100"
            pages = []
            while url:
                document, link = self._get(
                    url, "application/vnd.github+json", True)
                _require(isinstance(document, list), "releases page")
                pages.extend(document)
                match = NEXT_LINK.search(link)
                url = match.group(1) if match else None
            return parse_releases(pages)
        return self._cached(("releases", repo), fetch)

    def package_sets(self) -> list:
        url = (f"{self.api_base}/repos/purescript/registry/git/trees/"
               "main:package-sets")
        return self._cached("package-sets", lambda: parse_package_sets(
            self._get(url, "application/vnd.github+json", True)[0]))

    def purescript_package_versions(self, package: str) -> list:
        url = (f"{self.raw_base}/purescript/registry/main/metadata/"
               f"{urllib.parse.quote(package)}.json")
        return self._cached(("purescript", package),
                            lambda: parse_package_metadata(
                                self._get(url, "application/json", False)[0]))
