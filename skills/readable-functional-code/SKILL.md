---
name: readable-functional-code
description: Rules for writing functional code that reads top-down and can be tested a piece at a time, in PureScript or Haskell, with a reference for TypeScript written with Effect. Covers where over let-in, named transformations and named lambdas, branches that call named functions, maybe and either over two-arm matches, named numbers, per-declaration complexity budgets, file length and line width, module order, a denylist of abbreviations, tail recursion, range bounds, and how docstrings and comments are written. Use it whenever writing, refactoring or reviewing PureScript or Haskell, when a function grows past one screen or a branch holds a formula, when briefing an agent to write functional code, when building a lint for any of these rules, and, through its reference file, whenever writing or reviewing TypeScript that uses Effect. These are a house style. In a project with its own conventions, apply them only where the project has adopted them or the user asks.
license: MIT
---

# Readable functional code

Functional code invites density: a point-free chain, a lambda inside a
`map` inside a `case`, a constant nobody named. Each saves a line at the
reader's expense. These rules give up that density for code that reads
from the top down and whose every decision can be tested on its own.

The examples are PureScript, as of purs 0.15. The rules carry over to
Haskell, with the differences noted where evaluation order matters:
PureScript evaluates eagerly and Haskell lazily. For TypeScript written
with Effect, read [effect-ts-idioms.md](effect-ts-idioms.md).

These rules are a house style. Where a project has adopted them, or the
user asks for them, they govern. In a project with other conventions,
follow its conventions and raise any rule here as a proposal; don't
restyle code the task didn't touch.

Related skills: decision-core-architecture says where pure functions go
in an application, and purescript-rows-and-newtypes covers how their
types record requirements and errors.

## Lint, or review

Rules 2 and 10, marked "review", and the writing conventions need a
reviewer. A lint can check the rest: a line count for rule 7, and for
the others a lint that parses each module and decides on its syntax
tree. Each rule states exactly what counts as a finding, so a lint and a
reviewer draw the same line.

Build such a lint on a parser, not on text matching. A regular
expression cannot tell code from a comment or a string, and it misses a
construct split across lines. Test the lint with a suite of small
modules, each marked to pass or to fail with a given message, because a
checker can be wrong like any other code.

A new rule lands together with the refactor that satisfies it, with no
allowlist. When a rule is wrong for some case, change the lint; never
switch it off at the line. gate-integrity covers that discipline.

## 1. `where`, not `let … in`

A `where` puts the expression first and its parts after it, so the
reader sees the point before the detail.

```purescript
totalPrice order = subtotal + shipping
  where
  subtotal = sum (lineTotal <$> order.lines)
  shipping = shippingFor order.destination
```

A `let` statement inside `do` or `ado` is fine, because its bindings can
use a value bound by `←` above them, which a `where` cannot see. A
`let … in` expression is a finding everywhere else: at the top level, in
a `where`, in an instance, in a case arm, and inside a `do` block too.

## 2. Name what you pass, in `where` (review)

A lambda or inline transformation handed to `map`, `<$>`, `traverse`,
`maybe` or `either` gets a descriptive name in `where`, however short
the lambda.

```purescript
-- not this
tables = map (\rates → buildTable rates region) (validRates quotes)

-- this
tables = tableFor <$> validRates quotes
  where
  tableFor rates = buildTable rates region
```

The name says what the function makes, and the body reads as one line.
No lint checks this, and agents often miss it, so put it in every brief.

## 3. A branch calls a named function

A case arm, a guard or an `if` branch may hold:

- a name, a literal (`[]` and `{}` count), or a field of a name;
- a call, a constructor, a record, an array, a record update or an
  operator on those, with an operand that may be negated;
- at most one call on names nested inside one of those.

Anything else is logic and moves into a named function. That includes
a lambda, an `if` inside a branch, and an operator applied to a call. A
`do` block in a branch is allowed only in a test module.

```purescript
-- the arm holds a formula
priceFor tier base = case tier of
  Wholesale → base * (1.0 - wholesaleDiscount) + handlingFee
  Retail → base

-- each arm calls a name, and the formula has its own test
priceFor tier base = case tier of
  Wholesale → wholesalePrice base
  Retail → base
```

A formula or decision that a user of the software would recognize is
exported and tested on its own. Plumbing, such as one step of a fold or
the assembly of a record, stays a local function or a `where` binding.

Two PureScript details bite here; purescript-gotchas has more.

- **A `where` value is computed on every call.** PureScript is eager, so
  logic moved out of a branch into a `where` value runs even on the path
  that never uses it. If it is costly, make it a function of what it
  reports on. In Haskell the value is lazy and this cost does not arise.
- **A `where` after guards scopes over the last guard alone** (as of
  purs 0.15; Haskell's covers every guard). A value several guards share
  must be bound by an inner function instead.

## 4. Use the eliminator, not a two-arm match

A `case` on `Just` and `Nothing`, or on `Left` and `Right`, whose arms
only hand the value to a function or return a fallback, is `maybe` or
`either`. Where the `Just` arm returns the value itself, it is
`fromMaybe`. The eliminator states the whole decision in one line: which
function each outcome goes to.

```purescript
either reportFailure saveReceipt (chargeCard request)
```

An arm hands the value on only when its body is the bound name, or a
call whose last argument is the bound name and whose function and other
arguments are plain values that do not mention it. A fallback arm
(`Nothing`, or `_` beside `Just`) qualifies only when it is a plain
value or a constructor on plain values, such as `Left reason`. An arm
that does work of its own keeps the `case`. So do matches on two values
at once, matches with three arms, a guard or a `where`, and nested
patterns such as `Just (Tuple key value)`.

**A computed fallback stays a `case`.** PureScript evaluates every
argument before the call, so `fromMaybe (missingKey key) found` computes
the fallback on every call, and crashes on every call if the fallback
crashes. Keep the `case`, or use the lazy variants `maybe'` and
`fromMaybe'`, which take the fallback as a function and call it only on
`Nothing`. Haskell's arguments are lazy, so there the plain eliminator
is safe.

Treat the rule as a default. Where a match genuinely reads better, or
both arms do real work, the shapes above already leave it alone.

## 5. Name every number except 0, 1 and 2

A number literal belongs in a named top-level constant: a value with no
arguments, or a field of a settings record, where the field names it.
Anywhere else it is a finding, including in a pattern, an instance, a
`where` binding or a `let` in `do`; negating it does not exempt it, so
`-0.5` needs a name. 0, 1 and 2 need none, so a midpoint, a count and a
halving stay as they are.

```purescript
secondsPerHour = 3600.0

hoursFor seconds = seconds / secondsPerHour
```

A published coefficient is named with its source, in the constant's
docstring. Unit conversions live in one module, so each is written once.
Test modules are exempt, because a test's inputs are data.

## 6. Budgets per declaration

Each top-level declaration stays within these budgets.

| Measure | Budget |
|---|---|
| Depth of nested decisions (`case`, `if`, guards, `where`) | 3 |
| Branches | 8 |
| Lines | 30 |
| `where` bindings | 8 |

Each figure was set at the knee of a measured distribution: count every
declaration's depth, branches, lines and bindings across the tree, and
put the budget where the curve bends, so it catches the tail and leaves
the bulk alone. For another codebase, measure that tree before choosing,
rather than adopting these numbers unexamined.

A branch counts only when its body does something. Arms whose bodies
are bare names or literals form a lookup table, and splitting one would
make it harder to read.

Without the bindings budget, rule 3 would be easy to dodge: it pushes
logic out of branches into `where` helpers, and a long `where` can hide
a whole program inside one declaration. Past eight bindings the helpers
become top-level functions, with their own tests.

When a change pushes a declaration over budget, even a rename that
lengthens its lines, split the declaration; the budget stays where it
is. Test modules are exempt.

## 7. File length and line width

These are two separate rules with separate checks.

- **File length:** aim for about 100 physical lines per module, with a
  hard limit of 250. Comments and blank lines count: both are part of
  what a reader navigates. Tests and tooling count too.
- **Line width:** 80 columns. Count characters, not bytes, because `∷`
  is one column and three bytes. A formatter's width setting is the
  width it lays code out to, not a limit it enforces: it may leave a
  long comment, string or signature alone and still pass. Split a long
  string into pieces joined with `<>`, so its value does not change.
  Rewrap a long comment without rewording it.

## 8. Modules read top-down

A module runs in this order: types with their instances, then constants,
then exported functions, then private ones. It may move forward through
those sections as often as it likes, and never back. Do not order the
body by the export list, which is often alphabetical.

Tell a constant from a function by its signature, not by its arguments.
A point-free function takes no arguments and is still a function. A
value with no arguments is a constant even when its type is an action.

Test modules are exempt, since they read as a list of cases with each
fixture beside the test that uses it.

## 9. Names say the word they stand for

Spell out the word a name shortens. The test is whether the name would
be acceptable in a newspaper article.

Enforce this with a denylist, not a minimum length. The same letter is a
placeholder in one function and a terse concept in the next: `x` means
any value in `square x = x * x` and a position elsewhere. No length
threshold separates those, so deciding which short names stand for a
concept takes a reader. The list holds what a lint can catch, for
example:

`acc`, `sofar`, `lo`, `hi`, `expr`, `decl`, `env`, `dir`, `pts`

These stay allowed: type variables; `_`; a symmetric pair such as
`a` and `b` in `combine a b`; a name meaning any value at all; the
established notation of the domain or a standard (`t` for a parameter
along a segment, `x` and `y` on a screen); and acronyms such as `json`.

The lint reports what binds a name, never what mentions one. A record
pun on a library's field both reads the label and binds a name of
yours, so it is reported; `{ expr: expression }` clears it and leaves
the library's label alone. Row labels count. Test modules are not
exempt.

The report lists bindings; each rename must also reach every use, which
the compiler finds. When warnings are errors, the compiler may reject
the obvious spelling for shadowing an import, and a longer name is
needed.

## 10. Recursion that grows with the input is a tail call (review)

A loop whose length grows with the input (characters, tokens, records)
is a self tail call, which purs 0.15 compiles to a loop, or `tailRecM`
from `Control.Monad.Rec.Class` when it runs in a monad. Ordinary
recursion of that depth overflows the stack on large input. Accumulate
without copying: `Array.snoc`, `uncons` and `drop` copy the array on
every item, so build a `List` and reverse it once, or index into the
array.

In Haskell, tail position alone is not enough: a lazy accumulator builds
a chain of unevaluated thunks, so make it strict with `foldl'` or a bang
pattern. A test with very large input checks only the paths it drives,
so a reviewer checks the rest.

## 11. No computed bounds on a range

`Array.range` (and its operator `..`) is a finding unless both bounds
are written out at the call and each is a literal, a named constant, or
arithmetic on those. A range that is partly applied or passed unapplied
is reported too, since its bounds are not visible where it is. Test
modules are not exempt, and no module may re-export `range`.

There are two reasons. A computed bound is an index loop in disguise: it
lists positions and looks each one up, which `mapWithIndex`, a fold,
`zip items (drop 1 items)` or chunking does directly. And in PureScript
`range` counts down when the upper bound is below the lower, so for an
empty array `range 0 (length items - 1)` is `[0, -1]`, not `[]`. A later
`index` that returns `Nothing` for the bogus positions then makes the
code correct by accident.

For a genuine count of positions, write small helpers that return an
empty array where `range` would count down. Haskell's `[0 .. n - 1]` is
empty when `n` is 0, so the trap is PureScript's, but the first reason
holds in both.

## Writing docstrings and comments

- **Write docstrings plainly.** Use short declarative sentences and
  exact terms, and state the reason once. Drop metaphor and drama:
  flourish costs clarity, and it can hide a false claim, such as a
  comment saying a range check rejects NaN when it does not.
- **Comments say why.** The code already says what it does.
- **Keep necessary technical notation, and use words where words
  serve.** A formula the code implements, a standard's own symbols and a
  domain's established terms stay. Elsewhere write "the weights add up
  to one", not sigma notation. When a technical term is worth using,
  define it once in a sentence, then go on in plain language.

humanized-prose-review covers longer prose.

## Reviewing code against this skill

1. Is there a `let … in` expression anywhere? (A `let` statement in
   `do` or `ado` is fine.)
2. Is any lambda or inline transformation passed without a name in
   `where`?
3. Does any branch hold logic beyond the allowed shapes? Is each
   formula a user would recognize exported and tested?
4. Is any two-arm `Maybe` or `Either` match only handing values on?
   Does any eliminator compute its fallback eagerly?
5. Is any number other than 0, 1 or 2 unnamed outside a test?
6. Is any declaration over depth 3, 8 branches, 30 lines or 8 `where`
   bindings?
7. Is any module over 250 lines, or any line over 80 columns?
8. Does any module move back through types, constants, exported and
   private functions?
9. Does any binding use a denylisted or unexplained abbreviation?
10. Does any recursion that grows with the input lack a tail call, or
    copy the array per item?
11. Does any `range` have a computed bound?
12. Do the docstrings and comments say why, in plain words?
