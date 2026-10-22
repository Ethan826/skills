# Effect idioms for TypeScript

Read this when writing or reviewing TypeScript that uses the Effect
library. It applies the rules of SKILL.md to TypeScript: name the steps,
keep decisions in combinators, and keep partial operations out.

**Version.** These idioms are for Effect 4, checked against
`effect@4.0.0-rc.116`, a release candidate, not a final release. Names
can still change before 4.0.0; re-check each one against the final release
before relying on this file. Effect 4 renamed much of the 3.x API: `Either` is
`Result`, `Option` and `Result` are no longer Effects, and several
`unsafeX` functions became `xUnsafe`. Before relying on a name below,
check that it exists in the version installed, by searching the
package's own source.

## Reach for the combinator

When you reach for an imperative pattern, find the combinator that
replaces it.

| Instead of | Write |
|---|---|
| `for`, `for...of` loop | `Array.map`, `Array.filter`, `Effect.forEach` |
| `for...in` loop | `Record.keys`, `Record.toEntries` |
| `array[0]` | `Array.head` (returns `Option`) |
| `array.length === 0` | `Array.isReadonlyArrayEmpty`, or `Array.isReadonlyArrayNonEmpty` |
| `array.push(x)` | `Array.append`, `Array.appendAll` |
| `record[key]`, which may be missing | `Record.get` (returns `Option`) |
| a `null` or `undefined` check | `Option.fromNullishOr`, then `Option.match` |
| `str === ""` | `String.isEmpty`, `String.isNonEmpty` |
| `low <= x && x <= high` | `Number.between`, `Order.isBetween` |
| `() => value` | `constant(value)` from `effect/Function` |
| `pipe(transform(input), ...)` | `pipe(input, transform, ...)` |
| `try`/`catch` | `Effect.try`, `Effect.tryPromise`, `Effect.catchTag` |
| `throw` | `Effect.fail` with a tagged error |
| `new Promise(...)` | `Effect.tryPromise` with a typed error |
| `JSON.parse` | `Schema.fromJsonString` with `Schema.decodeUnknownEffect`, `Schema.decodeUnknownOption` or `Schema.decodeUnknownResult` |
| `JSON.stringify` | `Schema.fromJsonString` with `Schema.encodeEffect` |
| a type assertion (`as`) | a `Schema` decode at the boundary |
| `if`/`else` or `instanceof` on a tagged union | `Match.tag` |
| a `??` chain or hand-written merge | `Struct.makeCombiner`, `Option.makeReducer` |
| `async` outside a real I/O boundary | an Effect pipeline |

`async` belongs at the boundary itself, such as a storage call or a
`fetch`, not in the code that decides what to do with the result.

## Never

Each of these either throws, hides a failure, or tells the compiler
something it cannot check. A lint can ban all of them by syntax.

- `Schema.decodeUnknownSync`, `decodeSync`, `encodeSync`,
  `encodeUnknownSync`, `validateSync`: they throw. Use the `Effect`,
  `Option` or `Result` variants.
- `getOrThrow` and `getOrThrowWith`, on `Option` or `Result`: partial.
  Use `Option.match`, `Option.getOrElse` or `Result.match`, or lift into
  the Effect.
- `Effect.promise`: it turns a rejection into a defect, which no typed
  handler sees. Use `Effect.tryPromise` with a typed error.
- `JSON.parse` and `JSON.stringify`: both throw, the second on a
  `BigInt` or a cycle.
- `instanceof`, a `switch` on `_tag`, `x._tag === "..."` and
  `"_tag" in x`.
- non-null assertions (`x!`) and type assertions other than `as const`.
- loops, `.push`, `.length`, `array[0]`, `throw`, `try`, and `async`
  away from a boundary, outside test files.
- a comment that switches a lint rule off. If a rule is wrong for a
  case, change the rule.

Test files may relax the loop, mutation and parsing rules, since
mutable fixtures and parsing test data are normal there. They keep the
ban on switching rules off.

## Sequential steps are one generator block

A storage read, then a decode, then an action, is one `Effect.gen` with
`yield*` on each step. Do not nest `.pipe(Effect.flatMap(...))` or
`.then()` chains, and do not re-check a hand-written cancellation flag
at each level.

```ts
const DraftFromJson = Schema.fromJsonString(Draft);

const restoreDraft = Effect.gen(function* () {
  const stored = yield* readStoredDraft;
  const text = yield* Effect.fromOption(stored);
  const draft = yield* Schema.decodeUnknownEffect(DraftFromJson)(text);
  yield* showDraft(draft);
});
```

To cancel, interrupt the fiber that `Effect.runFork` returns with
`Fiber.interrupt`.

## Lift Option and Result

In Effect 4, `Option` and `Result` cannot be yielded directly inside
`Effect.gen`. Lift them with `Effect.fromOption` and
`Effect.fromResult`, as in the example above. A `None` or a failure then
ends the whole block, and a `Some` or a success is the plain value on
the next line. That replaces `Option.match`, `Option.isNone` and nested
pipes inside a generator. The same holds in a `flatMap`:

```ts
const settingIn = (key: string) => (settings: Settings) =>
  Effect.fromOption(Record.get(settings, key));

const readSetting = (key: string) =>
  pipe(loadSettings, Effect.flatMap(settingIn(key)));
```

The step passed to `flatMap` has a name, as rule 2 of SKILL.md asks.

## Match on tags with the matcher

Read a tagged union with `Match`, never by reading `_tag`:

```ts
const describe = (event: OrderEvent) =>
  Match.value(event).pipe(
    Match.tag("Placed", describePlaced),
    Match.tag("Shipped", describeShipped),
    Match.exhaustive,
  );
```

For errors, `Effect.catchTag` and `Effect.catchTags` recover from a
tag, and `Effect.tapErrorTag` runs a side effect such as a log without
consuming the error. Read an `Option` or a `Result` with its own
`match` or `getOrElse`.

Do not reach for `instanceof` either: it fails across module copies and
cannot see a tag. Convert a library's thrown error into a tagged domain
error at the boundary.

Before adding `Effect.ignore`, ask whether one of the failures it
swallows should be logged. A blanket ignore makes a corrupted file and
an absent one look the same.

## Arrow functions

Write every function as an arrow expression, `const total = (lines) =>
...`, never as a `function` declaration or a named function expression.
The lint rules `func-style` (set to `expression`, allowing arrows) and
`prefer-arrow-callback` enforce this. The one exception is the generator
passed to `Effect.gen`, because JavaScript has no arrow generators.

## Boundaries decode with a schema

A value that crosses a real boundary, such as storage, a network
response, a picked file, a bundled JSON file or another language's
output, is `unknown` until a `Schema` decodes it. After that it is typed
and trusted, and nothing deeper re-checks it. If code deep in the
program feels it must re-check a value's shape, fix the boundary that
handed it over.

Decode several optional inputs in one pass with a `Schema.Struct` and
`Schema.optional`, instead of a chain of `if (x !== undefined)` checks.
Represent absence with `Option`, not `null` or `undefined`, in domain
state and in internal payloads: the values passed between modules inside
the core. An external payload, which crosses a public boundary such as a
facade to a UI shell, a wire format or an outside caller, uses that
boundary's plain representation, usually `undefined` or `null`. Where the
two conflict, the boundary rule wins: convert with `Option.getOrUndefined`
or `Option.getOrNull` at the facade, and decode back to `Option` on the
way in (decision-core-architecture, "The facade").
