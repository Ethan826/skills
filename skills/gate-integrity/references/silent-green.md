# Silent green: checks that pass while checking nothing

Each entry below is a way a gate reports success without having tested
the rule. Each gives the mechanism, how to notice it, and the test that
keeps it from coming back. Most are prevented by the standard block in
SKILL.md, section 3, above all its empty-input case and its scan floor.

Illustrations are in TypeScript or POSIX shell. They are small and the
same mechanisms occur in other stacks.

## The catalogue

### Test files that no runner collects

A test file whose name or directory does not match the runner's
discovery pattern is never run. It passes in the sense that nothing
fails. The same happens when discovery is a hand-kept list that someone
forgot to update.

- **Notice it:** compare the files that look like tests with the files
  the runner reports having collected.
- **Prevent it:** assert that discovery finds a minimum number of files
  and a named file, and fail on any file matching the test naming
  convention that the runner did not collect.

### Mocks of modules that do not exist, or one module mocked twice

A mock registered for a misspelled or deleted module path can succeed
silently, so the code under test uses the real module, or another mock,
and the test checks the wrong thing. Two mocks for one module leave the
outcome to registration order.

- **Prevent it:** resolve every mocked path and fail if it does not
  resolve; fail on duplicate registrations.

### Exit status taken from the last command in a pipe

```sh
# illustration: the test runner's failure is lost
run-tests | tee test.log
```

Without `set -o pipefail` (or the shell's equivalent), the pipeline's
status is that of `tee`, which succeeds.

- **Prevent it:** set `pipefail` in every check script, and add a fixture
  where the first command fails and the script must exit non-zero.

### A resolver that returns null

A gate that resolves names to values (colour tokens to colours, config
keys to settings, symbols to definitions) and then skips anything that
resolved to null measures nothing once resolution breaks.

- **Prevent it:** an unresolved name fails the gate. Assert a minimum
  number of measured pairs and a named pair that must be measured.

### An index search that restarts at the beginning

```ts
// illustration: indexOf with a negative start searches from 0
const at = text.indexOf(marker, previous - 1); // previous is 0 on the first pass
```

`indexOf` clamps a negative start position to 0, so a loop meant to
advance can find the same match again, or a check meant to look after a
position looks at the whole string.

- **Prevent it:** prefer a parser. Where a scan is unavoidable, add a
  fixture whose match occurs only before the start position, and assert
  zero.

### Runtime globals undefined under the test runner

Code that tests for a global the production runtime provides (a browser
or server object) finds it undefined under the test runner, takes the
fallback branch, and every test exercises the fallback.

- **Prevent it:** assert in setup that the globals the code depends on
  exist, or test both branches explicitly.

### Warnings that never fail

A lint rule set to warning level prints its findings and exits 0. The
findings accumulate, and the rule is report-only whatever its
configuration says.

- **Prevent it:** required rules run at error level, or the run fails
  on any warning. A warning-level rule is listed as report-only.

### A drift check that passes with zero sections

A check that compares marked sections between two files passes when it
finds no markers in either, for example after the marker syntax
changes.

- **Prevent it:** pin the expected section names, and fail when any is
  missing or when the count is below the inventory.

### A lock that passes on an empty directory

A hash lock compares the files present against recorded hashes. With
no files present there are no mismatches. If the lock's failure message
also offers a command that rewrites every hash, the routine response to
any mismatch is to accept it.

- **Prevent it:** the lock declares its inventory and fails when a
  listed file is missing. Updating it is a per-file, reviewed action,
  never one command that accepts everything.

### A lint pragma in a form that does nothing

Some languages accept a pragma or attribute in more than one spelling,
and only one of them reaches the linter. The other compiles and is
ignored. The setting it was meant to make never takes effect, and the
writer believes the rule is configured as written.

- **Prevent it:** a probe for each spelling, asserting the linter's
  observed behavior, not the presence of the text.

### Shard flags that never reach the runner

A wrapper script that does not forward its arguments drops the shard
selection, so every shard runs the whole suite. The run is green and
slow, and a report that "shard 3 passed" says nothing about shard 3.

- **Prevent it:** each shard reports the tests it collected. Assert
  that the shards are disjoint, that together they equal the full
  inventory, and that none is empty.

### Accepting either of two outcomes

A check that passes when the response is "found" or "not found" passes
when the thing it checks is deleted.

- **Prevent it:** assert the exact expected outcome for each item, and
  read the items from the source of truth.

## Incomplete diagnostics (not silent green)

A chained check that stops at its first failing step (`a && b && c`, or
a script under `set -e`) still fails, so it is not silent green. It
hides the later failures: a run that reports one failure may have
several behind it.

- Read which step stopped the run, as well as the exit status.
- Expect more failures after a fix. Rerun the whole chain, and do not
  report "one failure, fixed" as "clean" until the full chain has
  passed.
- Where the full list matters, run each step, collect the results, and
  exit non-zero at the end if any step failed.
