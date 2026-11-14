#!/usr/bin/env bash
# Tests for run.sh. Each case builds a fake repository (the reference config
# and anchors.json) and, where the defect is in the check itself, a copy of
# this directory, plants one defect, and runs run.sh against them. Every
# failing case shares its setup with "clean (reused deps)" and differs from it
# only by the planted defect, so that passing case is the reverted mutant of
# each of them. Usage: test-run.sh  (exit 0 when every case behaves as named)
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
scratch=$(mktemp -d "${TMPDIR:-/tmp}/effect-v4-lint-test.XXXXXX")
trap 'rm -rf "$scratch"' EXIT

passed=0
failed=0

# One shared install for the cases that pass --deps; its cache is removed as
# soon as the install finishes.
mkdir -p "$scratch/deps"
cp "$here/package.json" "$here/bun.lock" "$scratch/deps/"
if ! (cd "$scratch/deps" && BUN_INSTALL_CACHE_DIR="$scratch/deps/cache" \
      bun install --frozen-lockfile >"$scratch/deps/install.log" 2>&1); then
  cat "$scratch/deps/install.log"
  echo "FAIL  shared dependency install"
  exit 1
fi
rm -rf "$scratch/deps/cache"

rules=skills/effect-v4/lint/eslint.rules.js

# setup NAME: fresh fake repo at $scratch/NAME/repo and check copy at
# $scratch/NAME/check; sets $r and $c.
setup() {
  r="$scratch/$1/repo"
  c="$scratch/$1/check"
  mkdir -p "$r/skills/effect-v4/lint"
  cp "$repo/anchors.json" "$r/"
  cp "$repo/$rules" "$r/$rules"
  mkdir -p "$c"
  (cd "$here" && tar -cf - --exclude node_modules .) | (cd "$c" && tar -xf -)
}

# plant FILE PERL-EXPR: apply a perl substitution and fail the case setup if it
# changed nothing, so a stale pattern cannot leave a mutant unplanted.
plant() {
  cp "$1" "$1.orig"
  perl -0pi -e "$2" "$1"
  if cmp -s "$1" "$1.orig"; then
    echo "FAIL  planting into $1 changed nothing: $2"
    exit 1
  fi
}

# expect WANT REGEX NAME CMD...: run CMD; WANT is 0 or "fail" (any non-zero);
# the combined output must match the extended regex REGEX.
expect() {
  local want=$1 re=$2 name=$3 got ok=1
  shift 3
  "$@" >"$scratch/out" 2>&1
  got=$?
  if [ "$want" = 0 ]; then [ "$got" -eq 0 ] || ok=0; else [ "$got" -ne 0 ] || ok=0; fi
  grep -Eq -- "$re" "$scratch/out" || ok=0
  if [ "$ok" -eq 1 ]; then
    echo "PASS  $name (exit $got)"
    passed=$((passed + 1))
  else
    echo "FAIL  $name (wanted exit $want and /$re/, got exit $got)"
    sed 's/^/      /' "$scratch/out"
    failed=$((failed + 1))
  fi
}

ok_re='^effect-v4-lint check: OK \(42 must-fail fixtures \(94 expected reports\), 12 clean controls\)$'
run() { "$c/run.sh" --repo "$r" --deps "$scratch/deps"; }

setup clean
expect 0 "$ok_re" "clean (fresh install)" "$c/run.sh" --repo "$r"

setup clean-deps
expect 0 "$ok_re" "clean (reused deps)" run

# Mutants of the reference config: each removes one rule or one entry.
setup no-let-removed
plant "$r/$rules" 's/^\s*"functional\/no-let": "error",\n//m'
expect fail 'src/domain/let\.ts: expected functional/no-let' \
  "rule removed: functional/no-let" run

setup method-removed
plant "$r/$rules" 's/"findLastIndex", //'
expect fail "native-array-iterate\\.ts: expected no-restricted-properties \"'findLastIndex' is restricted\"" \
  "native method removed from the list" run

setup literal-group-removed
plant "$r/$rules" 's/, parsing, literalSchemas\]/, parsing]/'
expect fail 'literals-inline-array\.ts: expected no-restricted-syntax "Schema\.Literals takes a named"' \
  "Schema.Literals ban removed" run

setup alias-ignored
plant "$r/$rules" 's/const named = \(module\) => nameRegExp\(\[module, \.\.\.aliasesOf\(module\)\]\)/const named = (module) => nameRegExp([module])/'
expect fail 'literals-alias\.ts: expected no-restricted-syntax' \
  "aliases not applied to the Schema selectors" run

setup vocabulary-exemption-too-wide
plant "$r/$rules" 's/\.filter\(\(v\) => v\.module !== module\)/.filter((v) => module === null)/'
expect fail 'sources\.ts: expected no-restricted-syntax "Bare closed-vocabulary string: use Channels"' \
  "a vocabulary module may spell every vocabulary" run

setup core-null-ban-removed
plant "$r/$rules" 's/const coreOnly = \[nullish, nativeCollections\]/const coreOnly = [nativeCollections]/'
expect fail 'eq-null\.ts: expected no-restricted-syntax "Comparing with null"' \
  "null-check ban removed from core" run

setup layer-edge-opened
plant "$r/$rules" 's/\.filter\(\(other\) => other !== layer && !layers\[layer\]\.includes\(other\)\)/.filter((other) => other !== layer \&\& other !== "format" \&\& !layers[layer].includes(other))/'
expect fail 'import-format\.ts: expected no-restricted-imports "features may import only domain"' \
  "layer edge opened" run

setup test-relaxed-too-far
plant "$r/$rules" 's/noRestrictedSyntax\(\.\.\.testGroups, bareNamesExcept\(null\)\)/noRestrictedSyntax(...testGroups)/'
expect fail 'test/bare-names\.ts: expected no-restricted-syntax' \
  "vocabulary ban dropped from tests" run

setup module-list-short
plant "$r/$rules" 's/"Graph", //'
expect fail 'effect exports Graph, which effectModules does not list' \
  "an Effect module missing from effectModules" run

setup module-list-extra
plant "$r/$rules" 's/"Version",/"Version", "Arr",/'
expect fail 'effectModules lists Arr, which effect does not export' \
  "a name effect does not export in effectModules" run

# Mutants of the check itself.
setup unlisted-fixture
cp "$c/fixtures/src/domain/ok.ts" "$c/fixtures/src/domain/ok-copy.ts"
expect fail 'fixture not in expected\.json: src/domain/ok-copy\.ts' \
  "fixture missing from expected.json" run

setup dirty-control
printf 'export const n = (x: number | null): boolean => x === null\n' >>"$c/fixtures/src/domain/ok.ts"
expect fail 'clean control src/domain/ok\.ts: no-restricted-syntax' \
  "clean control reports a problem" run

setup parse-error
printf 'export const = \n' >"$c/fixtures/src/domain/ok.ts"
expect fail 'parse error in src/domain/ok\.ts' \
  "parse error in a fixture" run

setup anchor-bumped
plant "$r/anchors.json" 's/("id": "effect-v4\/eslint", .*?"version": ")9\.39\.2"/${1}9.39.1"/'
expect fail 'anchors\.json effect-v4/eslint says 9\.39\.1, package\.json pins 9\.39\.2' \
  "anchors.json bumped, package.json not" run

setup shared-pin-drift
plant "$r/anchors.json" 's/("id": "effect-v4\/effect", .*?"version": ")4\.1\.4"/${1}4.1.3"/'
expect fail 'package\.json pins effect 4\.1\.4, anchors\.json effect-v4/effect says 4\.1\.3' \
  "effect anchor moved without the lint check's pin" run

setup range-pin
plant "$c/package.json" 's/"eslint": "9\.39\.2"/"eslint": "^9.39.2"/'
expect fail 'package\.json pins eslint to "\^9\.39\.2", not an exact version' \
  "range pin in package.json" run

setup lockfile-stale
plant "$c/package.json" 's/"eslint-plugin-functional": "9\.0\.4"/"eslint-plugin-functional": "9.0.3"/'
plant "$r/anchors.json" 's/("id": "effect-v4\/eslint-plugin-functional", .*?"version": ")9\.0\.4"/${1}9.0.3"/'
expect fail 'bun install --frozen-lockfile failed' \
  "package.json and anchors bumped, bun.lock not (fresh install)" "$c/run.sh" --repo "$r"

setup config-missing
rm "$r/$rules"
expect fail 'no reference config at' "reference config missing" run

echo "$passed passed, $failed failed"
[ "$failed" -eq 0 ]
