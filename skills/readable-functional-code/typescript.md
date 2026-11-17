# TypeScript house style

Read this when writing or reviewing TypeScript in a project that has
adopted this house style. It applies the rules of SKILL.md to
TypeScript. Effect's API (which combinator replaces a loop, which calls
to ban, how to lift `Option` and `Result`, how to decode) is in the
effect-v4 skill.

## Budgets, file length and line width

Rule 6's per-declaration budgets and rule 7's limits apply to TypeScript
as written: depth 3, 8 branches, 30 lines and 8 local bindings per
top-level declaration, a hard limit of 250 lines per module, and 80
columns. Count `if`, `switch` and conditional expressions where SKILL.md
counts `case`, `if` and guards, and count a declaration's local `const`
bindings where it counts `where` bindings.

## Name what you pass

Rule 2 holds here: a step passed to `map`, `flatMap`, `filter` or any
other combinator gets a descriptive name, however short the lambda.

Not this:

```ts
import { Effect, Record, pipe } from "effect"

const readSetting = (key: string) =>
  pipe(
    loadSettings,
    Effect.flatMap((settings) => Effect.fromOption(Record.get(settings, key))),
  )
```

This:

```ts
import { Effect, Record, pipe } from "effect"

const settingIn = (key: string) => (settings: Settings) =>
  Effect.fromOption(Record.get(settings, key))

const readSetting = (key: string) =>
  pipe(loadSettings, Effect.flatMap(settingIn(key)))
```

## Arrow functions

Write every function as an arrow expression, `const total = (lines) =>
...`, never as a `function` declaration or a named function expression.
The lint rules `func-style` (set to `expression`, allowing arrows) and
`prefer-arrow-callback` enforce this. The exception is a generator
passed to `Effect.gen` or `Effect.fn`, because JavaScript has no arrow
generators.

## Document with TSDoc

Every exported declaration gets a TSDoc comment (`/** ... */`) directly
above it. So does a private helper with a rule in it; a one-line adapter
needs none. The comment says what the declaration is or does, its units
and edge cases where they matter, and the design rule it implements,
named so a reader can find it. A file-level `//` comment documents
nothing below it, and neither does a line comment between the TSDoc and
the declaration.

Not this:

```ts
// Estimates.
export const estimate = (increases: ReadonlyArray<number>) =>
  Math.max(minEstimatePoints, ...increases)
```

This:

```ts
/**
 * The estimate for a role's next step, in percentage points: the largest
 * recent increase, raised to `minEstimatePoints` if lower, because every
 * reservation reserves at least one point (design rule O15). An empty
 * list gives `minEstimatePoints`.
 */
export const estimate = (increases: ReadonlyArray<number>) =>
  Math.max(minEstimatePoints, ...increases)
```

Check the exports with a gate that reads the syntax tree.
[`tsdoc/tsdoc-gate.ts`](tsdoc/tsdoc-gate.ts) is a reference: copy it
into the project and run it from the check command with a scan minimum,
as in `bun tsdoc-gate.ts --min 60 src`. It fails on an export with no
TSDoc, an empty TSDoc, a line comment between the TSDoc and the
declaration, a file that does not parse, and a scan below the minimum.
The top of the file states its blind spots: it sees only that a comment
is there and cannot tell whether the comment is true. It does not check private code,
re-exports or class members. Private helpers rest on review.
`checks/readable-functional-code-tsdoc` in this repository holds the
gate's own must-fail cases and mutants.

## Never switch a lint rule off

No comment may switch a lint rule off, in source or in tests. If a rule
is wrong for a case, change the rule. gate-integrity covers that
discipline.
