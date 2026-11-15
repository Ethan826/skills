#!/usr/bin/env python3
"""Flag AI-writing tells by span. Standard library only, Python 3.9 or later.

A finding is a candidate for an auditor to judge, not proof of AI authorship.
Exit codes: 0 nothing blocking, 1 blocking findings, 2 could not check.

Blind spots: this is a text check that over-matches on purpose inside the
scope of its word and phrase lists. It cannot see meaning, so it misses a
tell spelled in a way the rules do not list, and everything marked
"**Lint:** none" in references/researched-tells.md. An empty result means
only that the listed spellings are absent, so an auditor still has to read it.
"""
import argparse
import json
import re
import statistics
import sys
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parent / "tell_rules.json"
REQUIRED = ("id", "tier", "ref", "pattern", "probes", "near_misses")
PARTICIPIAL = re.compile(
    r",\s+(?!including\b|according\b|during\b|following\b|regarding\b"
    r"|concerning\b|pending\b)[a-z]+ing\b(?!,| and\b| or\b)")


class LintError(Exception):
    """The check could not run, which is never the same as a clean result."""


def load_rules(path=RULES_PATH):
    try:
        rules = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LintError("cannot load rules from %s: %s" % (path, error))
    if not isinstance(rules, list) or not rules:
        raise LintError("no rules in %s" % path)
    for rule in rules:
        missing = [key for key in REQUIRED if key not in rule]
        if missing:
            raise LintError("rule %s lacks %s" % (rule.get("id"), ", ".join(missing)))
        if rule["tier"] not in ("strong", "weak"):
            raise LintError("rule %s has unknown tier" % rule["id"])
        flags = re.MULTILINE | (0 if rule.get("case") else re.IGNORECASE)
        try:
            rule["regex"] = re.compile(rule["pattern"], flags)
        except re.error as error:
            raise LintError("rule %s has a bad pattern: %s" % (rule["id"], error))
    return rules


def blank(match):
    return re.sub(r"[^\n]", " ", match.group(0))


def mask(text, plain=False, spans=True):
    """Blank what is not prose, keeping every offset and line number.

    spans=False keeps inline code visible, for rules whose tell is what the
    prose says about a code span (a "code" rule); fences stay blank.
    """
    text = re.sub(r"\A---\n.*?\n---\n", blank, text, flags=re.S)
    if not plain:
        text = re.sub(r"^(```|~~~)[^\n]*\n.*?^\1[ \t]*$", blank, text, flags=re.S | re.M)
        if spans:
            text = re.sub(r"`[^`\n]+`", blank, text)
    return re.sub(r"\bhttps?://[^\s)>\]]+", blank, text)


def isbn_valid(raw):
    digits = re.sub(r"[ -]", "", raw).upper()
    if len(digits) == 13 and digits.isdigit():
        total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
        return total % 10 == 0
    if len(digits) == 10 and digits[:9].isdigit() and re.match(r"[0-9X]$", digits[9]):
        values = [10 if d == "X" else int(d) for d in digits]
        return sum(v * (10 - i) for i, v in enumerate(values)) % 11 == 0
    return False


def paragraph_of(text, offset):
    return len(re.findall(r"\n[ \t]*\n", text[:offset]))


def is_quoted(text, offset):
    start = text.rfind("\n", 0, offset) + 1
    before = text[start:offset]
    return before.lstrip().startswith(">") or len(re.findall("[\"“”]", before)) % 2 == 1


def find(text, masked, rule, spans_visible=None):
    source = text if rule.get("raw") else masked
    if rule.get("code"):
        source = spans_visible
    for match in rule["regex"].finditer(source):
        if rule.get("kind") == "isbn" and isbn_valid(match.group(1)):
            continue
        start = match.start()
        line_start = text.rfind("\n", 0, start) + 1
        yield {
            "rule": rule["id"], "tier": rule["tier"], "ref": rule["ref"],
            "line": text.count("\n", 0, start) + 1, "col": start - line_start + 1,
            "text": match.group(0).strip(), "paragraph": paragraph_of(text, start),
            "quoted": is_quoted(text, start), "offset": start,
        }


def line_text(text, finding):
    return text.split("\n")[finding["line"] - 1]


def apply_keep(text, findings, keep):
    """Take kept findings out of the running. Every entry must be used in full."""
    kept = []
    for entry in keep:
        if not entry.get("rule") or not entry.get("reason") or not (
                entry.get("all") or (entry.get("text") and entry.get("count"))):
            raise LintError("keep entry needs rule, reason, and text with count or all")
        matches = [f for f in findings if f["rule"] == entry["rule"] and (
            entry.get("all") or entry["text"] in line_text(text, f))]
        wanted = len(matches) if entry.get("all") else entry["count"]
        if not matches or len(matches) < wanted:
            raise LintError("keep entry matches nothing, or fewer than its count: %s"
                            % json.dumps(entry))
        for finding in matches[:wanted]:
            findings.remove(finding)
            kept.append(dict(finding, reason=entry["reason"]))
    return kept


def choose_blocking(findings):
    """A strong tell blocks alone; a weak one needs a different tell beside it."""
    live = [f for f in findings if not f["quoted"]]
    company = {}
    for finding in live:
        company.setdefault(finding["paragraph"], set()).add(finding["rule"])
    blocking = []
    for finding in live:
        if finding["tier"] == "strong" or len(company[finding["paragraph"]]) > 1:
            blocking.append(finding)
    return blocking


def metrics(masked):
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", masked)
    sentences = [s for s in re.split(r"[.!?]+(?:\s+|$)", masked) if re.search(r"\w", s)]
    lengths = [len(re.findall(r"\w+", s)) for s in sentences]
    paragraphs = [len(re.findall(r"\w+", p)) for p in re.split(r"\n\s*\n", masked)
                  if re.search(r"\w", p)]

    def per_1000(count):
        return round(1000 * count / len(words), 1) if words else 0.0

    return {
        "words": len(words), "sentences": len(sentences),
        "sentence_length_mean": round(statistics.mean(lengths), 1) if lengths else 0.0,
        "sentence_length_stdev": round(statistics.pstdev(lengths), 1) if lengths else 0.0,
        "paragraph_length_stdev": round(statistics.pstdev(paragraphs), 1) if paragraphs else 0.0,
        "participial_per_1000_words": per_1000(len(PARTICIPIAL.findall(masked))),
        "commas_per_1000_words": per_1000(masked.count(",")),
        "parentheses_per_1000_words": per_1000(masked.count("(")),
    }


def scan(text, plain=False, keep=(), rules=None):
    rules = load_rules() if rules is None else rules
    masked = mask(text, plain)
    spans_visible = mask(text, plain, spans=False)
    findings = []
    for rule in rules:
        if rule.get("plain") and not plain:
            continue
        findings.extend(find(text, masked, rule, spans_visible))
    findings.sort(key=lambda f: (f["offset"], f["rule"]))
    kept = apply_keep(text, findings, keep)
    return {
        "findings": findings, "kept": kept, "metrics": metrics(masked),
        "blocking": choose_blocking(findings),
    }


def read_text(path):
    try:
        data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    except OSError as error:
        raise LintError("cannot read %s: %s" % (path, error))
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise LintError("%s is not UTF-8" % path)


def read_keep(path):
    if not path:
        return []
    try:
        return json.loads(read_text(path))
    except ValueError as error:
        raise LintError("bad keep file %s: %s" % (path, error))


def render(path, result):
    blocking = {id(f) for f in result["blocking"]}
    lines = []
    for finding in result["findings"]:
        state = "BLOCK" if id(finding) in blocking else "note "
        lines.append("%s:%d:%d %s %s [%s] %s" % (
            path, finding["line"], finding["col"], state, finding["rule"],
            finding["ref"], finding["text"]))
    for finding in result["kept"]:
        lines.append("%s:%d kept  %s: %s" % (
            path, finding["line"], finding["rule"], finding["reason"]))
    lines.append("%d findings, %d blocking, %d kept, %d words scanned" % (
        len(result["findings"]), len(result["blocking"]), len(result["kept"]),
        result["metrics"]["words"]))
    lines.append("metrics (report only): " + json.dumps(result["metrics"]))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Flag AI-writing tells by span.")
    parser.add_argument("path", help="file to check, or - for standard input")
    parser.add_argument("--plain", action="store_true",
                        help="the target is plain text, so markdown syntax is a tell")
    parser.add_argument("--keep", help="JSON list of reviewed, pinned exceptions")
    parser.add_argument("--rules", default=RULES_PATH, help=argparse.SUPPRESS)
    parser.add_argument("--report", action="store_true", help="always exit 0 after checking")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        rules = load_rules(args.rules)
        text = read_text(args.path)
        result = scan(text, args.plain, read_keep(args.keep), rules)
        if result["metrics"]["words"] == 0:
            raise LintError("no prose to check in %s" % args.path)
    except LintError as error:
        print("tell_lint: %s" % error, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2) if args.json else render(args.path, result))
    return 0 if args.report or not result["blocking"] else 1


if __name__ == "__main__":
    sys.exit(main())
