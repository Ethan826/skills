# readable-functional-code-tsdoc check

Tests the reference TSDoc gate,
`skills/readable-functional-code/tsdoc/tsdoc-gate.ts`, with TypeScript at
the version in `package.json` and `bun.lock` (5.9.3), which must equal the
`anchors.json` tool entry for this check.

```bash
checks/readable-functional-code-tsdoc/run.sh        # the check; needs bun 1.3.6
checks/readable-functional-code-tsdoc/test-run.sh   # the check's own tests
```

`run.sh` copies the gate beside a pinned install in a temporary directory
and runs `cases.ts`, which fails when:

- an inline must-fail case (no comment, a line comment, a header comment
  only, a plain block comment, an empty TSDoc, a line comment between the
  TSDoc and the export, TSDoc text inside a string, and each kind of
  exported declaration, default export, `export =` and export list) does
  not give exactly its expected findings;
- a must-pass or near-miss case (a re-export, a commented-out export, an
  export inside a string, an undocumented private helper) gives any;
- the clean fixtures do not pass with exactly 9 exported declarations in 2
  files, or the dirty fixtures do not give exactly their 4 findings;
- an unparseable file, an empty directory or a scan minimum above the
  count does not fail with its named message.

`test-run.sh` plants one defect per case and requires the named failure:
a plain block comment accepted, a line comment after the TSDoc accepted,
an earlier comment accepted, an empty TSDoc accepted, export lists or
default exports skipped, a syntax error ignored, an empty directory
passing, the scan minimum dropped, the pin and the anchor disagreeing, a
range pin, and the gate missing.

## What it does not catch

- A spelling of an export that no case contains.
- Every blind spot listed at the top of `tsdoc-gate.ts`, including
  whether a comment is accurate.
- A project's copy of the gate drifting from this one.
