#!/usr/bin/env bash
# Lints the fixtures under fixtures/ with the reference ESLint config
# skills/effect-v4/lint/eslint.rules.js, at the pinned versions, and compares
# every report with expected.json. Checks the pins against anchors.json. Works
# in a temporary directory removed on exit, with bun's cache inside it. See
# README.md for what it does not catch.
#
# Usage: run.sh [--repo DIR] [--deps DIR] [--verbose]
#   --repo DIR  repository whose skill and anchors.json are checked
#               (default: the repository containing this script)
#   --deps DIR  reuse DIR/node_modules instead of a fresh install (test-run.sh)
#   --verbose   print the work directory's size before it is removed
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
deps=""
verbose=0
while [ $# -gt 0 ]; do
  case $1 in
    --repo) repo=$(cd "${2:?--repo needs a directory}" && pwd) || exit 2; shift 2 ;;
    --deps) deps=$(cd "${2:?--deps needs a directory}" && pwd) || exit 2; shift 2 ;;
    --verbose) verbose=1; shift ;;
    *) echo "usage: run.sh [--repo DIR] [--deps DIR] [--verbose]" >&2; exit 2 ;;
  esac
done

fail() { echo "effect-v4-lint check: FAIL: $*" >&2; exit 1; }
command -v bun >/dev/null || fail "bun is not on PATH"

rules="$repo/skills/effect-v4/lint/eslint.rules.js"
[ -f "$rules" ] || fail "no reference config at $rules"

work=$(mktemp -d "${TMPDIR:-/tmp}/effect-v4-lint-check.XXXXXX") || exit 2
cleanup() {
  if [ "$verbose" -eq 1 ]; then du -sh "$work" >&2; fi
  rm -rf "$work"
}
trap cleanup EXIT

cp "$here"/{package.json,bun.lock,expected.json,lint.ts,modules.ts,versions.ts} "$work/" || fail "copying the check"
cp -R "$here/fixtures" "$work/" || fail "copying the fixtures"
cp "$rules" "$work/eslint.rules.js" || fail "copying the reference config"
cd "$work" || exit 2

# 1. Dependencies, exactly as bun.lock records them.
if [ -n "$deps" ]; then
  [ -d "$deps/node_modules" ] || fail "--deps $deps has no node_modules"
  ln -s "$deps/node_modules" node_modules
elif ! BUN_INSTALL_CACHE_DIR="$work/bun-cache" bun install --frozen-lockfile >install.log 2>&1; then
  cat install.log >&2
  fail "bun install --frozen-lockfile failed"
fi
if [ "$verbose" -eq 1 ]; then du -sh "$work" >&2; fi  # peak: install plus cache
rm -rf "$work/bun-cache"
bun versions.ts "$repo/anchors.json" package.json node_modules || fail "versions disagree"

# 2. The Effect module list in the config equals effect's namespace exports.
bun modules.ts eslint.rules.js node_modules || fail "effectModules disagrees with effect"

# 3. Lint the fixtures and compare with expected.json.
summary=$(bun lint.ts "$work/fixtures" expected.json) || fail "lint fixtures"

echo "effect-v4-lint check: OK ($summary)"
