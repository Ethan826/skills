#!/usr/bin/env bash
# Tests for run.sh. Each case copies the gate and anchors.json into a fake
# repository, plants one defect, and runs run.sh against it. Every failing case
# differs from "clean (reused deps)" only by its planted defect, so that
# passing case is the reverted mutant of each. Usage: test-run.sh
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
scratch=$(mktemp -d "${TMPDIR:-/tmp}/tsdoc-check-test.XXXXXX")
trap 'rm -rf "$scratch"' EXIT
passed=0
failed=0

mkdir -p "$scratch/deps"
cp "$here/package.json" "$here/bun.lock" "$scratch/deps/"
if ! (cd "$scratch/deps" && BUN_INSTALL_CACHE_DIR="$scratch/deps/cache" \
      bun install --frozen-lockfile >"$scratch/deps/install.log" 2>&1); then
  cat "$scratch/deps/install.log"
  echo "FAIL  shared dependency install"
  exit 1
fi
rm -rf "$scratch/deps/cache"

gate=skills/readable-functional-code/tsdoc/tsdoc-gate.ts

# setup NAME: fake repo at $scratch/NAME/repo and check copy at
# $scratch/NAME/check; sets $r and $c.
setup() {
  r="$scratch/$1/repo"
  c="$scratch/$1/check"
  mkdir -p "$r/$(dirname "$gate")" "$c"
  cp "$repo/anchors.json" "$r/"
  cp "$repo/$gate" "$r/$gate"
  (cd "$here" && tar -cf - --exclude node_modules .) | (cd "$c" && tar -xf -)
}

# plant FILE PERL-EXPR: fail the setup if the substitution changed nothing.
plant() {
  cp "$1" "$1.orig"
  perl -0pi -e "$2" "$1"
  if cmp -s "$1" "$1.orig"; then
    echo "FAIL  planting into $1 changed nothing: $2"
    exit 1
  fi
}

# expect WANT REGEX NAME CMD...: WANT is 0 or "fail"; output must match REGEX.
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

ok_re='^readable-functional-code-tsdoc check: OK \(36 cases\)$'
run() { "$c/run.sh" --repo "$r" --deps "$scratch/deps"; }

setup clean
expect 0 "$ok_re" "clean (fresh install)" "$c/run.sh" --repo "$r"
setup clean-deps
expect 0 "$ok_re" "clean (reused deps)" run

# Mutants of the gate.
setup any-block-comment
plant "$r/$gate" 's/if \(!comment\.startsWith\("\/\*\*"\) \|\| /if (/'
expect fail 'must fail: a plain block comment' "a plain block comment accepted" run
setup last-block-comment
plant "$r/$gate" 's/const last = ranges\[ranges\.length - 1\]/const last = ranges.filter((r) => r.kind === ts.SyntaxKind.MultiLineCommentTrivia).pop()/'
expect fail 'must fail: a line comment between TSDoc and export' "a line comment after the TSDoc accepted" run
setup first-comment
plant "$r/$gate" 's/ranges\[ranges\.length - 1\]/ranges[0]/'
expect fail 'must fail: a line comment between TSDoc and export' "an earlier comment accepted" run
setup empty-tsdoc
plant "$r/$gate" 's/""\)\.length > 0/"").length >= 0/'
expect fail 'must fail: an empty TSDoc comment' "an empty TSDoc accepted" run
setup lists-skipped
plant "$r/$gate" 's/if \(statement\.moduleSpecifier !== undefined \|\| statement\.exportClause === undefined\) continue/continue/'
expect fail 'must fail: an export list of an undocumented const' "export lists skipped" run
setup default-skipped
plant "$r/$gate" 's/if \(!ts\.isExportAssignment\(statement\) && /if (/'
expect fail 'must fail: an undocumented default export' "export default skipped" run
setup syntax-ignored
plant "$r/$gate" 's/syntax\.length > 0/false/'
expect fail 'unparseable file' "a syntax error ignored" run
setup empty-passes
plant "$r/$gate" 's/if \(paths\.length === 0\)/if (false)/'
expect fail 'empty directory' "an empty directory passes" run
setup no-floor
plant "$r/$gate" 's/exported < min/false/'
expect fail 'scan minimum above the count' "the scan minimum dropped" run

# Mutants of the check.
setup anchor-drift
plant "$r/anchors.json" 's/("id": "readable-functional-code\/typescript \(tsdoc\)", .*?"version": ")5\.9\.3"/${1}5.9.2"/'
expect fail 'anchors\.json says typescript 5\.9\.2, package\.json pins 5\.9\.3' "anchors.json and the pin disagree" run
setup range-pin
plant "$c/package.json" 's/"typescript": "5\.9\.3"/"typescript": "^5.9.3"/'
expect fail 'not an exact version' "range pin in package.json" run
setup gate-missing
rm "$r/$gate"
expect fail 'no gate at' "gate missing" run

echo "$passed passed, $failed failed"
[ "$failed" -eq 0 ]
