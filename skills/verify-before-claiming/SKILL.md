---
name: verify-before-claiming
description: Requires fresh evidence before any claim that work is complete, fixed, passing or clean. The agent runs the command that proves the claim, reads its full output, and only then states the result, with every failure it saw named in the report. Covers builds and test runners that under-report, performance claims measured on the build users run, upgrades and mechanical sweeps, pure-move diffs, figures recomputed from source, claims in design docs and agent reports, tools of record, and the issue and tracker updates that finish a task. Use it whenever the agent is about to say something is done or working, express satisfaction with a result, commit, push, open a PR, close an issue, move to the next task, or relay another agent's success report. Paraphrases and implied success count, so it applies even when a claim feels too small to check. Replaces superpowers' verification-before-completion.
license: MIT
---

# Verify Before Claiming

## Overview

**Core principle:** evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**
Rewording a claim does not exempt it. "Looks good", "that should do it"
and a satisfied "Done!" all assert success, and each needs the same
evidence as "all tests pass".

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you have not run the verification command in this message, you cannot
claim it passes. An earlier run describes the code as it was then.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

A claim made after skipping a step is a false report, however it is worded.
```

## When to Apply

Run the gate before:

- any claim of success or completion, in any wording;
- any expression of satisfaction with the work;
- any positive statement about the state of the work;
- committing, pushing, opening a PR, or marking a task or issue done;
- moving to the next task;
- delegating to an agent, and accepting what it reports back.

The rule covers exact phrases, paraphrases and synonyms, and anything
that implies the work is complete or correct. It also covers claims
written down rather than spoken: design documents, review summaries and
diagnostics (see "Claims Without a Check" below).

## What Each Claim Requires

| Claim | Requires | Not sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 (from a clean output directory if the claim is "clean") | Linter passing, logs look good; for "clean", an incremental build |
| Bug fixed | Original symptom tested: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows the changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |
| Ticket done | Acceptance criteria walked against evidence in an issue comment; issue state read back from the tracker | Tests passing; remembering you meant to close it |
| A figure or measurement | Recomputed now from the source data | Copied from a document, an issue, or an earlier run |
| A change only moved code | Per-file sorted-lines diff is empty | "It was just a reorder" |
| A regression exists | Baseline rebuilt from the branch's own merge-base | A diff against a main that has moved since the branch forked |
| A tool-owned fact (lockfile, migration status, deployed config) | The owning tool's output, run now | Your own recomputation of it |
| A design or review claim | A named test, fixture or oracle property, or the label "argument, not yet checked" | The claim repeated from its source |
| It is fast enough | A measurement in the build users actually run, with the median of several runs after a warm-up | A timing from an optimized or release build users don't run; a single run |
| An upgrade or migration preserved behavior | The suite and the affected paths exercised under the new version, against a baseline taken on main under the same install | A clean type check; the count of compile errors falling to zero |

## Key Patterns

**Tests:**
```
Good: [Run test command] [See: 34/34 pass] "All tests pass"
Bad: "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
Good: Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
Bad: "I've written a regression test" (without red-green verification)
```
For proving that a test can fail at all, and for spotting tests that pass
vacuously, see test-first.

**Build:**
```
Good: [Run build] [See: exit 0] "Build passes"
Bad: "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
Good: Re-read plan → Create checklist → Verify each → Report gaps or completion
Bad: "Tests pass, phase complete"
```

**Agent delegation:**
```
Good: Agent reports success → Check VCS diff → Verify changes → Report actual state
Bad: Trust agent report
```

**Pure moves (reorder, split a module, move declarations):**
```
Good: for each file: diff <(git show "BASE:$path" | sort) <(sort "$path")  → empty
Bad: "Tests pass, so nothing changed"
```
Empty output proves that every line still exists and none was edited. It
does not prove that a comment stayed with the right declaration; for
that, read the diff.

## Know How Your Build Under-Reports

Every toolchain has a command that looks like verification and is not: a
build that skips modules whose cache key you did not change, a test
runner that prints warnings without failing on them, a cache that
survives a config change, a check script that stops at its first failing
step. Trust one of these and you get a confident zero that means nothing.

- When the claim is "the build is clean", verify from a clean output
  directory. Deleting the output forces the rebuild; touching source
  files often does not.
- If the project's bar is zero warnings, use the strict mode that turns
  warnings into failures.
- For a chained check, read which step it stopped at as well as its exit
  code.
- When you find a command that under-reports, record it in AGENTS.md or
  the project's equivalent instruction file, beside the command that
  reports honestly. The next agent will reach for the obvious one too.

## Measuring Performance

A performance claim is a measurement, and it is only as good as the build
it was measured on.

- **Measure the build users run.** If users run a debug or interpreted
  build, measure that one. An optimizing compiler or JIT can hide the cost
  you are trying to remove. Where you cannot run the users' build, emulate
  it: run with the optimizer switched off.
- **Count allocations as well as time.** In a garbage-collected runtime,
  allocation is often the cost, and it is steadier to measure than wall
  time.
- **Take the median of several runs after a warm-up,** and say how many.
  One run measures the machine's mood.
- **Prefer ratios to absolute times.** "The shared path costs less than
  a quarter of computing each part alone" travels further than "under
  40 ms", which holds only on your machine. A ratio is still not
  machine-independent: cache sizes, core counts, the runtime version and
  load from other processes can shift the two sides differently. State
  its preconditions as assertions first (enough rows that the ratio
  means something, both sides measured in the same process on the same
  build), so the gate cannot pass vacuously on tiny input. Take each
  side as the median of warm runs, and investigate a failure rather
  than rerunning until green (gate-integrity).
- **Aim for headroom.** A change that just clears the bar will fail it on
  the next device or the next feature.
- **Don't predict from reasoning alone.** Profile before choosing what to
  optimize, and measure after. Guesses about where the time goes are
  usually wrong.

## Upgrades and Mechanical Sweeps

After a major-version upgrade or a codemod across the codebase, a clean
type check is the start of verification, not the end.

- **Take the baseline on main first,** under the new install: lint, test
  and build results before your change. Then a failure you see afterwards
  is yours, not the upgrade's.
- **Exercise runtime behavior.** Types can line up while semantics moved:
  a value that used to be implicitly converted, or an error that used to
  surface as one kind and now surfaces as another. Run the paths the
  release notes flag.
- **Count what a sweep may have stripped.** Mechanical rewrites can drop
  trailing comments, including suppression and lint-directive comments.
  Count them before and after (`git grep -c` on the directive), and
  account for every difference.
- **The type-error count is not the metric.** Driving it to zero with
  casts or suppressions converts compile errors into runtime ones.

## The Tool of Record

When a tool owns a piece of state (a package manager's lockfile, a
migration tool's status, a cloud provider's deployed configuration), its
output is the observation. Run it and read it. Do not reimplement its
checksum, re-derive its manifest, or recompute what it just wrote. Your
reimplementation is less reliable than the tool, and when the two
disagree, the guess your version rests on gets reported as a finding.

Spend your skepticism on what no tool owns: a ticket's account of the
mechanism, an agent's report, whether a gate actually fails, and the gap
between declared and deployed infrastructure. For that last one, query
the deployed state; reading the declaration tells you only what was
intended.

## Claims Without a Check

Design documents, review summaries and diagnostics make claims too:
"rejects only invalid input", "terminates", "covers every case". Each
such claim names the test, fixture or oracle property that backs it, or
is marked **argument, not yet checked**. When you relay a claim from an
agent, a ticket or a document, check it or say it is unverified.
Repeating a claim does not make it any stronger.

A check that passes only on the examples that motivated it can pass a
false claim. For each claim, also try a case built to tell it apart from
its nearest weaker or stronger variant. "Rejects only invalid input"
needs a valid input right at the boundary as well as invalid ones.

## Every Failure Goes in the Report

A green run of the file you changed is not a green suite. Run the whole
check even when the task named a single test. Every failure in that run's
output goes in the report by name, including one you did not cause and
one that "was already broken". A red line that scrolled past without
mention makes the report false by omission. A failure that is someone
else's still goes in: fix it or file it, and say which you did.

A failure that passes on a rerun is still a failure. See
root-cause-debugging, "There Is No Such Thing as a Flake".

## Done Includes the Records

Code and tests give you a failing signal when something is wrong;
trackers do not. A task therefore feels finished at the last step that
gave feedback, and the steps that give none get dropped. Before you
report work done:

- Walk the acceptance criteria in a comment on the issue, including what
  could not be verified and why. Posting it needs the same authorization
  as filing; without it, draft the comment locally and ask once.
- Read the issue state back from the tracker (on GitHub, `gh issue view
  N --json state`) instead of trusting that you closed it.
- Update every record the change made stale: backlog rows, product docs,
  AGENTS.md, READMEs, related issues. If a follow-up is out of scope,
  record it: file it if filing is authorized, or write a local draft
  and ask once (decisions-as-issues, "Record follow-ups instead of
  offering to"). Ending with an offer and nothing written down leaves
  it unrecorded.

## Red Flags: Stop

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit, push or open a PR without verification
- Trusting an agent's success report
- Relying on partial verification
- Quoting a number from a document or an earlier run
- Recomputing what a tool of record already reports
- Leaving a failure out of the report because you did not cause it
- Offering to file a follow-up with no issue or local draft behind it
- Thinking "just this once"
- Tired and wanting the work over
- **Any wording that implies success when you have not run the verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | Run the verification |
| "I'm confident" | Confidence is not evidence |
| "Just this once" | No exceptions |
| "Linter passed" | The linter is not the compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Tiredness does not change what the output says |
| "Partial check is enough" | A partial check proves only the part it ran |
| "Different words, so the rule doesn't apply" | The rule follows the meaning, not the wording |
| "It was just a reorder" | Run the sorted-lines diff |
| "The doc already gives the number" | Recompute it from the source |
| "That failure isn't ours" | Name it in the report, then fix it or file it |
| "I closed the issue" | Read its state back from the tracker |
