#!/usr/bin/env python3
"""Drift detection: what moved upstream since each anchor in anchors.json.

Usage: python3 scripts/detect_drift.py [--root DIR] --out FILE [--workdir DIR]

Reads anchors.json under --root and asks the live upstreams (npm, GitHub,
the PureScript registry, git clones) what changed. Read-only network; it
never writes to the repository. GITHUB_TOKEN, when set, is sent to the
GitHub API only. Clones go into --workdir, or a temporary directory that
is deleted on exit.

Exit 0: FILE holds the result, also when there is no drift.
Exit 1: an upstream could not be read, or anchors.json could not be
loaded. The reason goes to stderr and FILE is not written or changed, so
a failed run can never look like "no drift".

Output (drift.json), UTF-8, two-space indent, trailing newline, items
sorted by id, keys in this order, so equal results are equal bytes:

    {"version": 1, "items": [
      {"id": str, "skill": str, "kind": str,
       "from": str | null, "to": str | null, "link": str | null,
       "detail": [str, ...]}]}

kind     id                         from            to            link
fork     anchor id                  anchor (7)      newest commit compare anchor...to
                                                    on the path
vendored anchor id                  anchor (7)      as fork       as fork
installed anchor id                 first commit    as fork       compare from...to, or
                                    with the                      the path's history when
                                    installed tree,               from is "unknown"
                                    or "unknown"
tool     anchor id                  anchored        latest        registry page for to
                                    version         version
new-upstream-skill
         new-upstream-skill/        null            HEAD (7)      tree at HEAD
         <owner>/<repo>/<name>
unregistered
         unregistered/<skill>       null            null          null
anchor-missing
         anchor id                  anchored        null          the anchor commit or
                                    commit (7)                    repository
                                    or hash

detail: fork, vendored and installed list "<sha7> <subject>" for each
commit on the path after from, newest first; vendored puts "latest
release: <tag>" first when a newer SemVer tag exists. anchor-missing and
unregistered give the reason. Others are empty.

Rules:
- fork, vendored: commits on the default branch (HEAD of the clone) after
  the anchor that touch the anchored path (git log <anchor>..HEAD --
  <path>). Commits elsewhere in the repository are ignored, so "to" is
  the newest commit on the path, not HEAD. An anchor that is not a
  commit, is not an ancestor of HEAD (a force-push), or lacks the path is
  reported as anchor-missing; the other anchors are still checked.
- installed: the tree ID at HEAD:<path> against folderHash (the skills
  lock records git tree IDs; checked 2026-11-14). On a difference, walk
  the commits touching the path, newest first, to the first whose tree
  equals folderHash. A path gone at HEAD is anchor-missing, and so is a
  folderHash that names an object other than a tree (the lock records a
  commit ID for a skill at a repository root; detection does not guess
  what that means).
- tool: the highest SemVer version from the ecosystem's source, above
  the anchored version. Pre-releases count only when the anchor is one.
  GitHub releases: drafts and releases marked pre-release are skipped,
  and the tag loses a leading "v". Strings that are not SemVer are
  skipped.
- new-upstream-skill: for each repository with a fork entry, directories
  under skills/ at HEAD that no fork, installed entry or repo/path
  decline names.
- unregistered: the gate's UNREGISTERED findings (check_repo), one each.
- declines: an item whose id and to equal a decline's anchor and to is
  dropped. A decline therefore stops matching once upstream moves.

Blind spots:
- what changed inside a tool release; detection reports the version only;
- upstream branches other than the default branch;
- renamed upstream paths: a fork whose path moved reports the removal
  commit, not the new location;
- tags and versions that are not SemVer (skipped, not reported);
- the gate's other findings (NOTICE, THIRD_PARTY, Versions); the push
  gate owns those.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import anchors_gate as gate
import semver
from sources import ECOSYSTEM_READERS, NetworkSources, SourceError

ITEM_KEYS = ("id", "skill", "kind", "from", "to", "link", "detail")
GIT_ENV = {"GIT_NO_LAZY_FETCH": "1", "GIT_TERMINAL_PROMPT": "0"}


def item(id, skill, kind, from_, to, link, detail):
    return dict(zip(ITEM_KEYS, (id, skill, kind, from_, to, link,
                                list(detail))))


# --------------------------------------------------------------------- git

def git(repo: Path, *args: str, ok=(0,)):
    done = subprocess.run(["git", "-C", str(repo), *args],
                          capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV})
    if done.returncode not in ok:
        raise SourceError(f"git {' '.join(args)} in {repo}: "
                          f"{done.stderr.strip()}")
    return done.returncode, done.stdout


def pathspec(path: str) -> list:
    return ["--", path] if path else []


def resolve(repo: Path, spec: str):
    """The object ID spec names, or None when there is no such object."""
    code, out = git(repo, "rev-parse", "--verify", "--quiet", spec,
                    ok=(0, 1, 128))
    return out.strip() if code == 0 else None


def in_history(repo: Path, commit: str) -> bool:
    code, _ = git(repo, "merge-base", "--is-ancestor", commit, "HEAD",
                  ok=(0, 1))
    return code == 0


def path_log(repo: Path, rev_range: str, path: str) -> list:
    """(sha, subject) for commits in rev_range touching path, newest first."""
    _, out = git(repo, "log", "--format=%H%x09%s", rev_range,
                 *pathspec(path))
    return [tuple(line.split("\t", 1)) for line in out.splitlines() if line]


def describe(commits: list) -> list:
    return [f"{sha[:7]} {subject}" for sha, subject in commits]


def compare(repo: str, base: str, head: str) -> str:
    return f"https://github.com/{repo}/compare/{base}...{head}"


# ---------------------------------------------------------- anchor kinds

def missing(entry, reason, from_=None, link=None):
    return item(entry["id"], entry["skill"], "anchor-missing",
                from_, None, link or f"https://github.com/{entry['repo']}",
                [reason])


def detect_commit_anchor(entry, sources):
    """fork and vendored: commits after the anchor on the anchored path."""
    repo = sources.clone(entry["repo"])
    anchor = entry["commit"]
    short = anchor[:7]
    link = f"https://github.com/{entry['repo']}/commit/{anchor}"
    if resolve(repo, f"{anchor}^{{commit}}") is None:
        return missing(entry, f"commit {anchor} not found upstream",
                       short, link)
    if not in_history(repo, anchor):
        return missing(entry, f"commit {anchor} is not in the history of "
                       "the default branch (force-push?)", short, link)
    if resolve(repo, f"{anchor}:{entry['path']}") is None:
        return missing(entry, f"path {entry['path']!r} not found at "
                       f"{short}", short, link)
    commits = path_log(repo, f"{anchor}..HEAD", entry["path"])
    if not commits:
        return None
    detail = describe(commits)
    if entry["kind"] == "vendored":
        detail = newer_tag(repo, entry) + detail
    newest = commits[0][0]
    return item(entry["id"], entry["skill"], entry["kind"], short,
                newest[:7], compare(entry["repo"], anchor, newest), detail)


def newer_tag(repo: Path, entry) -> list:
    _, out = git(repo, "tag", "--list")
    names = [line.strip() for line in out.splitlines() if line.strip()]
    tags = {name[1:] if name.startswith("v") else name: name
            for name in names}
    anchored = semver.parse(entry["version"])
    latest = semver.latest_stable(list(tags), anchored.is_prerelease)
    if latest is None or semver.parse(latest) <= anchored:
        return []
    return [f"latest release: {tags[latest]}"]


def detect_installed(entry, sources):
    repo = sources.clone(entry["repo"])
    path = entry["path"]
    head_tree = resolve(repo, f"HEAD:{path}")
    if head_tree is None:
        return missing(entry, f"path {path!r} not found at the default "
                       "branch's HEAD")
    if head_tree == entry["folderHash"]:
        return None
    code, out = git(repo, "cat-file", "-t", entry["folderHash"],
                    ok=(0, 128))
    kind = out.strip() if code == 0 else None
    if kind not in (None, "tree"):
        return missing(entry, f"folderHash {entry['folderHash']} is a "
                       f"{kind}, not a tree; re-anchor by tree ID",
                       entry["folderHash"][:7])
    commits = path_log(repo, "HEAD", path)
    since = None
    after = []
    for sha, subject in commits:
        tree = resolve(repo, f"{sha}:{path}")
        if tree == entry["folderHash"]:
            since = sha
            break
        after.append((sha, subject))
    newest = commits[0][0]
    if since is None:
        history = f"https://github.com/{entry['repo']}/commits/{newest}"
        if path:
            history += f"/{path}"
        return item(entry["id"], entry["skill"], "installed", "unknown",
                    newest[:7], history,
                    [f"installed tree {entry['folderHash']} is not in the "
                     f"history of {path or 'the repository root'}"])
    return item(entry["id"], entry["skill"], "installed", since[:7],
                newest[:7], compare(entry["repo"], since, newest),
                describe(after))


def tool_candidates(entry, sources):
    """(version, link) pairs from the ecosystem's source."""
    ecosystem, package = entry["ecosystem"], entry["package"]
    reader = getattr(sources, ECOSYSTEM_READERS[ecosystem])
    if ecosystem == "npm":
        return [(v, f"https://www.npmjs.com/package/{package}/v/{v}")
                for v in reader(package)]
    if ecosystem == "github-release":
        return [(r.tag[1:] if r.tag.startswith("v") else r.tag, r.url)
                for r in reader(package)
                if not r.draft and not r.prerelease]
    if ecosystem == "purescript-package-set":
        return [(v, "https://github.com/purescript/registry/blob/main/"
                 f"package-sets/{v}.json") for v in reader()]
    return [(v, f"https://pursuit.purescript.org/packages/"
             f"purescript-{package}/{v}") for v in reader(package)]


def detect_tool(entry, sources):
    candidates = dict(tool_candidates(entry, sources))
    allow_pre = semver.parse(entry["version"]).is_prerelease
    latest = semver.latest_stable(list(candidates), allow_pre)
    if latest is None or \
            semver.parse(latest) <= semver.parse(entry["version"]):
        return None
    return item(entry["id"], entry["skill"], "tool", entry["version"],
                latest, candidates[latest], [])


def detect_new_upstream(repo_name, anchors, declined, sources):
    repo = sources.clone(repo_name)
    _, out = git(repo, "ls-tree", "-d", "--name-only", "HEAD", "skills/")
    known = {e["path"] for e in anchors
             if e["kind"] in ("fork", "installed") and
             e["repo"] == repo_name}
    declined_paths = {d["path"] for d in declined
                      if d.get("repo") == repo_name}
    known |= declined_paths
    head = resolve(repo, "HEAD")
    found = []
    for path in out.splitlines():
        if path in known:
            continue
        name = path.split("/", 1)[1]
        found.append(item(f"new-upstream-skill/{repo_name}/{name}", name,
                          "new-upstream-skill", None, head[:7],
                          f"https://github.com/{repo_name}/tree/{head}/"
                          f"{path}", []))
    return found


# -------------------------------------------------------------------- run

def detect(root: Path, sources) -> list:
    """Every drift item for the anchors under root, sorted by id.

    Raises SourceError when an upstream cannot be read, and
    anchors_gate.GateError when anchors.json cannot be loaded.
    """
    anchors = gate.load_anchors(root / "anchors.json")
    items = []
    for entry in anchors.anchors:
        kind = entry["kind"]
        if kind in ("fork", "vendored"):
            items.append(detect_commit_anchor(entry, sources))
        elif kind == "installed":
            items.append(detect_installed(entry, sources))
        elif kind == "tool":
            items.append(detect_tool(entry, sources))
    fork_repos = sorted({e["repo"] for e in anchors.anchors
                         if e["kind"] == "fork"})
    for repo_name in fork_repos:
        items.extend(detect_new_upstream(repo_name, anchors.anchors,
                                         anchors.declined, sources))
    for finding in gate.check_repo(root):
        if finding.code == "UNREGISTERED":
            items.append(item(f"unregistered/{finding.subject}",
                              finding.subject, "unregistered", None, None,
                              None, [finding.message]))
    declined_targets = {(d["anchor"], d["to"]) for d in anchors.declined
                        if "anchor" in d}
    kept = [found for found in items if found is not None and
            (found["id"], found["to"]) not in declined_targets]
    return sorted(kept, key=lambda found: found["id"])


def render(items: list) -> str:
    return json.dumps({"version": 1, "items": items}, indent=2,
                      ensure_ascii=False) + "\n"


def main(argv=None, sources=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workdir", type=Path)
    args = parser.parse_args(argv)
    with tempfile.TemporaryDirectory(prefix="skill-drift-") as scratch:
        if sources is None:
            sources = NetworkSources(os.environ.get("GITHUB_TOKEN") or None,
                                     args.workdir or Path(scratch))
        try:
            items = detect(args.root, sources)
        except (SourceError, gate.GateError) as error:
            print(f"detect_drift: {error}", file=sys.stderr)
            return 1
    partial = args.out.with_name(args.out.name + ".partial")
    partial.write_text(render(items), encoding="utf-8")
    os.replace(partial, args.out)
    print(f"detect_drift: {len(items)} item(s) written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
