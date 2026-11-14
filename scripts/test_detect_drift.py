"""Tests for detect_drift.py and sources.py, offline.

Run from the repository root: python3 -m unittest discover -s scripts
DETECT_DRIFT_PATH swaps in another detector, which is how the mutant test
works.

Upstream repositories are real git repositories built in a temporary
directory by fixtures/detect/upstream.py. Registry responses are either
the trimmed recorded ones in fixtures/detect/recorded/ or small synthetic
documents in the same shape. No test touches the network: the one
NetworkSources test points it at a closed local port.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fixtures" / "detect"))

import sources  # noqa: E402
from upstream import Upstream  # noqa: E402

DETECTOR = Path(os.environ.get("DETECT_DRIFT_PATH", HERE / "detect_drift.py"))
RECORDED = HERE / "fixtures" / "detect" / "recorded"
REPO = "obra/superpowers"


def load_detector():
    spec = importlib.util.spec_from_file_location("detect_drift", DETECTOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


detect_drift = load_detector()


# ---------------------------------------------------------------- builders

def fork(skill, path, commit, repo=REPO):
    return {"id": skill, "skill": skill, "kind": "fork", "repo": repo,
            "path": path, "commit": commit, "release": "v1.0.0"}


def vendored(skill, path, commit, repo="someone/vendor", version="1.0.0",
             tag="v1.0.0"):
    return {"id": skill, "skill": skill, "kind": "vendored", "repo": repo,
            "path": path, "local": "references/vendored.md",
            "version": version, "tag": tag, "commit": commit}


def installed(skill, path, folder_hash, repo="someone/installed"):
    return {"id": f"installed/{skill}", "skill": skill, "kind": "installed",
            "repo": repo, "path": path, "folderHash": folder_hash}


def tool(skill, ecosystem, package, version):
    return {"id": f"{skill}/{package}", "skill": skill, "kind": "tool",
            "ecosystem": ecosystem, "package": package, "version": version,
            "row": package, "check": "checks/x"}


def none(skill):
    return {"id": skill, "skill": skill, "kind": "none", "reason": "test"}


class Case(unittest.TestCase):
    """A temporary root, fixture directory and upstream repositories."""

    def setUp(self):
        self.room = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.room)
        self.root = self.room / "root"
        self.fixtures = self.room / "fixtures"
        self.fixtures.mkdir()
        self.repos = {}

    def upstream(self, repo):
        built = Upstream(self.room / "upstreams" / repo.replace("/", "__"))
        self.repos[repo] = built.path
        return built

    def write_root(self, anchors, declined=(), extra_skills=()):
        skills = {a["skill"] for a in anchors if a["kind"] != "installed"}
        for skill in sorted(skills | set(extra_skills)):
            target = self.root / "skills" / skill / "SKILL.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f"---\nname: {skill}\n---\n", encoding="utf-8")
        self.root.mkdir(exist_ok=True)
        (self.root / "anchors.json").write_text(json.dumps(
            {"version": 1, "anchors": list(anchors),
             "declined": list(declined)}), encoding="utf-8")

    def fixture(self, rel, document):
        target = self.fixtures / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(document), encoding="utf-8")

    def npm(self, package, versions):
        self.fixture(f"npm/{package.replace('/', '__')}.json",
                     {"name": package, "versions": {v: {} for v in versions}})

    def detect(self):
        return detect_drift.detect(
            self.root, sources.FixtureSources(self.fixtures, self.repos))

    def by_id(self):
        return {item["id"]: item for item in self.detect()}


def superpowers_with_anchor(case, extra=None):
    """An upstream with two skills at an anchor commit, as forks see it."""
    up = case.upstream(REPO)
    anchor = up.commit("anchor", {
        "skills/alpha/SKILL.md": "alpha v1\n",
        "skills/beta/SKILL.md": "beta v1\n",
        **(extra or {})})
    return up, anchor


# ------------------------------------------------------------------ forks

class Forks(Case):
    def test_fork_no_change(self):
        up, anchor = superpowers_with_anchor(self)
        self.write_root([fork("a", "skills/alpha", anchor),
                         fork("b", "skills/beta", anchor)])
        self.assertEqual(self.detect(), [])

    def test_fork_change_on_path_reported(self):
        up, anchor = superpowers_with_anchor(self)
        first = up.commit("alpha: tighten wording",
                          {"skills/alpha/SKILL.md": "alpha v2\n"})
        up.commit("unrelated", {"README.md": "hi\n"})
        last = up.commit("alpha: add example",
                         {"skills/alpha/extra.md": "x\n"})
        up.commit("unrelated again", {"README.md": "hello\n"})
        self.write_root([fork("a", "skills/alpha", anchor),
                         fork("b", "skills/beta", anchor)])
        items = self.detect()
        self.assertEqual([i["id"] for i in items], ["a"])
        item = items[0]
        self.assertEqual(item["kind"], "fork")
        self.assertEqual(item["skill"], "a")
        self.assertEqual(item["from"], anchor[:7])
        self.assertEqual(item["to"], last[:7])
        self.assertEqual(
            item["link"],
            f"https://github.com/{REPO}/compare/{anchor}...{last}")
        self.assertEqual(item["detail"], [
            f"{last[:7]} alpha: add example",
            f"{first[:7]} alpha: tighten wording"])

    def test_fork_change_elsewhere_ignored(self):
        up, anchor = superpowers_with_anchor(self)
        up.commit("beta moves", {"skills/beta/SKILL.md": "beta v2\n"})
        up.commit("readme", {"README.md": "x\n"})
        self.write_root([fork("a", "skills/alpha", anchor)],
                        declined=[{"repo": REPO, "path": "skills/beta",
                                   "reason": "test"}])
        self.assertEqual(self.detect(), [])

    def test_fork_path_prefix_is_not_a_match(self):
        """skills/alpha must not match skills/alpha-two."""
        up, anchor = superpowers_with_anchor(self)
        up.commit("alpha-two", {"skills/alpha-two/SKILL.md": "x\n"})
        self.write_root([fork("a", "skills/alpha", anchor)],
                        declined=[{"repo": REPO, "path": p, "reason": "t"}
                                  for p in ("skills/beta",
                                            "skills/alpha-two")])
        self.assertEqual(self.detect(), [])

    def test_unknown_anchor_commit_reports_anchor_missing(self):
        up, anchor = superpowers_with_anchor(self)
        moved = up.commit("beta moves", {"skills/beta/SKILL.md": "beta v2\n"})
        self.write_root([fork("a", "skills/alpha", "f" * 40),
                         fork("b", "skills/beta", anchor)])
        items = self.by_id()
        self.assertEqual(sorted(items), ["a", "b"])
        self.assertEqual(items["a"]["kind"], "anchor-missing")
        self.assertEqual(items["a"]["from"], "fffffff")
        self.assertIsNone(items["a"]["to"])
        self.assertEqual(items["b"]["kind"], "fork")
        self.assertEqual(items["b"]["to"], moved[:7])

    def test_force_pushed_anchor_reports_anchor_missing(self):
        """The anchor object still exists but is not in HEAD's history."""
        up, base = superpowers_with_anchor(self)
        anchor = up.commit("later", {"skills/alpha/SKILL.md": "alpha v2\n"})
        up.reset_hard(base)
        up.commit("rewritten", {"skills/beta/SKILL.md": "beta v2\n"})
        self.write_root([fork("a", "skills/alpha", anchor),
                         fork("b", "skills/beta", base)])
        items = self.by_id()
        self.assertEqual(items["a"]["kind"], "anchor-missing")
        self.assertIn("not in the history", items["a"]["detail"][0])
        self.assertEqual(items["b"]["kind"], "fork")

    def test_anchor_path_absent_at_anchor_reports_anchor_missing(self):
        up, anchor = superpowers_with_anchor(self)
        self.write_root([fork("a", "skills/gamma", anchor),
                         fork("b", "skills/alpha", anchor)],
                        declined=[{"repo": REPO, "path": "skills/beta",
                                   "reason": "t"}])
        items = self.by_id()
        self.assertEqual(list(items), ["a"])
        self.assertEqual(items["a"]["kind"], "anchor-missing")


class Vendored(Case):
    def test_vendored_change_and_newer_tag(self):
        up = self.upstream("someone/vendor")
        anchor = up.commit("v1", {"SKILL.md": "v1\n"})
        up.git("tag", "v1.0.0", anchor)
        head = up.commit("v2", {"SKILL.md": "v2\n"})
        up.git("tag", "v2.0.0", head)
        up.git("tag", "v3.0.0-rc.1", head)
        self.write_root([vendored("h", "SKILL.md", anchor)])
        items = self.detect()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["kind"], "vendored")
        self.assertEqual(items[0]["to"], head[:7])
        self.assertEqual(items[0]["detail"],
                         ["latest release: v2.0.0", f"{head[:7]} v2"])

    def test_vendored_unchanged_file_no_item(self):
        up = self.upstream("someone/vendor")
        anchor = up.commit("v1", {"SKILL.md": "v1\n"})
        up.commit("other", {"README.md": "x\n"})
        up.git("tag", "v2.0.0")
        self.write_root([vendored("h", "SKILL.md", anchor)])
        self.assertEqual(self.detect(), [])


# -------------------------------------------------------------- installed

class Installed(Case):
    def setUp(self):
        super().setUp()
        self.up = self.upstream("someone/installed")
        self.c1 = self.up.commit("add skill", {"skills/s/SKILL.md": "1\n"})
        self.c2 = self.up.commit("other", {"README.md": "x\n"})
        self.installed_tree = self.up.tree(self.c2, "skills/s")

    def test_installed_same_tree_no_item(self):
        self.write_root([installed("s", "skills/s", self.installed_tree)])
        self.assertEqual(self.detect(), [])

    def test_installed_changed_tree_reports_since_commit(self):
        c3 = self.up.commit("skill v2", {"skills/s/SKILL.md": "2\n"})
        self.up.commit("other again", {"README.md": "y\n"})
        c5 = self.up.commit("skill v3", {"skills/s/more.md": "3\n"})
        self.write_root([installed("s", "skills/s", self.installed_tree)])
        items = self.detect()
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["id"], "installed/s")
        self.assertEqual(item["kind"], "installed")
        self.assertEqual(item["from"], self.c1[:7])
        self.assertEqual(item["to"], c5[:7])
        self.assertEqual(item["link"], "https://github.com/someone/installed"
                         f"/compare/{self.c1}...{c5}")
        self.assertEqual(item["detail"], [f"{c5[:7]} skill v3",
                                          f"{c3[:7]} skill v2"])

    def test_installed_hash_not_in_history_reports_unknown_from(self):
        c3 = self.up.commit("skill v2", {"skills/s/SKILL.md": "2\n"})
        self.write_root([installed("s", "skills/s", "a" * 40)])
        item = self.detect()[0]
        self.assertEqual(item["kind"], "installed")
        self.assertEqual(item["from"], "unknown")
        self.assertEqual(item["to"], c3[:7])
        self.assertIn("a" * 40, item["detail"][0])

    def test_installed_tree_on_side_branch_only_is_unknown(self):
        """History is the default branch's; another branch does not count."""
        self.up.git("checkout", "-q", "-b", "side")
        self.up.commit("side change", {"skills/s/SKILL.md": "side\n"})
        side_tree = self.up.tree("HEAD", "skills/s")
        self.up.git("checkout", "-q", "main")
        self.write_root([installed("s", "skills/s", side_tree)])
        self.assertEqual(self.detect()[0]["from"], "unknown")

    def test_installed_repo_root_path(self):
        root_tree = self.up.tree(self.c2, "")
        self.write_root([installed("s", "", root_tree)])
        self.assertEqual(self.detect(), [])
        c3 = self.up.commit("anything", {"x.md": "x\n"})
        item = self.detect()[0]
        self.assertEqual((item["from"], item["to"]),
                         (self.c2[:7], c3[:7]))

    def test_installed_hash_naming_a_commit_reports_anchor_missing(self):
        """The skills lock records a commit ID for a repo-root skill
        (blader/humanizer, 2026-11-14). Detection does not guess what that
        means; it reports the entry for the owner to re-anchor."""
        self.up.commit("later", {"README.md": "y\n"})
        self.write_root([installed("s", "", self.c2)])
        item = self.detect()[0]
        self.assertEqual(item["kind"], "anchor-missing")
        self.assertEqual(item["from"], self.c2[:7])
        self.assertIn("is a commit, not a tree", item["detail"][0])

    def test_installed_repo_root_with_commit_resolves_from_commit(self):
        """The blader/humanizer shape after re-anchoring (owner, 2026-11-14):
        path "" (the skill is the repository root), commit = the lock's
        skillFolderHash, folderHash = that commit's root tree. It must
        resolve to an installed item from that commit, not anchor-missing.
        A later revert to the same root tree must not move "from"."""
        entry = dict(installed("s", "", self.up.tree(self.c2, "")),
                     commit=self.c2)
        self.write_root([entry])
        self.assertEqual(self.detect(), [])
        c3 = self.up.commit("change", {"x.md": "x\n"})
        c4 = self.up.commit("revert", {"x.md": None})
        c5 = self.up.commit("change again", {"y.md": "y\n"})
        item = self.detect()[0]
        self.assertEqual(item["kind"], "installed")
        self.assertEqual((item["from"], item["to"]), (self.c2[:7], c5[:7]))
        self.assertEqual(item["link"], "https://github.com/someone/installed"
                         f"/compare/{self.c2}...{c5}")
        self.assertEqual(item["detail"], [f"{c5[:7]} change again",
                                          f"{c4[:7]} revert",
                                          f"{c3[:7]} change"])

    def test_installed_commit_disagreeing_with_folder_hash_is_anchor_missing(
            self):
        """commit and folderHash must name the same tree; the original
        humanizer entry (folderHash holding the commit ID) fails here even
        with commit recorded."""
        self.up.commit("later", {"README.md": "y\n"})
        entry = dict(installed("s", "", self.c2), commit=self.c2)
        self.write_root([entry])
        item = self.detect()[0]
        self.assertEqual(item["kind"], "anchor-missing")
        self.assertIn("disagree", item["detail"][0])
        other = dict(installed("s", "skills/s", self.installed_tree),
                     commit=self.c1)
        self.up.commit("skill v2", {"skills/s/SKILL.md": "2\n"})
        self.write_root([other])
        item = self.detect()[0]
        self.assertEqual(item["kind"], "installed")
        self.assertEqual(item["from"], self.c1[:7])
        wrong = dict(other, folderHash="b" * 40)
        self.write_root([wrong])
        self.assertEqual(self.detect()[0]["kind"], "anchor-missing")

    def test_installed_commit_off_default_branch_is_anchor_missing(self):
        self.up.git("checkout", "-q", "-b", "side")
        side = self.up.commit("side change", {"skills/s/SKILL.md": "side\n"})
        self.up.git("checkout", "-q", "main")
        self.up.commit("main change", {"skills/s/SKILL.md": "main\n"})
        entry = dict(installed("s", "skills/s", self.up.tree(side, "skills/s")),
                     commit=side)
        self.write_root([entry])
        item = self.detect()[0]
        self.assertEqual(item["kind"], "anchor-missing")
        self.assertIn("not in the history", item["detail"][0])

    def test_installed_path_gone_reports_anchor_missing(self):
        self.up.commit("remove", {"skills/s/SKILL.md": None})
        self.write_root([installed("s", "skills/s", self.installed_tree)])
        item = self.detect()[0]
        self.assertEqual(item["kind"], "anchor-missing")


# ------------------------------------------------------------------ tools

class Tools(Case):
    def test_tool_npm_newer_stable(self):
        self.npm("@effect/vitest", ["4.1.1", "4.1.2", "4.10.0"])
        self.write_root([tool("e", "npm", "@effect/vitest", "4.1.1")])
        item = self.detect()[0]
        self.assertEqual((item["id"], item["kind"], item["from"], item["to"]),
                         ("e/@effect/vitest", "tool", "4.1.1", "4.10.0"))
        self.assertEqual(item["link"],
                         "https://www.npmjs.com/package/@effect/vitest/v/4.10.0")

    def test_tool_npm_same_version_no_item(self):
        self.npm("effect", ["4.0.0", "4.1.1"])
        self.write_root([tool("e", "npm", "effect", "4.1.1")])
        self.assertEqual(self.detect(), [])

    def test_tool_npm_prerelease_ignored(self):
        self.npm("effect", ["4.1.1", "4.2.0-beta.1", "5.0.0-rc.1"])
        self.write_root([tool("e", "npm", "effect", "4.1.1")])
        self.assertEqual(self.detect(), [])

    def test_tool_prerelease_anchor_sees_prerelease(self):
        self.npm("effect", ["4.2.0-beta.1", "4.2.0-beta.2"])
        self.write_root([tool("e", "npm", "effect", "4.2.0-beta.1")])
        self.assertEqual(self.detect()[0]["to"], "4.2.0-beta.2")

    def test_purs_release_draft_and_prerelease_ignored(self):
        def release(tag, prerelease=False, draft=False):
            return {"tag_name": tag, "prerelease": prerelease,
                    "draft": draft,
                    "html_url": f"https://example.invalid/{tag}"}
        self.fixture("github-releases/purescript__purescript.json", [
            release("v0.15.16"), release("v0.15.17"),
            release("v0.15.18", draft=True),
            release("v0.15.19", prerelease=True),
            release("v0.16.0-0"), release("nightly")])
        self.write_root([tool("p", "github-release", "purescript/purescript",
                              "0.15.16")])
        item = self.detect()[0]
        self.assertEqual((item["from"], item["to"], item["link"]),
                         ("0.15.16", "0.15.17",
                          "https://example.invalid/v0.15.17"))

    def test_package_set_newer(self):
        self.fixture("package-sets.json", {"truncated": False, "tree": [
            {"path": "81.0.0.json", "type": "blob"},
            {"path": "9.0.0.json", "type": "blob"},
            {"path": "81.1.0.json", "type": "blob"},
            {"path": "README.md", "type": "blob"}]})
        self.write_root([tool("ps", "purescript-package-set", "registry",
                              "81.0.0")])
        item = self.detect()[0]
        self.assertEqual(item["to"], "81.1.0")
        self.assertEqual(item["link"], "https://github.com/purescript/"
                         "registry/blob/main/package-sets/81.1.0.json")

    def test_truncated_package_set_listing_is_a_source_error(self):
        self.fixture("package-sets.json", {"truncated": True, "tree": []})
        self.write_root([tool("ps", "purescript-package-set", "registry",
                              "81.0.0")])
        with self.assertRaises(sources.SourceError):
            self.detect()

    def test_purescript_package_newer_and_unpublished_ignored(self):
        self.fixture("purescript-package/prelude.json", {
            "published": {"6.0.2": {}, "6.0.3": {}},
            "unpublished": {"7.0.0": {}}})
        self.write_root([tool("g", "purescript-package", "prelude", "6.0.2")])
        item = self.detect()[0]
        self.assertEqual(item["to"], "6.0.3")
        self.assertEqual(item["link"], "https://pursuit.purescript.org/"
                         "packages/purescript-prelude/6.0.3")


class RecordedResponses(Case):
    """The parsers read the trimmed real responses recorded 2026-11-14."""

    def test_recorded_fixtures_parse(self):
        def load(name):
            return json.loads((RECORDED / name).read_text(encoding="utf-8"))
        npm = sources.parse_npm(load("npm-effect.json"))
        self.assertIn("4.1.4", npm)
        self.assertIn("4.0.0-beta.107", npm)
        releases = sources.parse_releases(
            load("github-releases-purescript-purescript.json"))
        self.assertIn(sources.Release(
            "v0.15.17", False, False,
            "https://github.com/purescript/purescript/releases/tag/v0.15.17"),
            releases)
        sets = sources.parse_package_sets(
            load("github-tree-registry-package-sets.json"))
        self.assertEqual(sorted(sets),
                         ["0.0.1", "81.0.0", "82.0.0", "82.1.0", "82.1.1",
                          "9.0.0"])
        prelude = sources.parse_package_metadata(
            load("registry-metadata-prelude.json"))
        self.assertIn("6.0.3", prelude)

    def test_recorded_responses_drive_detection(self):
        for name, rel in [
                ("npm-effect.json", "npm/effect.json"),
                ("github-releases-purescript-purescript.json",
                 "github-releases/purescript__purescript.json"),
                ("github-tree-registry-package-sets.json",
                 "package-sets.json"),
                ("registry-metadata-prelude.json",
                 "purescript-package/prelude.json")]:
            target = self.fixtures / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(RECORDED / name, target)
        self.write_root([
            tool("g", "npm", "effect", "4.1.1"),
            tool("g", "github-release", "purescript/purescript", "0.15.16"),
            tool("g", "purescript-package-set", "registry", "81.0.0"),
            tool("g", "purescript-package", "prelude", "6.0.2")])
        found = {i["id"]: i["to"] for i in self.detect()}
        self.assertEqual(found, {
            "g/effect": "4.1.4", "g/purescript/purescript": "0.15.17",
            "g/registry": "82.1.1", "g/prelude": "6.0.3"})


# ------------------------------------------- new upstream skills, declines

class NewUpstreamSkills(Case):
    def test_new_upstream_skill_reported(self):
        up, anchor = superpowers_with_anchor(self)
        head = up.commit("add gamma", {"skills/gamma/SKILL.md": "g\n"})
        self.write_root([fork("a", "skills/alpha", anchor),
                         fork("b", "skills/beta", anchor)])
        items = self.detect()
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item["id"], f"new-upstream-skill/{REPO}/gamma")
        self.assertEqual(item["kind"], "new-upstream-skill")
        self.assertEqual(item["skill"], "gamma")
        self.assertIsNone(item["from"])
        self.assertEqual(item["to"], head[:7])
        self.assertEqual(item["link"],
                         f"https://github.com/{REPO}/tree/{head}/skills/gamma")

    def test_installed_upstream_skill_not_reported(self):
        up, anchor = superpowers_with_anchor(self)
        self.write_root([fork("a", "skills/alpha", anchor),
                         installed("beta", "skills/beta",
                                   up.tree(anchor, "skills/beta"), repo=REPO)])
        self.assertEqual(self.detect(), [])

    def test_declined_upstream_skill_not_reported(self):
        up, anchor = superpowers_with_anchor(self)
        up.commit("add gamma", {"skills/gamma/SKILL.md": "g\n"})
        self.write_root([fork("a", "skills/alpha", anchor),
                         fork("b", "skills/beta", anchor)],
                        declined=[{"repo": REPO, "path": "skills/gamma",
                                   "reason": "not adopted"}])
        self.assertEqual(self.detect(), [])

    def test_decline_for_another_repo_does_not_apply(self):
        up, anchor = superpowers_with_anchor(self)
        up.commit("add gamma", {"skills/gamma/SKILL.md": "g\n"})
        self.write_root([fork("a", "skills/alpha", anchor),
                         fork("b", "skills/beta", anchor)],
                        declined=[{"repo": "other/repo",
                                   "path": "skills/gamma", "reason": "t"}])
        self.assertEqual([i["kind"] for i in self.detect()],
                         ["new-upstream-skill"])

    def test_repo_without_forks_not_scanned(self):
        up = self.upstream("someone/installed")
        c1 = up.commit("two skills", {"skills/s/SKILL.md": "1\n",
                                      "skills/t/SKILL.md": "1\n"})
        self.write_root([installed("s", "skills/s", up.tree(c1, "skills/s"))])
        self.assertEqual(self.detect(), [])

    def test_declined_drift_target_not_reported_until_upstream_moves(self):
        up, anchor = superpowers_with_anchor(self)
        moved = up.commit("alpha v2", {"skills/alpha/SKILL.md": "alpha v2\n"})
        anchors = [fork("a", "skills/alpha", anchor),
                   fork("b", "skills/beta", anchor)]
        self.write_root(anchors)
        self.assertEqual(self.detect()[0]["to"], moved[:7])
        self.write_root(anchors, declined=[
            {"anchor": "a", "to": moved[:7], "reason": "not wanted"}])
        self.assertEqual(self.detect(), [])
        up.commit("unrelated", {"README.md": "x\n"})
        self.assertEqual(self.detect(), [])
        again = up.commit("alpha v3", {"skills/alpha/SKILL.md": "alpha v3\n"})
        items = self.detect()
        self.assertEqual([(i["id"], i["to"]) for i in items],
                         [("a", again[:7])])

    def test_declined_tool_target_not_reported(self):
        self.npm("effect", ["4.1.1", "4.2.0"])
        self.write_root([tool("e", "npm", "effect", "4.1.1")],
                        declined=[{"anchor": "e/effect", "to": "4.2.0",
                                   "reason": "t"}])
        self.assertEqual(self.detect(), [])


class Unregistered(Case):
    def test_unregistered_local_skill_reported(self):
        self.write_root([none("known")], extra_skills=["stray"])
        items = self.detect()
        self.assertEqual(len(items), 1)
        self.assertEqual(
            (items[0]["id"], items[0]["skill"], items[0]["kind"]),
            ("unregistered/stray", "stray", "unregistered"))

    def test_none_only_root_reports_nothing(self):
        self.write_root([none("known")])
        self.assertEqual(self.detect(), [])


# --------------------------------------------------------------- contract

class WriterContract(Case):
    """Real detect() output, every kind, goes through the issue writer's
    validation and rendering (drift_issue.load_items and render)."""

    def test_every_detected_kind_is_accepted_by_the_writer(self):
        import drift_issue
        up, anchor = superpowers_with_anchor(self)
        up.commit("alpha v2", {"skills/alpha/SKILL.md": "alpha v2\n"})
        up.commit("add gamma", {"skills/gamma/SKILL.md": "g\n"})
        vend = self.upstream("someone/vendor")
        v1 = vend.commit("v1", {"SKILL.md": "v1\n"})
        vend.commit("v2", {"SKILL.md": "v2\n"})
        inst = self.upstream("someone/installed")
        c1 = inst.commit("add skill", {"skills/s/SKILL.md": "1\n"})
        inst.commit("skill v2", {"skills/s/SKILL.md": "2\n"})
        self.npm("effect", ["4.1.1", "4.1.2"])
        # A GitHub release without html_url: detection must say null.
        self.fixture("github-releases/purescript__purescript.json", [
            {"tag_name": "v0.15.17", "prerelease": False, "draft": False}])
        self.write_root([
            fork("a", "skills/alpha", anchor),
            fork("b", "skills/beta", anchor),
            fork("m", "skills/alpha", "f" * 40),
            vendored("h", "SKILL.md", v1),
            installed("s", "skills/s", inst.tree(c1, "skills/s")),
            tool("e", "npm", "effect", "4.1.1"),
            tool("p", "github-release", "purescript/purescript", "0.15.16"),
        ], extra_skills=["stray"])
        items = self.detect()
        self.assertEqual({i["kind"] for i in items}, set(drift_issue.KINDS))
        release = next(i for i in items if i["id"] == "p/purescript/purescript")
        self.assertIsNone(release["link"])
        path = self.room / "drift.json"
        path.write_text(detect_drift.render(items), encoding="utf-8")
        loaded = drift_issue.load_items(path)
        body = drift_issue.render(loaded, None)
        self.assertEqual(set(drift_issue.parse_ticks(body)),
                         {i["id"] for i in items})
        self.assertNotIn("(None)", body)
        self.assertNotIn("]()", body)


# -------------------------------------------------------------------- CLI

class Cli(Case):
    def run_main(self, out, srcs):
        return detect_drift.main(["--root", str(self.root), "--out",
                                  str(out)], sources=srcs)

    def fixture_sources(self):
        return sources.FixtureSources(self.fixtures, self.repos)

    def test_source_error_exits_1_and_writes_nothing(self):
        self.npm("effect", ["4.1.1"])
        self.write_root([tool("e", "npm", "effect", "4.1.1"),
                         tool("e", "npm", "typescript", "5.9.3")])
        out = self.room / "drift.json"
        self.assertEqual(self.run_main(out, self.fixture_sources()), 1)
        self.assertFalse(out.exists())

    def test_missing_clone_exits_1(self):
        self.write_root([fork("a", "skills/alpha", "f" * 40)])
        out = self.room / "drift.json"
        self.assertEqual(self.run_main(out, self.fixture_sources()), 1)
        self.assertFalse(out.exists())

    def test_network_failure_exits_1_and_writes_nothing(self):
        self.write_root([tool("e", "npm", "effect", "4.1.1")])
        out = self.room / "drift.json"
        closed = "http://127.0.0.1:9"
        network = sources.NetworkSources(
            None, self.room / "work", npm_base=closed, api_base=closed,
            raw_base=closed)
        self.assertEqual(self.run_main(out, network), 1)
        self.assertFalse(out.exists())

    def test_empty_result_written(self):
        self.write_root([none("known")])
        out = self.room / "drift.json"
        self.assertEqual(self.run_main(out, self.fixture_sources()), 0)
        self.assertEqual(json.loads(out.read_text()),
                         {"version": 1, "items": []})

    def test_output_is_stable(self):
        up, anchor = superpowers_with_anchor(self)
        up.commit("alpha v2", {"skills/alpha/SKILL.md": "alpha v2\n"})
        up.commit("beta v2", {"skills/beta/SKILL.md": "beta v2\n"})
        up.commit("add gamma", {"skills/gamma/SKILL.md": "g\n"})
        self.npm("effect", ["4.1.1", "4.2.0"])
        self.write_root([tool("z", "npm", "effect", "4.1.1"),
                         fork("b", "skills/beta", anchor),
                         fork("a", "skills/alpha", anchor)],
                        extra_skills=["stray"])
        first, second = self.room / "1.json", self.room / "2.json"
        self.assertEqual(self.run_main(first, self.fixture_sources()), 0)
        self.assertEqual(self.run_main(second, self.fixture_sources()), 0)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        document = json.loads(first.read_text())
        ids = [i["id"] for i in document["items"]]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(ids), 5)
        for item in document["items"]:
            self.assertEqual(list(item), ["id", "skill", "kind", "from", "to",
                                          "link", "detail"])
        self.assertTrue(first.read_text().endswith("\n"))


class LiveRepository(unittest.TestCase):
    """The real anchors.json loads, and detection covers each of its kinds."""

    def test_live_anchors_cover_every_detected_kind(self):
        sys.modules.setdefault("anchors_gate", detect_drift.gate)
        anchors = detect_drift.gate.load_anchors(HERE.parent / "anchors.json")
        kinds = {a["kind"] for a in anchors.anchors}
        self.assertTrue({"fork", "vendored", "tool", "installed"} <= kinds)
        ecosystems = {a["ecosystem"] for a in anchors.anchors
                      if a["kind"] == "tool"}
        self.assertEqual(ecosystems, set(sources.ECOSYSTEM_READERS))
        self.assertGreaterEqual(
            len([a for a in anchors.anchors if a["kind"] == "fork"]), 12)


# ------------------------------------------------------------ mutants

class CheckerMutant(unittest.TestCase):
    """A broken detector must fail this suite."""

    MUTANTS = [
        ("fork log drops the pathspec",
         'return ["--", path] if path else []', "return []"),
        ("declined targets ignored",
         "not in declined_targets]", "not in ()]"),
        ("anchor ancestry not checked", "return code == 0", "return True"),
        ("prereleases always allowed",
         "allow_pre = semver.parse(entry[\"version\"]).is_prerelease",
         "allow_pre = True"),
        ("declined upstream skills reported",
         "known |= declined_paths", "pass"),
        ("installed walk takes the newest commit",
         "if tree == entry[\"folderHash\"]:", "if True:"),
    ]

    @unittest.skipIf("DETECT_DRIFT_PATH" in os.environ,
                     "already running a mutant")
    def test_each_mutant_fails_the_suite(self):
        source = (HERE / "detect_drift.py").read_text(encoding="utf-8")
        for name, old, new in self.MUTANTS:
            with self.subTest(mutant=name), \
                    tempfile.TemporaryDirectory() as room:
                self.assertEqual(source.count(old), 1, name)
                broken = Path(room) / "detect_drift.py"
                broken.write_text(source.replace(old, new), encoding="utf-8")
                done = subprocess.run(
                    [sys.executable, "-m", "unittest", "test_detect_drift"],
                    cwd=HERE, capture_output=True, text=True,
                    env={**os.environ, "DETECT_DRIFT_PATH": str(broken)})
                self.assertNotEqual(done.returncode, 0, name)


if __name__ == "__main__":
    unittest.main()
