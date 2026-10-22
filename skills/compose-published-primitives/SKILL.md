---
name: compose-published-primitives
description: Keeps the novelty of a system in how it composes well-understood parts, and keeps those parts to published algorithms, textbook data structures and widely used components that each name their source. Before planning, it maps every algorithmic component to the paper, textbook or library it comes from, flags anything without one as invented, offers the standard alternative with its cost, and requires a demonstrated need, an argument, evidence and explicit approval for any departure. Use it whenever designing or planning a solver, checker, resolver, scheduler, merge or sync rule, cache policy, protocol, concurrency scheme or any component whose correctness your human partner cannot easily judge, and whenever a design or an agent proposes its own rule for a problem the literature already covers, even if the custom rule is well tested.
license: MIT
---

# Compose published primitives

Put a system's inventiveness in how its features combine and in the
problems the combination solves. Build each part from something well
understood: a published algorithm, a textbook data structure, a framework
or library in wide use. Then every part can be explained by pointing at
its source, and the people responsible for the system can account for
what it does.

This matters most when an agent writes much of the code. An agent can
produce plausible new machinery quickly, test it extensively, and still
leave nobody able to say why it is correct, where it breaks, or what it
was meant to be. Extensive tests of an invented rule show that it passes
the cases someone thought of. A published algorithm also comes with the
analysis, the known failure modes and the years of use behind it.

The surface of a system may be original: its syntax, its interface, its
product rules. This skill is about the machinery underneath.

## When it applies

Apply it to new or materially changed algorithmic components: anything
that decides, solves, searches, merges, schedules, resolves, orders or
guarantees. A routine edit to an existing component does not need it, and
neither does a refactor or a new message for an existing failure.

Watch for these signs that a design has started inventing:

- "A small custom rule handles this case", followed by a second rule for
  the case the first one missed.
- Special handling that accumulates per case: per-item bounds, quiet
  exceptions, a bespoke drain or retry policy.
- A component that is well tested but that nobody can name a source for.
- A design document that explains the mechanism only in its own terms.

## The process

### 1. Map each component to its source before planning

Write a provenance table in the design document, before any
implementation plan exists:

| Component | Source | Fidelity |
|---|---|---|
| Version selection | Backtracking search over a constraint problem (standard CSP formulation) | Faithful |
| Conflict detection | Interval overlap via a sorted sweep (textbook) | Faithful |
| Merge of concurrent edits | None found | Invented |

- **Source** is something a reader can look up: a paper with its authors
  and title, a textbook section, or a library in wide use.
- **Fidelity** says how closely the component follows that source:
  *faithful*, *adapted* (state each change), or *invented* (no source).

Anything marked invented is a finding. Report it to your human partner
before planning goes further, because the cheapest time to replace an
invented part is before anything depends on it.

### 2. Offer the standard alternative and its cost

For each invented component, find the closest standard mechanism and say
what it would cost to use it instead. Typical costs:

- the user writes an extra annotation or makes an explicit choice;
- the result is less general, or rejects some inputs the custom rule
  would have accepted;
- it runs slower, or takes more memory;
- it needs a dependency the project does not have yet.

Accepting such a cost to stay with the standard mechanism is the default.
A little more work for the user is usually a better trade than a part
that nobody can explain.

### 3. Departures need a case, and approval

A departure from a published source can be justified, but only with all
of the following, gathered before approval:

- **A demonstrated need.** Show that the published mechanism, modelled
  faithfully, fails a real requirement. "It might not handle X" is a
  hypothesis; build the case and run it.
- **A clear argument** for why the departure is correct: what it
  preserves, what it gives up, and why it terminates.
- **Reproducible evidence**: tests against an independent reference,
  exhaustive checks over small domains, executable examples. Run the
  adversarial-procedure-review skill on the departure.
- **Explicit approval from your human partner**, given after they have
  seen the standard alternative and its cost.

A departure approved this way gets its own entry in the provenance table,
marked *adapted*, with a link to the argument and the evidence.

### 4. Black boxes must be ones used elsewhere

Some components will not be explained from first principles: a SAT
solver, a database's query planner, a compression library. That is fine
when the box is widely used, because its behavior is known from that use.
A black box that exists only in this project is not acceptable, because
nobody else has found its failures.

### 5. Assurance and explanation

- **Assurance** is a proof, or very robust testing: an oracle that does
  not share the implementation's logic, exhaustive enumeration of small
  domains, and executable fixtures for every worked example. The
  verify-before-claiming and test-first skills cover what counts as
  evidence.
- **Explanation**: the documentation explains each component in terms of
  its source, so that someone who knows the source can follow the code,
  and someone who does not knows what to read.

### 6. Record influence, and do not copy code

Keep a provenance record of what was read and what it contributed: the
paper, the documentation page, the other project's design. Implement from
the published description, not by copying another project's code. Reusing
code is a licensing decision, separate from this skill, and it needs the
source's license to allow it.

## Worked example

A note-taking app needs to merge edits made offline on two devices. The
first design proposes a custom rule set: "newer timestamp wins per field,
except list fields, which concatenate and then drop duplicates, except
when one side deleted an item, in which case the deletion wins unless the
other side edited it."

The provenance map flags the rule set as invented. The review then
proceeds:

1. **Standard alternative.** Conflict-free replicated data types: a
   last-writer-wins register for scalar fields and an observed-remove set
   for lists. Both are published and widely implemented, with known
   convergence guarantees.
2. **Cost.** The observed-remove set keeps metadata for removed items,
   and "edit wins over delete" becomes an explicit choice between the
   set's add-wins and remove-wins variants, instead of a side effect of
   rule order.
3. **Decision.** The cost is small and the guarantees are known, so the
   design adopts the CRDTs. The edit-versus-delete behavior goes to your
   human partner as a product decision, with both options shown.

Had the team wanted to keep part of the custom rule, step 3 above would
apply: show a case the CRDTs get wrong for a real requirement, argue the
replacement converges, test it against an independent model, and get
approval.

## Reviewing a design against this skill

1. Does the design have a provenance table, and does every algorithmic
   component appear in it?
2. Is anything marked invented? Was the standard alternative offered, with
   its cost?
3. Does any adapted component state exactly what changed from its source?
4. For each departure, was the need demonstrated with a faithful model of
   the standard mechanism, before approval?
5. Is every black box one in wide use?
6. Does the documentation explain each component by its source?
7. Was any code copied from a source whose license has not been checked?
