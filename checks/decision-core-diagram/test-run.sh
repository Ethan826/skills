#!/usr/bin/env bash
# Tests for run.sh. Each case copies the diagram directory into a fake
# repository, plants one defect, and runs run.sh against it. The "clean" case
# is the reverted mutant of every failing case.
# Usage: test-run.sh  (exit 0 when every case behaves as named)
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
scratch=$(mktemp -d "${TMPDIR:-/tmp}/decision-core-diagram-test.XXXXXX")
trap 'rm -rf "$scratch"' EXIT
passed=0
failed=0
d=skills/decision-core-architecture/diagram

setup() {
  r="$scratch/$1"
  mkdir -p "$r/$d"
  cp "$repo/$d/onion.ts" "$repo/$d/onion.svg" "$r/$d/"
}

plant() {
  cp "$1" "$1.orig"
  perl -0pi -e "$2" "$1"
  if cmp -s "$1" "$1.orig"; then
    echo "FAIL  planting into $1 changed nothing: $2"
    exit 1
  fi
  rm "$1.orig"
}

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

run() { "$here/run.sh" --repo "$r"; }

setup clean
expect 0 '^decision-core-diagram check: OK \(onion\.svg matches the generator, 6 layers\)$' "clean" run

setup svg-edited
plant "$r/$d/onion.svg" 's/>wiring</>glue</'
expect fail 'committed onion\.svg differs' "committed SVG edited by hand" run

setup generator-edited
plant "$r/$d/onion.ts" 's/note: "wiring"/note: "glue"/'
expect fail 'committed onion\.svg differs' "generator changed, SVG not regenerated" run

setup unknown-import
plant "$r/$d/onion.ts" 's/imports: \["Domain", "Features", "Format", "Runtime"\]/imports: ["Domain", "Shell"]/'
expect fail 'Shell is imported but is not a layer' "import list names no layer" run

setup dark-mode-dropped
plant "$r/$d/onion.ts" 's/\@media \(prefers-color-scheme: dark\)/\@media print/g'
(cd "$r/$d" && bun onion.ts >onion.svg)
expect fail 'no dark-mode override' "dark-mode override removed (SVG regenerated)" run

setup css-variable
plant "$r/$d/onion.ts" 's/fill: #1f2328; \}/fill: var(--fg, #1f2328); }/'
(cd "$r/$d" && bun onion.ts >onion.svg)
expect fail 'uses var\(\)' "CSS variable added (SVG regenerated)" run

echo "$passed passed, $failed failed"
[ "$failed" -eq 0 ]
