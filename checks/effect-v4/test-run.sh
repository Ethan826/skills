#!/usr/bin/env bash
# Tests for run.sh. Each case builds a fake repository (the two checked skill
# files and anchors.json) and, where the defect is in the check itself, a copy
# of this directory, plants one defect, and runs run.sh against them. Every
# failing case shares its setup with "clean (reused deps)" and differs from it
# only by the planted defect, so that passing case is the reverted mutant of
# each of them. Usage: test-run.sh  (exit 0 when every case behaves as named)
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
scratch=$(mktemp -d "${TMPDIR:-/tmp}/effect-v4-test.XXXXXX")
trap 'rm -rf "$scratch"' EXIT

passed=0
failed=0

# One shared install for the cases that pass --deps; its cache is removed
# as soon as the install finishes.
mkdir -p "$scratch/deps"
cp "$here/package.json" "$here/bun.lock" "$scratch/deps/"
if ! (cd "$scratch/deps" && BUN_INSTALL_CACHE_DIR="$scratch/deps/cache" \
      bun install --frozen-lockfile >"$scratch/deps/install.log" 2>&1); then
  cat "$scratch/deps/install.log"
  echo "FAIL  shared dependency install"
  exit 1
fi
rm -rf "$scratch/deps/cache"

# setup NAME: fresh fake repo at $scratch/NAME/repo and check copy at
# $scratch/NAME/check; sets $r and $c.
setup() {
  r="$scratch/$1/repo"
  c="$scratch/$1/check"
  mkdir -p "$r/skills/effect-v4" "$r/skills/readable-functional-code"
  cp "$repo/anchors.json" "$r/"
  cp "$repo/skills/effect-v4/SKILL.md" "$r/skills/effect-v4/"
  cp "$repo/skills/readable-functional-code/typescript.md" "$r/skills/readable-functional-code/"
  mkdir -p "$c"
  (cd "$here" && tar -cf - --exclude node_modules --exclude blocks .) | (cd "$c" && tar -xf -)
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

ok_re='^effect-v4 check: OK \(9 \+ 2 blocks, 7 must-fail errors, runtime claim holds\)$'
skill=skills/effect-v4/SKILL.md
tsmd=skills/readable-functional-code/typescript.md

# Line number of the Nth ```ts opening fence in FILE.
ts_fence() { grep -n '^```ts$' "$1" | sed -n "${2}p" | cut -d: -f1; }

setup clean
expect 0 "$ok_re" "clean (fresh install)" "$c/run.sh" --repo "$r"

setup clean-deps
expect 0 "$ok_re" "clean (reused deps)" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup v3-name
line=$(ts_fence "$r/$skill" 1)
sed -i.bak "${line}a\\
Effect.catchAll
" "$r/$skill"
expect fail 'blocks/effect-v4-01\.ts\([0-9]+,[0-9]+\): error TS2339' \
  "v3 name in block 01" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup block-removed
open=$(ts_fence "$r/$skill" 9)
close=$(awk -v s="$open" 'NR > s && /^```$/ { print NR; exit }' "$r/$skill")
sed -i.bak "${open},${close}d" "$r/$skill"
expect fail 'expected 9 effect-v4 blocks, found 8' \
  "last effect-v4 block removed" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup ts-md-block-removed
open=$(ts_fence "$r/$tsmd" 2)
close=$(awk -v s="$open" 'NR > s && /^```$/ { print NR; exit }' "$r/$tsmd")
sed -i.bak "${open},${close}d" "$r/$tsmd"
expect fail 'expected 2 typescript blocks, found 1' \
  "typescript.md block removed" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup typescript-fence
line=$(ts_fence "$r/$skill" 1)
sed -i.bak "${line}s/^\`\`\`ts\$/\`\`\`typescript/" "$r/$skill"
expect fail 'untyped-checked fence: .*SKILL\.md line [0-9]+ \(typescript\)' \
  "typescript fence" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup tsx-fence
line=$(ts_fence "$r/$tsmd" 1)
sed -i.bak "${line}s/^\`\`\`ts\$/\`\`\`tsx/" "$r/$tsmd"
expect fail 'untyped-checked fence: .*typescript\.md line [0-9]+ \(tsx\)' \
  "tsx fence" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup unterminated
printf '\n```ts\nconst x = 1\n' >>"$r/$tsmd"
expect fail 'unterminated fence' \
  "unterminated fence" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup orphan-prelude
cp "$c/preludes/effect-v4-09.ts" "$c/preludes/effect-v4-10.ts"
expect fail 'orphan prelude: preludes/effect-v4-10\.ts' \
  "orphan prelude" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup mustfail-fixed
sed -i.bak 's/^Effect\.catchAll$/Effect.catch/' "$c/mustfail-raw/must-fail.ts"
expect fail 'expected 7 must-fail errors, found 6' \
  "must-fail control stops failing" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup mustfail-moved
# Same seven errors, each one line lower: a count-only check would pass.
awk '{ print } /^import / { print "" }' "$c/mustfail-raw/must-fail.ts" >"$c/mf.ts"
mv "$c/mf.ts" "$c/mustfail-raw/must-fail.ts"
expect fail 'must-fail errors differ' \
  "must-fail count kept, lines moved" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup runtime-claim
sed -i.bak 's/^const viaPromise = await Effect.runPromiseExit(Effect.promise(rejecting))$/const viaPromise = await Effect.runPromiseExit(Effect.tryPromise({ try: rejecting, catch: (reason) => new FetchFailed({ reason }) }))/' \
  "$c/runtime/promise-rejection.ts"
expect fail 'CLAIM FAILS' \
  "runtime claim broken" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup anchor-bumped
sed -i.bak 's/"id": "effect-v4\/effect", \(.*\)"version": "4\.1\.4"/"id": "effect-v4\/effect", \1"version": "4.1.5"/' "$r/anchors.json"
expect fail 'anchors\.json effect-v4/effect says 4\.1\.5, package\.json pins 4\.1\.4' \
  "anchors.json bumped, package.json not" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup package-bumped-deps
sed -i.bak 's/"effect": "4\.1\.4"/"effect": "4.1.5"/' "$c/package.json"
sed -i.bak 's/"version": "4\.1\.4", "row": "effect"/"version": "4.1.5", "row": "effect"/g' "$r/anchors.json"
expect fail 'installed effect is 4\.1\.4, package\.json pins 4\.1\.5' \
  "package.json and anchors bumped, deps not (reused deps)" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

setup package-bumped-fresh
sed -i.bak 's/"effect": "4\.1\.4"/"effect": "4.1.5"/' "$c/package.json"
sed -i.bak 's/"version": "4\.1\.4", "row": "effect"/"version": "4.1.5", "row": "effect"/g' "$r/anchors.json"
expect fail 'bun install --frozen-lockfile failed' \
  "package.json and anchors bumped, bun.lock not (fresh install)" "$c/run.sh" --repo "$r"

setup range-pin
sed -i.bak 's/"vitest": "5\.1\.0"/"vitest": "^5.1.0"/' "$c/package.json"
expect fail 'package\.json pins vitest to "\^5\.1\.0", not an exact version' \
  "range pin in package.json" "$c/run.sh" --repo "$r" --deps "$scratch/deps"

echo "$passed passed, $failed failed"
[ "$failed" -eq 0 ]
