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

## Never switch a lint rule off

No comment may switch a lint rule off, in source or in tests. If a rule
is wrong for a case, change the rule. gate-integrity covers that
discipline.
