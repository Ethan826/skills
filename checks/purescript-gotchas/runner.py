#!/usr/bin/env python3
"""Compile one small module set per purescript-gotchas claim and check the result.

run.sh installs the pinned toolchain into a throwaway directory and calls
`runner.py run`. Each case in cases.json lists the exact compiler errors
and warnings it expects (code, module, optionally line and message
fragments); an empty list means none. A case passes only when the
diagnostics match those lists exactly, as multisets. The decision rests
on errorCode, moduleName and the start line in purs's --json-errors
output; a message fragment that no longer appears is reported as
"wording changed", a separate failure class, because the skill quotes
the compiler. Some cases also run the compiled program with node or
call `purs graph` (the case's "run" entry).

Version check: purs --version, spago --version and spago.lock's package
set and package versions must equal the skill's Versions table (parsed
with the anchors gate's own parser) and every anchors.json tool entry
for this check.

Blind spots: see README.md.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
CHECK = "checks/purescript-gotchas"
CASE_KEYS = {"name", "claim", "section", "errors", "warnings", "run",
             "codeGuessed", "control"}
REQUIRED_CASE_KEYS = {"name", "claim", "section", "errors", "warnings"}
DIAGNOSTIC_KEYS = {"code", "module", "line", "includes"}
LOCKED_PACKAGES = ("prelude", "quickcheck", "quickcheck-laws", "js-bigints",
                   "bigints")
NOT_EXERCISED = ("purs-tidy",)


class CheckError(Exception):
    pass


class Diagnostic(NamedTuple):
    code: str
    message: str
    module: str
    line: int
    filename: str = ""


class Outcome(NamedTuple):
    status: str
    errors: list
    warnings: list


# ---------------------------------------------------------------- manifest

def load_cases(path: Path) -> list:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CheckError(f"{path}: cannot read: {error}")
    if not isinstance(data, dict) or data.get("version") != 1 or \
            not isinstance(data.get("cases"), list) or \
            set(data) != {"version", "expectedCases", "cases"}:
        raise CheckError(f"{path}: want {{\"version\": 1, \"expectedCases\""
                         f": N, \"cases\": [...]}}")
    cases = data["cases"]
    if not cases:
        raise CheckError(f"{path}: no cases")
    # The count is pinned: a case removed together with its directory
    # still passes the inventory check below, so only this catches it.
    # Change expectedCases only with the owner's approval.
    expected = data["expectedCases"]
    if type(expected) is not int or len(cases) != expected:
        raise CheckError(f"{path}: {len(cases)} cases, expectedCases says "
                         f"{expected!r}")
    names = []
    for item in cases:
        if not isinstance(item, dict):
            raise CheckError(f"{path}: case is not an object: {item!r}")
        unknown = set(item) - CASE_KEYS
        missing = REQUIRED_CASE_KEYS - set(item)
        label = item.get("name", "?")
        if unknown or missing:
            raise CheckError(f"case {label}: unknown keys {sorted(unknown)}, "
                             f"missing keys {sorted(missing)}")
        for want in item["errors"] + item["warnings"]:
            bad = set(want) - DIAGNOSTIC_KEYS
            if bad or "code" not in want or "module" not in want:
                raise CheckError(f"case {label}: diagnostic {want!r} needs "
                                 "code and module, allows line and includes")
        names.append(item["name"])
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise CheckError(f"{path}: duplicate case names {duplicates}")
    case_dir = Path(path).parent / "cases"
    dirs = sorted(p.name for p in case_dir.iterdir()) \
        if case_dir.is_dir() else []
    unlisted = sorted(set(dirs) - set(names))
    absent = sorted(set(names) - set(dirs))
    if unlisted or absent:
        raise CheckError(f"cases/ and cases.json disagree: directories not "
                         f"in cases.json {unlisted}, cases with no "
                         f"directory {absent}")
    for name in names:
        if not list((case_dir / name).glob("*.purs")):
            raise CheckError(f"case {name}: no .purs files")
    return cases


# ------------------------------------------------------- compiler output

def parse_compiler_output(text: str) -> dict:
    """The JSON object purs --json-errors prints on stdout."""
    lines = [line for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.lstrip().startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                break
    raise CheckError("compiler output is not JSON: " + text[:300])


def diagnostics(items) -> list:
    found = []
    for item in items:
        position = item.get("position") or {}
        found.append(Diagnostic(item["errorCode"], item.get("message", ""),
                                item.get("moduleName") or "",
                                position.get("startLine", 0),
                                item.get("filename") or ""))
    return found


def classify(result_json: dict) -> Outcome:
    if not isinstance(result_json, dict) or \
            not isinstance(result_json.get("errors"), list) or \
            not isinstance(result_json.get("warnings"), list):
        raise CheckError("compiler JSON lacks errors and warnings lists")
    errors = diagnostics(result_json["errors"])
    warnings = diagnostics(result_json["warnings"])
    return Outcome("error" if errors else "ok", errors, warnings)


MODULE_HEADER = re.compile(r"^module\s+([A-Z][\w.]*)", re.MULTILINE)


def fill_modules(outcome: Outcome, base: Path) -> Outcome:
    """Name the module of diagnostics where purs leaves moduleName null.

    purs 0.15.16 does so for parse errors, MissingClassMember and
    NonAssociativeError; the module is then read from the file's header.
    """
    def fill(found: Diagnostic) -> Diagnostic:
        if found.module or not found.filename:
            return found
        path = Path(found.filename)
        path = path if path.is_absolute() else base / path
        try:
            header = MODULE_HEADER.search(path.read_text(encoding="utf-8"))
        except OSError:
            return found
        return found._replace(module=header.group(1)) if header else found
    return Outcome(outcome.status, [fill(d) for d in outcome.errors],
                   [fill(d) for d in outcome.warnings])


def flat(text: str) -> str:
    return " ".join(text.split())


def same_place(want: dict, got: Diagnostic) -> bool:
    return got.code == want["code"] and got.module == want["module"] and \
        ("line" not in want or got.line == want["line"])


def describe(want: dict) -> str:
    where = want["module"] + (f":{want['line']}" if "line" in want else "")
    return f"{want['code']} at {where}"


def check_kind(name: str, kind: str, wanted: list, got: list) -> list:
    problems = []
    remaining = list(got)
    for want in wanted:
        match = next((d for d in remaining if same_place(want, d)), None)
        if match is None:
            found = ", ".join(f"{d.code} at {d.module}:{d.line}"
                              for d in got) or "none"
            problems.append(f"case {name}: wanted {kind} {describe(want)}, "
                            f"got {found}")
            continue
        remaining.remove(match)
        for fragment in want.get("includes", []):
            if flat(fragment) not in flat(match.message):
                problems.append(
                    f"case {name}: wording changed: {kind} {describe(want)} "
                    f"no longer includes {fragment!r}; message: "
                    f"{flat(match.message)!r}")
    for extra in remaining:
        problems.append(f"case {name}: unexpected {kind} {extra.code} at "
                        f"{extra.module}:{extra.line}: "
                        f"{flat(extra.message)[:300]}")
    return problems


def check_case(case: dict, outcome: Outcome) -> list:
    """Problems with outcome against case; empty when it matches."""
    return check_kind(case["name"], "error", case["errors"],
                      outcome.errors) + \
        check_kind(case["name"], "warning", case["warnings"],
                   outcome.warnings)


# ---------------------------------------------------------- run outputs

def check_run_output(spec: dict, data: dict) -> list:
    """Problems with a program's JSON report against a named assertion."""
    kind = spec.get("assert")
    if kind == "fraction-bands":
        # Each band names the report keys whose fraction must lie in
        # [low, high]. An empty band list or band would pass vacuously.
        if not spec.get("bands"):
            raise CheckError("fraction-bands with no bands")
        problems = []
        for band in spec["bands"]:
            if not band.get("keys"):
                raise CheckError("fraction-bands band with no keys")
            for key in band["keys"]:
                if key not in data:
                    problems.append(f"no fraction for {key}")
                elif not band["low"] <= data[key] <= band["high"]:
                    problems.append(f"{key}: fraction {data[key]} outside "
                                    f"[{band['low']:.4f}, "
                                    f"{band['high']:.4f}]")
        return problems
    if kind == "unit-interval-sample":
        problems = []
        if data.get("count") != spec["count"]:
            problems.append(f"sampled {data.get('count')}, "
                            f"wanted {spec['count']}")
        if data.get("outside") != 0:
            problems.append(f"{data.get('outside')} values outside [0, 1)")
        if not (0 <= data.get("min", -1) < 0.01):
            problems.append(f"min {data.get('min')} not in [0, 0.01)")
        if not (0.99 < data.get("max", 2) < 1):
            problems.append(f"max {data.get('max')} not in (0.99, 1)")
        return problems
    raise CheckError(f"unknown run assertion {kind!r}")


# ---------------------------------------------------------------- versions

def versions_table(repo: Path) -> dict:
    sys.path.insert(0, str(repo / "scripts"))
    try:
        from anchors_gate import parse_versions_table
    finally:
        sys.path.pop(0)
    text = (repo / "skills" / "purescript-gotchas" / "SKILL.md").read_text(
        encoding="utf-8")
    table = parse_versions_table(text)
    if not table:
        raise CheckError("purescript-gotchas SKILL.md has no Versions table")
    return table


def load_anchor_entries(repo: Path) -> list:
    data = json.loads((repo / "anchors.json").read_text(encoding="utf-8"))
    return [e for e in data["anchors"]
            if e.get("kind") == "tool" and e.get("check") == CHECK]


def stated(table: dict, row: str):
    if row not in table:
        return None
    tokens = table[row].split()
    return tokens[0] if tokens else ""


def check_versions(versions_table: dict, spago_lock: dict,
                   tool_versions: dict, anchors=None) -> list:
    """Disagreements between the observed toolchain and the stated pins."""
    observed = dict(tool_versions)
    try:
        observed["registry package set"] = \
            spago_lock["workspace"]["package_set"]["address"]["registry"]
    except (KeyError, TypeError):
        observed["registry package set"] = None
    packages = spago_lock.get("packages", {})
    for name in LOCKED_PACKAGES:
        observed[name] = (packages.get(name) or {}).get("version")
    problems = []
    for row, actual in observed.items():
        want = stated(versions_table, row)
        if want is None:
            problems.append(f"Versions table has no row {row!r}")
        elif actual != want:
            problems.append(f"{row}: observed {actual!r}, Versions table "
                            f"says {want!r}")
    for entry in anchors or []:
        row = entry.get("row")
        if row in NOT_EXERCISED:
            continue
        if row not in observed:
            problems.append(f"anchors.json row {row!r} is not checked here")
        elif observed[row] != entry.get("version"):
            problems.append(f"{row}: observed {observed[row]!r}, "
                            f"anchors.json says {entry.get('version')!r}")
    return problems


# ---------------------------------------------------------------- running

def command(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def first_line(args: list, cwd: Path) -> str:
    result = command(args, cwd)
    if result.returncode != 0:
        raise CheckError(f"{' '.join(args)} failed: {result.stderr[:300]}")
    return result.stdout.strip().split()[0]


def dependency_sources(project: Path) -> list:
    result = command(["spago", "sources"], project)
    if result.returncode != 0:
        raise CheckError(f"spago sources failed: {result.stderr[:300]}")
    globs = [line.strip() for line in result.stdout.splitlines()
             if line.strip().startswith(".spago/")]
    if len(globs) < 10:
        raise CheckError(f"spago sources listed {len(globs)} package globs")
    return [str(project / g) for g in globs]


def run_node(case: dict, out: Path) -> list:
    spec = case["run"]
    entry = (out / spec["module"] / "index.js").as_uri()
    script = f"import {{ main }} from '{entry}'; main();"
    result = command(["node", "--input-type=module", "-e", script], out)
    name = case["name"]
    if spec["assert"] == "exits-zero":
        return [] if result.returncode == 0 else \
            [f"case {name}: program exited {result.returncode}: "
             f"{result.stderr[-500:]}"]
    if spec["assert"] == "fails-with":
        problems = [] if result.returncode != 0 else \
            [f"case {name}: program exited 0, wanted a failure"]
        problems += [f"case {name}: stderr lacks {fragment!r}: "
                     f"{result.stderr[-500:]}"
                     for fragment in spec["stderrIncludes"]
                     if fragment not in result.stderr]
        return problems
    if result.returncode != 0:
        return [f"case {name}: program exited {result.returncode}: "
                f"{result.stderr[-500:]}"]
    try:
        data = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return [f"case {name}: program output is not JSON: "
                f"{result.stdout[:300]}"]
    print(f"  {name}: {json.dumps(data)}")
    return [f"case {name}: {p}" for p in check_run_output(spec, data)]


def run_graph(case: dict, sources: list, files: list, project: Path) -> list:
    spec = case["run"]
    result = command(["purs", "graph"] + sources + files, project)
    name = case["name"]
    if result.returncode != 0:
        return [f"case {name}: purs graph exited {result.returncode}: "
                f"{result.stderr[:300]}"]
    try:
        graph = json.loads(result.stdout)
    except ValueError:
        return [f"case {name}: purs graph output is not JSON"]
    node = graph.get(spec["module"]) if isinstance(graph, dict) else None
    if not isinstance(node, dict):
        return [f"case {name}: purs graph has no key {spec['module']!r}"]
    return [f"case {name}: purs graph: {spec['module']} does not depend on "
            f"{dep}" for dep in spec["depends"]
            if dep not in node.get("depends", [])]


def run_case(case: dict, check_dir: Path, project: Path, out: Path,
             sources: list) -> list:
    files = sorted(str(p) for p in
                   (check_dir / "cases" / case["name"]).glob("*.purs"))
    result = command(["purs", "compile", "--json-errors", "--output",
                      str(out)] + sources + files, project)
    try:
        outcome = fill_modules(classify(parse_compiler_output(
            result.stdout)), project)
    except CheckError as error:
        return [f"case {case['name']}: {error}; stderr: "
                f"{result.stderr[-300:]}"]
    if (result.returncode == 0) != (outcome.status == "ok"):
        return [f"case {case['name']}: purs exited {result.returncode} with "
                f"status {outcome.status}"]
    problems = check_case(case, outcome)
    run = case.get("run")
    if problems or not run:
        return problems
    if run["kind"] == "graph":
        return run_graph(case, sources, files, project)
    if run["kind"] == "node":
        return run_node(case, out)
    raise CheckError(f"case {case['name']}: unknown run kind {run['kind']!r}")


def run(check_dir: Path, project: Path, out: Path, repo: Path) -> int:
    cases = load_cases(check_dir / "cases.json")
    lock = json.loads((project / "spago.lock").read_text(encoding="utf-8"))
    tools = {"purs": first_line(["purs", "--version"], project),
             "spago": first_line(["spago", "--version"], project)}
    problems = check_versions(versions_table(repo), lock, tools,
                              anchors=load_anchor_entries(repo))
    sources = dependency_sources(project)
    for case in cases:
        found = run_case(case, check_dir, project, out, sources)
        print(f"{'FAIL' if found else 'ok  '} {case['name']}")
        problems += found
    if problems:
        for problem in problems:
            print(problem)
        print(f"purescript-gotchas check: FAILED ({len(problems)} problems, "
              f"{len(cases)} cases)")
        return 1
    print(f"purescript-gotchas check: OK ({len(cases)} cases)")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", type=Path, required=True,
                        help="directory where spago install ran")
    parser.add_argument("--out", type=Path, required=True,
                        help="purs output directory with dependencies built")
    parser.add_argument("--repo", type=Path, default=HERE.parent.parent)
    args = parser.parse_args(argv)
    try:
        return run(HERE, args.project, args.out, args.repo)
    except CheckError as error:
        print(f"purescript-gotchas check: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
