---
name: adversarial-procedure-review
description: Tries to break a proposed algorithm, decision procedure or validator, and the claims made about it, before it is approved for implementation or proof. It writes each claim down with the check that backs it, tables every restriction the representation adds beyond the intended meaning, runs separate soundness and completeness passes, builds examples that separate each claim from its nearest weaker or stronger variant, checks the claim against a bounded brute-force oracle, and hands the result to a reviewer whose job is to find a false statement. Use it before approving any new or materially changed solver, checker, resolver, matcher, scheduler, migration rule or access rule, whenever a design says a procedure is sound, complete, exhaustive, convergent or terminating, whenever every example in a design passes, and before trusting a diagnostic that names a culprit.
license: MIT
---

# Adversarial procedure review

A proposed procedure usually passes the examples that motivated it. That
says little, because in motivating examples two different properties
often coincide: the greedy choice happens to be the right one, the field
that exists also has the right type, the newest version is also the one
that fits. A procedure that tests one property while claiming the other
passes every such example and fails the first case where they come apart.

So review a proposal by trying to break it, before anyone builds on it:
look for where it is false.

## When it applies

Apply it to new or materially changed procedures whose results someone
will rely on, and to the claims made about them. That includes a
dependency resolver, a type or schema checker, a permission rule, a
scheduler, a data migration, or a matching rule.

Routine edits do not need it: a refactor, new wording for an existing
error, or an existing rule extended to a new form with the same meaning.
Where the evidence below cannot be had (no independent oracle can be
written, or the domain is too large to enumerate), the review says so and
names the test that covers the claim instead.

## The review

### 1. Write the claims down, each with its backing

List every claim the design makes about the procedure:

- what it accepts, and what it rejects;
- that it is sound (it accepts only valid inputs);
- that it is complete (it accepts every valid input);
- that it terminates, is deterministic, or converges;
- what each of its outputs means.

For each claim, name the test, fixture or oracle property that backs it,
or mark it **argument, not yet checked** with the reason. This list is
the claims ledger. A claim with neither a check nor a label does not pass
review.

"Several solutions" is a claim about a count. "No
solution exists" is a claim of impossibility. An incomplete procedure
that gives up has not shown either, and should say "unresolved".

### 2. Table the restrictions

A representation almost always restricts the meaning it encodes. List
every restriction the proposal adds beyond the intended semantics, why it
is believed harmless, and an example built to challenge it: something the
semantics allows that the representation cannot express.

| Restriction | Why believed harmless | Challenge example |
|---|---|---|
| Considers only the newest compatible version of each package | Newest is usually best | A needs B and C<2; B's newest needs C>=2, but B's previous version works with C 1.x |
| Treats each constraint as independent | Constraints rarely interact | Two constraints on the same package that are only jointly unsatisfiable |

Put the table in the design before asking for approval.

### 3. Run soundness and completeness as separate passes

- **Soundness pass:** try to make the procedure accept something invalid.
  Start from the rules and look for an input that satisfies the checks
  but violates the meaning.
- **Completeness pass:** start from a valid construction and try to make
  the procedure reject it. Build the valid case first, by hand, from the
  semantics; then run the procedure on it.

They are separate passes because they need opposite starting points.
Searching for both at once usually means searching from only one of them.

### 4. Build distinguishing examples

For each claim, build at least one example that separates it from its
nearest weaker or stronger variant. The motivating examples do not count
toward this: they are the cases where the variants agree.

In the resolver above, the claim "if the resolver reports no solution,
none exists" has a nearby weaker variant: "if the resolver reports no
solution, the newest versions conflict". The example in the restrictions
table separates them. A greedy resolver passes every motivating example
and fails this one.

### 5. Check the claim with an oracle at the claim's level

Where a claim quantifies over inputs ("rejects only invalid inputs",
"finds a solution whenever one exists"), check it with an oracle that
enumerates small inputs and evaluates the semantics directly, by brute
force, without using any of the procedure's logic. Compare the two on
every input.

- **Fix the oracle's grammar and bounds before running it.** Write down
  which inputs it generates and how large they get. "Exhaustive" means
  exhaustive within that grammar and nothing more. If you change the
  grammar after a run, label the change and report the results from
  before and after.
- **Cross-check fast searches.** Before trusting a fast search's "none
  found", run it against brute force on inputs small enough for both.
- **Say that the evidence is bounded.** Passing on every input up to size
  five is strong evidence and still not a proof.

### 6. Make results explicit, and classify every failure

- A procedure that can give up returns three kinds of result: solved,
  contradiction (shown impossible) and unresolved (gave up). Build messages
  and downstream decisions from the kind of result alone.
- Where internal failures are turned into results, classify each one
  explicitly, with no catch-all:
  - a violated constraint is a contradiction;
  - a depth or resource limit is an operational stop;
  - a broken internal invariant is an internal error;
  - an unfinished stage is a placeholder stop.

  Then adding a new failure forces a decision about what it shows. Test
  the classifier on its own by injecting each failure directly, because
  generated inputs rarely reach the limits and the invariants.

### 7. When the output names a culprit

A diagnostic that assigns blame ("field `email` caused the conflict") is
a claim too, and it needs its own evidence.

- State what the selection establishes before implementing it: what
  shows that this part caused the failure?
- Different is not the same as incompatible. A value that differs from
  the expected one may still be acceptable.
- Test an earlier plausible suspect that is fine beside a later one that
  fails, in both orders. Also test that making the failing part
  compatible makes the whole input pass.
- When the procedure is unsure, it keeps the failure's own message
  instead of guessing at a culprit.
- Review "rejects the right inputs" and "explains the rejection
  correctly" separately. An oracle for the first says nothing about the
  second.

### 8. Hand it to an adversarial reviewer

Give an independent reviewer the design, the claims ledger, the
restrictions table and the oracle results. Its task is "find a false
statement or a missing case", not "check whether this looks right". If
you dispatch an agent, the dispatching-agents skill covers the brief.

The reviewer's counterexamples are arguments, not conclusions. Check each
one yourself, against the semantics, before acting on it.

### 9. Close findings with checks

A finding is closed by a regression fixture or an oracle property that
would catch it again. A document edit alone does not close it.

## The report

Return the review in this shape:

1. **Claims ledger:** each claim, its backing check or its label.
2. **Restrictions table.**
3. **Soundness pass:** the inputs tried and what happened.
4. **Completeness pass:** the valid constructions tried and what
   happened.
5. **Distinguishing examples**, one or more per claim.
6. **Oracle:** grammar, bounds and results, including any change of
   grammar after a run.
7. **Open items:** each one an argument not yet checked, or a finding
   not yet closed.
8. **Verdict:** approve, approve with fixes, or reject.
