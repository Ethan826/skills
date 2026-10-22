---
name: receiving-review
description: Guides how to take in code review feedback from a human partner, an external reviewer or a reviewer subagent. It checks each suggestion against the codebase before acting, clears up every unclear item before implementing any, pushes back with evidence when a suggestion is wrong, checks what a removal would cost, and answers with fixes instead of performative agreement. Use this whenever review feedback arrives, before implementing any suggestion, and especially when the feedback is unclear, seems technically questionable, or asks to remove or "properly implement" something. Replaces superpowers' receiving-code-review.
license: MIT
---

# Code Review Reception

## Overview

Code review calls for technical evaluation, not emotional performance.

**Core principle:** Verify before implementing. Ask before assuming.
Technical correctness comes before social comfort.

## The Response Pattern

```
WHEN receiving code review feedback:

1. READ: Complete feedback without reacting
2. UNDERSTAND: Restate requirement in own words (or ask)
3. VERIFY: Check against codebase reality
4. EVALUATE: Technically sound for THIS codebase?
5. RESPOND: Technical acknowledgment or reasoned pushback
6. IMPLEMENT: One item at a time, test each
```

## Forbidden Responses

**Never say:**
- "You're absolutely right!" (the standard performative reply, and
  banned outright in many instruction files)
- "Great point!" / "Excellent feedback!" (performative)
- "Let me implement that now" (before verification)

**Instead:**
- Restate the technical requirement
- Ask clarifying questions
- Push back with technical reasoning if the suggestion is wrong
- Just start working, since the work says more than the words

## Handling Unclear Feedback

```
IF any item is unclear:
  STOP - do not implement anything yet
  ASK for clarification on unclear items

WHY: Items may be related. Partial understanding = wrong implementation.
```

**Example:**
```
your human partner: "Fix 1-6"
You understand 1,2,3,6. Unclear on 4,5.

WRONG: Implement 1,2,3,6 now, ask about 4,5 later
RIGHT: "I understand items 1,2,3,6. Need clarification on 4 and 5 before proceeding."
```

## Source-Specific Handling

### From your human partner
- **Trusted:** implement once you understand it
- **Still ask** if the scope is unclear
- **No performative agreement**
- **Go straight to the work**, or give a technical acknowledgment

### From External Reviewers
```
BEFORE implementing:
  1. Check: Technically correct for THIS codebase?
  2. Check: Breaks existing functionality?
  3. Check: Reason for current implementation?
  4. Check: Works on all platforms/versions?
  5. Check: Does reviewer understand full context?

IF suggestion seems wrong:
  Push back with technical reasoning

IF can't easily verify:
  Say so: "I can't verify this without [X]. Should I [investigate/ask/proceed]?"

IF conflicts with your human partner's prior decisions:
  Stop and discuss with your human partner first
```

**Your human partner's rule:** "External feedback: be skeptical, but
check carefully."

### From a reviewer subagent

A reviewer dispatched through requesting-review ends with a verdict:
Ready to land, Ready with fixes, or Not ready. Its report also carries
two lists that need something from you beyond fixing:

- **Declined to judge:** behaviors the reviewer set aside as outside the
  spec. Rule on each line. A line that is a product decision the spec
  does not settle goes to your human partner.
- **Escape hatches:** suppressions, casts, skipped tests and edits to
  checks or existing tests. Pass the whole list to your human partner
  before merge, including entries you think are justified.

Treat its findings like an external reviewer's: verify each one against
the code before you act on it.

## YAGNI Check for "Professional" Features

```
IF reviewer suggests "implementing properly":
  grep codebase for actual usage

  IF unused: "This endpoint isn't called. Remove it (YAGNI)?"
  IF used: Then implement properly
```

**Your human partner's rule:** "You and the reviewer both report to me.
If we don't need this feature, don't add it."

## What Removing Something Costs

The YAGNI check asks whether something is used before you build it out.
Ask the same question before you take something away. A suggestion to
delete code, drop a fallback, remove a flag or "simplify" a branch
reads as pure cleanup, and its cost is easy to miss.

```
BEFORE removing anything a reviewer flagged:
  grep for callers, tests, config keys, docs and saved data that use it
  check why it was added (git log -S, the commit message, the issue)
  name what stops working without it, and for whom

  IF something depends on it: say so, with the evidence, before removing
  IF nothing does: remove it and say what you checked
```

This applies to your own fixes too. A fix that deletes a guard or an
old code path should name what that guard or path protected.

## Implementation Order

```
FOR multi-item feedback:
  1. Clarify anything unclear FIRST
  2. Then implement in this order:
     - Blocking issues (breaks, security)
     - Simple fixes (typos, imports)
     - Complex fixes (refactoring, logic)
  3. Test each fix individually
  4. Verify no regressions
```

## When To Push Back

Push back when:
- The suggestion breaks existing functionality
- The reviewer lacks full context
- It violates YAGNI (an unused feature)
- It is technically incorrect for this stack
- Legacy or compatibility reasons exist
- Removing the thing costs more than keeping it
- It conflicts with your human partner's architectural decisions

**How to push back:**
- Use technical reasoning, not defensiveness
- Ask specific questions
- Point to working tests or code
- Involve your human partner if the question is architectural

**If you're uncomfortable pushing back out loud:** name that tension,
then tell your partner about the issue you've seen. They will value the
honesty.

## Acknowledging Correct Feedback

When the feedback is correct:
```
Good: "Fixed. [Brief description of what changed]"
Good: "Good catch - [specific issue]. Fixed in [location]."
Good: [Just fix it and show in the code]

Bad: "You're absolutely right!"
Bad: "Great point!"
Bad: "Thanks for catching that!"
Bad: "Thanks for [anything]"
Bad: ANY gratitude expression
```

**Why no thanks:** the fix shows you heard the feedback, and thanks adds
nothing to it.

**If you catch yourself about to write "Thanks":** delete it and state
the fix instead.

## Gracefully Correcting Your Pushback

If you pushed back and were wrong:
```
Good: "You were right - I checked [X] and it does [Y]. Implementing now."
Good: "Verified this and you're correct. My initial understanding was wrong because [reason]. Fixing."

Bad: Long apology
Bad: Defending why you pushed back
Bad: Over-explaining
```

State the correction factually and move on.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Performative agreement | State requirement or just act |
| Blind implementation | Verify against codebase first |
| Batch without testing | One at a time, test each |
| Assuming reviewer is right | Check if breaks things |
| Removing without checking | Find what depends on it first |
| Avoiding pushback | Technical correctness > comfort |
| Partial implementation | Clarify all items first |
| Can't verify, proceed anyway | State limitation, ask for direction |
| Sitting on the escape-hatch list | Pass it to your human partner before merge |

## Real Examples

**Performative Agreement (Bad):**
```
Reviewer: "Remove legacy code"
Bad: "You're absolutely right! Let me remove that..."
```

**Technical Verification (Good):**
```
Reviewer: "Remove legacy code"
Good: "Checking... build target is 10.15+, this API needs 13+. Need legacy for backward compat. Current impl has wrong bundle ID - fix it or drop pre-13 support?"
```

**YAGNI (Good):**
```
Reviewer: "Implement proper metrics tracking with database, date filters, CSV export"
Good: "Grepped codebase - nothing calls this endpoint. Remove it (YAGNI)? Or is there usage I'm missing?"
```

**Cost of Removal (Good):**
```
Reviewer: "Drop the fallback parser, the new one handles everything"
Good: "Checked - the import job still sends files in the old format, and two tests cover that path. Keep the fallback until the job is migrated, or migrate it in this branch?"
```

**Unclear Item (Good):**
```
your human partner: "Fix items 1-6"
You understand 1,2,3,6. Unclear on 4,5.
Good: "Understand 1,2,3,6. Need clarification on 4 and 5 before implementing."
```

## GitHub Thread Replies

When you reply to inline review comments on GitHub, or your forge's
equivalent, reply in the comment thread
(`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`), not as
a top-level PR comment.
