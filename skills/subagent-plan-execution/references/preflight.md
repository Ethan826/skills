# The pre-flight conflict scan

Part of subagent-plan-execution. Run it once, at setup, before
dispatching Task 1.

Before dispatching Task 1, scan the plan once for conflicts, and write
down what you checked as you check it. Look for:

- tasks that contradict each other or the plan's Global Constraints;
- anything the plan explicitly mandates that the review rubric treats as
  a defect, such as a test that asserts nothing or a logic block
  duplicated verbatim.

The scan produces a table, not a verdict:

- one row for every pair of tasks that share a file or an interface,
  giving the two tasks, what one produces against what the other
  consumes, and what you found;
- one row for every task, saying whether its text agrees with itself:
  the tests it specifies against the code it specifies, and the files it
  creates against the files it later touches.

If you can't produce those rows, you haven't run the scan, whatever you
call it.

Write the table to the ledger. Rule on each conflict before execution
begins, weighing the finding against the plan text that mandates it, with
the spec as the binding authority and the plan as its argument. Record
each ruling beside its row, then dispatch Task 1. If the scan is clean,
go ahead without comment. The review loop still catches conflicts that
only show up during implementation.
