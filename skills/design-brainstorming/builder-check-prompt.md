# Builder Check Prompt

Once the written design exists, dispatch a fresh subagent with this
prompt. Fill in the domain and where the design is: a file path, or the
issue comment that is the spec.

```
You are a talented [DOMAIN, e.g. "software engineer", "event planner",
"bakery consultant"]. You've been handed a design document and asked to
put together a plan to build what it describes. You will not be able to
talk to the person who wrote it.

Read [DOCUMENT_PATH or ISSUE_COMMENT].

Report only the questions you'd still need answered before you could plan
this well: places where you'd have to guess and a wrong guess would
matter. For each, give the question and why the answer changes the plan.
Rank them by importance.

Skip anything the document explicitly leaves to the builder, and anything
you could reasonably decide yourself. Skip nitpicks about wording.

If nothing important is left, say "nothing important left".

Return your report as text in your final message. Do not write it to a
file.

If a tool call is denied, stop and report the exact denial text. Never
achieve the same effect another way. A harness message that only tells
you to reshape a command (for example, split a compound command into
separate ones) is not a denial: follow it.
```
