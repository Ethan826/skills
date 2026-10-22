---
name: implementation-planning
description: Turns a spec or a set of requirements into an implementation plan that an engineer new to the codebase can carry out task by task, with exact files, signatures, tests and commit steps. The plan header carries the spec's global constraints, the published source and fidelity of every algorithmic component, a review focus with its distinguishing examples and, for a bug fix, the mechanism as verified by observation. The plan ends with a costed handoff to subagent or inline execution. Use it whenever a spec, design, ticket or requirements list describes multi-step work, before any code is touched, including when someone says "plan this", "break this into tasks" or "write up the plan", and right after design-brainstorming approves a design, even when the work looks small enough to start coding directly. Replaces superpowers' writing-plans.
license: MIT
---

# Implementation Planning

## Overview

Write implementation plans for an engineer who has not seen this codebase or this spec. Assume they write idiomatic code in the project's language once they know the exact interface and the exact test, and that they will make a reasonable choice wherever the plan leaves one open. What they cannot know is what you decided: which files, which names and signatures, which values from the spec, which tests prove each task. Write those decisions down, and give them the whole plan as small tasks. Keep to DRY, YAGNI and test-first, and commit often.

**Announce at start:** "I'm using the implementation-planning skill to create the implementation plan."

If the work runs in an isolated worktree, that worktree is created with the isolated-workspaces skill when execution starts, not while you plan.

## Where the Plan Lives

Where the spec and plan live is set per project. Read AGENTS.md or the project's equivalent instruction file for a `Plans:` line.

- If it names a directory, the design spec and the plan are committed files in that directory: `<date>-<topic>-design.md` and `<date>-<topic>-plan.md`.
- If it says `issues`, or says nothing:
  - The design spec is the issue, and the design is posted as a comment on it. Name that comment as the spec; often it is the last one.
  - The plan is a working file at `.superpowers/plans/<issue>-<slug>.md`, kept out of git by `printf '*\n' > .superpowers/plans/.gitignore`.
  - Decisions that must outlive the branch go in the issue, not the plan.
  - The plan file is deleted with the workspace when the branch lands.

Your human partner's stated preference for a plan location overrides both.

## Scope Check

If the spec covers several independent subsystems, design-brainstorming should already have split it into one spec per sub-project. If it did not, suggest one plan per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, list the files you will create or modify and what each one is responsible for. The decomposition is decided here, and the tasks follow from it.

- Design units with clear boundaries and well-defined interfaces. Give each file one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In an existing codebase, follow its established patterns. If it uses large files, don't restructure it on your own initiative; but if a file you are modifying has grown unwieldy, a split in the plan is reasonable.

Each task should then produce a self-contained change that makes sense on its own.

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle and is worth a
fresh reviewer's gate. When drawing task boundaries: fold setup,
configuration, scaffolding, and documentation steps into the task whose
deliverable needs them; split only where a reviewer could meaningfully
reject one task while approving its neighbor. Each task ends with an
independently testable deliverable.

## Step Granularity

**Each step is one action with a checkable result:**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

Every plan starts with this header. Executors and reviewers read it before any task, and Global Constraints, Provenance and Review Focus apply to every task, so a plan without it leaves each implementer to guess them.

Keep the heading exactly `## Global Constraints`, and write "None" under it when there are none. The executors' `task-brief` script copies that section verbatim to the top of every task brief, and refuses a plan with any other constraints heading before the first task.

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-plan-execution (recommended) or inline-plan-execution to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Spec:** [path to the spec file, or a link to the issue comment that holds
the spec — the plan argues from the spec, so the spec travels with it;
executors read both]

**Verified premise:** [Only when the plan fixes a ticket or bug report: the
mechanism as you observed it (the request you spied on, the query you ran,
the status you asserted), not as the ticket describes it. Where the two
differ, say so in one line.]

## Global Constraints

[The spec's project-wide requirements — version floors, dependency limits,
naming and copy rules, platform requirements — one line each, with exact
values copied verbatim from the spec. Every task's requirements implicitly
include this section.]

## Provenance

[One line per algorithmic component, carried over from the design's
provenance table: the component, its published source, and its fidelity
(faithful, adapted or invented). An adapted or invented line also names
the approval and the evidence that justify it. "None" if the plan has no
algorithmic component.]

## Review Focus

[The five input classes or failure modes the spec implies but no task's
tests exercise that are most likely to bite a person using this software
— one line each, naming the input or condition and the behavior a
reasonable person would expect, most likely first. The spec is a vision
document: it says what the software must do, not everything it will
meet, and its silence on an input is not permission for that input to
break the program. Write the list here, once, with the spec in front of
you. Then, for each line, add the test that pins it to the task that
owns the code, in that task's own step style.]

[When the plan implements a procedure that makes claims (sound, complete,
terminating and the like): the distinguishing examples and oracle checks
from its adversarial-procedure-review report, one line each, each naming
the task whose tests pin it.]

---
```

### Filling in Provenance

Copy the provenance table from the design (see compose-published-primitives); don't rebuild it from memory. Every algorithmic component the tasks implement gets a line, including ones the design treats as routine.

For each line marked *adapted* or *invented*, name the approval from your human partner and the evidence behind the departure: the argument, the tests against an independent reference, the adversarial-procedure-review report. If either is missing, stop. Raise the component with your human partner before you write any task, because every task built on an unapproved invented part is work that may be thrown away.

### Filling in the Verified Premise

A ticket states a mechanism, and the mechanism can be wrong. Before planning a fix, observe it as root-cause-debugging describes, and write what you saw. Tasks argue from the verified premise. If the observation contradicts the ticket, record the correction on the issue as well.

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, parameter
  and return types. A task's implementer sees only their own task; this
  block is how they learn the names and types neighboring tasks use.]

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Implement `function(input: InputType) -> ResultType` in `exact/path/to/file.py`**

One line on the approach when the signature and the test leave a choice
(which library call, which data structure); a code block only for an
algorithm they do not determine.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

Every commit step stages explicit file paths, as the template does: the files the task's **Files:** block lists, and no directory. `git add .` or `git add -A` would also sweep in your human partner's own untracked files and any working files in the tree. Before committing, the executor compares `git status --short` with the snapshot taken when the session started, so anything new that the task did not create is left alone.

## What a Step Contains

A step is done when the implementer can write exactly one reasonable thing
from it. That is the whole requirement: unambiguous, not complete. Each kind
of step carries what makes it unambiguous and nothing more:

- **A test step:** the test's name and its assertions, as code, with the
  spec's exact values in them.
- **A code step:** the exact signature (name, parameters, return type), the
  file it lives in, and the specific values the spec pins. The implementer
  writes the body. A body appears only for an algorithm the signature and
  tests do not determine, or for exact copy the spec fixes.
- **A verification step:** the command to run and the output that means it
  passed.
- **A reference to another task:** that task's Interfaces block says what
  to use; the plan does not repeat that task's code.

A plan is the set of decisions the implementer cannot make alone. A plan
longer than the code it describes has written the code instead. Lines that
decide nothing ("TBD", "handle edge cases", "add appropriate validation",
"write tests for the above", a type or function no task defines) are the
opposite failure, and the self-review catches both.

## Self-Review

After writing the complete plan, reread the spec and check the plan against it. You run this checklist yourself; it is not a subagent dispatch.

**1. Spec coverage:** Go through each section and requirement of the spec. Can you point to a task that implements it? List any gaps.

**2. Step scan:** Every step must let the implementer write exactly one reasonable thing, and no step may carry more than that. A line that decides nothing is a gap; a function body that the signature and tests already determine is a transcript. Fix both.

**3. Type consistency:** Do the types, method signatures and property names in later tasks match what earlier tasks defined? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

**4. Review Focus:** For each input class or failure mode the spec implies, is there a task whose tests exercise it? The five uncovered ones most likely to bite a person go in the Review Focus section, and each line there gets its test added to the owning task. If the plan implements a procedure that makes claims, does every distinguishing example and oracle check from its adversarial-procedure-review report appear, pinned to a task that has a test for it? An empty section means you checked and found nothing, not that you skipped the check.

**5. Proportion:** Compare the plan's length with the spec's. A plan several times longer than the spec it implements is a transcript of the program. If code blocks make up most of the document, replace bodies with signatures, test names and assertions, and check that each step is still unambiguous.

**6. Provenance:** Does every algorithmic component a task implements have a line, and does each line match the design's provenance table? Does every adapted or invented line name an approval and evidence that actually exist? If one does not, stop and raise it with your human partner; don't paper over it in the plan.

**7. Verified premise:** If the plan fixes a ticket, does the header state the mechanism you observed, and do the tasks fix that mechanism rather than the one the ticket described?

Fix what you find inline; there is no need to review again afterward. If a spec requirement has no task, add the task.

## Execution Handoff

After saving and self-reviewing the plan, link it for your human partner
to read. If they have already explicitly supplied an execution method, ask
them to review the plan and confirm it captures what they want; wait for that
review before implementation, then use the preserved method. Otherwise, ask
them to review the plan and choose an execution method before implementation.

Give a rough cost for each option: time, agent dispatches and tokens. Work it out from the plan; it doesn't need to be precise, only close enough for your human partner to choose.

- **Subagent:** count about three dispatches per task (implementer, task reviewer and, often, a fixer) plus one whole-branch review. Tokens are roughly the dispatch count times what each dispatch reads: its task, the files it touches and the diff it reviews.
- **Inline:** one dispatch, for the whole-branch review. Tokens are this session's context growing over every task, plus that review.

If the spend is substantial, meaning one your human partner would notice (by 2026 prices, more than about 500,000 tokens or more than about ten agent dispatches; revise these figures as prices change), state it and ask for a yes to the spend along with the review. Otherwise state it and go on to the execution choice. Size evidence to risk: run corpus-wide or exhaustive comparisons only for changes to core behavior, stored state or saved formats.

**When no execution method has already been supplied:**

**"Plan complete and saved to `<plan path>`. Please review the plan. Which execution approach would you prefer?**

- **Subagent** (subagent-plan-execution) - A fresh subagent implements each task and a fresh reviewer checks it before the next one starts, then a whole-branch review at the end. Most thorough; costs a fresh context per task and per review. Rough cost: <time>, <N> dispatches, <tokens>.
- **Inline** (inline-plan-execution) - I implement every task myself in this session, then one fresh reviewer on the most capable model available checks the whole branch. Cheapest and fastest; no independent review until the end. Runs well with a mid-tier session model, since the plan carries the design. Rough cost: <time>, 1 dispatch, <tokens>.

**For this plan I recommend <one of the two>, because <one sentence from the plan: how much the tasks depend on each other's interfaces, how many there are, what a shipped mistake would cost>. Does the plan capture what you want, and which approach should we use?"**

**When an execution method has already been supplied:**

**"Plan complete and saved to `<plan path>`. Please review the plan. Does it capture what you want? Rough cost with <method>: <time>, <N> dispatches, <tokens>."**

When the spend is substantial, end either message by asking for a yes to that cost.

**If Subagent chosen:**
- **REQUIRED SUB-SKILL:** Use subagent-plan-execution

**If Inline chosen:**
- **REQUIRED SUB-SKILL:** Use inline-plan-execution
