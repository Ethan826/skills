#!/usr/bin/env python3
"""Keep the record of a review loop and decide when it ends.

The agent runs the audits and rewrites. This script refuses audits it cannot
tie to the current text or to a new auditor, reruns the lint, compares facts
with the round-0 source, and states the verdict, so a loop cannot end on the
writer's own say-so.
Exit codes: 0 CLEAN, 1 CONTINUE, 2 could not record, 3 stopped without CLEAN.

Blind spots: the fact floor sees numbers, URLs, code spans and mid-sentence
capitalized words, not changed meaning, so an auditor still compares the
claims. Auditor names are self-reported, so the script can catch a reused
name but cannot prove the agent behind a new name had no context.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tell_lint  # noqa: E402

RECURRENCE_LIMIT = 3


class LoopError(Exception):
    """The round could not be recorded."""


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def new_state(source, max_rounds=5, keep=(), plain=False):
    return {"source": source, "max_rounds": max_rounds, "keep": list(keep),
            "plain": plain, "rounds": [], "ended": None}


def facts(text):
    urls = [u.rstrip(".,;:") for u in re.findall(r"\bhttps?://[^\s)>\]]+", text)]
    code = re.findall(r"`[^`\n]+`", text)
    rest = re.sub(r"\bhttps?://[^\s)>\]]+|`[^`\n]+`", " ", text)
    numbers = re.findall(r"(?<![\w.])\d(?:[\d,.]*\d)?(?!\w)", rest)
    names = re.findall(r"(?<=[a-z,;:] )[A-Z][A-Za-z0-9]+(?!\w)", rest)
    return list(dict.fromkeys(urls + code + numbers + names))


def fact_floor(source, text):
    """Items in the source that no longer appear in the text."""
    return [item for item in facts(source)
            if not re.search(r"(?<!\w)" + re.escape(item) + r"(?!\w)", text)]


def locate(text, span):
    """Where a span starts, ignoring line wraps. An auditor quotes a sentence
    on one line even when the file wraps it."""
    pattern = r"\s+".join(re.escape(word) for word in span.split())
    match = re.search(pattern, text)
    return match.start() if match else None


def check_audit(state, text, audit):
    if not isinstance(audit, dict) or not all(
            key in audit for key in ("text_sha256", "auditor", "findings")):
        raise LoopError("audit needs text_sha256, auditor and findings")
    if audit["text_sha256"] != sha(text):
        raise LoopError("audit is of another text")
    if any(r["auditor"] == audit["auditor"] for r in state["rounds"]):
        raise LoopError("auditor %s already read this loop; use a fresh one"
                        % audit["auditor"])
    for finding in audit["findings"]:
        if not isinstance(finding, dict):
            raise LoopError("finding must be an object: %s" % json.dumps(finding))
        if finding.get("tier") not in ("strong", "weak"):
            raise LoopError("finding has unknown tier: %s" % json.dumps(finding))
        if not finding.get("pattern") or not finding.get("span"):
            raise LoopError("finding needs span and pattern: %s" % json.dumps(finding))
        if locate(text, finding["span"]) is None:
            raise LoopError("span not in text: %s" % finding["span"])
    for loss in audit.get("accepted_losses", []):
        if not isinstance(loss, dict) or not loss.get("item") or not loss.get("reason"):
            raise LoopError("accepted loss needs item and reason: %s" % json.dumps(loss))


def blocking_audit(text, findings):
    """The lint's rule, applied to the auditor's findings."""
    company = {}
    for finding in findings:
        paragraph = tell_lint.paragraph_of(text, locate(text, finding["span"]))
        company.setdefault(paragraph, set()).add(finding["pattern"])
    return [f for f in findings if f["tier"] == "strong" or len(
        company[tell_lint.paragraph_of(text, locate(text, f["span"]))]) > 1]


def decide(state, this_round):
    earlier = state["rounds"]
    if not (this_round["lint_blocking"] or this_round["audit_blocking"]
            or this_round["lost"]):
        return "CLEAN"
    if any(r["text_sha256"] == this_round["text_sha256"] for r in earlier):
        return "STOP_OSCILLATION"
    for finding in this_round["audit_blocking"]:
        key = [finding["pattern"], finding["span"]]
        seen = sum(key in r["audit_keys"] for r in earlier) + 1
        if seen >= RECURRENCE_LIMIT:
            return "STOP_RECURRING"
    if len(earlier) + 1 >= state["max_rounds"]:
        return "STOP_CAP"
    return "CONTINUE"


def reopen(state):
    """One more round after CLEAN, against the same source and auditors. A
    stopped loop stays stopped, so this cannot be used to get past a cap."""
    if state["ended"] != "CLEAN":
        raise LoopError("only a CLEAN loop can be reopened")
    state["ended"] = None
    state["max_rounds"] = max(state["max_rounds"], len(state["rounds"]) + 1)


def record(state, text, audit, keep=None):
    if state["ended"]:
        raise LoopError("loop already ended: %s; use reopen after CLEAN" % state["ended"])
    check_audit(state, text, audit)
    if keep is not None:
        state["keep"] = keep
    lint = tell_lint.scan(text, state["plain"], state["keep"])
    accepted = {loss["item"] for r in state["rounds"] for loss in r["accepted_losses"]}
    accepted |= {loss["item"] for loss in audit.get("accepted_losses", [])}
    blocking = blocking_audit(text, audit["findings"])
    this_round = {
        "round": len(state["rounds"]) + 1, "auditor": audit["auditor"],
        "text_sha256": sha(text), "findings": audit["findings"],
        "accepted_losses": audit.get("accepted_losses", []),
        "lint_blocking": [f["rule"] for f in lint["blocking"]],
        "audit_blocking": blocking,
        "audit_keys": [[f["pattern"], f["span"]] for f in blocking],
        "lost": [item for item in fact_floor(state["source"], text)
                 if item not in accepted],
    }
    this_round["verdict"] = decide(state, this_round)
    state["rounds"].append(this_round)
    if this_round["verdict"] != "CONTINUE":
        state["ended"] = this_round["verdict"]
    return this_round


def load_json(path, label):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LoopError("cannot read %s %s: %s" % (label, path, error))


def report(this_round):
    print("round %d: %s" % (this_round["round"], this_round["verdict"]))
    for rule in this_round["lint_blocking"]:
        print("  lint: %s" % rule)
    for finding in this_round["audit_blocking"]:
        print("  audit: %s: %s" % (finding["pattern"], finding["span"]))
    for item in this_round["lost"]:
        print("  lost from source: %s" % item)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="snapshot the source before any rewrite")
    init.add_argument("--state", required=True)
    init.add_argument("--text", required=True)
    init.add_argument("--max-rounds", type=int, default=5)
    init.add_argument("--keep")
    init.add_argument("--plain", action="store_true")
    step = commands.add_parser("record", help="record one audit and print the verdict")
    step.add_argument("--state", required=True)
    step.add_argument("--text", required=True)
    step.add_argument("--audit", required=True)
    step.add_argument("--keep", help="the user's reviewed keep list, replacing any earlier one")
    again = commands.add_parser("reopen", help="allow one more round after CLEAN")
    again.add_argument("--state", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "reopen":
            state = load_json(args.state, "state")
            reopen(state)
            Path(args.state).write_text(json.dumps(state, indent=2), encoding="utf-8")
            print("loop reopened at round %d" % (len(state["rounds"]) + 1))
            return 0
        text = tell_lint.read_text(args.text)
        if args.command == "init":
            if Path(args.state).exists():
                raise LoopError("state already exists: %s" % args.state)
            state = new_state(text, args.max_rounds, tell_lint.read_keep(args.keep),
                              args.plain)
            Path(args.state).write_text(json.dumps(state, indent=2), encoding="utf-8")
            print("loop started; text sha256 %s" % sha(text))
            return 0
        state = load_json(args.state, "state")
        keep = tell_lint.read_keep(args.keep) if args.keep else None
        this_round = record(state, text, load_json(args.audit, "audit"), keep)
        Path(args.state).write_text(json.dumps(state, indent=2), encoding="utf-8")
    except (LoopError, tell_lint.LintError) as error:
        print("clean_loop: %s" % error, file=sys.stderr)
        return 2
    report(this_round)
    verdict = this_round["verdict"]
    return 0 if verdict == "CLEAN" else 1 if verdict == "CONTINUE" else 3


if __name__ == "__main__":
    sys.exit(main())
