# The fix loop

Part of subagent-plan-execution. Read this before every fix round: the
task review reported spec FAIL, a Critical or Important finding, or a CANNOT VERIFY FROM DIFF
item you confirmed as a real gap.

Two kinds of finding leave before the loop starts:

- **Minor findings** go in the ledger as you go
  (`Task <N>: minor (deferred): <one-liner>`). Point the final review at
  that list so it can decide which must be fixed before merge; a roll-up
  nobody reads is a silent discard. Minor findings never enter the loop.
- **A finding labeled plan-mandated**, or any finding that conflicts with
  what the plan's text requires, is yours to rule on. Weigh it against the
  plan text, decide with the spec as the binding authority, and ledger the
  ruling before you act. Don't dismiss the finding because the plan
  mandates it, and don't dispatch a fix that contradicts the plan without
  a recorded ruling.

Everything else enters the loop. A fix round is one fix dispatch plus one
scoped re-review, and a task gets at most five rounds.

**Rounds 1 to 3: resume the original implementer.** Send it the open
findings verbatim. Its context is intact: it knows the task, the code and
its own choices. If your harness cannot send another message to a live
subagent, dispatch a fresh implementer with the brief path, the
report-file path and the findings. Either way the report file is the
persistent memory.

**Rounds 4 and 5: dispatch a fresh implementer on a more capable model**
(see [Model selection](../SKILL.md#model-selection)), with
the brief path, the report-file path, the open findings and this framing:
"A prior implementer attempted this task [N] times; you own it now. Read
the report file for what was tried." A loop that survives three resumes
usually means the implementer cannot see its own problem, and this gives
it fresh eyes and more capability at once. Dispatch it from
[implementer-prompt.md](../implementer-prompt.md).

**Every round:** the implementer fixes, re-runs the tests covering the
amended code, and returns its fix report as text. Append it to the same
report file. Before dispatching the re-review, check that the fix report
has the covering tests, the command run and the output. Name the covering
test files in the fix message; a one-line fix doesn't need the whole
suite.

**The re-review is scoped.** Run
`bash scripts/review-package PLAN_FILE FIX_BASE HEAD`, where FIX_BASE is
the head the previous review saw, and dispatch
[re-review-prompt.md](../re-review-prompt.md) with the findings list, the
brief, the report file and the printed diff path. Write its returned
report to `task-N-re-review-R.md`. The re-reviewer marks each finding
ADDRESSED or NOT ADDRESSED and flags new breakage in the fix diff only.
New Critical or Important breakage in the fix diff joins the open
findings. Out-of-scope observations go to the ledger as deferred minors
and never extend the loop.

**After each round,** append to the ledger:
`Task <N>: fix round <R>/5 (<X> addressed, <Y> open — <finding one-liners>; commits <a7>..<b7>)`

Never fix findings yourself in the controller session. Your context stays
clean for coordination, and a controller fix skips review.

**The breaker.** When round 5's re-review still leaves findings open, stop
dispatching. Adjudicate each open finding yourself, since you hold the
plan and the cross-task context the reviewer lacks:

- **The reviewer is wrong, or the point is contestable:** park it as
  `Task <N>: parked — <finding> — Ruling: <why the code stands>`. The final
  review sees both sides.
- **Real, but nothing downstream builds on it:** park it the same way,
  with a ruling that says it is real and deferred.
- **Real and load-bearing** (a later task builds on it, or it reveals a
  plan defect): rule on the smallest change that unblocks the dependent
  work, ledger it as
  `Task <N>: Ruling: <finding> — <what you decided and why>`, and carry it
  into the next task's dispatch. Parking a structural failure quietly lets
  every dependent task build on it. Stop only for a stop condition: the
  defect leaves every path forward a guess, it turns on a product decision
  the spec does not settle, or a project rule blocks the fix.

Adjudicate only at the cap; adjudicating earlier to end a loop is
pre-judging under another name. Every adjudication is a ledger entry, and
silent discards are forbidden.

When the loop ends, with every finding addressed or every open one parked
with a ruling at the cap, go back to SKILL.md's "Complete the task".
