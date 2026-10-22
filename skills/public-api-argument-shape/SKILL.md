---
name: public-api-argument-shape
description: Shapes the parameters of public functions, methods, interfaces and injected callbacks so that a wrong call fails to compile instead of running. No two parameters may accept each other's values, so a transposed call becomes a type error; booleans and optionals are never positional; context is never read from untyped ambient state, with the tenant and the acting user as explicit parameters in a fixed position and capabilities such as the clock as parameters or a typed environment; and past a stated parameter count the tail goes into a record. It also gives a gate that asks the type checker about assignability, proves itself with planted and near-miss probes, and states what it misses. Use it whenever you add or change an exported signature, repository or service interface, use case, SDK or library API, or callback type, when a bug turns out to be arguments passed in the wrong order, and when you write or review a lint or test that checks signatures. Language-neutral, illustrated in TypeScript.
license: MIT
---

# Argument shape for public APIs

A public signature is called from places its author never sees. Every
call site is a chance to pass the right values in the wrong slots, and
the compiler is the only reviewer that reads all of them. So shape the
signature until a wrong call does not compile. A doc comment asking
callers to take care protects none of them.

This is "make illegal states unrepresentable" applied to argument
position. Three shapes let a wrong call compile:

- **Transposable arguments.** Two parameters accept each other's values,
  so `assign(reviewer, author)` compiles as readily as
  `assign(author, reviewer)`.
- **Positional booleans and optionals.** `archive(id, true, false)` says
  nothing at the call site, and an omitted optional leaves no trace
  there at all.
- **Ambient context.** The tenant, the actor or the clock is read from
  somewhere the call site cannot see, so a call made without it still
  compiles.

The examples are TypeScript, as illustration. The rules hold in any
language with a static type checker. In a dynamic language the same
shapes are worth adopting, but only tests can enforce them.

## Scope

The rules apply to anything callable from outside its module: exported
functions, interface and port definitions, use cases, repository and
gateway methods, SDK surfaces, and the types of injected callbacks. A
callback type is a signature too. If an interface method takes
`(owner, member)` and a helper one layer up accepts it as an injected
function with the same parameter list, fixing only the interface leaves
the hazard at the injection site.

Two things are exempt:

- **Internal single-use closures.** They have one caller, in plain view.
- **Established library idioms,** such as the data-first and data-last
  forms of a pipeable combinator. That is one idiom with two calling
  conventions, and replacing it makes your code read unlike the library
  it is built on.

## Rule 1: no two parameters may be interchangeable

No two parameters in a public signature may be mutually assignable. If
the type checker would accept a call with two arguments swapped, change
the signature until it would not. A subtype beside its supertype counts
too: a caller holding two values of the narrower type can swap them
without an error. So the working test is whether either parameter's type
is assignable to the other's.

There are two fixes. Choose by what the values are.

| The two values are | Fix | Example |
|---|---|---|
| Different kinds of thing that share a representation | Distinct branded types or newtypes | `OrderId` and `ShelfId`, both strings underneath |
| The same kind of thing in different roles | A record with named fields | an author and a reviewer, both users |
| Two ends of one thing | A record, often a named value type | `{ startsAt, endsAt }` as a `TimeWindow` |

Branding the roles of one kind of thing is usually the wrong fix. An
author and a reviewer are both users, the same user can hold both roles,
and a brand per role needs a cast wherever a user becomes an author.
Each cast is a place where the checker stops looking. A record makes the
role a field name, which the caller writes out at every call:

```ts
// Before: assign(workspace, reviewerId, authorId) compiles.
assign(workspace: WorkspaceId, authorId: UserId, reviewerId: UserId): Promise<Assignment>

// After: the transposed call cannot be written without naming the wrong field.
assign(workspace: WorkspaceId, roles: { readonly author: UserId; readonly reviewer: UserId }): Promise<Assignment>
```

Branded IDs close most of the gap by themselves. This rule covers the
cases where both sides are honestly the same type. For the PureScript
form of one newtype per meaning, with a private constructor, see
purescript-rows-and-newtypes. For keeping these types at the boundary of
a pure core, see decision-core-architecture.

The parameter count does not measure the hazard. A three-parameter
signature with three distinct types is safe, and a three-parameter
signature with two `UserId` is not. That is why this rule is separate
from the count limit in Rule 4.

## Rule 2: no positional booleans, no positional optionals

- **A boolean goes in a record field,** or becomes a two-case type:
  `{ includeArchived: true }`, or `Visibility = "all" | "active"`.
  `list(id, true)` can only be read by opening the definition.
- **An optional parameter is not positional.** Put it in the record. Where
  absence means something ("no exclusion", "no deadline"), make the
  field an explicit `Option` or `Maybe` rather than `?` or a nullable, so
  the caller writes `none` and the reader sees the choice.
- **No optional record of optional fields.** `opts?: { flag?: boolean }`
  gives three ways to say the same thing. Make the record required and
  give its fields explicit defaults or explicit `Option`s.

## Rule 3: context is explicit, and it comes first

Context means the values that scope an operation without being its
subject: the tenant or workspace, the acting user, the clock, a request
or correlation ID. Each one is explicit, never read from untyped ambient
state. Identity is a parameter, in the same position in every signature,
and that position is first; a capability may instead be a typed
environment, as below.

- **Explicit,** because a missing context then fails to compile at every
  call site. Read from a request-local global, a thread-local or
  async-local storage, it is invisible to the type checker: a background
  job, a retry or a test runs without it, or with whatever an earlier
  request left behind, and still compiles. For the tenant case and what
  goes wrong when it is ambient, see multi-tenant-security-review.
- **Identity is a parameter; capabilities may be a typed environment.**
  A required environment that the types track, such as Effect's `R`
  channel or a Reader, is not ambient: running a program before it is
  provided is a compile error. Even so, this collection passes
  request-scoped identity (the tenant, the acting user) as explicit
  parameters. That is a security policy, not a type-safety argument: it
  keeps the scope of every operation visible at the call site and in
  review. Capabilities, such as the clock, a repository or a logger, may
  come through the project's chosen typed Reader or Effect environment
  instead; purescript-rows-and-newtypes teaches that design.
- **First,** because a fixed position stops drift, where some signatures
  lead with the tenant and others trail it. When the rule lands, move
  every signature that trails, including the ones whose types make them
  safe. A rule the codebase visibly breaks on the day it is written tells
  the next reader that the rules here are decorative.
- **The clock is context.** A function that reads the current time
  takes a clock or an instant as a parameter, or a clock capability from
  a typed environment, so tests can pin it.
  decision-core-architecture covers why the core never reads time
  itself.

A project may bundle its context into one record, such as
`ctx: { tenant, actor, clock }`, or pass the parts as leading positional
parameters in a documented order. Pick one and use it everywhere. If
context parts share a type (an actor and a subject that are both
`UserId`), Rule 1 applies to them like any other pair, and the bundled
record is the natural fix.

## Rule 4: past a count, the tail is a record

This is a readability rule, and a project choice. State it in AGENTS.md
or the project's equivalent instruction file.

**Default:** context does not count. After it, a public signature takes
at most two positional parameters: the subject (the entity acted on) and
one input record describing the operation. A third positional parameter
is the signal to fold the tail into the record. So the widest shape is
`(context, subject, input)`.

A hard cap with no exceptions (every function unary, or at most two
positional arguments counting context) was considered and rejected. It
churns signatures that are already safe, and it still admits a
two-parameter function with two `UserId`. Rule 1 catches the bugs; this
rule only keeps call sites readable.

## Enforcing the rules with a gate

A rule with no check behind it drifts. A rule checked in one place
drifts everywhere else: in the second package of a monorepo, in the
front end, in the new directory the gate's glob does not match. Enforce
Rules 1 and 2 with a gate that runs in the build, in every package the
rules cover. Rule 4 is a judgement about reading and is
better left to review. Follow gate-integrity for the general method.
What follows is specific to this gate.

### State which kind of gate it is

There are two kinds, and they catch different things.

| Kind | Asks | Catches | Misses |
|---|---|---|---|
| Written-type comparison | Are two parameters' type annotations the same text? | two parameters both written `UserId` | an alias of the same underlying type (`type Note = string` beside `string`); two structurally identical types with different names; a subtype beside its supertype; a union that contains another parameter's type |
| Assignability analysis | Does the type checker accept one parameter's type where the other's is expected? | everything in the row above | none of those cases, provided it asks in both directions |

A written-type gate reads source text. That makes it easy to write and
blind to aliases, structure and subtyping. An assignability gate needs
the compiler's API. In TypeScript that is `checker.isTypeAssignableTo`,
declared public from TypeScript 5.4 (checked against the shipped
`typescript.d.ts` in 5.3.3, where it is absent, and 5.4.2 and 5.9.3,
where it is present). Before 5.4 it existed only as an undeclared
internal.

- **Write a new gate as an assignability gate.**
- **Count a pair as colliding when either type is assignable to the
  other.** Strict mutual assignability misses a subtype: with
  `fit(outer: Shape, inner: Square)`, a caller holding two squares can
  swap them silently. The cost is that a branded ID beside its own base
  type (`OrderId` beside `string`) is flagged too. Brand the other
  parameter or use a record.
- **A written-type gate is acceptable only if it states its blind spot**
  in a comment beside the rule and in the instruction file, naming the
  cases it misses. Otherwise readers assume it covers them.

### What the gate must prove about itself

A gate that asserts "no findings" passes just as well when its detector
is broken. Give it three self-checks in the same test file:

1. **A planted-violation probe per form.** Run the same analysis over a
   small inline source with exactly one violation and assert exactly one
   finding. Plant one in every syntax form the public surface can take:
   in TypeScript, a function declaration, an exported arrow, a method, a
   call signature, a constructor and the rest. Make each planted case one
   the weaker kind would miss, such as an alias beside its base type, so
   the probe also proves the kind.
2. **A near-miss probe.** Run it over a source that is close but legal,
   such as two distinct brands of the same base type, or a record whose
   two fields share a type, or an internal closure inside a public
   function, and assert no findings. This catches a detector that flags
   everything, or one that reaches past the public surface.
3. **A minimum number of signatures read.** Count signatures, not files,
   and assert a floor near the real number. A file count stays green
   when the walker stops descending into interfaces. Raise the floor as
   the API grows. A floor met by one form can hide a form never read,
   which is why probe 1 covers each form.

Find the surface from the exports, through the type checker, rather than
by matching syntax node kinds; a syntax walker misses whichever forms it
did not list. Reach no further than the public surface, so internal
closures stay exempt. Fail, never pass, when the source does not parse
or a type does not resolve.

Also check that the test runner collects the gate at all. A new test
file that matches no runner's include pattern is run by nobody, and so
it never fails. When the gate lands, fix every existing violation it
finds, not only the ones that prompted it.

### Illustration

The core of an assignability gate, in TypeScript (5.4 or later). A
complete sketch with its probes is in
[references/assignability-gate.md](references/assignability-gate.md);
read it when you are writing the gate.

```ts
const params = signature.getParameters().map((p) => ({ name: p.getName(), type: checker.getTypeOfSymbol(p) }));
params.forEach((a, i) =>
  params.slice(i + 1).forEach((b) => {
    if (checker.isTypeAssignableTo(a.type, b.type) || checker.isTypeAssignableTo(b.type, a.type)) {
      findings.push(`${a.name} and ${b.name} are interchangeable`);
    }
  }),
);
```

## Worked example: a transposed pair of IDs

The example is a composite, with invented names. A review tool has a
repository method that assigns a reviewer to a document:

```ts
assign(workspace: WorkspaceId, authorId: UserId, reviewerId: UserId): Promise<void>
```

Every ID in the codebase is branded, and the team took that as
protection. One call site passed `(workspace, reviewerId, authorId)`. It
compiled, its tests passed (they used the same user for both roles), and
in production the author was recorded as the reviewer. Since only the
reviewer may approve, authors could approve their own documents. The
fault was in authorization, and nothing failed loudly.

The fix and what it found:

- **The signature took a record,** `{ author, reviewer }`, and the
  compiler then pointed at every call site. Per-role brands were
  rejected for the reason in Rule 1: a user can be both.
- **A scan for the class found more than the reported bug:** a time
  window passed as two positional dates, so that swapping them inverted
  an overlap check; a rate limit taking `(limit: number, windowMs:
  number)`; and an injected `canReview(workspace, authorId, reviewerId)`
  callback one layer above the repository. When you fix one instance,
  scan for the whole class.
- **The first gate compared written types.** It caught the
  `UserId`-beside-`UserId` case and passed when someone added
  `type Approver = UserId` beside a `UserId`. Its only self-check was a
  file count, so a broken detector would also have passed. The
  replacement asks the type checker and carries the three probes above.

## Review checklist

1. Does any public signature, including callback types, have two
   parameters where either type is assignable to the other? If so, is the
   fix a record (same kind, different roles) or distinct brands (different
   kinds)?
2. Is any boolean or optional positional? Are meaningful absences
   explicit `Option` or `Maybe` fields, with no optional record of
   optional fields?
3. Is every identity value (tenant, actor) an explicit parameter in the
   project's fixed first position, with none read from untyped ambient
   state, and is every capability either a parameter or in a typed
   environment?
4. Does every signature stay within the project's stated count, by
   default `(context, subject, input)`?
5. Is there a gate for Rules 1 and 2 in every package the rules cover, and
   does the runner actually collect it?
6. Does the gate state its kind? If it compares written types, does it
   name what it misses beside the rule?
7. Does the gate find the surface from the exports, plant a violation in
   each syntax form asserting exactly one finding each, carry a near-miss
   probe asserting none, fail on parse and type errors, and put a floor
   on signatures read?
8. When the rule or gate landed, were all existing violations fixed,
   including the safe ones that break the fixed context position?
