# "Cannot verify from diff" items

Part of subagent-plan-execution. Read this when a task reviewer reports
"CANNOT VERIFY FROM DIFF" items or a "Not judged" list, before you mark
the task complete.

The reviewer may report "CANNOT VERIFY FROM DIFF" items: requirements
that live in unchanged code or span tasks. They don't block the rest of
the review, but resolve each one yourself before marking the task
complete, since you hold the plan and the cross-task context the reviewer
lacks. If an item turns out to be a real gap, treat it as a failed spec
review: it enters the fix loop with the other findings. Read the
reviewer's "Not judged" list the same way, and cover anything on it that
matters.
