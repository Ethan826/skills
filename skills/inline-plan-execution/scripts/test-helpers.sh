#!/usr/bin/env bash
# Tests for the plan-execution helper scripts in this directory (sdd-repo,
# sdd-workspace, task-brief, review-package, and task-start and task-done
# where this directory has them). Runs in a scratch directory and touches
# nothing else. Also checks that every Markdown file in this skill that
# names a helper by its scripts/ path says to run it by its absolute path.
#
# This file ships identically in subagent-plan-execution/scripts and
# inline-plan-execution/scripts. Change both copies together.
#
# Usage: test-helpers.sh  (exit 0 when every case behaves as named)
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
skill=$(dirname "$here")
work=$(mktemp -d "${TMPDIR:-/tmp}/helpers-test.XXXXXX")
work=$(cd "$work" && pwd -P)
trap 'rm -rf "$work"' EXIT
# Keep git from finding a repository above the scratch directory.
export GIT_CEILING_DIRECTORIES=$work
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
cd "$work" || exit 2

passed=0
failed=0

pass() { echo "PASS  $1"; passed=$((passed + 1)); }
fail() {
  echo "FAIL  $1"
  [ -f "$work/out" ] && sed 's/^/      /' "$work/out"
  failed=$((failed + 1))
}

# expect WANT NAME CMD...: run CMD, compare its exit status with WANT.
# Output (stdout and stderr) is kept in $work/out for later checks.
expect() {
  local want=$1 name=$2 got
  shift 2
  "$@" >"$work/out" 2>&1
  got=$?
  if [ "$got" -eq "$want" ]; then
    pass "$name (exit $got)"
  else
    fail "$name (wanted exit $want, got $got)"
  fi
}

# has NAME TEXT: pass when the last command's output contains TEXT.
has() {
  if grep -qF -- "$2" "$work/out"; then pass "$1"; else fail "$1"; fi
}

# lacks NAME TEXT: pass when the last command's output does not contain TEXT.
lacks() {
  if grep -qF -- "$2" "$work/out"; then fail "$1"; else pass "$1"; fi
}

# file_has NAME FILE TEXT / file_lacks NAME FILE TEXT
file_has() {
  if [ -f "$2" ] && grep -qF -- "$3" "$2"; then pass "$1"; else fail "$1"; fi
}
file_lacks() {
  if [ -f "$2" ] && ! grep -qF -- "$3" "$2"; then pass "$1"; else fail "$1"; fi
}

h() { "${BASH:-bash}" "$here/$1" "${@:2}"; }

newrepo() {
  mkdir -p "$1"
  git -C "$1" init -q
  git -C "$1" config user.name test
  git -C "$1" config user.email test@example.com
}
commit() {
  printf '%s\n' "$2" >>"$1/file.txt"
  git -C "$1" add file.txt
  git -C "$1" commit -q -m "$2"
}

# ---------------------------------------------------------------- sdd-repo

mkdir -p outside
newrepo repo
commit repo one
newrepo empty

(cd outside && h sdd-repo) >"$work/out" 2>&1
got=$?
[ "$got" -eq 2 ] && pass "sdd-repo outside a working tree (exit 2)" \
  || fail "sdd-repo outside a working tree (wanted exit 2, got $got)"
has "the no-repo message names the current directory" "current directory: $work/outside"
has "the no-repo message ends with git's own line" "git said: fatal:"

(cd empty && h sdd-repo) >"$work/out" 2>&1
[ $? -eq 0 ] && pass "sdd-repo accepts a repository with no commit" \
  || fail "sdd-repo accepts a repository with no commit"
(cd empty && h sdd-repo --with-commit) >"$work/out" 2>&1
[ $? -eq 2 ] && pass "sdd-repo --with-commit refuses a repository with no commit" \
  || fail "sdd-repo --with-commit refuses a repository with no commit"
(cd repo && h sdd-repo --with-commit) >"$work/out" 2>&1
[ $? -eq 0 ] && grep -qx "$work/repo" "$work/out" \
  && pass "sdd-repo --with-commit prints the top level" \
  || fail "sdd-repo --with-commit prints the top level"
expect 2 "sdd-repo rejects an unknown argument" h sdd-repo extra

# ----------------------------------------------------------- sdd-workspace

cat >repo/plan.md <<'PLAN'
# Plan

## Global Constraints

- Port 8080.

## Task 1: First

Do one.

## Task 2: Second

Do two.
PLAN

(cd outside && h sdd-workspace "$work/repo/plan.md") >"$work/out" 2>&1
[ $? -eq 2 ] && pass "sdd-workspace outside a working tree (exit 2)" \
  || fail "sdd-workspace outside a working tree (exit 2)"
if [ -e outside/.superpowers ] || [ -e repo/.superpowers ]; then
  fail "sdd-workspace outside a working tree writes nothing"
else
  pass "sdd-workspace outside a working tree writes nothing"
fi

(cd outside && h sdd-workspace -C "$work/repo" "$work/repo/plan.md") >"$work/out" 2>&1
[ $? -eq 0 ] && grep -qx "$work/repo/.superpowers/sdd/plan" "$work/out" \
  && pass "sdd-workspace -C DIR uses DIR's working tree" \
  || fail "sdd-workspace -C DIR uses DIR's working tree"
expect 2 "sdd-workspace -C with a missing directory" h sdd-workspace -C "$work/nope" repo/plan.md

# -------------------------------------------------------------- task-brief

tb() { h task-brief "$@"; }
brief=$work/brief.md

expect 0 "task-brief writes task 1" tb repo/plan.md 1 "$brief"
file_has "the brief opens with the global constraints" "$brief" "Port 8080."
file_has "the brief holds task 1" "$brief" "Do one."
file_lacks "the brief stops before task 2" "$brief" "Do two."

(cd outside && h task-brief -C "$work/repo" plan.md 2) >"$work/out" 2>&1
[ $? -eq 0 ] && [ -f repo/.superpowers/sdd/plan/task-2-brief.md ] \
  && pass "task-brief -C DIR writes into DIR's workspace" \
  || fail "task-brief -C DIR writes into DIR's workspace"

cat >ids.md <<'PLAN'
# Plan

## Task 6: Six

six body

## Task 6b: Six b

six-b body

## Task 1: One

one body

## Task 1.1: One point one

one-one body

### Task 7: Seven

seven body

#### Task 7a: Seven a

seven-a body

### Task A1: Lane A

lane body

## Task Overview

overview body
PLAN

expect 0 "task-brief takes task 6" tb ids.md 6 "$brief"
file_lacks "task 6 leaves out sibling task 6b" "$brief" "six-b body"
expect 0 "task-brief takes task 6b" tb ids.md 6b "$brief"
file_has "task 6b is briefed whole" "$brief" "six-b body"
expect 0 "task-brief takes task 1" tb ids.md 1 "$brief"
file_lacks "task 1 leaves out sibling task 1.1" "$brief" "one-one body"
expect 0 "task-brief takes task 7" tb ids.md 7 "$brief"
file_has "task 7 keeps its deeper sub-task 7a" "$brief" "seven-a body"
file_lacks "task 7 stops at the next task" "$brief" "lane body"
expect 0 "task-brief takes an alphanumeric ID" tb ids.md A1 "$brief"
file_has "task A1 runs on through a heading without a digit" "$brief" "overview body"
expect 2 "task-brief rejects an ID with punctuation" tb ids.md '6(' "$brief"
expect 2 "task-brief rejects a path-like ID" tb ids.md '../x1' "$brief"
expect 2 "task-brief rejects an ID with no digit" tb ids.md Overview "$brief"
expect 3 "task-brief reports a missing task" tb ids.md 9 "$brief"
has "the missing task gets the not-found line" "task 9 not found"
lacks "a plan with Task headings gets no English-word hint" "English word"

cat >es.md <<'PLAN'
# Plan

## Tarea 1: Uno

uno
PLAN
expect 3 "task-brief on a plan with translated headings" tb es.md 1 "$brief"
has "it says task headings must use the English word" 'English word "Task"'
has "it lists the headings shaped like tasks" "## Tarea 1: Uno"

fence='```'
cat >fence-cut.md <<PLAN
# Plan

## Task 1: One

one body

## Task 2: Two

$fence
code left open

## Task 3: Three

three body
PLAN
expect 5 "an open fence that hides the next task refuses the brief" tb fence-cut.md 2 "$brief"
has "the refusal names where the fence opened" "line 9 of fence-cut.md never closes"
if [ -e "$brief" ]; then fail "the refused brief is not left behind"; else pass "the refused brief is not left behind"; fi
expect 3 "an open fence that hides the requested heading" tb fence-cut.md 3 "$brief"
has "the not-found error names the fence first" "line 9 of fence-cut.md never closes"
has "the not-found line still follows" "task 3 not found"
lacks "the fence case gets no English-word hint" "English word"
expect 0 "an open fence in a later task leaves an earlier brief alone" tb fence-cut.md 1 "$brief"
lacks "the earlier brief gets no fence warning" "never closes"

cat >fence-stray.md <<PLAN
# Plan

## Task 1: One

one body
$fence
PLAN
expect 0 "a stray fence that hides no task still briefs" tb fence-stray.md 1 "$brief"
has "the stray fence gets a warning" "it hides no Task heading, so this brief is complete"

printf '# Plan\n\n## Constraints\n\n- x\n\n## Task 1: One\n\nbody\n' >c1.md
expect 4 "a constraints heading other than Global Constraints" tb c1.md 1 "$brief"
printf '# Plan\n\n## Global Constraints\n\n- x\n\n## Global Constraints\n\n- y\n\n## Task 1: One\n\nbody\n' >c2.md
expect 4 "a second Global Constraints heading" tb c2.md 1 "$brief"
printf '# Plan\n\n## Global Constraints\n\n## Task 1: One\n\nbody\n' >c3.md
expect 4 "an empty Global Constraints section" tb c3.md 1 "$brief"
printf '# Plan\n\n## Task 1: One\n\nbody\n' >c4.md
expect 0 "a plan without constraints" tb c4.md 1 "$brief"
file_has "the brief says the plan has none" "$brief" "The plan has no Global Constraints section."

# ---------------------------------------------------------- review-package

base=$(git -C repo rev-parse HEAD)
commit repo two
head=$(git -C repo rev-parse HEAD)

(cd outside && h review-package -C "$work/repo" plan.md "$base" "$head") >"$work/out" 2>&1
[ $? -eq 0 ] && [ -f "repo/.superpowers/sdd/plan/review-${base:0:7}..${head:0:7}.diff" ] \
  && pass "review-package -C DIR writes DIR's range into DIR's workspace" \
  || fail "review-package -C DIR writes DIR's range into DIR's workspace"
(cd outside && h review-package "$work/repo/plan.md" "$base" "$head") >"$work/out" 2>&1
[ $? -eq 2 ] && grep -qF "SDD scripts must run" "$work/out" \
  && pass "review-package outside a working tree stops with the shared message" \
  || fail "review-package outside a working tree stops with the shared message"
(cd repo && h review-package plan.md "$head" "$head") >"$work/out" 2>&1
[ $? -eq 3 ] && pass "review-package refuses an empty range (exit 3)" \
  || fail "review-package refuses an empty range (exit 3)"
(cd repo && h review-package plan.md "$head" "$base") >"$work/out" 2>&1
[ $? -eq 3 ] && pass "review-package refuses a non-descendant HEAD (exit 3)" \
  || fail "review-package refuses a non-descendant HEAD (exit 3)"
(cd repo && h review-package plan.md nosuchref "$head") >"$work/out" 2>&1
[ $? -eq 2 ] && pass "review-package refuses a bad BASE (exit 2)" \
  || fail "review-package refuses a bad BASE (exit 2)"
cp repo/plan.md empty/plan.md
(cd empty && h review-package plan.md HEAD~1 HEAD) >"$work/out" 2>&1
[ $? -eq 2 ] && grep -qF "SDD scripts must run" "$work/out" \
  && pass "review-package in a repository with no commit stops with the shared message" \
  || fail "review-package in a repository with no commit stops with the shared message"

# ------------------------------------------------- task-start and task-done

if [ -f "$here/task-start" ]; then
  (cd repo && h task-start plan.md 1) >"$work/out" 2>&1
  [ $? -eq 0 ] && grep -qx "base: $head" "$work/out" \
    && grep -qx "brief: $work/repo/.superpowers/sdd/plan/task-1-brief.md" "$work/out" \
    && pass "task-start prints the brief path and BASE" \
    || fail "task-start prints the brief path and BASE"
  rm -rf repo/.superpowers
  (cd outside && h task-start "$work/repo/plan.md" 1) >"$work/out" 2>&1
  [ $? -eq 2 ] && grep -qF "SDD scripts must run" "$work/out" \
    && pass "task-start outside a working tree stops with the shared message" \
    || fail "task-start outside a working tree stops with the shared message"
  if [ -e repo/.superpowers ] || [ -e outside/.superpowers ]; then
    fail "task-start outside a working tree writes nothing"
  else
    pass "task-start outside a working tree writes nothing"
  fi
  (cd empty && h task-start plan.md 1) >"$work/out" 2>&1
  [ $? -eq 2 ] && ! grep -qF "base:" "$work/out" \
    && pass "task-start with no commit stops without printing a BASE" \
    || fail "task-start with no commit stops without printing a BASE"
  cp fence-cut.md repo/fence-cut.md
  (cd repo && h task-start fence-cut.md 2) >"$work/out" 2>&1
  [ $? -eq 5 ] && pass "task-start passes on task-brief's exit 5" \
    || fail "task-start passes on task-brief's exit 5"
fi

if [ -f "$here/task-done" ]; then
  (cd repo && h task-done plan.md 1 "$base" -- true) >"$work/out" 2>&1
  [ $? -eq 0 ] && grep -qF "Task 1: complete (commits ${base:0:7}..${head:0:7}" repo/.superpowers/sdd/plan/progress.md \
    && pass "task-done records a passing task in the ledger" \
    || fail "task-done records a passing task in the ledger"
  (cd repo && h task-done plan.md 2 "$base" -- false) >"$work/out" 2>&1
  [ $? -eq 1 ] && ! grep -qF "Task 2:" repo/.superpowers/sdd/plan/progress.md \
    && pass "task-done records nothing for a failing task" \
    || fail "task-done records nothing for a failing task"
  (cd outside && h task-done "$work/repo/plan.md" 1 "$base" -- true) >"$work/out" 2>&1
  [ $? -eq 2 ] && grep -qF "SDD scripts must run" "$work/out" \
    && pass "task-done outside a working tree stops with the shared message" \
    || fail "task-done outside a working tree stops with the shared message"
fi

# ------------------------------------------------------ helper invocations

# Every scripts/<helper> named in this skill's Markdown must say, within
# that line and the next three (joined), to run it by its absolute path: a helper run from
# the skill's own directory acts on the wrong working tree.
: >"$work/out"
while IFS= read -r md; do
  awk -v f="$md" '
    { line[NR] = $0 }
    END {
      for (i = 1; i <= NR; i++) {
        if (line[i] !~ /scripts\/(sdd-workspace|task-brief|review-package|task-start|task-done)/) continue
        text = ""
        for (j = i; j <= i + 3 && j <= NR; j++) text = text " " line[j]
        gsub(/[ \t]+/, " ", text)
        if (text !~ /by its absolute path/) print f ":" i ": " line[i]
      }
    }' "$md" >>"$work/out"
done < <(find "$skill" -name '*.md')
if [ -s "$work/out" ]; then
  fail "every helper invocation says to run it by its absolute path"
else
  pass "every helper invocation says to run it by its absolute path"
fi

echo "$passed passed, $failed failed"
[ "$failed" -eq 0 ]
