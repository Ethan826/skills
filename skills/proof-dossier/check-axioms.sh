#!/usr/bin/env bash
# Proof gate for a Lean 4 project. Run it from the project root.
#
# Usage: check-axioms.sh <source-dir> <axioms-file> <committed-report> <theorem-list>
# Example: check-axioms.sh Resolver Resolver/Axioms.lean axioms-report.txt theorems.txt
#
# <theorem-list> holds one fully qualified theorem name per line; blank
# lines and lines starting with # are ignored. It must name exactly the
# theorems written in <source-dir>, which the gate reads back from the
# built environment, so a theorem left out of both the list and the
# report still fails. <source-dir> is relative to the project root, and
# its modules are <source-dir>.lean (if present) and every .lean file
# under it. Exits 0 only if every check passes, 1 if a check fails and 2
# on bad usage.
#
# The inventory step uses Lean's metaprogramming API (checked on Lean
# 4.35.0); a toolchain that changes it fails the gate rather than
# passing it.

set -euo pipefail

if [ $# -ne 4 ]; then
  echo "Usage: $0 <source-dir> <axioms-file> <committed-report> <theorem-list>" >&2
  exit 2
fi
SRC=${1%/} AXIOMS=$2 REPORT=$3 THEOREMS=$4
case $SRC in
  /* | ../* | . | '') echo "source dir must be a path below the project root" >&2; exit 2 ;;
esac
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

fail() { echo "FAIL: $*" >&2; exit 1; }

# grep exits 0 on a match, 1 on none and 2 on an error. errexit cannot
# enforce "must not match", so each status is handled here.
must_not_match() {
  local what=$1 status=0
  shift
  grep "$@" || status=$?
  case $status in
    0) fail "$what" ;;
    1) ;;
    *) fail "grep could not run ($what)" ;;
  esac
}

[ -d "$SRC" ] || fail "source directory $SRC not found"
# Module names: <source-dir>.lean, then every .lean file under it.
MODULES=$(
  { if [ -f "$SRC.lean" ]; then echo "$SRC.lean"; fi
    find "$SRC" -name '*.lean' | LC_ALL=C sort; } |
    sed -e 's/\.lean$//' -e 's#/#.#g'
)
[ -n "$MODULES" ] || fail "no .lean files under $SRC"

# 1. Rebuild from clean: the default targets, then every module under
# <source-dir> by name, since the default targets can leave out a file
# nothing imports.
lake clean || fail "lake clean failed"
MODULE_ARGS=()
while IFS= read -r module; do MODULE_ARGS+=("$module"); done <<< "$MODULES"
if ! { lake build && lake build "${MODULE_ARGS[@]}"; } > "$WORK/build.log" 2>&1; then
  tail -n 40 "$WORK/build.log" >&2
  fail "lake build failed"
fi

# 2. No placeholder in the build output or the sources. The source scan
# also matches comments, which errs on the safe side.
# Lean has quoted the name both ways ('sorry' and `sorry`) across releases.
must_not_match "a declaration uses sorry" -nE "declaration uses ['\`]sorry['\`]" "$WORK/build.log"
must_not_match "sorry or admit in the sources" -rnwE 'sorry|admit' --include='*.lean' "$SRC"

# 3. Regenerate the axioms report.
if ! lake env lean "$AXIOMS" > "$WORK/axioms.new" 2>&1; then
  cat "$WORK/axioms.new" >&2
  fail "lake env lean $AXIOMS failed"
fi

# 4. The theorem list names exactly the theorems written in the sources,
# read from the built environment. A theorem counts if it has source
# declaration ranges and is not private, which leaves out generated
# lemmas (eq_1, injEq, sizeOf_spec). A private theorem cannot be named
# in the axioms file; the placeholder checks above still cover it.
[ -f "$THEOREMS" ] || fail "theorem list $THEOREMS not found"
{
  echo "import Lean"
  echo "$MODULES" | sed 's/^/import /'
  echo 'open Lean in'
  echo '#eval show CoreM Unit from do'
  echo '  let env ← getEnv'
  echo "  let mods : Array Name := #[$(echo "$MODULES" | sed 's/^/`/' | paste -sd, -)]"
  echo '  for (n, ci) in env.constants.map₁.toList do'
  echo '    if let .thmInfo _ := ci then'
  echo '      if let some idx := env.getModuleIdxFor? n then'
  echo '        if mods.contains env.header.moduleNames[idx.toNat]! && !isPrivateName n then'
  echo '          if (← findDeclarationRanges? n).isSome then'
  echo '            IO.println n'
} > "$WORK/Inventory.lean"
if ! lake env lean "$WORK/Inventory.lean" > "$WORK/inventory.raw" 2>&1; then
  cat "$WORK/inventory.raw" >&2
  fail "could not read the theorem inventory from the built project"
fi
LC_ALL=C sort -u "$WORK/inventory.raw" > "$WORK/inventory.txt"
STATUS=0
grep -v -e '^[[:space:]]*$' -e '^#' "$THEOREMS" > "$WORK/listed.raw" || STATUS=$?
[ "$STATUS" -le 1 ] || fail "grep could not read $THEOREMS"
LC_ALL=C sort -u "$WORK/listed.raw" > "$WORK/listed.txt"
[ -s "$WORK/inventory.txt" ] || fail "no theorems found under $SRC"
UNLISTED=$(LC_ALL=C comm -23 "$WORK/inventory.txt" "$WORK/listed.txt")
[ -z "$UNLISTED" ] || fail "theorems in $SRC missing from $THEOREMS: $(echo $UNLISTED)"
UNKNOWN=$(LC_ALL=C comm -13 "$WORK/inventory.txt" "$WORK/listed.txt")
[ -z "$UNKNOWN" ] || fail "theorems in $THEOREMS not found in $SRC: $(echo $UNKNOWN)"

# 5. Every listed theorem is in the report.
COUNT=0
while IFS= read -r name || [ -n "$name" ]; do
  case $name in '' | '#'*) continue ;; esac
  COUNT=$((COUNT + 1))
  awk -v p="'$name' " 'index($0, p) == 1 && /depends? on (any )?axioms/ { found = 1 }
    END { exit !found }' "$WORK/axioms.new" ||
    fail "theorem $name is missing from the axioms report"
done < "$THEOREMS"
[ "$COUNT" -gt 0 ] || fail "theorem list $THEOREMS names no theorems"

# 6. The regenerated report matches the committed one.
STATUS=0
diff -u "$REPORT" "$WORK/axioms.new" || STATUS=$?
case $STATUS in
  0) ;;
  1) fail "axioms report differs from $REPORT" ;;
  *) fail "diff could not compare against $REPORT" ;;
esac

echo "OK: clean build, no placeholders, $COUNT theorems in an unchanged axioms report"
