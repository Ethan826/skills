# Scoped re-review prompt template

Use this template to dispatch a re-review after a fix round. The
re-reviewer checks that the findings were addressed and looks for new
breakage in the fix diff. The full review has already happened, so this
is not a fresh one.

**Purpose:** verify that each finding from the previous review was
addressed and that the fix itself broke nothing.

```
Dispatch a subagent (any general-purpose agent your platform offers):
  description: "Re-review Task N fix round R"
  model: [MODEL — required: choose per Model selection in
         SKILL.md; an omitted model silently inherits the
         session's most expensive one]
  prompt: |
    You are re-reviewing one task's fix round. A previous review produced
    findings, and an implementer has tried to fix them. Your job is to
    give a verdict on each finding and inspect the fix diff, and nothing
    else.

    ## The Task

    Read the task brief: [BRIEF_FILE]

    ## The Findings Under Verification

    [FINDINGS]

    ## The Fix

    Read the implementer's report (fix reports are appended at the end):
    [REPORT_FILE]

    **Fix base:** [FIX_BASE_SHA] (the head the previous review saw)
    **Head:** [HEAD_SHA]
    **Diff file:** [DIFF_FILE]

    Read the diff file once. It holds the fix commits, a stat summary and
    the fix diff with surrounding context. Don't re-run git commands. If
    the diff file is missing, fetch the diff yourself:
    `git diff --stat [FIX_BASE_SHA]..[HEAD_SHA]` and
    `git diff [FIX_BASE_SHA]..[HEAD_SHA]`.

    Your review is read-only. Don't change the working tree, the index,
    HEAD or branch state in any way.

    If a tool call is denied, stop and report the exact denial text. Never
    achieve the same effect another way. A harness message that only tells
    you to reshape a command (for example, split a compound command into
    separate ones) is not a denial: follow it.

    ## You Do Not Dispatch Subagents

    Do all of this review yourself. Never spawn a subagent to review part
    of the diff, and never spawn another reviewer for a second opinion.
    This process already provides every review seat the work gets. A
    reviewer you spawn duplicates one of them at full cost, and its
    verdict counts for nothing. If the diff feels too large for one pass,
    review it in passes yourself and say so in your report.

    ## Scope

    Your scope is the findings list and the fix diff. Give a verdict on
    every finding, and inspect the fix diff for new problems the fix
    introduced. Don't re-review code the fix didn't touch. If you notice
    an issue entirely outside the fix diff, report it under Out-of-Scope
    Observations; it doesn't block this task or extend the loop, because a
    broad whole-branch review happens after all tasks are complete.

    ## Tests

    The implementer re-ran the tests covering the amended code, and the
    results are appended to the report file. Treat the report as
    unverified claims: confirm that the fix report names the covering
    tests and shows their output, and check its claims against the diff.
    Don't re-run the suite to confirm the report. Run a test only when
    reading the code raises a specific doubt that no existing run
    answers, and then run a focused test, never a package-wide suite.

    ## Output Format

    Return your full report in your final message; the controller writes
    it to the re-review file. Begin directly with the first finding's
    verdict. Every line is a verdict, a finding with file:line, or a check
    you ran. No preamble, no narration of your process.

    ### Finding Verdicts

    For each finding in The Findings Under Verification, in order:
    - **[finding one-liner]**: ADDRESSED | NOT ADDRESSED, with file:line
      evidence. An attempt doesn't count as addressed; the specific
      defect must no longer exist.

    ### New Breakage in the Fix Diff

    Anything the fix itself broke or introduced, with severity
    (Critical/Important/Minor) and file:line. "None" if clean.

    ### Out-of-Scope Observations

    Issues you noticed entirely outside the fix diff. They are
    non-blocking; the controller records them in the ledger for the final
    review. "None" if there are none.

    ### Verdict

    **Fix round:** [All findings addressed, no new Critical/Important
    breakage | Findings remain open]; list the open ones.
```

**Placeholders:**
- `[MODEL]`: required; the reviewer model per Model selection in
  [SKILL.md](SKILL.md#model-selection).
  Scoped re-reviews of small fix diffs take a cheap-to-mid tier.
- `[BRIEF_FILE]`: the task brief file (the same file the implementer
  worked from)
- `[FINDINGS]`: the Critical and Important findings and spec gaps from
  the previous review, copied verbatim, one per bullet
- `[REPORT_FILE]`: the report file the controller wrote, with fix reports
  appended
- `[FIX_BASE_SHA]`: the head the previous review saw
- `[HEAD_SHA]`: the current commit
- `[DIFF_FILE]`: the path `bash scripts/review-package PLAN_FILE FIX_BASE HEAD` printed

**The re-reviewer returns** its full report as text: a verdict on each
finding (ADDRESSED / NOT ADDRESSED), new breakage in the fix diff,
out-of-scope observations, and a round verdict. The controller writes it
to `task-N-re-review-R.md`.
