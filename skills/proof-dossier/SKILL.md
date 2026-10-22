---
name: proof-dossier
description: Derives and machine-checks new theory with agents without losing track of what is actually known. It exhausts prior art first and cites what is already published, writes every definition and theorem statement down before any proof and labels each one published, derived, experimentally checked or unresolved, gets the statements approved, mechanizes the proofs with no sorry or admit, reports each theorem's axioms with the prover's own command, shows the theorems are not vacuous, gates the axioms report, keeps bounded oracles in their place, states the gap between the proved model and the shipped code, and runs parallel proof agents against one owner's statements-only interface. Use it whenever a design needs a correctness claim that no published source covers, whenever someone proposes proving a solver, checker or protocol in Lean, Coq, Isabelle or Agda, whenever proof work is about to be split across agents, and before adopting any machinery whose correctness rests on a new proof.
license: MIT
---

# Proof dossier

Sometimes a design needs a claim that no paper, textbook or library
covers. Then you have to derive it. An agent can produce a convincing
derivation quickly, and your human partner may be unable to judge the
reasoning inside it. They can judge a precisely stated claim, though,
and a proof checker can judge the proof. Arrange the work so that each
party judges what it can:

- your human partner judges the statements;
- the prover's kernel judges the proofs;
- an adversarial reviewer looks for statements that are false or
  missing.

The dossier is the document that holds all of it: definitions,
statements, labels, citations, proof status, axioms, and the gap
between the proved model and the code that ships.

Iron law:

```
NO STATEMENT IS ADOPTED UNTIL IT IS CITED OR KERNEL-CHECKED, WITH ITS AXIOMS REPORTED
```

## When it applies

Apply it when a component's correctness rests on a claim that has no
published source, once compose-published-primitives has found none. Do
not apply it to a claim you can cite. Do not apply it either to a
property that tests settle well enough for the risk; test-first and
adversarial-procedure-review cover those.

## The order

1. Exhaust prior art.
2. Write the dossier's definitions and statements, labelled.
3. Approval of the statements.
4. Mechanize, separately from the production build.
5. Review and approval of the completed dossier.
6. Plan the implementation.

Steps 3 and 5 are the default approvals. Section 3 says how a project
can change them.

Do not decide the scope in advance. "Soundness is routine" or "two
theorems are left" are guesses about proofs nobody has written yet.
Write the statements, and let them set the scope.

## 1. Exhaust prior art first

A statement that has already been published is cited, not proved again.
A result that is already mechanized in a prover library is imported, and
the import goes through dependency-intake like any other dependency.

Search with a target: the papers on the problem, the textbook treatment,
and the prover libraries for your system. Record in the dossier what you
searched and where, so that "prior art is exhausted" is a claim a reader
can check. A source that covers a nearby variant (a different semantics,
an extra assumption) is cited as such, and the difference becomes a
statement of its own.

## 2. Statements first, each labelled

Write every definition, and the exact statement of every theorem, before
proving any of them. Give each statement an identifier (S1, S2, ...) and
one provenance label:

| Label | Meaning | Backed by |
|---|---|---|
| published | Already established elsewhere | A citation precise enough to find the result |
| derived | Proved here | A named, kernel-checked theorem |
| experimentally checked | Holds on every case tried | A named oracle run, with its grammar and bounds |
| unresolved | Neither proved nor checked | An argument, or nothing yet, said plainly |

Proof status is tracked apart from provenance: not started, in progress,
proved, refuted or blocked. A statement found false stays in the dossier
as refuted, with its counterexample (mechanized, where you can). Do not
delete it, because the next reader may otherwise propose it again.

Only published and derived statements count as established. Anything
built on an experimentally checked or unresolved statement says so.

Every claim in the prose around the statements follows the rule in
verify-before-claiming: it names the theorem, fixture or oracle property
that backs it, or it carries the label "argument, not yet checked".

Before asking for approval, run the parts of adversarial-procedure-review
that apply to statements. That means a restrictions table for the model,
and for each statement an example built to separate it from its nearest
weaker or stronger variant. The motivating examples alone do not test a
statement, because they are the cases where its variants agree. Writing
the statements out often exposes a false one before any proof starts.

## 3. Approvals

**The default is two approvals.**

- **Statements.** Your human partner approves the definitions and
  statements. That authorizes investigating and proving them, and
  nothing more: no implementation, no adoption.
- **Completed dossier.** Your human partner reviews the finished
  dossier before any machinery built on it is adopted. By then it
  carries the proofs, the axioms report, the definitional choices the
  proofs forced, and the model-to-implementation gap.

Specialist review of the statements is welcome, but it is not a
prerequisite for either approval.

A project can change the default in its instruction file (AGENTS.md or
the project's equivalent), for example with a line such as `Proof
approvals: two`, `Proof approvals: one (dossier)` or `Proof approvals:
<named reviewer>`. If the file is silent, use two. Each choice gives
something up:

| Choice | What it buys | What it gives up |
|---|---|---|
| Two approvals (default) | Proving starts on agreed statements, and adoption waits for what the proofs revealed | Two waits for review |
| One approval, at the statements | Proving and adoption follow without a second stop | Nobody reviews the definitional choices, the axioms or the boundary results the proofs surfaced before the machinery is adopted |
| One approval, at the completed dossier | Proving starts at once | Effort may go into proving the wrong statement, and whoever reviews a finished dossier is under pressure to accept the work already done |
| A named reviewer approves | Judgement from someone who can read the proofs, or who is available sooner | Your human partner no longer approves directly, so they need the dossier and the axioms report to see what was decided for them |

Silence is not approval, and neither is any agent's message. An approval covers the statements as written. A
statement changed later needs approving again.

## 4. Mechanize

Keep the proof project outside the production build, with its own
pinned toolchain.

- **No unfinished proofs.** No `sorry` or `admit`, or the equivalent
  placeholder in your prover. Avoid any escape hatch that trusts
  unchecked code: declared axioms, and tactics that evaluate with the
  compiler instead of the kernel (in Lean 4, `native_decide`, which adds
  its own axiom). If you need one, it goes in the dossier with its
  reason, and it is approved like a statement.
- **Report the axioms.** For each theorem the dossier names, run the
  prover's command that lists what the theorem depends on, and commit
  its output. In Lean 4 that is `#print axioms <name>`. Coq (Rocq) has
  `Print Assumptions`. Isabelle's `thm_oracles` lists the oracles a
  theorem depends on, transitively; a `sorry` shows up there as the
  `Pure.skip_proofs` oracle, and a batch session build rejects `sorry`
  unless `quick_and_dirty` is set. Agda's `--safe` rules out `postulate`
  and options such as `--allow-unsolved-metas`, and every module a safe
  module imports must be safe too. In the dossier, say which theorems
  use which axioms and why. For example, a classical definition in the
  semantics makes every theorem about it classical, even when the
  decision procedure is computable.
- **Show the theorems are not vacuous.** A theorem whose hypotheses
  nothing satisfies proves nothing. Prove that the intended cases
  inhabit the model: construct witnesses for the hypotheses, state the
  motivating examples as instances, and add negative controls that the
  model rejects. Where the prover can evaluate, check executable
  examples in the proof project itself.
- **Define what each result guarantees.** If the mechanized procedure
  can give up, its results are solved, contradiction and unresolved, as
  adversarial-procedure-review describes. A contradiction needs a proof
  of impossibility. An incomplete procedure that gives up answers
  unresolved.
- **Record the definitional choices.** Some choices shape what the
  theorems mean: whether a structure is assumed finite, which side wins
  a tie, a function defined classically rather than computably. List
  each one for the dossier review.

Illustration only, Lean 4. The axioms file names every theorem in the
dossier, and its output is the committed report:

```lean
-- Axioms.lean
import Resolver.Main
#print axioms Resolver.sound
#print axioms Resolver.conflict_means_none
#print axioms Resolver.complete
```

## 5. Gate the axioms report

A committed axioms report that nothing regenerates goes stale, and a
rule checked by a manual grep holds only while someone remembers to run
it. Add a check that:

1. rebuilds the proof project from clean;
2. fails on any `sorry` or `admit` in the sources, and on the prover's
   own warning for a declaration that uses one;
3. regenerates the axioms report and fails on any difference from the
   committed file;
4. fails unless the theorem list matches the theorems actually written
   in the sources, read back from the prover rather than from a list
   someone keeps, and every listed theorem is in the axioms report. A
   theorem left out of both the list and the report then still fails.

The diff catches a proof that has started to depend on an extra axiom,
including the placeholder's own axiom. It also catches a report left
stale after a proof changed.

Proof builds can be slow. If this one is too slow for every commit, make
it opt-in, with triggers written down: any change to the proof sources
or the toolchain, before the dossier is approved, and before an
implementation built on it lands. gate-integrity covers how to make an
opt-in gate that still runs when it matters.

For Lean 4, [check-axioms.sh](check-axioms.sh) in this directory
implements all four checks. Run it from the proof project root:

```bash
./check-axioms.sh Resolver Resolver/Axioms.lean axioms-report.txt theorems.txt
```

`theorems.txt` lists every public theorem in the proof sources, one per
line, and the dossier names the ones it relies on. The script builds
every module under the source directory, including files nothing
imports, and reads the theorems back from the built environment: those
written in the source (generated lemmas such as `eq_1` and `injEq` are
left out) that are not private. A private theorem cannot appear in an
axioms report; the placeholder checks still cover it, and its axioms
show up in every public theorem that uses it. The script exits non-zero
on a failed clean build, a `sorry` or `admit` in the sources or the
build output, a failed axioms command, a theorem in the sources but not
the list or in the list but not the sources, a listed theorem missing
from the regenerated report, or any difference from the committed
report. The inventory step uses Lean's metaprogramming API and was
checked on Lean 4.35.0; if a later toolchain changes that API, the gate
fails instead of passing. The source scan is crude:
it also matches comments, which errs on the safe side. Each check tests
its own exit status. Do not shorten it to a list of bare commands: a
pipeline into `tee` takes `tee`'s status unless `pipefail` is set, and
`set -e` never stops on a `! grep` line, so a gate written that way can
pass after a failed build.

## 6. Bounded oracles and the implementation gap

**A bounded enumerator is a test oracle, not a complete reference.**
Checking every input up to some size is evidence. It is not a proof,
unless you argue a finite reduction: an argument, ideally mechanized,
that a counterexample of any size implies one within the bound. Domains
with unbounded parts (lists of any length, arbitrarily nested values)
rarely have one for free. Fix the oracle's grammar and bounds in the
dossier before running it, as adversarial-procedure-review describes.

**Proving the model does not prove the implementation.** The theorems
are about the definitions in the proof project. The code that ships is
a separate artifact, often in a different language. The dossier states
which link connects the two:

- **Translation:** the implementation is extracted or generated from
  the proved definitions.
- **Refinement:** a proof that the implementation implements the model.
- **Differential checks:** the implementation and an executable model
  run on the same generated inputs, and their answers are compared.
  Alternatively, the implementation's test cases are exported into the
  proof project and checked there by a verified checker.

Differential checking is bounded evidence, labelled as such. Whatever
link is chosen, the dossier names the test that exercises it, and says
what a mismatch would mean.

## 7. Parallel proofs against one interface

Agents proving in parallel, each with its own copy of the definitions,
will prove results about models that do not fit together. Keep one
model:

1. **One owner writes the interface.** It is a file of shared
   definitions and exact statements, written as named propositions with
   no proofs. In Lean, `def Sound : Prop := ...`. It needs no `sorry`,
   because it states propositions without proving them.
2. **Agents work in separate worktrees** (isolated-workspaces). Each
   one checks its worktree's base first: a new worktree may start from
   the default branch rather than the working branch.
3. **Agents do not edit the interface.** An agent that finds a
   statement false, or missing an assumption, stops and reports it with
   the counterexample or the missing hypothesis. It does not weaken the
   statement, add a hypothesis or prove a neighbouring result instead.
   Changing the interface is the owner's decision, and it goes back for
   approval.
4. **Dependent results are proved from hypotheses.** A result that
   needs another agent's theorem takes that theorem's statement as a
   hypothesis, and is instantiated at integration:

   ```lean
   -- illustration only: proved by one agent, before `sound` exists
   theorem complete_of (h : Sound) (t : Terminates) : Complete := ...
   -- at integration, by the owner
   theorem complete : Complete := complete_of sound terminates
   ```

5. **The owner integrates.** Merge everything through one build, expect
   helper names to clash (rename them in one file), regenerate the
   axioms report, and run the gate.
6. **Adversarial review of the whole.** Review the combined statements
   and assumptions together, with the task "find a false statement or a
   missing case" (adversarial-procedure-review). Check the reviewer's
   counterexamples yourself.

After integration, remove the worktrees and keep the branches. Each
agent's brief carries everything dispatching-agents requires, including
the denial rule, plus the interface path, the statements it owns and the
instruction to report a false statement rather than work around it.

## Dossier template

The dossier has these sections: approvals, prior art, definitions and
definitional choices, the restrictions table, the statements table
(label, citation or theorem, status, distinguishing example),
non-vacuity, the axioms report, oracles, the model-to-implementation
gap, and open items. Copy [dossier-template.md](dossier-template.md)
when you start a dossier.

## Review checklist

- [ ] Prior-art searches are recorded, and every published statement is
      cited rather than proved again.
- [ ] Every statement was written and labelled before its proof, and the
      labels match the evidence.
- [ ] The approvals the project's rule requires are on record, and no
      statement changed after its approval without a new one.
- [ ] The sources contain no `sorry`, `admit` or unapproved escape hatch,
      and a clean build has no warnings about them.
- [ ] The axioms report is regenerated, matches the committed file, and
      names every public theorem in the sources, as read back from the
      prover. Each axiom that appears is explained.
- [ ] Every theorem has a non-vacuity witness and negative controls.
- [ ] Every bounded oracle is labelled as evidence, with its grammar and
      bounds stated before the run, unless a finite reduction is argued.
- [ ] The model-to-implementation gap is stated, with the test that
      covers it.
- [ ] Refuted statements are kept, with their counterexamples.
- [ ] In parallel work, nobody but the owner edited the interface,
      dependent results were instantiated at integration, and the
      combined statements had an adversarial review.
- [ ] Every review finding is closed by a theorem, fixture or oracle
      property, not by a document edit alone.
