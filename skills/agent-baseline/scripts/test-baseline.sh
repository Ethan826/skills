#!/usr/bin/env bash
# Tests for baseline.sh. Runs in a scratch directory and touches nothing
# else. Usage: test-baseline.sh  (exit 0 when every case behaves as named)
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
bl="$here/baseline.sh"
block="$here/../baseline.md"
personal="$here/../personal.example.md"
work=$(mktemp -d "${TMPDIR:-/tmp}/baseline-test.XXXXXX")
trap 'rm -rf "$work"' EXIT
cd "$work" || exit 2

passed=0
failed=0

# expect WANT NAME CMD...: run CMD, compare its exit status with WANT.
expect() {
  local want=$1 name=$2 got
  shift 2
  "$@" >"$work/out" 2>&1
  got=$?
  if [ "$got" -eq "$want" ]; then
    echo "PASS  $name (exit $got)"
    passed=$((passed + 1))
  else
    echo "FAIL  $name (wanted exit $want, got $got)"
    sed 's/^/      /' "$work/out"
    failed=$((failed + 1))
  fi
}

# same NAME A B: pass when files A and B are byte-identical.
same() {
  if cmp -s "$2" "$3"; then
    echo "PASS  $1"
    passed=$((passed + 1))
  else
    echo "FAIL  $1"
    diff "$2" "$3" | sed 's/^/      /'
    failed=$((failed + 1))
  fi
}

printf '# Project\n\nLocal rules stay here.\n' >AGENTS.md
cp AGENTS.md original.md

expect 0 "install into a file without the block" "$bl" install AGENTS.md
cp AGENTS.md once.md
expect 0 "install a second time" "$bl" install AGENTS.md
same "second install leaves the file byte-identical" once.md AGENTS.md
expect 0 "check passes after install" "$bl" check AGENTS.md
head -n 3 AGENTS.md >head.md
same "install keeps the text outside the block" original.md head.md

expect 0 "install into a missing file creates it" "$bl" install new.md
expect 0 "check passes on the created file" "$bl" check new.md

sed 's/^- \*\*No emoji,\*\*/- **Few emoji,**/' AGENTS.md >edited.md
expect 1 "check fails after an edit inside the block" "$bl" check edited.md
cp edited.md reinstalled.md
expect 0 "install replaces an edited block" "$bl" install reinstalled.md
same "reinstall restores the installed file" AGENTS.md reinstalled.md

cp AGENTS.md nonl.md
printf '\nFooter with no final newline.' >>nonl.md
cp nonl.md nonl-before.md
expect 0 "install over a block with a footer lacking a final newline" \
  "$bl" install nonl.md
same "unchanged block leaves a no-newline footer byte-identical" \
  nonl-before.md nonl.md
cp edited.md nonl-edited.md
printf '\nFooter with no final newline.' >>nonl-edited.md
expect 0 "install replaces an edited block above a no-newline footer" \
  "$bl" install nonl-edited.md
same "replacing the block keeps the no-newline footer exactly" \
  nonl-before.md nonl-edited.md

sed -E 's/agent-baseline:start v[0-9]+/agent-baseline:start v0/' AGENTS.md >oldver.md
grep -q 'agent-baseline:start v0' oldver.md ||
  { echo 'FAIL  could not build the older-version fixture'; exit 1; }
expect 1 "check fails on an older block version" "$bl" check oldver.md

printf '# Nothing marked\n' >empty-a.md
printf '# Nothing marked either\n' >empty-b.md
expect 1 "check fails on a file with zero marked sections" "$bl" check empty-a.md
expect 1 "check-sync fails when both files have zero sections" \
  "$bl" check-sync empty-a.md empty-b.md
expect 1 "check-sync fails when only the copy has zero sections" \
  "$bl" check-sync AGENTS.md empty-b.md
expect 1 "check-sync fails when only the source has zero sections" \
  "$bl" check-sync empty-a.md AGENTS.md

printf '<!-- other:start v1 -->\nx\n<!-- other:end -->\n' >other-a.md
cp other-a.md other-b.md
expect 1 "check-sync fails when the pinned name is absent from both" \
  "$bl" check-sync other-a.md other-b.md
expect 0 "check-sync passes with --expect naming the section" \
  "$bl" check-sync --expect other other-a.md other-b.md

cp AGENTS.md source.md
"$bl" install source.md "$personal" >/dev/null
printf '# Harness file\n\nHarness-only notes.\n' >copy.md
expect 1 "check-sync fails before sync" "$bl" check-sync source.md copy.md
expect 0 "sync copies every section" "$bl" sync source.md copy.md
expect 0 "check-sync passes after sync" "$bl" check-sync source.md copy.md
expect 0 "check-sync passes with both names pinned" \
  "$bl" check-sync --expect agent-baseline,agent-personal source.md copy.md
cp copy.md copy-once.md
expect 0 "sync a second time" "$bl" sync source.md copy.md
same "second sync leaves the copy byte-identical" copy-once.md copy.md
expect 0 "sync keeps the copy's own text" grep -q 'Harness-only notes.' copy.md

sed 's/^- \*\*No emoji,\*\*/- **Few emoji,**/' copy.md >drift.md
expect 1 "check-sync fails when the copy drifts" "$bl" check-sync source.md drift.md
cp source.md extra.md
printf '\n<!-- stray:start v1 -->\ny\n<!-- stray:end -->\n' >>extra.md
expect 1 "check-sync fails on a section only one file has" \
  "$bl" check-sync source.md extra.md
expect 1 "sync refuses a stale section in the copy" "$bl" sync source.md extra.md

printf '<!-- agent-baseline:start v1 -->\nno end\n' >unterminated.md
expect 2 "check rejects a section with no end marker" "$bl" check unterminated.md
printf '<!-- agent-baseline:start v1 -->\n<!-- other:end -->\n' >mismatch.md
expect 2 "check rejects a mismatched end marker" "$bl" check mismatch.md
printf '<!-- agent-baseline:start -- v1 -->\n' >malformed.md
expect 2 "check rejects a malformed marker" "$bl" check malformed.md
expect 2 "install refuses to edit a malformed file" "$bl" install mismatch.md
expect 2 "install rejects a block file with two sections" \
  "$bl" install AGENTS.md source.md
expect 0 "check accepts the personal block once installed" \
  "$bl" check source.md "$personal"
expect 2 "an unknown subcommand is a usage error" "$bl" frobnicate
expect 0 "the shipped block file is itself well formed" "$bl" check "$block"

echo
echo "$passed passed, $failed failed"
[ "$failed" -eq 0 ]
