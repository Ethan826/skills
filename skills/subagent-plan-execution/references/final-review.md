# Final review and finish

Part of subagent-plan-execution. Read this when every task in the plan
is complete, before you dispatch the final reviewer.

## Final review

Run `bash scripts/review-package PLAN_FILE MERGE_BASE HEAD` (MERGE_BASE is
the commit the branch started from, for example `git merge-base main HEAD`)
and put the printed path in the final review dispatch, so the reviewer
reads one file instead of re-deriving the branch diff. Dispatch it on the
most capable model available (see
[Model selection](../SKILL.md#model-selection)), using
requesting-review's
[code-reviewer.md](../../requesting-review/code-reviewer.md). Point it at the
ledger's deferred-minor and parked lines so it can decide which must be
fixed before merge. Write its returned report to `final-review.md`.

### The escape-hatch grep

**Run the escape-hatch grep** over the whole branch before the final
review, and hand the hits to the final reviewer, which judges whether
each one is justified. It lists the ways a check can be switched off
rather than satisfied: directive comments, type-checker suppressions,
casts, skipped or focused tests, and edits to lint configs or check
scripts. The patterns below are a starting point; add the equivalents
for the project's languages and drop any that only produce noise there.

```bash
# Added lines that switch a check off
git diff -U0 MERGE_BASE HEAD | grep -nE '^\+.*(lint-disable|eslint-disable|noqa|nolint|type: *ignore|@ts-(ignore|expect-error|nocheck)|#\[allow|@Suppress|as any|as unknown|\.skip\(|\.only\(|\bxit\(|\bfit\(|fdescribe|@pytest\.mark\.skip|t\.Skip)'
# Files that configure or run the checks
git diff --name-only MERGE_BASE HEAD | grep -iE 'lint|eslint|ruff|flake8|pylint|tsconfig|pyproject|setup\.cfg|golangci|clippy|Makefile|(^|/)scripts/check'
```

List every hit for your human partner in your final message, with the
reviewer's judgment beside it, including the ones it found justified. A
hit the reviewer accepts is still a decision your human partner should
see.

### The fix wave

If the final review returns findings, dispatch one fix subagent with the
complete findings list, from the implementer template
([implementer-prompt.md](../implementer-prompt.md)), so it carries the
same rules. Don't dispatch one fixer per finding: each would rebuild
context and re-run suites, and in one real session a final-review fix wave
done that way cost more than all the tasks together. Then run exactly one
scoped re-review of the fix wave
(`bash scripts/review-package PLAN_FILE FIX_BASE HEAD` over the fix range,
[re-review-prompt.md](../re-review-prompt.md)). Adjudicate any residual
findings as in the fix loop's breaker ([fix-loop.md](fix-loop.md)): park
them with rulings, or rule on the load-bearing ones and ledger what you
decided. Only the stop conditions at the top of SKILL.md stop you here.
There is no second fix wave; residual load-bearing findings reach your
human partner when landing-a-branch presents the options.

## Finish

Before you delete anything, collect every ledger line containing
`Ruling:` (pre-flight rulings, parked findings, breaker adjudications,
all of them) into your final message under "Rulings I made", in the order
you made them, each with what it costs if wrong. The list is exhaustive:
if the ledger holds a ruling, the list holds it. It is the only place
your human partner sees the decisions you took on their behalf, and they
read it to rework whatever you got wrong. Put the escape-hatch list in
the same message.

When the final review is clean and its fixes are merged, delete this
plan's workspace (`rm -rf <workspace>`); the git history is the record
now. Sibling directories belong to other plans, so leave them alone. If
the plan is a working file under `.superpowers/plans/`, delete it when the
branch lands, after checking that any decision that must outlive the
branch is in the issue.

Use landing-a-branch.
