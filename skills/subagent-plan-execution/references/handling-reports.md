# Handling a report that isn't DONE

Part of subagent-plan-execution. Read this every time an implementer
returns DONE_WITH_CONCERNS, NEEDS_CONTEXT or BLOCKED, after you have
written the report to `task-N-report.md`.

**DONE_WITH_CONCERNS:** The implementer finished but has doubts. If they
concern correctness or scope, deal with them before review. If they are
observations ("this file is getting large"), note them and go on.

**NEEDS_CONTEXT:** The implementer needs information it wasn't given.
Supply it and re-dispatch. If the missing piece is a product decision the
spec does not settle, that is a stop condition: ask your human partner.

**BLOCKED:** The implementer cannot finish. Work out why:

1. a context problem: give it more context and re-dispatch on the same
   model;
2. the task needs more reasoning: re-dispatch on a more capable model;
3. the task is too large: break it into smaller pieces;
4. the plan itself is wrong: rule on the correction, ledger it, and
   re-dispatch with the ruling in the dispatch;
5. a project rule blocks the work: that is a stop condition. Report the
   rule and the line to your human partner.

Don't ignore an escalation, and don't make the same model retry with
nothing changed: if the implementer says it is stuck, something has to
change.
