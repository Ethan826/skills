---
name: root-cause-debugging
description: Finds the root cause of a bug before any fix is written, in four phases (investigate, compare against working code, test one hypothesis, fix at the source with a failing test first). Use it whenever a test fails, a build breaks, behavior surprises you, a bug report or ticket arrives, or a test "passes on rerun", and use it before proposing any fix, even one that looks obvious. It matters most under time pressure, after a fix has already failed, and when a failure looks flaky, environmental or "not ours". It covers reading raw data before the code that interprets it, treating reports as claims, capturing errors before re-running, checking for a stale baseline, verifying a blocker before settling for a weaker fix, and handing product decisions to your human partner after three failed fixes. Replaces superpowers' systematic-debugging.
license: MIT
---

# Root-Cause Debugging

## Overview

Find the root cause before you attempt a fix. A fix aimed at a symptom
leaves the cause in place, so the bug comes back somewhere else, often
with the evidence gone.

Following the letter of this process is how you follow its spirit. The
steps exist because the shortcuts around them feel reasonable at the
moment you take them.

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

Until you have finished Phase 1, do not propose a fix.

## When to Use

Use this for any technical problem:
- test failures
- bugs in production
- unexpected behavior
- performance problems
- build failures
- integration issues

It matters most when:
- you are under time pressure, because emergencies make guessing
  tempting;
- one quick fix seems obvious;
- you have already tried several fixes, or the last one didn't work;
- you don't fully understand the problem.

Don't skip it when:
- the problem looks simple, since simple bugs have root causes too;
- you are in a hurry, since rushing guarantees rework;
- someone wants it fixed now, since a systematic search is faster than
  thrashing.

## The Four Phases

Finish each phase before starting the next.

### Phase 1: Root Cause Investigation

Before attempting any fix:

1. **Read the error messages carefully**
   - Don't skip past errors or warnings. They often contain the exact
     answer.
   - Read stack traces all the way through.
   - Note line numbers, file paths and error codes.

2. **Read the raw data before the code that interprets it**
   - For anything that transforms data (a parser, a matcher, a pricing
     rule, a report), look at the inputs themselves first: the records,
     timestamps, payloads, rows. A short script over the raw input is
     cheap.
   - The data may show that the behavior is correct and the expectation
     is wrong. A fix written against correct behavior removes something
     that was right.

3. **Treat the report as a claim**
   - A ticket, a bug report or an agent's diagnosis states a mechanism.
     Quoting real code proves the code exists, not that the path runs.
   - Observe the mechanism before fixing what it implies: spy on the
     actual request, run the actual query, assert the actual status.
   - When the premise turns out to be wrong, record the correction on
     the issue. The correction is the more useful half.

4. **Reproduce consistently**
   - Can you trigger it reliably? What are the exact steps? Does it
     happen every time?
   - Capture the full error before re-running. The re-run destroys the
     evidence.
   - If you can't reproduce it, gather more data rather than guessing.
     See [There Is No Such Thing as a Flake](#there-is-no-such-thing-as-a-flake).

5. **Check recent changes**
   - What changed that could cause this? Look at the git diff and recent
     commits.
   - New dependencies, config changes, environmental differences.
   - Stale build output or a stale dev-server cache.

6. **Check that the baseline is current**
   - Before calling something a regression, check `git merge-base main
     <branch>` and `git log <merge-base>..main` for unrelated changes to
     the same code path.
   - A branch that forked before another change landed will differ from
     main by that change too. Rebuild the "before" from the branch's own
     merge-base, or rebase first.
   - A figure in a document can be stale. Recompute it.

7. **Gather evidence in multi-component systems**

   When the system has several components (CI → build → signing,
   API → service → database), add diagnostic instrumentation before you
   propose a fix:
   ```
   For EACH component boundary:
     - Log what data enters component
     - Log what data exits component
     - Verify environment/config propagation
     - Check state at each layer

   Run once to gather evidence showing WHERE it breaks
   THEN analyze evidence to identify failing component
   THEN investigate that specific component
   ```

   Example (multi-layer system):
   ```bash
   # Layer 1: Workflow
   echo "=== Secrets available in workflow: ==="
   echo "IDENTITY: $([ -n "${IDENTITY:-}" ] && echo SET || echo UNSET)"

   # Layer 2: Build script
   echo "=== Env vars in build script: ==="
   printenv IDENTITY >/dev/null 2>&1 && echo "IDENTITY in environment" || echo "IDENTITY not in environment"

   # Layer 3: Signing script
   echo "=== Keychain state: ==="
   security list-keychains
   security find-identity -v

   # Layer 4: Actual signing
   codesign --sign "$IDENTITY" --verbose=4 "$APP"
   ```

   One run shows which layer fails: secrets reach the workflow, but
   the workflow doesn't pass them to the build.

8. **Trace the data flow**

   When the error is deep in a call stack, use the backward tracing
   technique in [root-cause-tracing.md](root-cause-tracing.md). In short:
   - Where does the bad value originate?
   - What called this with the bad value?
   - Keep tracing up until you find the source.
   - Fix it at the source, not where the symptom shows.

### Phase 2: Pattern Analysis

Find the pattern before fixing:

1. **Find working examples.** Locate similar code in the same codebase
   that works. What works that resembles what's broken?

2. **Compare against references.** If you are implementing a pattern,
   read the reference implementation completely. Read every line rather
   than skimming, and understand the pattern before applying it.

3. **Identify the differences.** List every difference between the
   working and broken versions, however small. Don't assume a difference
   can't matter.

4. **Understand the dependencies.** What other components does this
   need? What settings, config and environment? What does it assume?

### Phase 3: Hypothesis and Testing

Use the scientific method:

1. **Form a single hypothesis.** State it plainly: "I think X is the
   root cause because Y." Write it down, and make it specific.

2. **Test it minimally.** Make the smallest change that tests the
   hypothesis. Change one variable at a time, and don't fix several
   things at once.

3. **Verify before continuing.** If it worked, go to Phase 4. If it
   didn't, form a new hypothesis. Don't pile more fixes on top.

4. **When you don't know, say so.** Say "I don't understand X" rather
   than pretending. Ask for help, or research further.

### Phase 4: Implementation

Fix the root cause, not the symptom:

1. **Create a failing test case**
   - The simplest reproduction you can write.
   - An automated test if possible, or a one-off script if there is no
     framework.
   - Have it before you fix anything. Use the `test-first` skill to
     write a proper failing test.

2. **Implement a single fix**
   - Address the root cause you identified, one change at a time.
   - No "while I'm here" improvements and no bundled refactoring.
   - **Verify the blocker before settling for a weaker fix.** "The
     proper fix would break X" is a hypothesis. Go and read X. Before
     you disable, mock, loosen or skip something, ask what regression
     the assertion could still catch afterward. If the answer is none,
     you have removed the test, not fixed the bug.
   - **Look for what the fix removes.** A symptom fix can remove a
     feature that shares its code path. Check what else runs through
     the lines you are changing.

3. **Verify the fix**
   - Does the test pass now? Are other tests still passing? Is the
     problem actually resolved?
   - Use the `verify-before-claiming` skill before claiming success.

4. **If the fix doesn't work**
   - Stop, and count how many fixes you have tried.
   - Fewer than three: return to Phase 1 and re-analyze with what you
     have learned.
   - Three or more: stop and question the architecture (step 5). Don't
     attempt a fourth fix without discussing it with your human partner.

5. **If three or more fixes have failed, question the architecture**

   These patterns point to an architectural problem:
   - each fix reveals new shared state, coupling or a problem in a
     different place;
   - fixes would need a large refactoring to implement;
   - each fix creates new symptoms elsewhere.

   Question the fundamentals:
   - Is this pattern sound?
   - Are we sticking with it through inertia?
   - Should we refactor the architecture rather than keep fixing
     symptoms?

   The question may also be a product decision rather than an
   architectural one. If you find yourself tuning a threshold or a
   heuristic until a case passes, or making a choice that a user of the
   software would recognize and could disagree with, the decision
   belongs to your human partner, not to you.

   Write down what each attempt showed, then discuss it with your human
   partner before trying anything more. Three failed fixes are not a
   failed hypothesis. They mean the architecture, or the question, is
   wrong.

## Red Flags: Stop and Follow the Process

If you catch yourself thinking:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- "Passed on rerun, probably flaky"
- "It's environmental / not ours / it was already broken"
- "One more fix attempt" (after two or more have failed)

Or catch yourself doing this:
- proposing a fix before tracing the data flow;
- proposing a fix before reading the data the code interprets;
- tuning a threshold until it passes;
- finding that each fix reveals a new problem in a different place.

Any of these means: stop and return to Phase 1. If three or more fixes
have failed, question the architecture and the question itself
(Phase 4, step 5).

## Your Human Partner's Signals You're Doing It Wrong

Watch for these redirections:
- "Is that not happening?" You assumed without verifying.
- "Will it show us...?" You should have added evidence gathering.
- "Stop guessing." You are proposing fixes without understanding.
- "Ultra-think this." Question the fundamentals, not only the symptoms.
- "We're stuck?" (frustrated). Your approach isn't working.

When you see one of these, stop and return to Phase 1.

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Issue is simple, don't need process" | Simple issues have root causes too. The process is fast for simple bugs. |
| "Emergency, no time for process" | Systematic debugging is faster than guess-and-check thrashing. |
| "Just try this first, then investigate" | The first fix sets the pattern. Do it right from the start. |
| "I'll write test after confirming fix works" | Untested fixes don't stick. Writing the test first proves the fix. |
| "Multiple fixes at once saves time" | You can't tell which one worked, and they cause new bugs. |
| "Reference too long, I'll adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "I see the problem, let me fix it" | Seeing symptoms is not understanding the root cause. |
| "One more fix attempt" (after 2+ failures) | Three failures point to the architecture or to a product decision. Question it; don't fix again. |
| "Passed on rerun, probably flaky" | The rerun destroyed the evidence. A failure that moves around is usually a real cross-cutting bug. |
| "This would break X, so I'll do the weaker fix" | That is a hypothesis. Read X first. |

## Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors and raw data, check the report's claim, reproduce, check changes and baseline, gather evidence | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare | Identify differences |
| **3. Hypothesis** | Form theory, test minimally | Confirmed or new hypothesis |
| **4. Implementation** | Create test, fix, verify | Bug resolved, tests pass |

## There Is No Such Thing as a Flake

"Flaky" names a symptom, not a cause. Treat an intermittent failure as a
bug you haven't found yet.

- **Capture the error before re-running.** Save the full output, the
  test name, the seed and the order the tests ran in. A green rerun
  tells you nothing about why the first run failed, and it erases the
  only evidence you had.
- **Read the shape of the failure.** A genuinely flaky test, one with an
  unguarded timing assumption, fails in the same place. A failure that
  moves between tests, never reproduces when run alone, and points
  somewhere unrelated to the change is the signature of a real
  cross-cutting bug: state shared between tests, cleanup racing a run
  that is still live, or module-level state that survives from one test
  to the next.
- **Reproduce the mechanism deliberately.** Force the interference: run
  the suspect tests together in the failing order, run them in
  parallel, or make the cleanup fire early. Then fix the mechanism.
- **Show that the fix contains it.** Re-run the same forced interference
  after the fix and show that it no longer fails. A suite that happens
  to pass proves nothing.

Two tools help. [find-polluter.sh](find-polluter.sh) bisects the test
files to find the one that leaves state behind.
[condition-based-waiting.md](condition-based-waiting.md) replaces
guessed delays with waits on the actual condition.

## When the Cause Is Outside the System

Retry or timeout handling is allowed only when the cause has been shown
to be outside the system, such as a third-party outage or a documented
timing contract, and the evidence is recorded in an issue. Show it: a
status page, a vendor's documentation, a captured response from the
dependency. Your own inability to find the cause is not evidence that
it is external.

It is never allowed for a failure that only passes on a rerun. That is
the case in the previous section, and it calls for more investigation.

## Supporting Techniques

These files in this directory are part of the process:

- **[root-cause-tracing.md](root-cause-tracing.md)**: trace a bug
  backward through the call stack to the original trigger.
- **[defense-in-depth.md](defense-in-depth.md)**: after finding the root
  cause, make the bad value impossible by construction, with a type at
  the boundary, environment guards at the runtime edge and
  instrumentation.
- **[condition-based-waiting.md](condition-based-waiting.md)**: replace
  arbitrary timeouts with condition polling.
- **[find-polluter.sh](find-polluter.sh)**: find the test that creates
  unwanted files or state.
