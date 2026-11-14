# effect-v4 check

Compiles the TypeScript examples in `skills/effect-v4/SKILL.md` and
`skills/readable-functional-code/typescript.md` against the versions in
`package.json` and `bun.lock` (effect 4.1.4, @effect/vitest 4.1.4,
vitest 5.1.0, TypeScript 7.0.2).

```bash
checks/effect-v4/run.sh            # the check; needs bun 1.3.6 on PATH
checks/effect-v4/test-run.sh       # the check's own tests (planted defects)
```

`run.sh` installs into a temporary directory, with bun's cache inside it, and
removes the directory on exit. A run uses about 240 MB at peak. It fails when:

- `package.json` pins a range, or its versions differ from the `anchors.json`
  `tool` entries whose `check` is `checks/effect-v4`, or from what is installed;
- `bun install --frozen-lockfile` fails, for example after a `package.json`
  change without a matching `bun.lock`;
- either file has an unterminated fence, or a fence tagged `typescript`, `tsx`,
  `js`, `javascript`, `mts` or `cts` (only `ts` blocks are extracted);
- the block counts differ from `expected.json`, or a prelude has no block;
- any block, with its prelude, or any file in `controls/` fails `tsc`;
- `mustfail-raw/must-fail.ts` (v3 names and other code the skill says does not
  compile) gives any errors other than the seven listed in `expected.json`, by
  line and code;
- `runtime/promise-rejection.ts` does not print `CLAIM HOLDS`.

Each block is compiled as its own module. A file in `preludes/` with the same
name supplies stubs for the names a block uses without declaring them.

## Adding or removing a block

Update the count in `expected.json`. If the block uses undeclared names, add
`preludes/<prefix>-NN.ts`, numbered by the block's position in its file.
Removing a block renumbers the blocks after it, so renumber their preludes too.

## What it does not catch

- Prose claims that no block or control exercises.
- Whether a stub in `preludes/` matches what the skill describes. A stub that
  is too loose can let a wrong block compile; `controls/types.ts` pins the
  inferred types of block 02 only.
- Fences in other files of either skill.
- Behavior at runtime, except for the one `Effect.promise` claim.
