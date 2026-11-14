"""Tests for drift_issue.py, offline.

Run from the repository root: python3 -m unittest discover -s scripts
DRIFT_ISSUE_PATH swaps in another writer, which is how the mutant test
works.

The GitHub API is injected: reconcile() takes an IssueClient, and the tests
pass a FakeClient that holds issues in memory and records every call.
GhClient is tested with a fake command runner fed the recorded shapes in
fixtures/issue/. Nothing here touches the network or GitHub.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
WRITER = Path(os.environ.get("DRIFT_ISSUE_PATH", HERE / "drift_issue.py"))
FIXTURES = HERE / "fixtures" / "issue"
START = "<!-- skill-drift:start -->"
END = "<!-- skill-drift:end -->"


def load_writer():
    spec = importlib.util.spec_from_file_location("drift_issue", WRITER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


drift_issue = load_writer()


def item(id_, to="b", from_="a", kind="fork", detail=(), skill=None):
    return {"id": id_, "skill": skill or id_.split("/")[-1], "kind": kind,
            "from": from_, "to": to,
            "link": f"https://github.com/o/r/compare/{from_}...{to}",
            "detail": list(detail)}


def recorded_items():
    return json.loads((FIXTURES / "drift.json").read_text())["items"]


def tick(body, id_):
    """The owner ticks the line whose key is id_."""
    lines = body.split("\n")
    marker = f"<!-- key:{drift_issue.encode(id_)} "
    hits = [i for i, line in enumerate(lines) if marker in line]
    assert len(hits) == 1, (id_, hits)
    lines[hits[0]] = lines[hits[0]].replace("- [ ]", "- [x]", 1)
    return "\n".join(lines)


def ticked(body):
    return {k for k, v in drift_issue.parse_ticks(body).items() if v.ticked}


class FakeClient:
    """In-memory issues; every call is recorded in .calls."""

    WRITES = {"create", "update", "close", "ensure_label"}

    def __init__(self, issues=(), labels=()):
        self.issues = {n: {"number": n, "body": b, "state": "open"}
                       for n, b in issues}
        self.labels = set(labels)
        self.calls = []

    def find_open(self, label):
        self.calls.append(("find_open", label))
        return [drift_issue.Issue(i["number"], i["body"])
                for i in sorted(self.issues.values(),
                                key=lambda i: i["number"])
                if i["state"] == "open"]

    def create(self, title, body, label):
        self.calls.append(("create", title, body, label))
        number = max(self.issues, default=0) + 1
        self.issues[number] = {"number": number, "body": body,
                               "state": "open"}
        return number

    def update(self, number, body):
        self.calls.append(("update", number, body))
        self.issues[number]["body"] = body

    def close(self, number, comment):
        self.calls.append(("close", number, comment))
        self.issues[number]["state"] = "closed"

    def ensure_label(self, name, color, description):
        self.calls.append(("ensure_label", name, color, description))
        self.labels.add(name)

    def writes(self):
        return [c for c in self.calls if c[0] in self.WRITES]


# ----------------------------------------------------------------- render

class Render(unittest.TestCase):
    def test_line_format(self):
        body = drift_issue.render([item("x", detail=["c1 one", "c2 two"])],
                                  None)
        self.assertIn(
            "- [ ] **x** (fork): a -> b. "
            "[diff](https://github.com/o/r/compare/a...b) "
            "<!-- key:x to:b -->\n  - `c1 one`\n  - `c2 two`\n", body)
        self.assertEqual(body.count(START), 1)
        self.assertEqual(body.count(END), 1)

    def test_recorded_items_render(self):
        body = drift_issue.render(recorded_items(), None)
        self.assertIn("**installed/humanizer** (anchor-missing): 8c307f3 "
                      "-> none. [link](https://github.com/blader/humanizer)",
                      body)
        self.assertIn("**effect-v4/effect** (tool): 4.1.1 -> 4.1.4. "
                      "[link](https://www.npmjs.com/package/effect/v/4.1.4)",
                      body)
        self.assertIn("**design-brainstorming** (fork): 2ce8aa1 -> 22f0b46. "
                      "[diff](https://github.com/obra/superpowers/compare/",
                      body)
        self.assertIn("<!-- key:effect-v4/effect to:4.1.4 -->", body)
        self.assertEqual(set(drift_issue.parse_ticks(body)),
                         {i["id"] for i in recorded_items()})

    def test_id_with_spaces_round_trips(self):
        id_ = "purescript-gotchas/registry package set"
        body = drift_issue.render([item(id_, to="82.0.0")], None)
        self.assertEqual(set(drift_issue.parse_ticks(body)), {id_})
        self.assertEqual(drift_issue.parse_ticks(tick(body, id_))[id_].to,
                         "82.0.0")

    def test_upstream_text_cannot_end_the_region_or_mention(self):
        hostile = ["c1 x <!-- skill-drift:end --> y", "c2 thanks @someone",
                   "c3 a `tick` -->"]
        body = drift_issue.render([item("x", detail=hostile)], None)
        self.assertEqual(body.count(START), 1)
        self.assertEqual(body.count(END), 1)
        self.assertEqual(body.count("-->"), body.count("<!--"))
        self.assertNotIn(" @someone", body.replace("`c2 thanks @someone`",
                                                   ""))
        self.assertIn("`c2 thanks @someone`", body)

    def test_long_detail_is_cut(self):
        detail = [f"c{n} subject" for n in range(25)]
        body = drift_issue.render([item("x", detail=detail)], None)
        self.assertIn("`c19 subject`", body)
        self.assertNotIn("`c20 subject`", body)
        self.assertIn("  - and 5 more; see the diff\n", body)

    def test_oversized_body_fails_before_any_write(self):
        items = [item(f"i{n}", detail=["x" * 4000] * 20) for n in range(2)]
        client = FakeClient()
        with self.assertRaises(drift_issue.WriterError):
            drift_issue.reconcile(items, client)
        self.assertEqual(client.writes(), [])

    def test_no_items_region_says_no_drift(self):
        body = drift_issue.render([], "keep me\n")
        self.assertIn("No drift found.", body)
        self.assertTrue(body.startswith("keep me\n"))

    def test_no_timestamps_render_is_deterministic(self):
        items = recorded_items()
        self.assertEqual(drift_issue.render(items, None),
                         drift_issue.render(items, None))

    def test_ticks_kept_by_key(self):
        items = [item("a"), item("b"), item("c")]
        body = tick(drift_issue.render(items, None), "b")
        again = drift_issue.render(items, body)
        self.assertEqual(ticked(again), {"b"})
        self.assertEqual(again, body)

    def test_reordered_lines_keep_ticks(self):
        items = [item("a", detail=["d1"]), item("b"), item("c")]
        body = tick(tick(drift_issue.render(items, None), "a"), "c")
        lines = body.split("\n")
        a = next(i for i, l in enumerate(lines) if "key:a " in l)
        c = next(i for i, l in enumerate(lines) if "key:c " in l)
        lines[a], lines[c] = lines[c], lines[a]
        again = drift_issue.render(items, "\n".join(lines))
        self.assertEqual(ticked(again), {"a", "c"})

    def test_text_outside_region_survives(self):
        items = [item("a")]
        first = drift_issue.render(items, None)
        edited = "Owner note above.\n\n" + first + "\nAnd below.\n"
        again = drift_issue.render([item("a"), item("b")], edited)
        self.assertTrue(again.startswith("Owner note above.\n\n"))
        self.assertTrue(again.endswith("\nAnd below.\n"))
        self.assertIn("key:b ", again)

    def test_tick_cleared_when_target_moves(self):
        """D12: an approval covered a specific diff."""
        body = tick(drift_issue.render([item("a", to="v2"), item("b")],
                                       None), "a")
        body = tick(body, "b")
        moved = drift_issue.render([item("a", to="v3"), item("b")], body)
        self.assertEqual(ticked(moved), {"b"})
        self.assertIn("(approval cleared: target moved from v2 to v3)",
                      moved)
        # The note stays while the target stays, so the next run is a
        # fixed point, and it goes when the target moves again.
        self.assertEqual(drift_issue.render([item("a", to="v3"), item("b")],
                                            moved), moved)
        retick = tick(moved, "a")
        self.assertEqual(ticked(drift_issue.render(
            [item("a", to="v3"), item("b")], retick)), {"a", "b"})
        again = drift_issue.render([item("a", to="v4"), item("b")], retick)
        self.assertIn("(approval cleared: target moved from v3 to v4)",
                      again)
        self.assertNotIn("from v2", again)

    def test_reticked_line_drops_the_cleared_note(self):
        """A re-tick at an unchanged target is a fresh approval of that
        target, so the note about the old one goes (SKILL.md, step 2)."""
        body = tick(drift_issue.render([item("a", to="v2")], None), "a")
        moved = drift_issue.render([item("a", to="v3")], body)
        self.assertIn("approval cleared", moved)
        again = drift_issue.render([item("a", to="v3")], tick(moved, "a"))
        self.assertEqual(ticked(again), {"a"})
        self.assertNotIn("approval cleared", again)
        self.assertNotIn("cleared:", again)
        self.assertEqual(drift_issue.render([item("a", to="v3")], again),
                         again)

    def test_crlf_body_keeps_ticks(self):
        """GitHub's web editor can send the body back with CRLF endings."""
        items = [item("a"), item("b")]
        body = tick("Owner note.\n\n" + drift_issue.render(items, None), "a")
        crlf = body.replace("\n", "\r\n")
        self.assertEqual(ticked(crlf), {"a"})
        again = drift_issue.render(items, crlf)
        self.assertEqual(ticked(again), {"a"})
        self.assertEqual(again, body)
        self.assertNotIn("\r", again)

    def test_null_link_renders_no_link(self):
        """detect_drift.py documents link as str | null (unregistered
        items always, a GitHub release without a page)."""
        entry = {"id": "unregistered/stray", "skill": "stray",
                 "kind": "unregistered", "from": None, "to": None,
                 "link": None, "detail": ["no anchors.json entry"]}
        with tempfile.TemporaryDirectory() as room:
            path = Path(room) / "drift.json"
            path.write_text(json.dumps({"version": 1, "items": [entry]}))
            loaded = drift_issue.load_items(path)
        body = drift_issue.render(loaded, None)
        self.assertIn("- [ ] **unregistered/stray** (unregistered): none -> "
                      "none. "
                      "<!-- key:unregistered/stray to: -->", body)
        self.assertNotIn("](", body)

    def test_empty_link_still_rejected(self):
        entry = dict(item("a"), link="")
        with tempfile.TemporaryDirectory() as room:
            path = Path(room) / "drift.json"
            path.write_text(json.dumps({"version": 1, "items": [entry]}))
            with self.assertRaises(drift_issue.WriterError):
                drift_issue.load_items(path)

    def test_upstream_names_cannot_mention_link_or_inject_html(self):
        """New upstream skill names come from git ls-tree, so any
        directory name upstream reaches the body."""
        hostile = ["@someone", "[x](https://e)", "<img src=x>", "a`b"]
        items = [item(f"new-upstream-skill/o/r/{n}", skill=n,
                      kind="new-upstream-skill") for n in hostile]
        for entry in items:
            entry["id"] = entry["skill"]
        body = drift_issue.render(items, None)
        for line in body.split("\n"):
            if "<!-- key:" not in line:
                continue
            shown = line[:line.index("<!-- key:")]
            outside = "".join(shown.split("`")[0::2])
            self.assertNotIn("@someone", outside, line)
            self.assertNotIn("[x]", outside, line)
            self.assertNotIn("<img", outside, line)
        self.assertIn("**`@someone`**", body)
        self.assertIn("**`a'b`**", body)
        self.assertEqual(set(drift_issue.parse_ticks(body)),
                         {e["id"] for e in items})
        self.assertIn("- [ ] **x** (fork)",
                      drift_issue.render([item("x")], None))

    def test_untick_target_move_adds_no_note(self):
        body = drift_issue.render([item("a", to="v2")], None)
        moved = drift_issue.render([item("a", to="v3")], body)
        self.assertNotIn("approval cleared", moved)

    def test_declined_item_drops_out(self):
        """D13: detection skips a declined (id, to); the writer drops an
        item that detection no longer reports, tick and all."""
        body = tick(drift_issue.render([item("a"), item("b")], None), "a")
        again = drift_issue.render([item("b")], body)
        self.assertNotIn("key:a ", again)
        self.assertIn("declined", again)  # the region says how to decline

    def test_missing_region_markers_appends_region(self):
        first = tick(drift_issue.render([item("a")], "Note.\n"), "a")
        stripped = first.replace(START + "\n", "").replace(END + "\n", "")
        again = drift_issue.render([item("a")], stripped)
        self.assertTrue(again.startswith(stripped))
        self.assertEqual(again.count(START), 1)
        self.assertEqual(again.count(END), 1)
        region = again[again.index(START):]
        self.assertIn("- [x] **a**", region)
        self.assertEqual(drift_issue.render([item("a")], again), again)

    def test_stray_marker_is_repaired_once(self):
        first = drift_issue.render([item("a")], "Note.\n")
        broken = first.replace(END + "\n", "")
        again = drift_issue.render([item("a")], broken)
        self.assertEqual(again.count(START), 1)
        self.assertEqual(again.count(END), 1)
        self.assertEqual(drift_issue.render([item("a")], again), again)

    def test_render_is_a_fixed_point(self):
        """Property, seeded: for random item sets, tick states, target moves
        and outside text, rendering the rendered body again changes
        nothing. That is what makes a second run write nothing."""
        rng = random.Random(20261114)
        for _ in range(200):
            ids = rng.sample(["a", "b/c", "d e", "f"], rng.randint(0, 4))
            items = [item(i, to=rng.choice(["1", "2"]),
                          detail=["x"] * rng.randint(0, 2))
                     for i in sorted(ids)]
            body = rng.choice([None, "", "top\n", "top\n\nmore\n"])
            body = drift_issue.render(items, body)
            for i in ids:
                if rng.random() < 0.5:
                    body = tick(body, i)
            if rng.random() < 0.3:
                body += "tail\n"
            moved = [dict(it, to=rng.choice(["1", "2", "3"]))
                     for it in items if rng.random() < 0.8]
            once = drift_issue.render(moved, body)
            self.assertEqual(drift_issue.render(moved, once), once)


# -------------------------------------------------------------- reconcile

class Reconcile(unittest.TestCase):
    def test_no_open_issue_creates_one_with_label(self):
        client = FakeClient(labels={"skill-drift"})
        action = drift_issue.reconcile(recorded_items(), client)
        self.assertEqual(action, "create")
        creates = [c for c in client.calls if c[0] == "create"]
        self.assertEqual(len(creates), 1)
        _, title, body, label = creates[0]
        self.assertEqual((title, label), ("Skill drift", "skill-drift"))
        self.assertEqual(body, drift_issue.render(recorded_items(), None))

    def test_label_created_if_missing(self):
        client = FakeClient()
        drift_issue.reconcile([item("a")], client)
        names = [c[0] for c in client.calls]
        self.assertLess(names.index("ensure_label"), names.index("create"))
        self.assertIn("skill-drift", client.labels)

    def test_existing_issue_updated_in_place(self):
        client = FakeClient(issues=[(7, "Note.\n")])
        action = drift_issue.reconcile([item("a")], client)
        self.assertEqual(action, "update")
        self.assertEqual([c[0] for c in client.writes()], ["update"])
        self.assertTrue(client.issues[7]["body"].startswith("Note.\n"))

    def test_idempotent_second_run_makes_no_write(self):
        client = FakeClient()
        drift_issue.reconcile(recorded_items(), client)
        client.issues[1]["body"] = tick(client.issues[1]["body"],
                                        "effect-v4/effect")
        drift_issue.reconcile(recorded_items(), client)  # keeps the tick
        client.calls.clear()
        action = drift_issue.reconcile(recorded_items(), client)
        self.assertEqual(action, "none")
        self.assertEqual(client.writes(), [])
        self.assertEqual(ticked(client.issues[1]["body"]),
                         {"effect-v4/effect"})

    def test_no_items_closes_open_issue(self):
        """D14."""
        client = FakeClient(issues=[(7, drift_issue.render([item("a")],
                                                           "Note.\n"))])
        action = drift_issue.reconcile([], client)
        self.assertEqual(action, "close")
        self.assertEqual([c[0] for c in client.writes()],
                         ["update", "close"])
        self.assertIn("No drift found.", client.issues[7]["body"])
        self.assertTrue(client.issues[7]["body"].startswith("Note.\n"))
        self.assertEqual(client.issues[7]["state"], "closed")

    def test_no_items_no_issue_does_nothing(self):
        client = FakeClient()
        self.assertEqual(drift_issue.reconcile([], client), "none")
        self.assertEqual(client.writes(), [])

    def test_two_open_drift_issues_fails(self):
        client = FakeClient(issues=[(3, ""), (9, "")])
        with self.assertRaises(drift_issue.WriterError) as caught:
            drift_issue.reconcile([item("a")], client)
        self.assertIn("#3", str(caught.exception))
        self.assertIn("#9", str(caught.exception))
        self.assertEqual(client.writes(), [])


# -------------------------------------------------------------------- CLI

class Cli(unittest.TestCase):
    def run_cli(self, path, client):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = drift_issue.main([str(path)], client=client)
        return code, out.getvalue(), err.getvalue()

    def test_recorded_drift_file_creates(self):
        client = FakeClient()
        code, out, _ = self.run_cli(FIXTURES / "drift.json", client)
        self.assertEqual((code, out.strip()), (0, "drift_issue: create"))

    def test_source_error_writes_nothing(self):
        """Review Focus 4: a missing or invalid drift.json must not read as
        'no drift' and close the issue."""
        bad = [None, "", "{", '{"version": 2, "items": []}',
               '{"version": 1}', '{"version": 1, "items": [{"id": "x"}]}',
               json.dumps({"version": 1, "items": [
                   dict(item("x"), kind="mystery")]}),
               json.dumps({"version": 1, "items": [
                   dict(item("x"), extra=1)]}),
               json.dumps({"version": 1, "items": [item("x"), item("x")]})]
        with tempfile.TemporaryDirectory() as room:
            for n, text in enumerate(bad):
                path = Path(room) / f"{n}.json"
                if text is not None:
                    path.write_text(text)
                client = FakeClient(issues=[(7, "x")])
                with self.subTest(text=text):
                    code, _, err = self.run_cli(path, client)
                    self.assertEqual(code, 1)
                    self.assertEqual(client.calls, [])
                    self.assertIn("drift_issue:", err)

    def test_two_open_issues_exit_1(self):
        client = FakeClient(issues=[(3, ""), (9, "")])
        code, _, err = self.run_cli(FIXTURES / "drift.json", client)
        self.assertEqual(code, 1)
        self.assertIn("#3", err)
        self.assertEqual(client.writes(), [])


# --------------------------------------------------------------- GhClient

class FakeRunner:
    def __init__(self, replies):
        self.replies = replies  # list of (argv prefix, stdout)
        self.calls = []

    def __call__(self, argv, stdin=None):
        self.calls.append((argv, stdin))
        for prefix, stdout in self.replies:
            if argv[:len(prefix)] == prefix:
                return stdout
        return ""


class Gh(unittest.TestCase):
    def client(self, replies=()):
        runner = FakeRunner(list(replies))
        return drift_issue.GhClient("o/r", run=runner), runner

    def test_find_open_skips_pull_requests(self):
        listing = (FIXTURES / "gh-issues-open.jsonl").read_text()
        gh, runner = self.client([(["gh", "api", "--paginate"], listing)])
        found = gh.find_open("skill-drift")
        self.assertEqual([i.number for i in found], [7])
        self.assertIn("Owner note.", found[0].body)
        argv = runner.calls[0][0]
        self.assertIn("repos/o/r/issues?state=open&labels=skill-drift"
                      "&per_page=100", argv)

    def test_find_open_normalizes_crlf(self):
        line = json.dumps({"number": 3, "body": "a\r\nb\rc\n"})
        gh, _ = self.client([(["gh", "api", "--paginate"], line + "\n")])
        self.assertEqual(gh.find_open("skill-drift")[0].body, "a\nb\nc\n")

    def test_writes_send_json_on_stdin(self):
        gh, runner = self.client([(["gh", "api"], '{"number": 12}')])
        self.assertEqual(gh.create("Skill drift", "B", "skill-drift"), 12)
        gh.update(12, "C")
        gh.close(12, "done")
        sent = [(c[0], json.loads(c[1])) for c in runner.calls]
        self.assertEqual(sent[0][0][-4:], ["-X", "POST", "--input", "-"])
        self.assertIn("repos/o/r/issues", sent[0][0])
        self.assertEqual(sent[0][1], {"title": "Skill drift", "body": "B",
                                      "labels": ["skill-drift"]})
        self.assertIn("repos/o/r/issues/12", sent[1][0])
        self.assertEqual(sent[1][1], {"body": "C"})
        self.assertIn("repos/o/r/issues/12/comments", sent[2][0])
        self.assertEqual(sent[2][1], {"body": "done"})
        self.assertEqual(sent[3][1], {"state": "closed",
                                      "state_reason": "completed"})

    def test_ensure_label_creates_only_when_missing(self):
        labels = (FIXTURES / "gh-labels.txt").read_text()
        gh, runner = self.client([(["gh", "api", "--paginate"], labels)])
        gh.ensure_label("skill-drift", "d4c5f9", "d")
        self.assertEqual(len(runner.calls), 2)
        self.assertEqual(json.loads(runner.calls[1][1]),
                         {"name": "skill-drift", "color": "d4c5f9",
                          "description": "d"})
        gh, runner = self.client([(["gh", "api", "--paginate"],
                                   labels + "skill-drift\n")])
        gh.ensure_label("skill-drift", "d4c5f9", "d")
        self.assertEqual(len(runner.calls), 1)


# --------------------------------------------------------------- workflow

class Workflow(unittest.TestCase):
    """A line-level reading of skill-drift.yml (no YAML parser in the
    stdlib). Blind spot: YAML it does not model, such as flow-style
    permissions or anchors, would need a hand review, so the test also
    refuses the characters those forms need."""

    PATH = HERE.parent / ".github" / "workflows" / "skill-drift.yml"

    UPLOAD = ("actions/upload-artifact@"
              "cf430e030ddbb5b0abf93d22962f4752f3646cd9 # v7.0.2")
    DOWNLOAD = ("actions/download-artifact@"
                "9000827ccba6bdab643e8b6fd33ac0654aef8333 # v8.0.2")
    CHECKOUT = ("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
                " # v7.0.1")

    def jobs(self, lines):
        """name -> its lines, for the two-space job keys under jobs:."""
        at = lines.index("jobs:")
        jobs, name = {}, None
        for line in lines[at + 1:]:
            if line.startswith("  ") and not line.startswith("   ") and \
                    line.endswith(":"):
                name = line.strip()[:-1]
                jobs[name] = []
            elif line and not line.startswith(" "):
                break
            elif name:
                jobs[name].append(line)
        return jobs

    def block(self, lines, header):
        """The stripped lines indented under header (exact line)."""
        at = lines.index(header)
        indent = len(header) - len(header.lstrip()) + 2
        out = []
        for line in lines[at + 1:]:
            if not line.startswith(" " * indent):
                break
            out.append(line.strip())
        return out

    def test_permissions_and_triggers(self):
        """Detection, which reads upstream content, holds no write token;
        the job that writes the issue gets the artifact and no network
        reads beyond GitHub."""
        lines = self.PATH.read_text().split("\n")
        self.assertEqual([l for l in lines if "permissions" in l],
                         ["permissions: {}", "    permissions:",
                          "    permissions:"])
        jobs = self.jobs(lines)
        self.assertEqual(list(jobs), ["detect", "issue"])
        detect, issue = jobs["detect"], jobs["issue"]
        self.assertEqual(self.block(detect, "    permissions:"),
                         ["contents: read"])
        self.assertEqual(self.block(issue, "    permissions:"),
                         ["contents: read", "issues: write"])
        self.assertIn("    needs: detect", issue)
        detect_text, issue_text = "\n".join(detect), "\n".join(issue)
        self.assertIn("scripts/detect_drift.py", detect_text)
        self.assertNotIn("drift_issue.py", detect_text)
        self.assertNotIn("GH_TOKEN", detect_text)
        self.assertIn("scripts/drift_issue.py", issue_text)
        self.assertNotIn("detect_drift.py", issue_text)
        self.assertNotIn("GITHUB_TOKEN", issue_text)
        self.assertEqual([l.strip() for l in detect if "uses:" in l],
                         ["- uses: " + self.CHECKOUT,
                          "- uses: " + self.UPLOAD])
        self.assertEqual([l.strip() for l in issue if "uses:" in l],
                         ["- uses: " + self.CHECKOUT,
                          "- uses: " + self.DOWNLOAD])
        self.assertEqual(issue_text.count("persist-credentials: false"), 1)
        self.assertEqual(detect_text.count("persist-credentials: false"), 1)
        self.assertIn('    - cron: "17 6 1 * *"', lines)
        self.assertIn("  workflow_dispatch: {}", lines)
        text = self.PATH.read_text()
        for absent in ("secrets.", "write-all", "&", "*", "pull_request"):
            self.assertNotIn(absent, text.replace('"17 6 1 * *"', ""))


# ----------------------------------------------------------------- mutant

class CheckerMutant(unittest.TestCase):
    """Each mutant restores a defect; the suite must fail on every one."""

    MUTANTS = [
        ("previous ticks ignored", "ticked = old.ticked", "ticked = False"),
        ("tick kept when target moves", "if old.to != to:", "if False:"),
        ("text outside region dropped", "body = head + region + tail",
         "body = region"),
        ("timestamp in body", 'lines = [START, NOTE, ""]',
         'lines = [START, NOTE, str(__import__("time").time()), ""]'),
        ("no drift leaves the issue open", "client.close(issue.number",
         "(lambda *a: None)(issue.number"),
        ("second open issue ignored", "if len(issues) > 1:",
         "if len(issues) > 99:"),
        ("unknown kind accepted", 'if entry["kind"] not in KINDS:',
         "if False:"),
    ]

    @unittest.skipIf("DRIFT_ISSUE_PATH" in os.environ,
                     "already running a mutant")
    def test_each_mutant_fails_the_suite(self):
        source = (HERE / "drift_issue.py").read_text(encoding="utf-8")
        for name, old, new in self.MUTANTS:
            with self.subTest(mutant=name), \
                    tempfile.TemporaryDirectory() as room:
                self.assertEqual(source.count(old), 1, name)
                broken = Path(room) / "drift_issue.py"
                broken.write_text(source.replace(old, new), encoding="utf-8")
                done = subprocess.run(
                    [sys.executable, "-m", "unittest", "test_drift_issue"],
                    cwd=HERE, capture_output=True, text=True,
                    env={**os.environ, "DRIFT_ISSUE_PATH": str(broken)})
                self.assertNotEqual(done.returncode, 0, name)


if __name__ == "__main__":
    unittest.main()
