# Oracles, equivalence checks and regression mutants

Detailed techniques for gates that compare outputs, and for showing that
a regression test detects its defect. SKILL.md sections 6 and 7 state
the obligations; this file covers how to meet them.

Two related techniques are covered in adversarial-procedure-review and
not repeated here: fixing an oracle's grammar and bounds before running
it (and labelling any change made after a run), with cross-checks of a
fast search's "none found" against brute force; and testing a failure
classifier by injecting each failure directly.

## Independent oracles

An oracle is a second way of computing the right answer. It is useful
only if it is independent of the code under test.

- **Share no logic with the procedure.** An oracle that calls the same
  helper, parser or normalizer inherits its bugs and agrees with them.
- **Test the oracle's sensitivity.** Corrupt the value the oracle reads
  back, on purpose, and require the comparison to fail. A comparison
  that still passes against a corrupted read-back is comparing nothing,
  for example because both sides were read from the same cache.
- **State the oracle's bounds.** An oracle that enumerates inputs is
  exhaustive only within its grammar and sizes. Report results with
  those bounds.

## Census of observed features

A generator of test inputs can drift until it tests very little: a
filter rejects most cases, a weighting change starves a branch, or a
refactor removes a constructor. The intended coverage stays in the
design; the actual coverage falls.

- Count the features the generated inputs actually exercised during the
  run (each constructor, each branch of interest, each edge such as the
  empty case and the maximum size), not the features the generator could
  produce.
- Set hard minimums for each, and fail the run if any falls short.
- Report the census beside the result, so a reader sees what the pass
  covered.

## Equivalence checks

When a change should preserve behavior (a refactor, an optimization, a
rewrite of a matcher), compare its outputs on a corpus of inputs.

- **Compare against an exact truth where one exists,** such as a
  reference implementation or recorded outputs that were themselves
  checked. A comparison against the parent build only shows that
  nothing changed, including the bugs.
- **When the parent build is the baseline, build it from the branch's
  merge-base.** A main branch that has moved since the branch forked
  attributes other people's changes to this one.
- **Size the corpus to the risk.** Run corpus-wide or exhaustive
  comparisons for changes to core behavior, stored state or saved
  formats. A local change gets a corpus that covers its paths.
- **Report differences by kind,** not only as a count: an expected
  improvement, an accepted change and an unexplained difference need
  different decisions.

## Regression mutants: mechanics

The obligation (SKILL.md section 6): every regression fix demonstrates
detection, with a mutant row where the harness supports one and a
recorded reproduction otherwise. test-first describes the basic method.
These are the details that make a mutant trustworthy.

### The expected failure names the symptom

A mutant row records the test and the failure it expects. Match on the
defect's symptom, such as the wrong value, the missing field or the
message the bug produces, not merely on "the test failed". Otherwise a
compile error, a timeout or an unrelated assertion satisfies the row.

```ts
// illustration: a mutant row
{
  defect: "discount applied twice when coupon and sale overlap",
  restore: "patches/double-discount.diff",
  test: "pricing.overlap.test.ts",
  expect: /expected total 90\.00, got 81\.00/,
}
```

### Put the mutant where the defect is raised

Restore the defect at the line that produced it. A mutant that breaks
an earlier stage (the input parser, a fixture loader, an import) makes
the test fail, but for a reason the fix never addressed. The row then
passes while proving nothing about the fix.

### Restorations that take several edits

Some defects cannot be restored in one change: the fix touched several
files, or the surrounding code has since moved. That is not an
exemption. Either restore the defect across the needed edits, as one
patch, or reproduce it on the commit before the fix and record the
command and both outputs. Record which method was used.

### Verify the clone

A mutant runs in an isolated copy, so restoring the defect cannot
damage the real tree. Check that the copy is really isolated and really
current:

- **No hard links.** A copy made with hard links shares file contents
  with the original, so writing the mutant into the copy writes it into
  the real tree. Copy file contents, or use a fresh worktree.
- **The copy builds what you think it builds.** Show once that an
  incremental build of the copy equals a clean build, or use a clean
  build. A stale build artifact can pass or fail independently of the
  mutant.
- **The copy is discarded afterwards,** and the test passes again on the
  real tree.

### Probes that might hang

A restored defect can turn a failure into an infinite loop or a
deadlock. Run each mutant in a child process with a timeout, and treat
a timeout as its own outcome. A timeout is not the expected symptom
unless the row says it is.

## What this evidence shows

- A mutant proves the test detects the defect it restores, and only
  that one.
- An oracle comparison proves agreement within its bounds and its
  corpus.
- A census proves which features the run exercised, not that each was
  checked correctly.

Write these limits beside the result.
