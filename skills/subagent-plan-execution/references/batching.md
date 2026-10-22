# Batching small edits of the same shape

Part of subagent-plan-execution. Read this before dispatching several
small edits of the same kind across files.

**Batch small edits of the same shape.** When the plan lists several
tasks that are each a small, independent edit of the same kind (the same
one-line fix, constant change or field addition repeated across files),
don't dispatch one subagent per task. Write one brief listing every file
and its change, send the whole batch to a single subagent, and review its
diff as one unit. Keep one dispatch per task for work that needs its own
judgment, its own tests or its own review.
