---
name: purescript-gotchas
description: "PureScript language and tooling facts that take seconds to look up and a compile-and-read cycle to discover: what a module can re-export, how a facade hides constructors, CycleInDeclaration from point-free definitions, orphan instances, newtype deriving through a wrapper, Generic on hidden constructors, Prelude name clashes, which Prelude types lack Semigroup, non-associative operators in Test.QuickCheck, which BigInt package pulls in an npm dependency, and the Gen variants in quickcheck-laws. Use it whenever you write or review PureScript, and especially before hiding a constructor, adding or deriving an instance, designing a module boundary, writing a law test or choosing a numeric package."
license: MIT
---

# PureScript facts worth knowing before the compiler tells you

Each of these facts can be checked in seconds, yet none sits where you
would first look, and each one otherwise costs a compile and a careful
read of the error. The rules they support are in
purescript-rows-and-newtypes. This skill collects the language and
library facts behind them.

## Versions

Every claim below was checked against these versions:

| Tool or package | Version |
|---|---|
| purs | 0.15.16 (the package set allows 0.15.15 up to 0.16.0) |
| spago | 1.0.4 |
| purs-tidy | 0.11.1 |
| registry package set | 81.0.0 |
| prelude | 6.0.2 |
| quickcheck | 8.0.1 |
| quickcheck-laws | 7.0.0 |
| js-bigints | 2.2.1 |
| bigints | 7.0.1 |

Compiler behavior and error wording can change between releases. After an
upgrade, re-check any claim you rely on; most take one small module to
test.

## Modules and exports

**An individually imported name cannot be re-exported** (as of purs
0.15.x). This fails with "Cannot export unknown type Thing":

```purescript
module Facade (Thing) where
import Other (Thing)
```

An export list can name only the module's own declarations, or whole
modules with `module X`.

**A whole-module re-export carries exactly what the facade imported,**
and no more:

```purescript
module Money (module Money.Cents) where
import Money.Cents (Cents, fromInt)   -- no (..)
```

Callers of `Money` get the type `Cents` and the function `fromInt`, but
not the data constructor. A caller that writes `import Money (Cents(..))`
and then uses `Cents 1` gets "Unknown data constructor Cents". That is how
a narrow public facade can sit over permissive submodules, and it is the
mechanism behind purescript-rows-and-newtypes' rule to hide the
constructor.

**There is no submodule privacy.** A module named `Internal` is public to
the whole program, and PureScript has nothing like Rust's `pub(crate)`.
If a rule says only one subtree may import a module, a check has to
enforce it. `purs graph` prints the import graph as JSON, which a short
script can test against an allowlist.

**Export forms:** `T` exports the type alone, `T(..)` the type and every
constructor, and `T(A, B)` the type and the named constructors.

**A point-free definition inside a recursive binding group is a
`CycleInDeclaration`** (as of purs 0.15.x). Here `go` is point-free, and
`one` calls back to `go`:

```purescript
names :: Array Expr -> Array String
names = go
  where
  go = concatMap one
  one (Var s) = [ s ]
  one (Block es) = go es
```

The error is:

```
The value of one is undefined here, so this reference is not allowed.
```

A point-free right-hand side is a value, evaluated when the group is
initialized, and a value in a recursive group can refer to a member that
does not exist yet. The same definition compiles until the group becomes
recursive, which is exactly when it stops looking suspicious. The fix is
to give it its argument, `go es = concatMap one es`, so that it is a
function rather than a value.

The error points at the reference it could not allow, which need not be
the definition to change: above, it names `one`, while the culprit is
`go`. Check every member of the group for a point-free definition before
you edit the one the error names.

## Instances

**No orphan instances** (as of purs 0.15.x). An instance must be declared
in the module of the class or the module of the type. Declaring
`instance Eq Price` anywhere else fails with `OrphanInstance`, and the
error names both legal homes and suggests a newtype wrapper.

**`derive newtype instance` needs the instance on the inner type.** Given
`newtype Price = Price Cents`, the line `derive newtype instance Eq Price`
fails with "No type class instance was found for Eq Cents" if `Cents` has
no `Eq`. If the inner type lacks the instance on purpose, write the outer
instance by hand and unwrap.

**`Generic` on a hidden constructor draws a `HiddenConstructors`
warning** (as of purs 0.15.16). It is a warning, not an error, so the
derive compiles. The warning gives the reason: `to` and `from` match and
build values of the type, so a type that exports `Percent` without `(..)`
but derives `Generic` has in effect made its constructor public.
Do not derive `Generic` for such a type, and write its `Show` by hand
instead of deriving it through `genericShow`. A build that treats
warnings as errors will reject it outright. This is why
purescript-rows-and-newtypes forbids `Generic` on types with an
invariant.

**Constrained data constructors do not exist** (as of purs 0.15.x).
`data Range a = Ord a => Range a a` fails to parse with "Unexpected token
'=>'". Haskell allows it with extensions, but PureScript has no syntax for
it. Constrain the functions that compare, not the type that holds the
values.

## Prelude surprises

These hold as of prelude 6.0.2.

**`Number` and `Int` have no `Semigroup` or `Monoid`.** Addition and
multiplication are both candidates, and the Prelude declines to choose.
So `derive newtype instance Semigroup Kilograms` over a `Number` fails
with "No type class instance was found for Semigroup Number", and the same
is true over an `Int`. Write the instance by hand, or wrap the value in
`Data.Monoid.Additive`. This is the fact behind
purescript-rows-and-newtypes' rule to give each type only the instances
whose laws hold for its meaning.

**`Semiring` is four operations, not one:** `add`, `zero`, `mul` and
`one`, and `Ring` adds `sub`. There is no way to take addition alone, so
deriving `Semiring` for a quantity also hands out multiplication, and
the product of two prices means nothing.

**`between` is in Prelude.** `Data.Ord.between` is a range predicate, and
Prelude re-exports it. A module that defines its own `between` causes
trouble for every consumer that imports Prelude openly. An explicit
import, `import Ranges (between)`, shadows Prelude's with a
`ScopeShadowing` warning. An open import, `import Ranges`, makes any use
of `between` a `ScopeConflict` error. Pick another name.

**`abs` and `signum` are in `Data.Ord`,** and Prelude does not re-export
them. With only `import Prelude`, `abs` is "Unknown value abs".

**There is no tuple syntax.** `(a, b)` fails to parse with "Unexpected
token ','", because parentheses only group. A pair is `Tuple a b` from
`Data.Tuple`, an ordinary constructor with no comma.

**Addition on `Number` is not associative.** `(a + b) + c` and
`a + (b + c)` differ on a large share of random triples: between a sixth
and a quarter in a quick test, at every magnitude tried. So if a
`Semigroup` instance's `append` is floating-point addition, its
associativity law is false, and an exact law test will find it. See
purescript-rows-and-newtypes on using an exact representation wherever a
law must hold.

## Operators

**`===` and `<?>` from `Test.QuickCheck` cannot be chained** (as of
quickcheck 8.0.1). Both are `infix 2`, which is non-associative, so
`x === y <?> "msg"` fails with `NonAssociativeError`. Nor do they compose
by type: `===` returns a `Result`, and `<?>` takes a `Boolean`. You do not
need the message anyway, because `===` prints both values when it fails.

## Packages

**`Data.BigInt` from `bigints` imports the npm package `big-integer`**
(as of bigints 7.0.1). Unless that package is installed, the program fails
at runtime with `ERR_MODULE_NOT_FOUND`, and it puts a JavaScript runtime
dependency under code that was meant to be pure. Use `JS.BigInt` from
`js-bigints` instead (as of 2.2.1). It binds the language's own `BigInt`
and has no npm dependency. It does need a JavaScript engine with native
`BigInt`, so check that your target runtime has it.

**`quickcheck-laws` has a `Gen` variant of every law checker** (as of
quickcheck-laws 7.0.0). `checkSemigroupGen :: Gen s -> Effect Unit` takes
a generator, while `checkSemigroup` takes a `Proxy` and needs an
`Arbitrary s` instance. An `Arbitrary` instance for a library type has
two bad homes: in the test suite it is an orphan, and in the type's own
module it puts a test dependency into library code. So use the `Gen`
variants. They run in `Effect`, so wrap them in `liftEffect` inside a
`Spec`.

**`Arbitrary Number` is `uniform`** (as of quickcheck 8.0.1), which
generates only values in `[0.0, 1.0)`. A property over bare `Number`
never sees a negative value or two values more than 1 apart. Write a
generator whose spread matches the values the code will meet.

## Typed holes

Writing `?name` in place of an expression produces a `HoleInferredType`
error that prints the hole's inferred type, the values in scope that fit
it, and the local context. It is the fastest way to scaffold a definition
and have the compiler say what fills it. The build stays red until every
hole is gone.

As of purs 0.15.16, the type checker stops at the first declaration in a
module that fails. Holes in the same declaration are reported together,
but holes in separate declarations appear one compile at a time.

## Reviewing a change

1. Does an export list name an individually imported item instead of
   re-exporting the whole module?
2. Does a facade import a constructor with `(..)` that its callers should
   not have?
3. Does a "private" module rely on its name alone, with no import check?
4. Is a definition in a recursive `where` or `let` group point-free?
5. Is any instance declared outside the class's module and the type's
   module?
6. Does a type with a hidden constructor derive `Generic`, or `Show`
   through `genericShow`?
7. Does a newtype over `Number` or `Int` derive `Semigroup`, `Monoid` or
   `Semiring`?
8. Does any module define a name Prelude already exports, such as
   `between`?
9. Does a law test rely on floating-point addition being associative?
10. Does any code import `Data.BigInt` from `bigints`?
11. Does a law test use an `Arbitrary` instance where a `Gen` variant
    would avoid an orphan?
12. Does a property over `Number` use the default `Arbitrary` instance?
