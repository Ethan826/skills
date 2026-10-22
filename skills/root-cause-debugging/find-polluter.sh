#!/usr/bin/env bash
# Bisection script to find which test creates unwanted files/state
# Usage: ./find-polluter.sh <file_or_dir_to_check> <test_pattern>
# Example: ./find-polluter.sh '.git' 'src/**/*.test.ts'
#
# Runs `npm test <file>` for each matching test file, one at a time, and
# stops at the first one after which the pollution exists.
#
# Exit status:
#   0  every candidate ran and passed, and none created the pollution
#   1  polluter found
#   2  the search could not start: bad usage, no matching test files,
#      pollution already present, or npm not found
#   3  no polluter found, but at least one test command failed, so the
#      search is inconclusive (a failing run may never reach the code
#      that pollutes)

set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Usage: $0 <file_to_check> <test_pattern>"
  echo "Example: $0 '.git' 'src/**/*.test.ts'"
  exit 2
fi

POLLUTION_CHECK="$1"
TEST_PATTERN="$2"

echo "Searching for test that creates: $POLLUTION_CHECK"
echo "Test pattern: $TEST_PATTERN"
echo ""

if ! command -v npm > /dev/null 2>&1; then
  echo "ERROR: npm not found on PATH; no tests were run" >&2
  exit 2
fi

# The search means nothing if the pollution is already there: every test
# would look clean or every test would look guilty. Remove it first.
if [ -e "$POLLUTION_CHECK" ]; then
  echo "ERROR: $POLLUTION_CHECK already exists before any test ran" >&2
  echo "Remove it and run the script again; no tests were run" >&2
  exit 2
fi

# Get list of test files (find . emits ./-prefixed paths, so accept the
# pattern written with or without a leading ./)
TEST_PATTERN="${TEST_PATTERN#./}"
# find -path can't match '**/' against zero directory levels, so a pattern
# like src/**/*.test.ts would skip src/top.test.ts; also try the pattern
# with '**/' collapsed to cover files directly under the base directory.
TEST_FILES=()
while IFS= read -r f; do
  TEST_FILES+=("$f")
done < <(find . \( -path "./$TEST_PATTERN" -o -path "./${TEST_PATTERN//\*\*\//}" \) | sort -u)
TOTAL=${#TEST_FILES[@]}

if [ "$TOTAL" -eq 0 ]; then
  echo "ERROR: no test files match '$TEST_PATTERN' under $(pwd)" >&2
  echo "Check the pattern and the directory; no tests were run" >&2
  exit 2
fi

echo "Found $TOTAL test files"
echo ""

LOG_DIR=$(mktemp -d "${TMPDIR:-/tmp}/find-polluter.XXXXXX")
RAN=0
FAILED=()
for TEST_FILE in "${TEST_FILES[@]}"; do
  RAN=$((RAN + 1))
  echo "[$RAN/$TOTAL] Testing: $TEST_FILE"

  LOG="$LOG_DIR/$RAN.log"
  if npm test "$TEST_FILE" > "$LOG" 2>&1; then
    STATUS=0
  else
    STATUS=$?
    FAILED+=("$TEST_FILE (exit $STATUS, log: $LOG)")
    echo "   test command failed (exit $STATUS); output in $LOG"
  fi

  if [ -e "$POLLUTION_CHECK" ]; then
    echo ""
    echo "FOUND POLLUTER (after $RAN of $TOTAL candidates)"
    echo "   Test: $TEST_FILE"
    echo "   Created: $POLLUTION_CHECK"
    if [ "$STATUS" -ne 0 ]; then
      echo "   Note: this test also failed (exit $STATUS); see $LOG"
    fi
    echo ""
    echo "Pollution details:"
    ls -la "$POLLUTION_CHECK"
    echo ""
    echo "To investigate:"
    echo "  npm test $TEST_FILE    # Run just this test"
    echo "  cat $TEST_FILE         # Review test code"
    exit 1
  fi
done

echo ""
if [ "${#FAILED[@]}" -gt 0 ]; then
  echo "INCONCLUSIVE: ran $RAN of $TOTAL candidates; none created" \
    "$POLLUTION_CHECK, but ${#FAILED[@]} test command(s) failed:"
  for f in "${FAILED[@]}"; do
    echo "   $f"
  done
  echo "A failed run may stop before the code that pollutes. Fix the" \
    "runner or setup failures and run again."
  exit 3
fi

echo "No polluter found: ran $RAN of $TOTAL candidates, all passed," \
  "none created $POLLUTION_CHECK"
rm -rf "$LOG_DIR"
exit 0
