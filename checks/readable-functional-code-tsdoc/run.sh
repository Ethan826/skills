#!/usr/bin/env bash
# Runs the TSDoc gate's own tests: cases.ts against
# skills/readable-functional-code/tsdoc/tsdoc-gate.ts and fixtures/, with
# TypeScript at the version package.json and bun.lock pin, which must equal
# the anchors.json entry. Works in a temporary directory removed on exit, with
# bun's cache inside it. See README.md for what it does not catch.
#
# Usage: run.sh [--repo DIR] [--deps DIR]
#   --repo DIR  repository whose gate and anchors.json are checked
#               (default: the repository containing this script)
#   --deps DIR  reuse DIR/node_modules instead of a fresh install (test-run.sh)
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
deps=""
while [ $# -gt 0 ]; do
  case $1 in
    --repo) repo=$(cd "${2:?--repo needs a directory}" && pwd) || exit 2; shift 2 ;;
    --deps) deps=$(cd "${2:?--deps needs a directory}" && pwd) || exit 2; shift 2 ;;
    *) echo "usage: run.sh [--repo DIR] [--deps DIR]" >&2; exit 2 ;;
  esac
done

fail() { echo "readable-functional-code-tsdoc check: FAIL: $*" >&2; exit 1; }
command -v bun >/dev/null || fail "bun is not on PATH"

gate="$repo/skills/readable-functional-code/tsdoc/tsdoc-gate.ts"
[ -f "$gate" ] || fail "no gate at $gate"

work=$(mktemp -d "${TMPDIR:-/tmp}/tsdoc-check.XXXXXX") || exit 2
trap 'rm -rf "$work"' EXIT
cp "$here"/{package.json,bun.lock,cases.ts} "$work/" || fail "copying the check"
cp -R "$here/fixtures" "$work/" || fail "copying the fixtures"
# The gate runs beside the pinned install, so it imports that TypeScript.
cp "$gate" "$work/tsdoc-gate.ts" || fail "copying the gate"
cd "$work" || exit 2

# 1. The pin is exact and equals the anchors.json tool entry for this check.
pin=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["devDependencies"]["typescript"])' package.json) \
  || fail "package.json does not pin typescript"
echo "$pin" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || fail "package.json pins typescript to \"$pin\", not an exact version"
anchor=$(python3 -c '
import json, sys
hits = [a["version"] for a in json.load(open(sys.argv[1]))["anchors"]
        if a.get("kind") == "tool" and a.get("check") == "checks/readable-functional-code-tsdoc"
        and a.get("package") == "typescript"]
print(hits[0] if len(hits) == 1 else "")' "$repo/anchors.json")
[ -n "$anchor" ] || fail "anchors.json has no single typescript tool entry for checks/readable-functional-code-tsdoc"
[ "$anchor" = "$pin" ] || fail "anchors.json says typescript $anchor, package.json pins $pin"

# 2. Dependencies, exactly as bun.lock records them.
if [ -n "$deps" ]; then
  [ -d "$deps/node_modules" ] || fail "--deps $deps has no node_modules"
  ln -s "$deps/node_modules" node_modules
elif ! BUN_INSTALL_CACHE_DIR="$work/bun-cache" bun install --frozen-lockfile >install.log 2>&1; then
  cat install.log >&2
  fail "bun install --frozen-lockfile failed"
fi
rm -rf "$work/bun-cache"
installed=$(python3 -c 'import json; print(json.load(open("node_modules/typescript/package.json"))["version"])')
[ "$installed" = "$pin" ] || fail "installed typescript $installed, pinned $pin"

# 3. The gate's cases.
summary=$(bun cases.ts "$work/tsdoc-gate.ts" "$work/fixtures") || fail "gate cases"
echo "readable-functional-code-tsdoc check: OK ($summary)"
