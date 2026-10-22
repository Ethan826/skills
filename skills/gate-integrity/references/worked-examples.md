# Worked examples

Ten failures of real gates, reconstructed in neutral form. Names,
identifiers and details are changed; each keeps the mechanism and what
was and was not known afterwards. None was exotic: in each case the
gate ran, passed and was trusted.

Each example gives the setup, what went wrong, the limits of the
evidence, and the rule from SKILL.md that would have caught it.

## 1. Shard flags swallowed by a wrapper

**Setup.** CI split the test suite into several shards. Each shard
called a shell wrapper with a shard flag, and the wrapper called the
test runner.

**What went wrong.** The wrapper did not forward its arguments, so the
runner never saw the flag. Every shard ran the whole suite. All shards
were green.

**Evidence limits.** No test was skipped, since every shard ran
everything, so the failure hid no defect. What it did hide was cost,
and the meaning of each shard's result: a green shard said nothing
about its own share.

**Rule.** Each shard reports what it collected; the gate asserts the
shards are disjoint, non-empty and together equal the inventory
(silent-green: shard flags).

## 2. A hash lock that passed on an empty directory

**Setup.** A lock file recorded hashes of generated files, and a check
compared the files on disk with it.

**What went wrong.** The check iterated over the files present. With
the directory empty, there was nothing to compare, and it passed. Its
failure message, when it did fail, suggested a command that recomputed
every hash, so the easy response to any mismatch was to accept all of
it.

**Evidence limits.** Reading the checker established the risk. It did
not establish whether bad content was ever accepted this way.

**Rule.** The empty-input case against the declared inventory, and a
scan floor (standard block, items 3 and 4). Updates to a lock are per
file and reviewed.

## 3. A drift check with zero sections

**Setup.** A check kept marked sections of a document in step with the
code they described.

**What went wrong.** After the marker format changed, the check found
no sections in either file, compared nothing and passed.

**Evidence limits.** Its green runs said nothing about whether the
sections matched. Any drift during that time had to be found by
comparing the files directly.

**Rule.** Pin a drift check's inventory (section 7).

## 4. Coverage thresholds lowered by hand

**Setup.** A ratchet script raised coverage thresholds as coverage
improved, and the thresholds were stored in configuration.

**What went wrong.** The thresholds were lowered by a direct edit to the
configuration, inside a commit about something else. The ratchet only
ever raised them, so nothing objected to a decrease.

**Evidence limits.** Whether the lower thresholds let a defect through
is unknown. What is known is that the gate's bar moved without anyone
deciding it should.

**Rule.** A threshold decrease needs the owner's explicit approval; a
changed record with a reason is not enough (section 5). The gate fails
when a threshold falls below its pinned value without that approval on
record.

## 5. An exclusion list that hid the buggy files

**Setup.** Coverage excluded a list of files said to be hard to test.

**What went wrong.** Several defects found later were in files on that
list. The coverage figure was high because the files most in need of
tests were outside its denominator.

**Evidence limits.** This is a correlation. It does not show that a
coverage gate would have caught the defects, only that the files were
never measured.

**Rule.** Pin the denominator: hash the exclusions and give each a
reason (section 5). Under the default policy, the list is empty.

## 6. A resolver that returned null

**Setup.** An accessibility gate resolved each colour token in the
interface to a value and checked foreground and background pairs for
contrast.

**What went wrong.** After the theme moved to a new format, the
resolver returned null for every token. The gate skipped unresolved
pairs, measured nothing and passed.

**Evidence limits.** The green runs gave no evidence either way about
contrast. Whether a low-contrast pair shipped meanwhile had to be
established by fixing the gate and running it again.

**Rule.** Fail closed on anything unresolved (section 2), keep a scan
floor with a named pair (standard block), and replace a gate whose
precondition no longer holds (section 8).

## 7. A QA script that accepted either status

**Setup.** A script requested each page of a web application and
checked the response.

**What went wrong.** It accepted either "ok" or "not found" as a pass,
to cope with pages that were optional. Pages that had been deleted by
mistake passed.

**Evidence limits.** The green runs gave no evidence about the deleted
pages, or about any page that answered "not found" when it should have
answered "ok".

**Rule.** Assert the exact expected outcome per item, and read the
inventory from the source of truth (section 7).

## 8. Inline pragmas as a second denominator channel

**Setup.** The coverage exclusion file was pinned by hash, so it could
not grow unnoticed.

**What went wrong.** Inline coverage-ignore pragmas were not counted.
Exclusions moved from the pinned file into pragmas, and the project's
own instructions recommended a pragma as the fix for uncovered code.

**Evidence limits.** How many pragmas replaced entries that would
otherwise have needed review is not known.

**Rule.** Every exemption channel is part of the allowlist (section 4);
count the pragmas and pin the count (section 5).

## 9. A lint whose warnings never failed

**Setup.** A set of lint rules ran at warning level in the check
command.

**What went wrong.** The check exited 0 whatever the warnings said.
Warnings accumulated until nobody read them, and the rules were in
effect off.

**Evidence limits.** Whether any of the warnings marked a real defect
was not established. The known cost is a rule set that people believed
was enforced.

**Rule.** Warnings that never fail are report-only; a required rule
runs at error level (section 9).

## 10. A mutant upstream of the defect

**Setup.** A regression fix in a validation step came with a mutant row
meant to prove its test.

**What went wrong.** The mutant broke the input parser, a stage before
the validator. The test failed, so the row passed, but it failed
because parsing broke, not because the validation defect was back. The
row proved nothing about the fix.

**Evidence limits.** The fix itself may have been sound. The misplaced
mutant could not show it either way, so the fix stood without evidence
of detection until the mutant was moved to the validator and rerun.

**Rule.** The mutant goes where the defect is raised, and the expected
failure names the symptom (section 6).
