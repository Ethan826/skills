#!/usr/bin/env python3
"""Turn detect_drift.py's output into one GitHub issue labeled skill-drift.

Usage: python3 scripts/drift_issue.py DRIFT_JSON [--repo OWNER/REPO]
(--repo defaults to $GITHUB_REPOSITORY; gh reads $GH_TOKEN). Prints
"drift_issue: <action>" with action none, create, update or close; exits 1
on an unreadable or invalid DRIFT_JSON, on two or more open skill-drift
issues, or on a failed gh call, and in the first two cases before any
GitHub call.

The issue body: text outside the region between START and END below is the
owner's and is kept byte for byte. Inside it, one checklist line per item,

  - [ ] **<name>** (<kind>): <from> -> <to>. [<label>](<link>) <!-- key:<id> to:<to> -->

<name> is the skill, or the item id when it differs (a skill with several
tool anchors has one line per package); a name with any character outside
[A-Za-z0-9._/ -] is shown in a code span, since upstream directory names
reach it. <label> is "diff" for a GitHub compare link and "link"
otherwise (a release page, a repository); an item whose link is null
(unregistered, a release without a page) has no link.

followed by the item's detail lines, each indented and in a code span (so
upstream commit subjects cannot @-mention anyone or close the region). id
and to are percent-encoded in the key comment, since ids may hold spaces.

Reconciliation (plan D12 to D14):
- A tick is read from the previous body by key, wherever the line sits in
  the region. It is kept while the item's to is unchanged. When to changes,
  a ticked line is unticked and notes "(approval cleared: target moved from
  <old> to <new>)" (the key comment records cleared:<old>, so the note
  survives later runs); an unticked line just takes the new target. When
  the owner ticks the line again at that target, the note and cleared:
  go: the tick is a fresh approval.
- The body is read with CRLF and CR line endings turned into LF (GitHub's
  web editor can send CRLF back).
- An item detection no longer reports is dropped with its tick. That
  includes an item the owner declined in anchors.json (D13): detection
  skips a declined (id, to) until upstream moves past it.
- No items: an open issue gets "No drift found." in its region and is
  closed (D14); with no open issue nothing happens.
- render() is a fixed point: rendering its own output with the same items
  returns it unchanged. There are no timestamps. So a second run with the
  same detection result and the same issue makes no API write.
- Region markers missing or unbalanced (the owner edited them): the old
  text is kept with stray markers removed, ticks are read from all of it,
  and a fresh region is appended.
- Two or more open skill-drift issues: exit 1 naming them; the writer does
  not guess which one is the issue.

Blind spots: the owner's edits inside the region are replaced (only ticks
are read back); a key comment the owner deletes loses that line's tick;
GitHub's rendering of the body is not checked; GhClient is tested against
recorded response shapes, not the live API.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, Optional, Protocol
from urllib.parse import quote, unquote

TITLE = "Skill drift"
LABEL = "skill-drift"
LABEL_COLOR = "d4c5f9"
LABEL_DESCRIPTION = "Monthly skill drift report (scripts/drift_issue.py)"
START = "<!-- skill-drift:start -->"
END = "<!-- skill-drift:end -->"
NOTE = ("Tick an item to approve that update; an agent asked to do the "
        "approved skill updates works through the ticked items with the "
        "skill-update skill. To decline an item, record it under `declined` "
        "in anchors.json (anchor id, `to`, reason); detection then skips it "
        "until upstream moves past that target. A tick is cleared when an "
        "item's target moves.")
NO_DRIFT = "No drift found."
CLOSE_COMMENT = ("No drift found; closing. The next run opens a new issue "
                 "if drift appears.")
KINDS = ("fork", "vendored", "installed", "tool", "new-upstream-skill",
         "unregistered", "anchor-missing")
ITEM_KEYS = {"id", "skill", "kind", "from", "to", "link", "detail"}
KEY_LINE = re.compile(r"^- \[([ xX])\] .*<!-- key:(\S+) to:(\S*)"
                      r"(?: cleared:(\S*))? -->[ \t]*$")
SAFE = "/@.+_~-"
SAFE_NAME = re.compile(r"[A-Za-z0-9._/ -]+")
# GitHub refuses an issue body over 65,536 characters; a long upstream
# history is cut to this many detail lines per item.
MAX_DETAIL = 20
MAX_BODY = 65536


class WriterError(Exception):
    pass


class GhError(WriterError):
    pass


class Issue(NamedTuple):
    number: int
    body: str


class Tick(NamedTuple):
    ticked: bool
    to: str
    cleared: Optional[str]


class IssueClient(Protocol):
    def find_open(self, label: str) -> list: ...
    def create(self, title: str, body: str, label: str) -> int: ...
    def update(self, number: int, body: str) -> None: ...
    def close(self, number: int, comment: str) -> None: ...
    def ensure_label(self, name: str, color: str,
                     description: str) -> None: ...


# ----------------------------------------------------------------- input

def load_items(path: Path) -> list:
    """Validated items from a detect_drift.py file, or WriterError."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise WriterError(f"cannot read {path}: {error}") from None
    if not isinstance(data, dict) or data.get("version") != 1 or \
            set(data) != {"version", "items"} or \
            not isinstance(data["items"], list):
        raise WriterError(f"{path}: not a version 1 drift file")
    seen = set()
    for n, entry in enumerate(data["items"]):
        where = f"{path}: item {n}"
        if not isinstance(entry, dict) or set(entry) != ITEM_KEYS:
            raise WriterError(f"{where}: keys must be {sorted(ITEM_KEYS)}")
        for key in ("id", "skill", "link"):
            if key == "link" and entry[key] is None:
                continue
            if not isinstance(entry[key], str) or not entry[key] or \
                    "\n" in entry[key]:
                raise WriterError(f"{where}: {key} must be a one-line string"
                                  + (" or null" if key == "link" else ""))
        if entry["kind"] not in KINDS:
            raise WriterError(f"{where}: unknown kind {entry['kind']!r}")
        for key in ("from", "to"):
            if entry[key] is not None and not isinstance(entry[key], str):
                raise WriterError(f"{where}: {key} must be a string or null")
        if not isinstance(entry["detail"], list) or \
                not all(isinstance(d, str) for d in entry["detail"]):
            raise WriterError(f"{where}: detail must be a list of strings")
        if entry["id"] in seen:
            raise WriterError(f"{where}: duplicate id {entry['id']!r}")
        seen.add(entry["id"])
    return data["items"]


# ---------------------------------------------------------------- render

def encode(value: Optional[str]) -> str:
    return quote(value or "", safe=SAFE)


def display(value: Optional[str]) -> str:
    return "none" if value is None else plain(value)


def plain(text: str) -> str:
    """One line with no HTML comment delimiters."""
    text = " ".join(text.split())
    return text.replace("<!--", "<!- -").replace("-->", "- ->")


def code_span(text: str) -> str:
    return "`" + plain(text).replace("`", "'") + "`"


def name_text(name: str) -> str:
    """A skill name or item id as shown. Upstream directory names reach
    here (new-upstream-skill), so anything outside SAFE_NAME goes in a
    code span, where GitHub renders no mention, link or HTML."""
    return plain(name) if SAFE_NAME.fullmatch(name) else code_span(name)


def normalize(body: str) -> str:
    """LF line endings; GitHub's web editor can return CRLF."""
    return body.replace("\r\n", "\n").replace("\r", "\n")


def split(body: str):
    """(head, region, tail, balanced). Unbalanced: head is the whole body
    with stray markers removed, region and tail empty."""
    body = normalize(body)
    if body.count(START) == 1 and body.count(END) == 1 and \
            body.index(START) < body.index(END):
        start, end = body.index(START), body.index(END) + len(END)
        tail = body[end:]
        if tail.startswith("\n"):
            tail = tail[1:]
        return body[:start], body[start:end], tail, True
    head = body
    for marker in (START, END):
        head = head.replace(marker + "\n", "").replace(marker, "")
    return head, "", "", False


def parse_ticks(body: str) -> dict:
    """id -> Tick for each keyed checklist line; the region only when it
    is intact, else the whole body. The first line for a key wins."""
    _, region, _, balanced = split(body)
    body = normalize(body)
    ticks = {}
    for line in (region if balanced else body).split("\n"):
        found = KEY_LINE.match(line)
        if found:
            key = unquote(found.group(2))
            cleared = found.group(4)
            ticks.setdefault(key, Tick(
                found.group(1) != " ", unquote(found.group(3)),
                None if cleared is None else unquote(cleared)))
    return ticks


def render_item(entry: dict, old: Optional[Tick]) -> list:
    to = entry["to"] or ""
    ticked, cleared = False, None
    if old is not None:
        ticked = old.ticked
        cleared = old.cleared
        if old.to != to:
            cleared = old.to if ticked else None
            ticked = False
        elif ticked:
            cleared = None  # re-ticked at this target: a fresh approval
    note = ""
    key = f"key:{encode(entry['id'])} to:{encode(to)}"
    if cleared is not None:
        note = (f" (approval cleared: target moved from "
                f"{display(cleared or None)} to {display(entry['to'])})")
        key += f" cleared:{encode(cleared)}"
    link, label, shown = "", "link", ""
    if entry["link"] is not None:
        link = quote(entry["link"], safe=":/?#[]@!$&'*+,;=%.~-_")
        label = "diff" if "/compare/" in link else "link"
        shown = f" [{label}]({link})"
    name = entry["skill"] if entry["id"] == entry["skill"] else entry["id"]
    lines = [f"- [{'x' if ticked else ' '}] **{name_text(name)}** "
             f"({entry['kind']}): {display(entry['from'])} -> "
             f"{display(entry['to'])}.{shown}{note} "
             f"<!-- {key} -->"]
    detail = entry["detail"]
    lines += [f"  - {code_span(d)}" for d in detail[:MAX_DETAIL]]
    if len(detail) > MAX_DETAIL:
        lines.append(f"  - and {len(detail) - MAX_DETAIL} more; see the "
                     f"{label}")
    return lines


def render(items: list, previous_body: Optional[str]) -> str:
    """The issue body for items, keeping the owner's text and ticks.
    WriterError when the body would exceed GitHub's limit."""
    head, _, tail, balanced = split(previous_body or "")
    if not balanced and head:
        head = head if head.endswith("\n") else head + "\n"
        head += "\n"
    ticks = parse_ticks(previous_body or "")
    if items:
        lines = [START, NOTE, ""]
        for entry in sorted(items, key=lambda e: e["id"]):
            lines += render_item(entry, ticks.get(entry["id"]))
        lines.append(END)
    else:
        lines = [START, NO_DRIFT, END]
    region = "\n".join(lines) + "\n"
    body = head + region + tail
    if len(body) > MAX_BODY:
        raise WriterError(f"issue body would be {len(body)} characters, "
                          f"over GitHub's {MAX_BODY}")
    return body


# ------------------------------------------------------------- reconcile

def reconcile(items: list, client: IssueClient) -> str:
    issues = client.find_open(LABEL)
    if len(issues) > 1:
        numbers = ", ".join(f"#{i.number}" for i in issues)
        raise WriterError(f"{len(issues)} open {LABEL} issues ({numbers}); "
                          "close all but one by hand")
    issue = issues[0] if issues else None
    if not items:
        if issue is None:
            return "none"
        body = render([], issue.body)
        if body != issue.body:
            client.update(issue.number, body)
        client.close(issue.number, CLOSE_COMMENT)
        return "close"
    if issue is None:
        body = render(items, None)
        client.ensure_label(LABEL, LABEL_COLOR, LABEL_DESCRIPTION)
        client.create(TITLE, body, LABEL)
        return "create"
    body = render(items, issue.body)
    if body == issue.body:
        return "none"
    client.update(issue.number, body)
    return "update"


# -------------------------------------------------------------- GitHub

def run_gh(argv: list, stdin: Optional[str] = None) -> str:
    done = subprocess.run(argv, input=stdin, capture_output=True, text=True)
    if done.returncode != 0:
        raise GhError(f"{' '.join(argv[:3])} failed: {done.stderr.strip()}")
    return done.stdout


class GhClient:
    """IssueClient over the gh CLI (token from $GH_TOKEN)."""

    def __init__(self, repo: str, run=run_gh):
        self.repo = repo
        self.run = run

    def send(self, path: str, method: str, payload: dict) -> str:
        return self.run(["gh", "api", f"repos/{self.repo}/{path}",
                         "-X", method, "--input", "-"], json.dumps(payload))

    def find_open(self, label: str) -> list:
        out = self.run(["gh", "api", "--paginate",
                        f"repos/{self.repo}/issues?state=open&labels="
                        f"{quote(label, safe='')}&per_page=100",
                        "--jq", ".[]"])
        found = []
        for line in out.splitlines():
            if line.strip():
                entry = json.loads(line)
                if not entry.get("pull_request"):
                    found.append(Issue(entry["number"],
                                       normalize(entry.get("body") or "")))
        return sorted(found, key=lambda i: i.number)

    def create(self, title: str, body: str, label: str) -> int:
        out = self.send("issues", "POST", {"title": title, "body": body,
                                           "labels": [label]})
        return json.loads(out)["number"]

    def update(self, number: int, body: str) -> None:
        self.send(f"issues/{number}", "PATCH", {"body": body})

    def close(self, number: int, comment: str) -> None:
        self.send(f"issues/{number}/comments", "POST", {"body": comment})
        self.send(f"issues/{number}", "PATCH",
                  {"state": "closed", "state_reason": "completed"})

    def ensure_label(self, name: str, color: str, description: str) -> None:
        out = self.run(["gh", "api", "--paginate",
                        f"repos/{self.repo}/labels?per_page=100",
                        "--jq", ".[].name"])
        if name not in out.splitlines():
            self.send("labels", "POST", {"name": name, "color": color,
                                         "description": description})


# ------------------------------------------------------------------- CLI

def main(argv=None, client: Optional[IssueClient] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("drift_json", type=Path)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    args = parser.parse_args(argv)
    try:
        items = load_items(args.drift_json)
        if client is None:
            if not args.repo:
                raise WriterError("no --repo and no $GITHUB_REPOSITORY")
            client = GhClient(args.repo)
        action = reconcile(items, client)
    except WriterError as error:
        print(f"drift_issue: {error}", file=sys.stderr)
        return 1
    print(f"drift_issue: {action}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
