#!/usr/bin/env python3
"""Registration and consistency gate for anchors.json.

anchors.json records what every skill under skills/ is anchored to: an
upstream fork, a vendored file, tool versions, an unmodified install, or
nothing. This gate fails when the record and the repository disagree.
It decides from parsed input only: the directory listing, anchors.json,
the first paragraph of each NOTICE.md (a fixed grammar), the table in
THIRD_PARTY.md, and each skill's "## Versions" table. Markdown headings,
tables and fenced code follow the CommonMark rules for ATX headings and
fences; text inside a fence neither trips nor satisfies a rule.

Usage: python3 scripts/anchors_gate.py [--root DIR]
Exit 0 prints "anchors gate: N skills, M anchors, OK". Exit 1 prints one
"CODE subject: message" line per finding.

Rules:
1. Every entry under skills/ is a directory with SKILL.md
   (NOT_A_SKILL_DIR) and has an anchor that is not "installed"
   (UNREGISTERED). An empty skills/ fails (SCHEMA).
2. Every non-installed anchor names an existing skill (NO_SUCH_SKILL); an
   installed anchor must not collide with a local skill (SCHEMA).
3. A "none" entry is its skill's only entry, and the skill has no
   Versions section, no NOTICE.md and no THIRD_PARTY.md row
   (NONE_FORBIDDEN).
4. fork and vendored entries agree with NOTICE.md and THIRD_PARTY.md in
   both directions (NOTICE_MISMATCH, NOTICE_UNPARSEABLE,
   THIRD_PARTY_MISMATCH). Files keep 7-character SHAs; anchors.json keeps
   40, and the short form must be a prefix.
5. A tool entry's check directory has an executable run.sh
   (CHECK_MISSING); the skill's Versions table has the entry's row with
   the entry's version as its first token (VERSIONS_MISMATCH); every
   Versions row has a tool entry (VERSIONS_UNANCHORED).
6. Schema: required and allowed keys by kind, 40-hex commits, unique ids
   (SCHEMA, DUPLICATE_ID). A decline naming an anchor states `to` in the
   form detection writes: 7 lowercase hex for fork, vendored and
   installed anchors, a SemVer version for tool anchors (SCHEMA).
7. Every workflow line whose first token is "uses:" or "- uses:" names an
   action pinned to a 40-hex commit or a local ./ path (UNPINNED_ACTION).
   This is a text check that over-matches within .github/workflows: a
   "uses:" line inside a block scalar is also checked. It cannot miss a
   step written in block style.

Blind spots (no gate here can see these):
- whether an anchor is true, for example that a fork really came from
  the recorded commit;
- whether a check exercises its skill's claims;
- version strings in descriptions, README rows and prose outside a
  Versions table (effect-v4's "Checked against effect 4.1.1", the prose
  version mentions in skills registered as "none");
- NOTICE.md text after its first paragraph;
- installed entries against the owner's real skills lock, which is not in
  this repository;
- a workflow's permissions block, and actions written in YAML flow style
  ({uses: ...}); there is no YAML parser in the standard library.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Optional

KINDS = ("fork", "vendored", "tool", "installed", "none")
REQUIRED = {
    "fork": {"id", "skill", "kind", "repo", "path", "commit", "release"},
    "vendored": {"id", "skill", "kind", "repo", "path", "local", "version",
                 "commit"},
    "tool": {"id", "skill", "kind", "ecosystem", "package", "version", "row",
             "check"},
    "installed": {"id", "skill", "kind", "repo", "path", "folderHash"},
    "none": {"id", "skill", "kind", "reason"},
}
OPTIONAL = {
    "fork": set(),
    "vendored": {"tag"},
    "tool": set(),
    "installed": {"commit", "basis"},
    "none": set(),
}
ECOSYSTEMS = ("npm", "github-release", "purescript-package-set",
              "purescript-package")
DECLINE_SHAPES = ({"repo", "path", "reason"}, {"anchor", "to", "reason"})

HEX40 = re.compile(r"[0-9a-f]{40}")
SHORT_SHA = re.compile(r"[0-9a-f]{7,40}")
SHORT_SHA7 = re.compile(r"[0-9a-f]{7}")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")
SKILL_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
RELEASE = re.compile(r"v\d+\.\d+\.\d+")
VERSION = re.compile(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?")
CHECK_PATH = re.compile(r"checks/[A-Za-z0-9_.-]+")
PINNED_ACTION = re.compile(
    r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^@\s]+)?@[0-9a-f]{40}")


class GateError(Exception):
    def __init__(self, code: str, subject: str, message: str):
        super().__init__(f"{code} {subject}: {message}")
        self.code = code
        self.subject = subject
        self.message = message


class Finding(NamedTuple):
    code: str
    subject: str
    message: str

    def __str__(self) -> str:
        return f"{self.code} {self.subject}: {self.message}"


@dataclass
class Anchors:
    anchors: list
    declined: list


@dataclass
class NoticeFacts:
    name: str
    repo: str
    commit: Optional[str] = None
    release: Optional[str] = None
    local: Optional[str] = None
    version: Optional[str] = None


@dataclass
class ThirdPartyRow:
    skill: str
    repo: str
    local: Optional[str] = None
    name: Optional[str] = None
    commit: Optional[str] = None
    version: Optional[str] = None


# ---------------------------------------------------------------- Markdown

def opening_fence(line: str):
    """Return (char, length) when the line opens a CommonMark fence."""
    match = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
    if not match:
        return None
    run, info = match.group(1), match.group(2)
    if run[0] == "`" and "`" in info:
        return None
    return run[0], len(run)


def closes_fence(line: str, fence) -> bool:
    char, length = fence
    match = re.match(r"^ {0,3}(`+|~+)[ \t]*$", line)
    return bool(match) and match.group(1)[0] == char and \
        len(match.group(1)) >= length


def unfenced_lines(text: str) -> list:
    """Each line with a flag: True when it is outside every fenced block."""
    marked = []
    fence = None
    for line in text.splitlines():
        if fence is None:
            fence = opening_fence(line)
            marked.append((line, fence is None))
        else:
            if closes_fence(line, fence):
                fence = None
            marked.append((line, False))
    return marked


def atx_heading(line: str):
    """Return (level, text) for a CommonMark ATX heading, else None."""
    match = re.match(r"^ {0,3}(#{1,6})(?:[ \t]+(.*))?$", line)
    if not match:
        return None
    content = (match.group(2) or "").rstrip(" \t")
    if re.fullmatch(r"#+", content):
        content = ""
    content = re.sub(r"[ \t]+#+$", "", content).strip(" \t")
    return len(match.group(1)), content


def is_versions_heading(line: str) -> bool:
    heading = atx_heading(line)
    return heading is not None and heading == (2, "Versions")


def versions_heading_count(text: str) -> int:
    return sum(1 for line, outside in unfenced_lines(text)
               if outside and is_versions_heading(line))


def split_cells(line: str) -> list:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", body)]


DELIMITER = re.compile(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$")


def tables(lines: list) -> list:
    """Tables among (line, outside) pairs: lists of rows of cells."""
    found = []
    index = 0
    while index + 1 < len(lines):
        line, outside = lines[index]
        after, after_outside = lines[index + 1]
        if outside and after_outside and "|" in line and \
                DELIMITER.match(after.strip()):
            rows = [split_cells(line)]
            index += 2
            while index < len(lines) and lines[index][1] and \
                    "|" in lines[index][0] and lines[index][0].strip():
                rows.append(split_cells(lines[index][0]))
                index += 1
            found.append(rows)
        else:
            index += 1
    return found


def versions_rows(text: str):
    """Body rows of every table in the level-2 Versions section(s).

    None when the skill has no Versions section.
    """
    marked = unfenced_lines(text)
    rows = None
    section = None
    for line, outside in marked + [("", True)]:
        heading = atx_heading(line) if outside else None
        if heading is not None and heading[0] <= 2 and section is not None:
            rows.extend(r for t in tables(section) for r in t[1:])
            section = None
        if outside and is_versions_heading(line):
            rows = rows if rows is not None else []
            section = []
        elif section is not None:
            section.append((line, outside))
    if section is not None:
        rows.extend(r for t in tables(section) for r in t[1:])
    return rows


def parse_versions_table(skill_md: str):
    rows = versions_rows(skill_md)
    if rows is None:
        return None
    return {row[0]: (row[1] if len(row) > 1 else "") for row in rows}


# ------------------------------------------------------------------ NOTICE

NOTICE_TOKEN = re.compile(
    r"`(?P<code>[^`]+)`"
    r"|\[(?P<text>[^\]]+)\]\((?P<url>[^)\s]+)\)"
    r"|\((?P<release>v\d+\.\d+\.\d+)\)"
    r"|\bversion (?P<version>\d+\.\d+\.\d+)\b")
NOTICE_GRAMMAR = {
    "fork": ["code", "link", "code", "release"],
    "vendored": ["code", "code", "link", "version"],
}


def first_paragraph(text: str) -> str:
    marked = unfenced_lines(text)
    for index, (line, outside) in enumerate(marked):
        if outside and atx_heading(line) == (1, "Notice"):
            paragraph = []
            for body, body_outside in marked[index + 1:]:
                if not body.strip():
                    if paragraph:
                        break
                    continue
                if not body_outside or atx_heading(body):
                    break
                paragraph.append(body.strip())
            if paragraph:
                return " ".join(paragraph)
            break
    raise GateError("NOTICE_UNPARSEABLE", "?",
                    "no paragraph under a '# Notice' heading")


def parse_notice(text: str, kind: str) -> NoticeFacts:
    """Parse a NOTICE.md first paragraph under the fixed grammar (D10)."""
    paragraph = first_paragraph(text)
    tokens = []
    for match in NOTICE_TOKEN.finditer(paragraph):
        if match.group("code") is not None:
            tokens.append(("code", match.group("code")))
        elif match.group("text") is not None:
            tokens.append(("link", (match.group("text"), match.group("url"))))
        elif match.group("release") is not None:
            tokens.append(("release", match.group("release")))
        else:
            tokens.append(("version", match.group("version")))
    shape = [kind_ for kind_, _ in tokens]
    if shape != NOTICE_GRAMMAR[kind]:
        raise GateError("NOTICE_UNPARSEABLE", "?",
                        f"first paragraph has {shape}, want "
                        f"{NOTICE_GRAMMAR[kind]} for a {kind} entry")
    link_text, url = next(value for k, value in tokens if k == "link")
    if not REPO.fullmatch(link_text) or \
            url != f"https://github.com/{link_text}":
        raise GateError("NOTICE_UNPARSEABLE", "?",
                        f"link [{link_text}]({url}) is not "
                        "[owner/repo](https://github.com/owner/repo)")
    values = [value for _, value in tokens]
    if kind == "fork":
        if not SHORT_SHA.fullmatch(values[2]):
            raise GateError("NOTICE_UNPARSEABLE", "?",
                            f"commit `{values[2]}` is not a hex SHA")
        return NoticeFacts(name=values[0], repo=link_text, commit=values[2],
                           release=values[3])
    return NoticeFacts(local=values[0], name=values[1], repo=link_text,
                       version=values[3])


# ------------------------------------------------------------- THIRD_PARTY

THIRD_PARTY_HEADER = ["Skill", "Derived from", "Upstream license"]
SKILL_CELL = re.compile(r"(\S+)(?:\s+\(`([^`]+)`\))?")
FORK_CELL = re.compile(
    r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+) `([^`]+)` @ `([0-9a-f]{7,40})`"
    r"(?:\s+\(.*\))?")
VENDORED_CELL = re.compile(
    r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+) (\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)")


def parse_third_party(text: str) -> dict:
    candidates = [t for t in tables(unfenced_lines(text))
                  if t[0][:3] == THIRD_PARTY_HEADER]
    if len(candidates) != 1:
        raise GateError("THIRD_PARTY_MISMATCH", "THIRD_PARTY.md",
                        f"want one table headed {THIRD_PARTY_HEADER}, "
                        f"found {len(candidates)}")
    rows = {}
    for cells in candidates[0][1:]:
        first = cells[0].split()[0] if cells[0].split() else "?"
        skill_match = SKILL_CELL.fullmatch(cells[0])
        derived = cells[1] if len(cells) > 1 else ""
        fork = FORK_CELL.fullmatch(derived)
        vendored = VENDORED_CELL.fullmatch(derived)
        if not skill_match or not (fork or vendored):
            raise GateError("THIRD_PARTY_MISMATCH", first,
                            f"row does not parse: {' | '.join(cells)}")
        if first in rows:
            raise GateError("THIRD_PARTY_MISMATCH", first, "duplicate row")
        if fork:
            rows[first] = ThirdPartyRow(
                skill=first, local=skill_match.group(2), repo=fork.group(1),
                name=fork.group(2), commit=fork.group(3))
        else:
            rows[first] = ThirdPartyRow(
                skill=first, local=skill_match.group(2),
                repo=vendored.group(1), version=vendored.group(2))
    return rows


# ------------------------------------------------------------- anchors.json

def validate_anchor(entry) -> None:
    subject = entry.get("id", "anchors.json") if isinstance(entry, dict) \
        else "anchors.json"
    if not isinstance(subject, str):
        subject = "anchors.json"
    if not isinstance(entry, dict):
        raise GateError("SCHEMA", subject, "an anchor must be an object")
    kind = entry.get("kind")
    if kind not in KINDS:
        raise GateError("SCHEMA", subject, f"kind {kind!r} not in {KINDS}")
    keys = set(entry)
    missing = REQUIRED[kind] - keys
    unknown = keys - REQUIRED[kind] - OPTIONAL[kind]
    if missing:
        raise GateError("SCHEMA", subject,
                        f"{kind} entry lacks {sorted(missing)}")
    if unknown:
        raise GateError("SCHEMA", subject,
                        f"unknown keys for {kind}: {sorted(unknown)}")
    for key, value in entry.items():
        empty_ok = kind == "installed" and key == "path"
        if not isinstance(value, str) or (not value and not empty_ok):
            raise GateError("SCHEMA", subject, f"{key} must be a string")
    patterns = {"skill": SKILL_NAME, "repo": REPO, "commit": HEX40,
                "folderHash": HEX40, "release": RELEASE}
    if kind in ("vendored", "tool"):
        patterns["version"] = VERSION
    if kind == "tool":
        patterns["check"] = CHECK_PATH
    for key, pattern in patterns.items():
        if key in entry and not pattern.fullmatch(entry[key]):
            raise GateError("SCHEMA", subject,
                            f"{key} {entry[key]!r} does not match "
                            f"{pattern.pattern}")
    if kind == "tool" and entry["ecosystem"] not in ECOSYSTEMS:
        raise GateError("SCHEMA", subject,
                        f"ecosystem {entry['ecosystem']!r} not in "
                        f"{ECOSYSTEMS}")


def load_anchors(path: Path) -> Anchors:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GateError("SCHEMA", "anchors.json", f"cannot read: {error}")
    if not isinstance(data, dict) or \
            set(data) != {"version", "anchors", "declined"}:
        raise GateError("SCHEMA", "anchors.json",
                        "top level must have exactly version, anchors, "
                        "declined")
    if data["version"] != 1:
        raise GateError("SCHEMA", "anchors.json", "version must be 1")
    if not isinstance(data["anchors"], list) or \
            not isinstance(data["declined"], list):
        raise GateError("SCHEMA", "anchors.json",
                        "anchors and declined must be lists")
    seen = {}
    for entry in data["anchors"]:
        validate_anchor(entry)
        if entry["id"] in seen:
            raise GateError("DUPLICATE_ID", entry["id"], "id used twice")
        seen[entry["id"]] = entry["kind"]
    for decline in data["declined"]:
        if not isinstance(decline, dict) or \
                set(decline) not in DECLINE_SHAPES or \
                not all(isinstance(v, str) and v for v in decline.values()):
            raise GateError("SCHEMA", "declined",
                            f"entry {decline!r} must have exactly "
                            "repo, path, reason or anchor, to, reason")
        if "anchor" in decline and decline["anchor"] not in seen:
            raise GateError("SCHEMA", "declined",
                            f"names unknown anchor {decline['anchor']!r}")
        if "anchor" in decline:
            # Detection writes to as 7 lowercase hex (fork, vendored,
            # installed) or a SemVer version (tool); a decline in any other
            # form never matches an item, so it would silently decline
            # nothing.
            kind = seen[decline["anchor"]]
            pattern = VERSION if kind == "tool" else SHORT_SHA7
            if not pattern.fullmatch(decline["to"]):
                raise GateError("SCHEMA", "declined",
                                f"{decline['anchor']!r}: to "
                                f"{decline['to']!r} must match "
                                f"{pattern.pattern} for a {kind} anchor")
    return Anchors(anchors=data["anchors"], declined=data["declined"])


# ------------------------------------------------------------------- checks

def skill_directories(root: Path, findings: list) -> list:
    skills_dir = root / "skills"
    entries = sorted(skills_dir.iterdir()) if skills_dir.is_dir() else []
    if not entries:
        findings.append(Finding("SCHEMA", "skills", "no skills found"))
    names = []
    for entry in entries:
        if not (entry / "SKILL.md").is_file():
            findings.append(Finding(
                "NOT_A_SKILL_DIR", entry.name,
                "every entry under skills/ must be a directory with SKILL.md"))
            continue
        names.append(entry.name)
    return names


def check_notice(root: Path, entry: dict, findings: list) -> None:
    skill = entry["skill"]
    notice = root / "skills" / skill / "NOTICE.md"
    if not notice.is_file():
        findings.append(Finding("NOTICE_MISMATCH", skill,
                                f"{entry['kind']} entry but no NOTICE.md"))
        return
    try:
        facts = parse_notice(notice.read_text(encoding="utf-8"),
                             entry["kind"])
    except GateError as error:
        findings.append(Finding(error.code, skill, error.message))
        return
    wrong = []
    if facts.repo != entry["repo"]:
        wrong.append(f"repo {facts.repo} != {entry['repo']}")
    if entry["kind"] == "fork":
        if facts.name != entry["path"].rsplit("/", 1)[-1]:
            wrong.append(f"upstream name `{facts.name}` != {entry['path']}")
        if not entry["commit"].startswith(facts.commit):
            wrong.append(f"commit `{facts.commit}` is not a prefix of "
                         f"{entry['commit']}")
        if facts.release != entry["release"]:
            wrong.append(f"release {facts.release} != {entry['release']}")
    else:
        if facts.local != entry["local"]:
            wrong.append(f"local `{facts.local}` != {entry['local']}")
        if facts.name != entry["path"]:
            wrong.append(f"upstream file `{facts.name}` != {entry['path']}")
        if facts.version != entry["version"]:
            wrong.append(f"version {facts.version} != {entry['version']}")
    for message in wrong:
        findings.append(Finding("NOTICE_MISMATCH", skill, message))


def check_third_party_row(entry: dict, row, findings: list) -> None:
    skill = entry["skill"]
    if row is None:
        findings.append(Finding("THIRD_PARTY_MISMATCH", skill,
                                f"{entry['kind']} entry but no "
                                "THIRD_PARTY.md row"))
        return
    wrong = []
    if row.repo != entry["repo"]:
        wrong.append(f"repo {row.repo} != {entry['repo']}")
    if entry["kind"] == "fork":
        if row.commit is None:
            wrong.append("row is not a fork row")
        else:
            if row.name != entry["path"].rsplit("/", 1)[-1]:
                wrong.append(f"upstream name `{row.name}` != {entry['path']}")
            if not entry["commit"].startswith(row.commit):
                wrong.append(f"commit `{row.commit}` is not a prefix of "
                             f"{entry['commit']}")
    else:
        if row.version != entry["version"]:
            wrong.append(f"version {row.version} != {entry['version']}")
        if row.local != entry["local"]:
            wrong.append(f"local `{row.local}` != {entry['local']}")
    for message in wrong:
        findings.append(Finding("THIRD_PARTY_MISMATCH", skill, message))


def check_tool(root: Path, entry: dict, table, findings: list) -> None:
    skill = entry["skill"]
    run = root / entry["check"] / "run.sh"
    if not (run.is_file() and os.access(run, os.X_OK)):
        findings.append(Finding("CHECK_MISSING", skill,
                                f"{entry['check']}/run.sh is missing or not "
                                "executable"))
    if table is None:
        findings.append(Finding("VERSIONS_MISMATCH", skill,
                                f"no '## Versions' section for "
                                f"{entry['row']}"))
        return
    if entry["row"] not in table:
        findings.append(Finding("VERSIONS_MISMATCH", skill,
                                f"Versions table has no row {entry['row']!r}"))
        return
    tokens = table[entry["row"]].split()
    stated = tokens[0] if tokens else ""
    if stated != entry["version"]:
        findings.append(Finding("VERSIONS_MISMATCH", skill,
                                f"{entry['row']}: table says {stated!r}, "
                                f"anchors.json says {entry['version']!r}"))


def check_skill(root: Path, skill: str, entries: list, third_party: dict,
                findings: list) -> None:
    text = (root / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    rows = versions_rows(text)
    table = parse_versions_table(text)
    local = [e for e in entries if e["kind"] != "installed"]
    kinds = [e["kind"] for e in local]
    if not local:
        findings.append(Finding("UNREGISTERED", skill,
                                "no entry in anchors.json"))
        return
    if versions_heading_count(text) > 1:
        findings.append(Finding("VERSIONS_MISMATCH", skill,
                                "more than one '## Versions' section"))
    if rows is not None and len(table) != len(rows):
        findings.append(Finding("VERSIONS_MISMATCH", skill,
                                "a Versions row label appears twice"))
    has_notice = (root / "skills" / skill / "NOTICE.md").is_file()
    if "none" in kinds:
        forbidden_reasons = []
        if len(kinds) > 1:
            forbidden_reasons.append("a none entry must be the only entry")
        if rows is not None:
            forbidden_reasons.append("the skill has a '## Versions' section")
        if has_notice:
            forbidden_reasons.append("the skill has a NOTICE.md")
        if skill in third_party:
            forbidden_reasons.append("the skill has a THIRD_PARTY.md row")
        if forbidden_reasons:
            for reason in forbidden_reasons:
                findings.append(Finding("NONE_FORBIDDEN", skill, reason))
    upstream = [e for e in local if e["kind"] in ("fork", "vendored")]
    if len(upstream) > 1:
        findings.append(Finding("SCHEMA", skill,
                                "more than one fork or vendored entry"))
    if has_notice and not upstream:
        findings.append(Finding("NOTICE_MISMATCH", skill,
                                "NOTICE.md without a fork or vendored "
                                "entry"))
    for entry in upstream:
        if entry["kind"] == "vendored" and \
                not (root / "skills" / skill / entry["local"]).is_file():
            findings.append(Finding("SCHEMA", skill,
                                    f"vendored file {entry['local']} "
                                    "does not exist"))
        check_notice(root, entry, findings)
        check_third_party_row(entry, third_party.get(skill), findings)
    tools = [e for e in local if e["kind"] == "tool"]
    tool_rows = [e["row"] for e in tools]
    for row in sorted({r for r in tool_rows if tool_rows.count(r) > 1}):
        findings.append(Finding("SCHEMA", skill,
                                f"two tool entries name row {row!r}"))
    for entry in tools:
        check_tool(root, entry, table, findings)
    for label in sorted(table or {}):
        if label not in tool_rows:
            findings.append(Finding("VERSIONS_UNANCHORED", skill,
                                    f"Versions row {label!r} has no tool "
                                    "entry"))


def check_workflow_pins(root: Path) -> list:
    findings = []
    workflows = root / ".github" / "workflows"
    files = sorted(list(workflows.glob("*.yml")) +
                   list(workflows.glob("*.yaml"))) \
        if workflows.is_dir() else []
    for path in files:
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines, start=1):
            match = re.match(r"^\s*(?:-\s+)?uses:\s*(.*)$", line)
            if not match:
                continue
            value = re.sub(r"\s+#.*$", "", match.group(1)).strip()
            value = value.strip("'\"")
            if value.startswith("./") or PINNED_ACTION.fullmatch(value):
                continue
            findings.append(Finding(
                "UNPINNED_ACTION", rel,
                f"line {number}: {value!r} is not pinned to a 40-hex "
                "commit"))
    return findings


def check_repo(root: Path) -> list:
    findings = []
    names = skill_directories(root, findings)
    findings.extend(check_workflow_pins(root))
    try:
        anchors = load_anchors(root / "anchors.json")
    except GateError as error:
        findings.append(Finding(error.code, error.subject, error.message))
        return findings
    third_party = {}
    third_party_path = root / "THIRD_PARTY.md"
    if third_party_path.is_file():
        try:
            third_party = parse_third_party(
                third_party_path.read_text(encoding="utf-8"))
        except GateError as error:
            findings.append(Finding(error.code, error.subject,
                                    error.message))
    by_skill = {}
    for entry in anchors.anchors:
        local = entry["kind"] != "installed"
        if local and entry["skill"] not in names:
            findings.append(Finding("NO_SUCH_SKILL", entry["skill"],
                                    f"anchor {entry['id']} names no skill "
                                    "directory"))
            continue
        if not local and (root / "skills" / entry["skill"]).exists():
            findings.append(Finding("SCHEMA", entry["id"],
                                    f"installed skill {entry['skill']} "
                                    "collides with a local skill"))
            continue
        by_skill.setdefault(entry["skill"], []).append(entry)
    for skill in names:
        check_skill(root, skill, by_skill.get(skill, []), third_party,
                    findings)
    upstream_skills = {e["skill"] for e in anchors.anchors
                       if e["kind"] in ("fork", "vendored")}
    for skill in sorted(set(third_party) - upstream_skills):
        findings.append(Finding("THIRD_PARTY_MISMATCH", skill,
                                "THIRD_PARTY.md row with no fork or vendored "
                                "entry"))
    return findings


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args(argv)
    findings = check_repo(args.root)
    if findings:
        for finding in sorted(set(findings)):
            print(finding)
        return 1
    names = sorted(p.name for p in (args.root / "skills").iterdir())
    count = len(load_anchors(args.root / "anchors.json").anchors)
    print(f"anchors gate: {len(names)} skills, {count} anchors, OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
