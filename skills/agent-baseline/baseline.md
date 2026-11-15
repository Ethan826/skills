<!-- agent-baseline:start v3 -->
## Agent baseline

These rules hold in every session and every subagent. They live here
because skills load only when they trigger, and this file is always read.
The agent-baseline skill installs this block from its source file, so
change that file and reinstall.

- Own every failure you see: name it in your report, then fix it or file
  it. "Already broken" exempts nothing, and a check that fails and then
  passes on a rerun has still failed. Fix every instance of a pattern,
  including the ones nobody pointed at. Writing a limitation down instead
  of fixing it keeps the failure. Treat each check as a floor: never
  loosen a tolerance, weaken an assertion or delete a test to get green
  (root-cause-debugging).
- Never use an escape hatch: no lint-disable or type-checker suppression
  comments, no casts or non-null assertions to silence the compiler, no
  skipped or focused tests, no new allowlist entries, and no edits to
  checks or configs to get green. Overriding a rule on your own judgment
  is worse than a mistake, however good the reason. If a rule blocks you,
  stop and report the line and the rule.
- In coding practice, take the stricter option without asking. Product
  decisions, such as a threshold, a default or behavior a user would
  notice, go to the human.
- Run the command that proves a claim before you make the claim
  (verify-before-claiming).
- Stage explicit paths, never a directory. Leave the user's untracked
  files alone; they are the user's work in progress.
- Never push, publish or file anything remotely without an explicit OK
  for that action. One OK covers one action. If CI or deploys are
  billed, batch commits and wait to be asked (landing-a-branch).
- If a tool call is denied, stop and quote the denial. Never reach the
  same effect another way, since that defeats the policy behind the
  denial. A message that only asks you to reshape a command
  is not a denial; follow it.
- Brief every subagent as if it sees only this file and its brief. Some
  harnesses pass memory or the conversation to a subagent and some do
  not, so never rely on either. Put the rules a subagent needs in this
  file or in its brief (dispatching-agents).
- Before expensive agent work, state the cost, and wait for a yes when
  the cost is large; the human pays for it. Answer status questions
  cheaply.
- Count a finding as captured only once it has a durable record, such as
  an issue. A chat message or an agent report does not count
  (decisions-as-issues).
- Use no emoji anywhere. Write words such as PASS and FAIL instead.
<!-- agent-baseline:end -->
