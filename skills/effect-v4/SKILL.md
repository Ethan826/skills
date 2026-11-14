---
name: effect-v4
description: "How to write TypeScript with Effect v4 (the effect package, 4.x): the v3 names that no longer exist or changed meaning (Either, Context.Tag, Effect.catchAll, Schema.decode, Option.fromNullable and others), the combinator to use in place of each imperative pattern, tagged errors and no throwing in core code, lifting Option and Result into Effect, Schema decoding instead of type assertions, Match on tags, Combiner and Reducer instead of hand-written merges, the dual data-first and data-last convention, services as Context.Service behind Layers built once in a ManagedRuntime, tests that substitute a Layer rather than a global, and tests that enforce these rules. Use it whenever you write, review or plan TypeScript that imports effect at version 4, when an Effect API name comes from memory, and when you add a service, a Layer, a runtime or a test double. Checked against effect 4.1.4."
license: MIT
---

# Writing TypeScript with Effect v4

Effect v4 renamed a large part of the v3 API, and most of what a model
remembers about Effect is v3. A v3 name usually fails to compile, which
costs a cycle. A few are worse: they still exist in v4 but mean
something else. This skill lists those names first, then gives the
practice for writing Effect code: combinators instead of statements,
typed failures instead of exceptions, decoding instead of asserting,
and dependencies as services behind Layers.

Related skills cover what this one leaves out. decision-core-architecture
says where pure decisions and effects live in an application.
readable-functional-code, in its reference file `typescript.md`, has
the house readability rules for TypeScript, for a project that has
adopted them. public-api-argument-shape
covers the parameters of your own public functions. gate-integrity covers
how to make the enforcing tests in the last section trustworthy.

## Versions

| Tool or package | Version |
|---|---|
| effect | 4.1.4 |
| @effect/vitest | 4.1.4 |
| typescript | 5.9.3 |

Every API name below was checked against effect 4.1.1 by reading
the package's own source (`node_modules/effect/src`) and the
documentation it ships (`node_modules/effect/AGENTS.md` and
`node_modules/effect/ai-docs`). That reading was not repeated for 4.1.4.
For 4.1.4, every code block was compiled against effect 4.1.4 with
TypeScript 5.9.3 under `strict` and `exactOptionalPropertyTypes`, given
stub declarations for the domain names a fragment leaves out, and a
search of the export statements in `node_modules/effect/src` covered the
table of v3 names below. The `@effect/vitest` names were checked by
compiling a use of each against `@effect/vitest` 4.1.4.

Before relying on a name here, confirm it in the version you have
installed: search `node_modules/effect/src/<Module>.ts` for
`export const <name>`. Names that are reserved words are exported under
an alias, such as `try_ as try` and `catch_ as catch` in `Effect.ts`. If
the installed package ships `AGENTS.md`, read it before writing Effect
code. It is written for the installed version, and it is more current
than this skill or your memory.

Pin `effect` and every `@effect/*` package to an exact version and
commit the lockfile. Do not install `effect@latest` or use a caret
range: minor releases add and rename APIs, and an unpinned upgrade
turns a name that compiled yesterday into an error nobody chose. Treat
an upgrade as a review, with dependency-intake.

## v3 names that are wrong in v4

Each row is a v3 name a model is likely to write, and what to use in
v4. Every name in the left column was checked in effect 3.19.15 and
every name in the right column in 4.1.1. A left-column name is either
gone from 4.1.1 or, where the row shows a different call shape, takes
different arguments there. In 4.1.4, a search of the source's export
statements found every right-column name exported and every left-column
name without a call shape absent; of the call-shape rows, only
`Schema.decode(schema)(input)` and `yield*` of an Option were compiled
again, as must-fail controls.

| v3 | v4 |
|---|---|
| `Either`, `Either.right`, `Either.left` | `Result`, `Result.succeed`, `Result.fail` |
| `Effect.either` | `Effect.result` |
| an `Either` yielded or piped as an Effect | `Effect.fromResult(result)` |
| `Context.Tag`, `Context.GenericTag`, `Effect.Tag`, `Effect.Service` | `Context.Service` (or `Context.Reference` when there is a default) |
| `Effect.catchAll` | `Effect.catch` |
| `Effect.catchAllCause` | `Effect.catchCause` |
| `Effect.fork`, `Effect.forkDaemon` | `Effect.forkChild`, `Effect.forkDetach` |
| `Effect.zipRight` | `Effect.andThen` |
| `Layer.scoped`, `Layer.scopedDiscard` | `Layer.effect`, `Layer.effectDiscard` (they run in the layer's scope) |
| `Option.fromNullable` | `Option.fromNullishOr` |
| `Array.isEmptyReadonlyArray`, `isNonEmptyReadonlyArray` | `Array.isReadonlyArrayEmpty`, `isReadonlyArrayNonEmpty` |
| `DateTime.unsafeNow` (the `unsafeX` naming) | `DateTime.nowUnsafe` (`xUnsafe`) |
| `Schema.decodeUnknown`, `Schema.decode(schema)(input)` returning an Effect | `Schema.decodeUnknownEffect`, `Schema.decodeEffect` |
| `Schema.parseJson` | `Schema.fromJsonString` |
| `Schema.optionalWith` | `Schema.optional` (key may be missing or `undefined`) or `Schema.optionalKey` (key may be missing) |
| `Schema.Literal("a", "b")` | `Schema.Literals(["a", "b"])`; `Schema.Literal` takes one value |
| `Schema.Union(A, B)` | `Schema.Union([A, B])`, an array |
| `Schema.transform` | `Schema.decodeTo` with a `SchemaTransformation` |
| `Semigroup`, `Monoid` from `@effect/typeclass` | `Combiner`, `Reducer` in `effect` |
| `yield* someOption` inside `Effect.gen` | `yield* Effect.fromOption(someOption)` |

Two of these names still exist in v4 and mislead. `Schema.decode`
builds a transformation from a pair of getters. It does not
run a decoder, so `Schema.decode(User)(input)` is a type error rather
than a decode. `Option` and `Result` are no longer Effects. They
have their own iterators for `Option.gen` and `Result.gen`, but
`Effect.gen` cannot yield them; lift them first (see "Lift Option and
Result").

## Reach for the combinator

When you reach for a statement, find the combinator that replaces it.

| Instead of | Write |
|---|---|
| `for` or `for...of` | `Array.map`, `Array.filter`, `Array.reduce`, `Effect.forEach` |
| `for...in` | `Record.keys`, `Record.toEntries` |
| `array[0]` | `Array.head`, which returns an `Option` |
| `array.length === 0` | `Array.isReadonlyArrayEmpty`, `Array.isReadonlyArrayNonEmpty` |
| `array.push(x)` | `Array.append`, `Array.appendAll` |
| `record[key]` that may be missing | `Record.get`, which returns an `Option` |
| `x !== null`, `x !== undefined` | `Option.fromNullishOr`, then `Option.match` |
| `str === ""` | `String.isEmpty`, `String.isNonEmpty` |
| `low <= x && x <= high` | `Number.between`, `Order.isBetween` |
| `() => value` | `constant(value)` from `effect/Function` |
| `pipe(f(input), g)` | `pipe(input, f, g)` |
| `try`/`catch` | `Effect.try`, `Effect.tryPromise`, then `Effect.catchTag` |
| `throw` | `return yield* new SomeError(...)`, or `Effect.fail` |
| `await somePromise` | `Effect.tryPromise({ try, catch })` with a typed error; `Effect.promise` only for a Promise that cannot reject |
| `new Promise(...)` | `Effect.tryPromise` with a typed error |
| `JSON.parse` | `Schema.fromJsonString` with `Schema.decodeUnknownEffect`, `Schema.decodeUnknownOption` or `Schema.decodeUnknownResult` |
| `JSON.stringify` | `Schema.fromJsonString` with `Schema.encodeEffect` |
| `x as T` | a `Schema` decode at the boundary |
| `if`/`switch`/`instanceof` on a tagged union | `Match.tag`, or `Effect.catchTag` for errors |
| a `??` chain or a hand-written merge | `Struct.makeCombiner`, `Option.makeReducer`, `Combiner.last` |
| `isString`-style helpers you write yourself | `Predicate.isString`, `Predicate.isObject` and the rest of `Predicate` |
| `Date.now()`, `new Date()` | `DateTime.now` or `Clock.currentTimeMillis`, which a test can control |

`async` and `await` belong only in the adapter that calls a Promise API.
The code that decides what to do with the result is an Effect pipeline.

## No throwing in core code

Core functions return `Effect`, `Result` or `Option`, and never throw.
A failure the caller can act on is a tagged error in the error channel:

```ts
import { Effect, Schema } from "effect"

export class InvalidLimit extends Schema.TaggedError<InvalidLimit>()(
  "InvalidLimit",
  { limit: Schema.Number },
) {}

export const requirePositive = Effect.fn("requirePositive")(function* (
  limit: number,
) {
  if (limit <= 0) {
    return yield* new InvalidLimit({ limit })
  }
  return limit
})
```

`Data.TaggedError("InvalidLimit")<{ readonly limit: number }>` also
works and does not need a schema. Use `Schema.TaggedError` when the
error must be encoded, such as across an RPC or into a log record. Write
`return yield*` when failing inside a generator, so the compiler knows
the code after it is unreachable.

A defect means the code is wrong. `Effect.die` and `Effect.orDie` turn
a failure into a defect, which no typed handler sees, so use them only
for what cannot happen when the code is correct. If the process must
stop on a defect, stop it once, in the entrypoint.

Before adding `Effect.ignore`, ask whether any failure it swallows
should be logged. A blanket ignore makes a corrupted file and a missing
one look the same. `Effect.ignore({ log: true })` logs the full cause
and then discards the failure.

These throw or hide a failure. A lint can ban all but one of them by
syntax, and the exception says how to gate it:

- `Schema.decodeUnknownSync`, `Schema.decodeSync` and the other `*Sync`
  decoders and encoders, and `Schema.asserts`, all of which throw. The
  `*Promise` forms (`Schema.decodePromise`, `decodeUnknownPromise`,
  `encodePromise`, `encodeUnknownPromise`) reject instead. Use the
  `Effect`, `Result` or `Option` variant.
- `Option.getOrThrow`, `Result.getOrThrow` and their `With` forms. Use
  `match` or `getOrElse`, or lift into the Effect.
- `Effect.promise` on a Promise that can reject. `Effect.promise` is
  only for a Promise that cannot reject. If it rejects anyway, the
  rejection becomes a defect, not a typed failure, so no `Effect.catch`
  or `Effect.catchTag` sees it. Anything that can reject goes through
  `Effect.tryPromise({ try, catch })`, with a `catch` that returns a
  tagged error. The one-argument form fails with `Cause.UnknownError`,
  which no domain handler names. No syntax check can tell whether a
  Promise can reject, so the lint flags every `Effect.promise`, and each
  one kept goes in the gate's allowlist with the reason it cannot
  reject.
- `JSON.parse` and `JSON.stringify`. Both throw, the second on a
  `BigInt` or a cycle. Use `Schema.fromJsonString` with a decode or
  encode.
- `instanceof` on errors, a `switch` on `_tag`, `x._tag === "..."` and
  `"_tag" in x`. `instanceof` fails across two copies of a module and
  cannot see a tag. Convert a library's thrown error into a tagged
  domain error at the boundary.
- non-null assertions (`x!`) and type assertions other than `as const`.
- loops, `.push`, `.length`, `array[0]`, `throw`, `try`, and `async`
  away from a boundary. The table in "Reach for the combinator" gives
  the replacement for each.

Test files may relax the loop, mutation and parsing rules, since
mutable fixtures and parsing test data are normal there. They keep the
rest.

## Lift Option and Result into Effect

Inside an Effect, an `Option` or a `Result` is not branched on. It is
lifted, and the absence or the failure ends the pipeline:

```ts
import { Data, Effect } from "effect"

class TaskNotFound extends Data.TaggedError("TaskNotFound")<{
  readonly taskId: string
}> {}

const taskTitle = Effect.fn("taskTitle")(function* (taskId: string) {
  const store = yield* TaskStore
  const task = yield* Effect.fromOption(store.find(taskId), () =>
    new TaskNotFound({ taskId }))
  return yield* Effect.fromResult(parseTitle(task.rawTitle))
})
```

This replaces `Option.match`, `Option.isNone` and nested pipes inside a
generator. The same lift works in a `flatMap`:

```ts
import { Effect, Record, pipe } from "effect"

const settingIn = (key: string) => (settings: Settings) =>
  Effect.fromOption(Record.get(settings, key))

const readSetting = (key: string) =>
  pipe(loadSettings, Effect.flatMap(settingIn(key)))
```

`Effect.fromOption` fails with `Cause.NoSuchElementError` when given no
second argument. Pass a function that returns a domain error when the
caller needs to tell this absence from another. To go the other way,
`Effect.result` turns an Effect's failure into a `Result` value and
`Effect.option` turns it into an `Option`.

Outside an Effect, keep using `Option` and `Result` directly, and read
one with its own `match` or `getOrElse`.

## Decode, never assert

A value from outside the program (a file, a response, a message, an
environment variable, a bundled JSON file, another process's output) is
`unknown` until a `Schema` decodes it. After that it is typed and
trusted, and nothing deeper re-checks it. If code deep in the program
feels it must re-check a value's shape, fix the boundary that handed it
over.

```ts
import { Schema } from "effect"

const Config = Schema.Struct({
  pollSeconds: Schema.Int,
  label: Schema.optional(Schema.String),
})

const ConfigFromJson = Schema.fromJsonString(Config)

const readConfig = (text: string) =>
  Schema.decodeUnknownEffect(ConfigFromJson)(text)
```

The decoders come in four shapes: `decodeUnknownEffect`,
`decodeUnknownResult`, `decodeUnknownOption` and `decodeUnknownExit`,
plus `decodeEffect` and the others for input that is already typed as
the encoded form. Pick by where the result goes; avoid the `Sync` forms.
Decode several optional inputs in one `Schema.Struct` with
`Schema.optional` fields rather than a chain of `if (x !== undefined)`.
Map the schema's issue to a tagged domain error at the boundary, so the
core never sees a parse error.

Absence is `Option.none()`, not `null` or `undefined`, in domain state
and in the payloads passed between modules inside the core. A payload
that crosses a public boundary (a facade to a UI shell, a wire format,
an outside caller) uses that boundary's plain representation, usually
`undefined` or `null`. Where the two conflict, the boundary wins:
convert with `Option.getOrUndefined` or `Option.getOrNull` at the
facade, and decode back to `Option` on the way in with
`Schema.OptionFromNullOr` or `Schema.OptionFromUndefinedOr`
(decision-core-architecture, "The facade").

## Match on tags

Read a tagged union with `Match`, which checks that every case is
handled:

```ts
import { Match } from "effect"

const describe = (event: TaskEvent) =>
  Match.value(event).pipe(
    Match.tag("Started", describeStarted),
    Match.tag("Finished", describeFinished),
    Match.exhaustive,
  )
```

For errors in the error channel, `Effect.catchTag` recovers from one tag
or an array of tags, `Effect.catchTags` takes a record of handlers, and
`Effect.tapErrorTag` runs a side effect without consuming the error.
`Effect.catch` catches every typed failure; reach for it last.

## Combine with Combiner and Reducer

When two values of one shape merge, or many fold into one, use the
algebraic instances in `effect` instead of `??` chains and reduce loops.
`Combiner` combines two values; `Reducer` adds an initial value and
`combineAll`.

```ts
import { Combiner, Number, Option, Struct } from "effect"

interface Totals {
  readonly runs: number
  readonly failures: number
  readonly lastError: Option.Option<string>
}

const TotalsReducer = Struct.makeReducer<Totals>({
  runs: Number.ReducerSum,
  failures: Number.ReducerSum,
  lastError: Option.makeReducer(Combiner.last<string>()),
})

const total = TotalsReducer.combineAll(perRunTotals)
```

`Number` here is Effect's module, imported from `effect`, and it shadows
the global `Number` in that file.

`Option.makeReducer` skips `None` and combines the `Some` values.
`Option.makeReducerFailFast` returns `None` as soon as one input is
`None`. Pick the one whose rule you mean, and say which in the name.

## Write effectful functions with Effect.fn

A storage read, then a decode, then an action, is one `Effect.gen` with
one `yield*` per step. Do not nest `.pipe(Effect.flatMap(...))` or
`.then()` chains, and do not re-check a hand-written cancellation flag
at each level:

```ts
import { Data, Effect, Schema } from "effect"

class NoStoredDraft extends Data.TaggedError("NoStoredDraft") {}

const DraftFromJson = Schema.fromJsonString(Draft)

const restoreDraft = Effect.gen(function* () {
  const stored = yield* readStoredDraft
  const text = yield* Effect.fromOption(stored, () => new NoStoredDraft())
  const draft = yield* Schema.decodeUnknownEffect(DraftFromJson)(text)
  yield* showDraft(draft)
})
```

To cancel, interrupt the fiber that `runtime.runFork` returns with
`Fiber.interrupt`.

For a reusable function that returns an Effect, use `Effect.fn("name")`,
which adds a tracing span and a better stack trace, or
`Effect.fnUntraced` on hot paths and in library code. Do not write a
function whose only body is `return Effect.gen(...)`. Add behavior such
as recovery or log annotations as extra arguments to `Effect.fn`, not
with `.pipe` on its result. Declare the return type with
`Effect.fn.Return<A, E, R>` when the inferred one is not what you mean.

## Argument shape: dual, and no uniform currying

Effect's own combinators are built with `dual` from `effect/Function`.
Each one takes its data first when called directly,
`Option.map(option, f)`, and last when used in a pipe, `pipe(option,
Option.map(f))`. The two call styles are one convention. Your
own combinators should follow it: write the implementation data-first
and wrap it with `dual(arity, implementation)`. Pass a predicate instead
of the arity when optional arguments make the arity ambiguous.

Inside a `pipe` or `.pipe(...)`, use the data-last form. Begin a pipe
with its input: `pipe(input, parse, validate)`, not
`pipe(parse(input), validate)`.

Making every function curried and unary was considered and rejected.
Effect v4 is built on `dual`, so currying your own code uniformly makes
it stop resembling the library it is written in. TypeScript's inference
also degrades through deeply nested return types, and callbacks lose
their contextual typing. Each argument costs a closure allocation, which
matters on paths that run per request, and stack traces get worse.
Public functions that are not combinators follow
public-api-argument-shape instead.

## Services, Layers and one runtime

A dependency the program reaches outside itself for (storage, a clock,
a process runner, an HTTP client, a model API) is a `Context.Service`.
Its implementation is a `Layer`. The core asks for the service in its
requirements, `R`, and never constructs it.

```ts
import { Context, Effect, FileSystem, Layer, Option } from "effect"

export class TaskStore extends Context.Service<TaskStore, {
  readonly find: (taskId: string) => Option.Option<Task>
  readonly save: (task: Task) => Effect.Effect<void, StoreError>
}>()("supervisor/TaskStore") {
  static readonly layer = Layer.effect(
    TaskStore,
    Effect.gen(function* () {
      const fs = yield* FileSystem.FileSystem
      // ...build find and save over fs...
      return TaskStore.of({ find, save })
    }),
  )
}
```

The string key names the package and the module path, so two services
never share one. Attach the live Layer as a static on the class, build it
with `Layer.effect` (it runs in the Layer's scope, so
`Effect.acquireRelease` inside it is released when the runtime shuts
down), and return the implementation with `TaskStore.of`. Use
`Context.Reference` for a service that has a sensible default, such as a
setting. Compose Layers with `Layer.provide`, which hides the
dependency, and `Layer.provideMerge`, which also exposes it. Put the
transport underneath: the services built over it require the transport,
and the code that calls those services requires only the services.

Build the application's Layers once, at the composition root, into one
`ManagedRuntime.make(AppLayer)`, and run every effect through it with
`runtime.runPromise` or `runtime.runFork`. Keep `R` in the type of
whatever helper runs effects for the rest of the program, so an effect
that needs a service the runtime does not build fails to compile at the
call site. `Effect.runPromise` takes only effects with `R = never`, so
in application code outside the entrypoint a call to it either reaches
no services or provides them ad hoc, and both are wrong. Tests are the
exception: there, providing a substitute Layer is the point. For a
process whose whole life is one program, `Layer.launch` or the
platform's `runMain` is the entrypoint instead. Dispose the runtime with
`runtime.dispose()` on shutdown so finalizers run.

In a decision-core application, these services, their Layers and the
runtime belong to the Runtime layer and the Program wiring. Domain and
Features stay pure and do not import them.

## Tests substitute a Layer, never a global

A test replaces a dependency by providing a different Layer for the
service it depends on. It does not reach past the code to replace
`globalThis.fetch` or `Date.now`. Needing to replace a global
means a dependency was never injected; fix the injection.

```ts
import { Effect, Layer, Option } from "effect"

const StoreWithOneTask = Layer.mock(TaskStore, {
  find: (taskId) => taskId === "t1" ? Option.some(sampleTask) : Option.none(),
})

const title = await Effect.runPromise(
  taskTitle("t1").pipe(Effect.provide(StoreWithOneTask)),
)
```

`Layer.mock` takes a partial implementation. A member left out that
returns an Effect fails with an unimplemented defect when called, so a
test that reaches a dependency it did not set up fails instead of
passing by accident. Wire the mock Layers into the test composition
root as well, so a unit test that reaches a real transport fails loudly.
When a test double needs state, keep it in a `Ref` behind its own
service, provided with `Layer.provideMerge` so the test can read it too.
`@effect/vitest` provides `it.effect` for Effect-returning tests and
`layer(...)` for sharing a Layer across a `describe`; pin it at the
version that matches `effect`.

`Clock` and `Random` are `Context.Reference` services with live
defaults, so a test can replace them. Read time through `Clock` or
`DateTime.now`, never `Date.now()`.

Put each test at the seam it checks. A test of the wire contract (which
call, which payload) runs against a stub transport. A test of how a use
case combines several calls runs against stub services. A test of a
derivation is a plain test of a pure function, with no Layer at all.

## Enforce the rules with tests

A rule written only in prose decays. Within months the forbidden pattern
is back in a file nobody reviewed with it in mind. For each rule above
that a machine can check, add a test that fails the build:

- Bans (sync decoders, `getOrThrow`, `Effect.promise`, `instanceof` on
  errors, reads of `_tag`, `JSON.parse`): an ESLint rule or a test that
  walks the TypeScript syntax tree, not a text search. A text search misses
  aliased imports and matches inside comments.
- Global doubles: fail on `vi.stubGlobal`, `vi.spyOn(globalThis,
  ...)` and assignment to a global anywhere except the one adapter's own
  test. Check for the act in all three spellings.
- `R` is carried: the helper that runs effects should accept an
  effect requiring a service the runtime builds and reject one requiring
  a service it does not. Assert both with type-level tests, and keep two
  controls beside them, a helper with `R` forced to `never` and one with
  `R` unbounded, so a check that accepts everything cannot pass.
- A mocked module that does not exist: fail on a `vi.mock` whose
  specifier resolves to nothing, which substitutes nothing and stays
  green.

Every exemption from such a gate sits in an allowlist next to the gate,
with the argument for it. When the allowlist empties, keep the gate as a
flat ban. gate-integrity covers proving that each of these checks can
fail.
