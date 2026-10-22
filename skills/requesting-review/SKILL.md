---
name: requesting-review
description: Dispatches a fresh reviewer subagent to check finished work against its plan or requirements before problems spread into later work. The reviewer gets the whole commit range as one diff file and a filled-in prompt template, never the session's history, and returns a three-way verdict with findings graded Critical, Important or Minor. Use this after each task in a multi-task plan, after any major feature, and always before merging or landing a branch. Also use it when stuck or before a large refactor. Do not skip it because a change looks small. Replaces superpowers' requesting-code-review.
license: MIT
---

# Requesting Code Review

Dispatch a reviewer subagent to catch problems before they spread into
later work. Give the reviewer context you have written for the job, never
your session's history, so it judges the work product and not your
reasoning about it.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-plan-execution
- After completing a major feature
- Before merging to main

**Optional but valuable:**
- When you are stuck and want a fresh view
- Before a refactor, to get a baseline
- After fixing a complex bug

## How to Request

**1. Find the range.**

```bash
BASE_SHA=<the commit you recorded before the work began>
# no recorded base? use where the branch left main:
BASE_SHA=$(git merge-base origin/main HEAD)
HEAD_SHA=$(git rev-parse HEAD)
```

Never use `HEAD~1` as the base. It covers only the last commit, so a
task or branch with several commits is reviewed as if the earlier ones
did not exist, and nothing in the output tells you so.

**2. Put the diff in one file.**

The reviewer should read the change in one go instead of reconstructing
it with a string of git commands. Write the commit list, the stat
summary and the diff with wide context into a single file:

```bash
out=review-${BASE_SHA:0:7}..${HEAD_SHA:0:7}.diff
{
  echo "## Commits";       git log --oneline "$BASE_SHA..$HEAD_SHA"; echo
  echo "## Files changed"; git diff --stat "$BASE_SHA..$HEAD_SHA";  echo
  echo "## Diff";          git diff -U10 "$BASE_SHA..$HEAD_SHA"
} > "$out"
```

Write it outside the repository or in a git-ignored directory so it is
never committed. If subagent-plan-execution is installed, its
`scripts/review-package PLAN_FILE BASE HEAD` builds the same file in that
skill's workspace, checks that the range is not empty and that HEAD
descends from BASE, and prints the path.

**3. Dispatch the reviewer.**

Dispatch a subagent (any general-purpose agent your platform offers) with
the template in [code-reviewer.md](code-reviewer.md) filled in.

Name the model in the dispatch. An omitted model inherits the session's,
which may be weaker or more expensive than the review calls for. A review
before merge is a judgment task, so give it the most capable model
available.

**Placeholders:**
- `{DESCRIPTION}`: a brief summary of what you built
- `{PLAN_OR_REQUIREMENTS}`: what it should do
- `{BASE_SHA}`: the starting commit
- `{HEAD_SHA}`: the ending commit

The template also takes the model and the path of the diff file.

Do not tell the reviewer what not to flag. If you expect a finding to be
a false positive, let the reviewer raise it and settle it on the
evidence when the report comes back. A prompt that says "do not flag X",
"X is intentional" or "at most Minor" makes the call before anyone has
looked, and it usually exists to spare you a round of fixes.

If your platform cannot dispatch a subagent, read code-reviewer.md and
do the review yourself against the diff file, as a separate pass. Tell
your human partner it was a self-review. An author reviewing their own
work is weaker than a fresh reviewer, and your partner decides whether
that is enough before merge.

**4. Act on the report.**

The reviewer returns its report as text. If you keep a record of it, you
write that file yourself.

- Fix Critical issues immediately.
- Fix Important issues before you go on.
- Note Minor issues for later.
- On "Not ready", fix and then request a fresh review of the whole
  range. "Ready with fixes" needs only the listed fixes.
- Rule on each line under "Declined to judge". Each one is a behavior
  the reviewer set aside, and nothing should be dropped without a
  decision.
- Pass the escape-hatch list to your human partner before merge, even
  if every entry looks justified to you.
- Push back when the reviewer is wrong, with the code or test that shows
  it.

Use receiving-review for how to weigh and answer the findings.

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=a7981ec   # recorded before Task 2 started
HEAD_SHA=$(git rev-parse HEAD)
[Write review-a7981ec..3df7661.diff]

[Dispatch code reviewer subagent, most capable model]
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DIFF_FILE: review-a7981ec..3df7661.diff

[Subagent returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Declined to judge: none
  Escape hatches: none
  Assessment: Ready with fixes

You: [Fix progress indicators]
[Continue to Task 3]
```

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll just review the diff myself instead of dispatching a reviewer" | You are the coordinator. Reviewing the diff inline spends the context you need to keep driving the work. A reviewer subagent holds the diff and the evaluation in its own context and sends back only the findings. |
| "The reviewer needs my whole session history to understand the change" | Give it context written for the review, never your session's history. That keeps the reviewer on the work product instead of your thought process. |
| "`HEAD~1` is close enough for the base" | It drops every commit but the last. Use the base you recorded, or `git merge-base`. |
| "I'll tell the reviewer that X is intentional so it doesn't waste time on it" | That decides the finding before anyone has checked it. Let it be raised and settle it on the evidence. |

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If the reviewer is wrong:**
- Push back with technical reasoning
- Show the code or tests that prove it works
- Ask for clarification

See the template at [code-reviewer.md](code-reviewer.md).
