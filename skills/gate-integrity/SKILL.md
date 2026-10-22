---
name: gate-integrity
description: Makes automated checks trustworthy, so that a green result means the rule held. It treats each gate as a claim with a stated blind spot, decides on parsed structure rather than matched text, gives every checker its own tests (fixtures, must-fail cases, scan minimums, near-miss probes), keeps allowlists empty by default and inventories every exemption channel, pins denominators and thresholds so they fall only with the owner's approval, requires every regression fix to show detection, and states what no gate can catch. Use it whenever writing, changing, reviewing or relying on a lint rule, test suite, coverage threshold, drift or contract check, lock or hash check, budget, CI job, check script or hook; whenever adding an allowlist entry, exclusion or ignore pragma; whenever a gate has never failed or passes on empty input; and before trusting a green run as evidence, even for a check that looks too simple to get wrong.
license: MIT
---

# Gate integrity

A gate is a check that can stop work: a lint rule, a test suite, a
coverage threshold, a drift check, a script in the check command. It
claims that a rule holds. The claim is worth something only if the gate
fails when the rule breaks. A green gate that cannot fail is worse than
a red one, because it tells everyone to stop looking.

```
A GATE THAT HAS NEVER BEEN SEEN TO FAIL HAS NOT BEEN SHOWN TO WORK
```

Related skills: test-first proves individual tests with mutants and
catches vacuous ones; verify-before-claiming governs what a green run
lets you say; adversarial-procedure-review covers oracle grammars and
classifier injection; agent-baseline forbids agents to widen a gate;
landing-a-branch covers hooks that guard billed pushes.

Reference files, read when the section that links them applies:

- [references/silent-green.md](references/silent-green.md): the ways a
  check passes while checking nothing, and the separate case of
  incomplete diagnostics. Read it when auditing an existing gate or a
  green run you doubt.
- [references/oracles.md](references/oracles.md): independent oracles,
  equivalence checks, feature censuses and the mechanics of regression
  mutants. Read it when a gate compares outputs or a fix needs a mutant.
- [references/worked-examples.md](references/worked-examples.md): ten
  reconstructed failures, each with its mechanism and the limits of what
  was known. Read it to calibrate how ordinary these failures are.

## 1. A gate is a claim

Rules that hold are the ones a gate checks. Rules kept only in prose
decay, because nothing tells anyone when they break.

Before trusting any gate or metric, ask the proxy question: **what would
make this actually correct, and would the gate still pass if I did
something else?** If a change that breaks the rule can still pass, the
gate measures a proxy, and the gap needs a test or a written limit.

- Write each gate's blind spot beside it, in the checker or its
  configuration: what it cannot see (aliases, re-exports, generated
  code, unscanned directories). Section 10 lists the common ones.
- A rule that no gate checks yet may stand as a **review convention**,
  if it is listed, labelled as a convention and given a reason why no
  gate exists. Each convention is a candidate for a gate. A budget with a
  standing exception is a convention, not a gate.

## 2. Decide on structure, not text

A semantic claim ("nothing imports the internal module", "every handler
checks authorization") needs a parser: the syntax tree, the compiler's
module graph or the type checker. Report what binds a name, not what
mentions it.

- **Fail closed on anything the gate cannot resolve:** a dynamic import,
  a file that does not parse, a region with no marker. An unresolved
  case is a failure with a named message, never a skip.
- **Code inside strings and comments must not trigger the gate,** and
  must not satisfy it either.
- **Keep every miss as a permanent case.** When a gate moves from text
  matching to a parser, each thing the old check missed becomes a
  fixture.
- **Text checks are allowed only as conservative over-matching within a
  defined scope.** Such a check may raise a false alarm; it may never
  miss. Write the scope and the over-matching down beside it. A text
  check that can miss a violation must move to a parser.
- **Text-native rules need no parser.** Line width (counted in
  characters, not bytes), a final newline and a file encoding are
  properties of the text itself.

## 3. The gate's own gate

A checker is code, and an untested checker hides its own bugs well,
because they read as success. Every checker carries this block, as
tests that run in the same command as the checker:

```
STANDARD BLOCK: required tests for every checker

1. Fixtures: each case either passes, or fails with a named message.
   Assert the message, not only the exit status.
2. Unparseable input: a fixture the checker cannot read must fail.
3. Empty input: must fail wherever empty violates the gate's declared
   inventory (it declares at least one module, or a named set of
   sections). A gate over a set that may legitimately be empty
   declares that, and passes on empty.
4. Scan floor: a minimum number of items scanned, plus a named member
   the scan must find.
5. Spelling probes: one probe for every spelling the gate claims to
   catch, asserting an exact count; one near-miss probe that must find
   zero.
6. Strings and comments: a violation written inside a string or a
   comment neither triggers nor satisfies the gate.
7. Checker mutant: a run that swaps in a deliberately broken copy of
   the checker and requires the fixture suite to fail.
8. Case mutants: each must-fail fixture is shown to pass once its
   defect is removed, so it fails for its own reason and not an
   incidental one. Mutate each case, not only the harness as a whole
   (see test-first).
9. Modes: if the gate has a report mode and an assert mode, a planted
   violation exits 0 when reporting and non-zero when asserting.
```

Items 3 and 4 are what keep a gate from passing on nothing. Many real
gates fail exactly there; see the silent-green reference.

## 4. Allowlists and exemptions

The default policy is **empty by decision**: the gate has no exemptions.
When code cannot meet the rule, change the code, or have the owner
change the rule openly. **Reviewed and pinned** exemptions are permitted only when the
owner explicitly chooses that policy for a gate. Under that policy:

- each entry names a file and the exact line or construct, with a
  reason;
- an entry that matches nothing fails the gate, so the list only
  shrinks;
- each allowed file has an exact count, so a new use inside an allowed
  file still fails;
- the list is pinned in both directions and tested with near-miss
  names;
- it widens only by a recorded decision of the owner.

Under either policy, **every exemption channel is part of the
allowlist.** Inventory them all: lint-config overrides, per-directory
configuration, inline disable and ignore pragmas, `--exclude` flags,
ignore files, directories the gate never scans, skipped or focused
tests. An empty allowlist beside a config override or an unscanned
directory is not empty. Each exemption lives in the one record the gate
reads, with its exact location.

An agent never widens a gate. It adds no entry, pragma, exclusion or
override; it stops and reports the line and the rule (see
agent-baseline).

## 5. Denominators and thresholds

A threshold is a ratio, and either side can move.

- **Pin the denominator as well as the threshold.** Hash the exclusion
  list, count the inline ignore pragmas, and fail when either changes
  without a matching record.
- **Thresholds ratchet up only.** A decrease requires the owner's
  explicit approval. Changing the pinned record and writing a reason is
  not approval.
- **Measure against the inventory.** A file that nothing loads is often
  absent from a coverage report rather than shown at zero. Compare the
  report's file list with the source tree.
- **Coverage is optional, and it is a signal, never the goal.** Where a
  project uses it, the rules above apply.
- **Label each budget as measured or fiat.** A measured budget sits at a
  knee of an observed distribution; a fiat budget is a chosen limit. Say
  which one each is, so a later reader knows what evidence would justify
  moving it.

## 6. Regression obligations

**Every regression fix demonstrates detection.** Showing that the new
test passes is not enough; show that it fails with the defect present.

1. Where the project's harness supports mutant rows, add one. The row
   restores the defect in an isolated copy, names the test and states
   the expected failure.
2. Where it does not, record an equivalent reproduction in the fix's
   record: the command, the failing output against the defective
   version, and the passing output against the fix.
3. A defect that takes several edits to restore still needs evidence.
   Restore it across those edits, or reproduce it on the commit before
   the fix. Difficulty is not an exemption.
4. The expected failure names the defect's symptom, so an unrelated
   failure cannot satisfy the mutant.
5. The mutant goes where the defect is raised, not upstream of it.
   Breaking an earlier stage makes the test fail for a different reason
   and proves nothing about the fix.

The mechanics (isolated copies, verifying the clone, timeouts for probes
that may hang) are in [references/oracles.md](references/oracles.md).
The general method is test-first's "Tests Written After the Code".

## 7. Contract-test obligations

Where two components agree on an interface (hand-written type
declarations and a built library, an API schema and its handlers, a
document and the code it describes), a contract test checks one against
the other.

- **Check the declaration against the built artifact,** not against
  another hand-written copy.
- **Read the inventory from the source of truth,** such as the exported
  API object or the server's handler registry, not from a hand-kept list.
- **Check every list in both directions:** everything declared exists,
  and everything that exists is declared.
- **Assert that the test is not vacuous:** the number of items compared
  is at least a stated floor, and a named member is among them.
- **Pin a drift check's inventory.** List the sections or names it must
  find. A drift check over an unpinned inventory passes when the
  inventory is empty.
- **Assert the exact expected outcome per item.** A check that accepts
  either of two outcomes passes when the thing it checks has been
  deleted.

## 8. Gates that stop looking

A gate is written against a precondition: every colour comes from the
token file, every test lives under one directory, every module has a
marker. When the codebase outgrows the precondition, the gate keeps
running and passes vacuously, because the things it should check are no
longer where it looks.

Replace such a gate with a rule that cannot be satisfied vacuously: one
that checks the precondition itself, fails on anything outside it, and
keeps the scan floor from the standard block. When a gate's scan count
drops sharply, treat that as a failure to investigate, not as progress.

## 9. Cost, placement and modes

- **The authoritative place runs every gate.** That is CI where it
  exists. Without CI, it is the documented local check command, and
  "this belongs in CI" does not excuse a gate from it.
- **Hooks are never the only place a gate runs.** A hook is a
  convenience and can be skipped. Hooks that guard billed pushes serve a
  different purpose; see landing-a-branch and agent-baseline.
- **The routine check always runs in full.** Price a check before making
  it routine. An expensive check may be separate only if it names its
  triggers and the evidence it must produce when triggered: for example,
  "changes to matching, stored state or saved formats run the replay
  corpus and report the diff count".
- **Report-only suites may be permanent** when they gather exploratory
  evidence. Label them report-only. A report-only failure is still
  investigated and tracked in a durable record, never left to scroll
  past.
- **Required correctness checks gate.** A required check does not become
  report-only to escape its failures, and it does not stay as a gate
  that sometimes fails. Make it deterministic: serial phases, ratios
  with their preconditions asserted, waits on conditions instead of
  sleeps.
- **Timing checks stay noisy.** A serial phase and a bound set as a
  multiple of the median of several warm runs, or a ratio gate, reduce
  the noise. They do not make the measurement dependable, so a timing
  failure is investigated, never rerun until green.
- **Warnings that never fail are report-only.** A rule the project
  requires runs at error level, or the run fails on any warning.
- **Cheap gates close tool gaps:** a final newline, width in characters,
  a pinned compiler version after a measured crash rate.

## 10. Enforcement limits

State these where gates are documented, so nobody over-trusts them:

- **Syntactic blind spots.** Aliased or re-exported names, dynamic
  imports, checks of direct imports only, and code generated at build
  time escape structural gates unless the gate handles them explicitly.
- **Nominal comparison is not a type query.** Two identical written
  types are not the same claim as mutual assignability.
- **Oracles and exhaustive runs are bounded.** "Exhaustive" means within
  the stated grammar and size.
- **A mutant proves only the defect it restores.**
- **Hooks can be bypassed,** for example with `git commit --no-verify`.
  An owner-only allowlist relies on someone reviewing the diff.
- **Review conventions are unenforced by definition.**
- **Directories a gate does not scan are outside it,** including any test
  code that lives there.
- **Timing on shared hosts is noisy.** Ratios and serial phases reduce
  the noise; they do not make a timing measurement dependable.
- **A drift or contract check is only as good as its inventory.** Pin
  the expected sections or names, or an empty inventory passes.

A failing chained check that stops at its first failing step is not
silent green, but it is incomplete diagnostics: expect more failures
behind the one it shows. See the silent-green reference.

## Review checklist

1. Does each gate state its rule and its blind spot? Is every ungated
   rule listed as a labelled convention, with a reason?
2. Does every semantic check use a parser and fail closed on what it
   cannot resolve? Is every text check scoped, over-matching and
   documented as such?
3. Does every checker carry the standard block, including the empty
   input case against its declared inventory and a scan floor with a
   named member?
4. Is the allowlist empty by decision, or reviewed and pinned by the
   owner's explicit choice? Has every exemption channel been
   inventoried, including configs, pragmas, exclude flags and unscanned
   directories?
5. Are denominators pinned? Did any threshold fall, and if so, is the
   owner's approval on record?
6. Does every regression fix show detection: a mutant row, or a recorded
   reproduction? Does the expected failure name the symptom, and does
   the mutant sit where the defect is raised?
7. Do contract tests check against the built artifact, read the
   inventory from the source of truth, run in both directions and assert
   they are not vacuous?
8. Has any gate outgrown its precondition? Has any scan count dropped?
9. Does the authoritative place (CI, or the documented check command)
   run every gate? Does each expensive check name its triggers and its
   required evidence? Is any gate only in a hook?
10. Are report-only suites labelled, with their failures tracked? Are
    required correctness checks gating and deterministic?
11. Are the enforcement limits written down where the gates are
    documented?
