#!/usr/bin/env bash
# Compiles every ```ts block of skills/effect-v4/SKILL.md and
# skills/readable-functional-code/typescript.md against the pinned effect and
# TypeScript, checks the must-fail and runtime controls, and checks the pins
# against anchors.json. Works in a temporary directory removed on exit, with
# bun's cache inside it. See README.md for what it does not catch.
#
# Usage: run.sh [--repo DIR] [--deps DIR] [--verbose]
#   --repo DIR  repository whose skills and anchors.json are checked
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

fail() { echo "effect-v4 check: FAIL: $*" >&2; exit 1; }
command -v bun >/dev/null || fail "bun is not on PATH"

work=$(mktemp -d "${TMPDIR:-/tmp}/effect-v4-check.XXXXXX") || exit 2
cleanup() {
  if [ "$verbose" -eq 1 ]; then du -sh "$work" >&2; fi
  rm -rf "$work"
}
trap cleanup EXIT

cp "$here"/{package.json,bun.lock,tsconfig.json,tsconfig.mustfail.json,expected.json} \
   "$here"/{extract.ts,versions.ts,mustfail.ts} "$work/" || fail "copying the check"
cp -R "$here"/{preludes,controls,mustfail-raw,runtime} "$work/" || fail "copying the check"
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

# 2. Extract the blocks into a fresh directory, so no stale block survives.
mkdir blocks
n_effect=$(bun extract.ts "$repo/skills/effect-v4/SKILL.md" effect-v4 blocks) || fail "extracting effect-v4"
n_ts=$(bun extract.ts "$repo/skills/readable-functional-code/typescript.md" typescript blocks) || fail "extracting typescript.md"

# 3. Block counts and preludes against expected.json.
expect_effect=$(bun --print "require('./expected.json')['effect-v4']")
expect_ts=$(bun --print "require('./expected.json')['typescript']")
[ "$n_effect" = "$expect_effect" ] || fail "expected $expect_effect effect-v4 blocks, found $n_effect"
[ "$n_ts" = "$expect_ts" ] || fail "expected $expect_ts typescript blocks, found $n_ts"
for p in preludes/*.ts; do
  b="blocks/$(basename "$p")"
  [ -f "$b" ] || fail "orphan prelude: $p has no block $(basename "$p" .ts)"
done

# 4. Every block and control compiles.
tsc="node_modules/typescript/lib/tsc.js"
if ! bun "$tsc" --noEmit -p tsconfig.json >tsc.out 2>&1; then
  cat tsc.out >&2
  fail "tsc reported errors for tsconfig.json"
fi

# 5. The must-fail file fails with exactly the expected errors.
bun "$tsc" --noEmit -p tsconfig.mustfail.json >mustfail.out 2>&1
bun mustfail.ts mustfail.out expected.json || fail "must-fail control"
n_mustfail=$(bun --print "require('./expected.json').mustFailErrors")

# 6. The runtime claim about Effect.promise.
bun runtime/promise-rejection.ts >runtime.out 2>&1
status=$?
cat runtime.out
if [ "$status" -ne 0 ] || ! grep -qx 'CLAIM HOLDS' runtime.out; then
  fail "runtime claim (exit $status)"
fi

echo "effect-v4 check: OK ($n_effect + $n_ts blocks, $n_mustfail must-fail errors, runtime claim holds)"
