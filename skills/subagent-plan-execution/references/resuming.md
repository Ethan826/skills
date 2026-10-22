# Resuming from an existing ledger

Part of subagent-plan-execution. Read this when this plan's workspace
already has a ledger at `<workspace>/progress.md`, or a stray ledger sits
at the old flat path `.superpowers/sdd/progress.md`.

If the ledger's first line names your plan file, every task with a
`Task <N>: complete` line is done: don't re-dispatch it, and resume at
the first task without one. A task whose last line is a fix round is
mid-loop, so resume the loop at the next round. A ledger whose first line
names a different plan file, or a stray ledger at the old flat path
`.superpowers/sdd/progress.md`, records another plan's progress. Leave it
where it is and start your own.
