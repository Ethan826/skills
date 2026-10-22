---
name: purescript-rows-and-newtypes
description: "Track what a PureScript function needs and what can go wrong in its type, using open rows: capabilities as fields of a Reader environment, errors as labels of a Variant, both combined by row union; plus newtypes with private constructors and smart constructors so that every value that exists is valid. Use whenever writing or reviewing a PureScript function that can fail or that needs a dependency, when designing an error type, a capability, a record that several types share, or a newtype over a primitive, and when deciding whether something should be a type class. In a project that structures effects another way, follow its approach unless the user asks to adopt this one."
license: MIT
---

# Rows for requirements and errors, newtypes for meaning

A function's type should say what it needs, what can go wrong, and what its
values mean:

- **What it needs** is a row of fields in a Reader environment.
- **What can go wrong** is a row of labels in a `Variant`.
- **What its values mean** is a newtype whose constructor is private.

The two rows stay open (`| r`), so composing two functions merges what they
need and what can go wrong without converting anything. Each signature then
lists exactly the capabilities the function reads and the failures it can
produce, and the compiler rejects a body that strays from either list.

These are the PureScript form of the rules in decision-core-architecture,
which says where such functions sit in a whole application. They govern
a project that has adopted this style or a user who asks for it. A
project built on another effect structure (a monad transformer stack,
tagless final, plain `Effect` with exceptions) keeps its own; propose a
move instead of making one inside an unrelated change.

`+` below is `Type.Row`'s `type (+)`, which joins two row aliases:
`(UnitErrors + DateErrors + r)` means `(UnitErrors (DateErrors r))`.

## Requirements: capabilities are values in an open row

A capability, such as a clock, a logger or an HTTP client, is a record of
functions wrapped in a newtype, not a type class.

```purescript
-- the capability, as a value
newtype Clock = Clock { now ∷ Effect Timestamp }

-- the slice of the environment that carries it
type Time r = (clock ∷ Clock | r)
type Logging r = (logger ∷ LogSink | Time r)

-- a function that needs it says so, and says nothing else
writeReport
  ∷ ∀ r m. MonadAsk (Record (Logging r)) m ⇒ MonadAff m ⇒ Path → m Unit
writeReport path = do
  logger ← asks _.logger
  ...
```

The program supplies a record literal at the top:

```purescript
main = launchAff_ $ runReaderT (writeReport path) { logger, clock, http }
```

The compiler checks that the record has every field each function asks for,
and `r` absorbs the fields a function does not read.

Rules:

- **Ask for the fields you read, and no others.** A function constrained on
  `Logging r` logs and states nothing else. Do not build a single
  application-wide `Env` record and pass it everywhere, because that hides
  what each function touches.
- **Put each row alias beside the type it carries.** `Time` lives with
  `Clock`, not in a central "environment" module.
- **Capabilities compose as ordinary functions.** A `LogSink → LogSink` can
  filter by level, and an `Http → Http` can add retries. As type class
  instances, each would need a fresh newtype and its own derives.
- **Tests pass a different value, not a different monad.** Pass a sink that
  writes to a `Ref`, or a clock stopped at a fixed timestamp so that times
  can be compared with `==`. A test needs no mock monad and no test instance.
- **When signatures sprawl, widen an existing row before naming a new
  combination.** If everything that logs also stamps the time, put the clock
  inside `Logging` (as above) so callers do not list it twice.
- **Inputs that arrive as data are not capabilities.** Key presses, received
  messages and parsed files are arguments. Only what the code *asks* for goes
  in the environment.

### When a type class is right instead

A type class is justified when it has laws you can state and test, or when it
must dispatch on a type that appears only in the result (`mempty`, `pure`,
`bottom`), which a record cannot do. `Monoid` and `Functor` are classes. A
logger is not one, because it has no laws.

Two instances are enough to justify a lawful class. No number of instances
justifies a class without laws. When the laws are real, property-test them
once over every instance (`quickcheck-laws`) instead of writing the same
check for each type.

PureScript has no `ConstraintKinds`. A constraint synonym has to be a class
with no methods and one instance implied by its superclasses, and it reads
like the effect classes this section argues against. Use one only when the
sprawl is real.

## Errors: open rows of a `Variant`, combined the same way

A function that can fail returns `Either (Variant row) a` with the row left
open. This is the error channel of Effect and fp-ts, where combining two
operations widens the error type to include both.

```purescript
-- the error, as a value
data UnitError = NotFinite Number | OutOfRange Number

-- the slice of the error row that carries it
type UnitErrors r = (unitError ∷ UnitError | r)

unitError ∷ ∀ r. UnitError → Variant (UnitErrors r)
unitError = inj (Proxy ∷ Proxy "unitError")

-- a function that can fail says which errors, and says nothing else
mkPercent ∷ ∀ r. Number → Either (Variant (UnitErrors r)) Percent
```

If `parseDate` returns `Either (Variant (DateErrors r)) Date`, a function that
calls both it and `mkPercent` in one `do` block returns
`Either (Variant (UnitErrors + DateErrors + r)) a`. The rows unify, and
neither error is converted on the way.

Rules:

- **One label per error type, not one per failure.** `unitError` carries the
  whole `UnitError`, as `clock` carries the whole `Clock`. Adding a case to
  `UnitError` then changes no signature anywhere.
- **Leave the row open in library code.** Close it only where the errors are
  handled: at the boundary that reports them (a CLI, an FFI export, a UI
  facade) and in tests, which need a closed row for `Eq` and `Show`:
  `Either (Variant (UnitErrors ())) Percent`. A library function that closes
  its row forces every caller to widen it again with `Data.Variant.expand`.
- **Wrap only to add context the inner error lacks.** A parser that knows
  which line of a file failed defines
  `BadLine Int (Variant (UnitErrors + DateErrors + ()))`, and the inner error
  is still a row. When the context belongs to the error itself, put it there:
  `TaxRateNotFinite` and `DiscountNotFinite` rather than a wrapper that says
  which number. Never define a wrapper type whose only job is to hold another
  module's error.
- **Handle with `on`, `onMatch` and `case_`, or `default`.** A chain of `on`
  ends in `case_` once every label is handled:

  ```purescript
  describe = case_
    # on (Proxy ∷ Proxy "unitError") describeUnit
    # on (Proxy ∷ Proxy "dateError") describeDate
  ```

  `case_` crashes in the library's source, but it takes `Variant ()`, which
  has no values, so the crash cannot be reached.
- **Write `Eq` by hand when a payload holds a `Number`.** A derived instance
  compares with `==`, and `NaN /= NaN`, so the error `mkPercent` returns for
  `NaN` would not equal itself and `Eq` would break reflexivity.
- **Never report a bug as an ordinary outcome.** If a failure can only mean
  the code is wrong, do not fold it into `Nothing` or "no match". If you do,
  a bug looks the same as bad input.

## Data: open records compose the same way

The same row discipline applies to the data:

```purescript
type Named r = (name ∷ String | r)
type Contact r = (email ∷ Email | r)

type User = Record (Named + Contact + (id ∷ UserId))

mailbox ∷ ∀ r. Record (Named + Contact + r) → Mailbox
```

`mailbox` accepts a `User`, a signup form or anything else with `name` and
`email`, with no common supertype and no need to anticipate its callers.
Define each row beside the types it names, as `Contact` is defined beside
`Email`.

## Newtypes: one per meaning, constructor private

Wrap every primitive that carries a meaning. Two `Number`s that mean
different things (a tax rate and a discount, a timestamp and a duration) must be
different types, so that swapping them is a compile error where it would
happen rather than a wrong answer later.

- **One newtype per meaning, not per unit.** A timestamp and a duration are
  both counted in milliseconds, but they are different types. `Milliseconds`
  (the unit) appears in a signature only inside the unit modules and in
  conversions. Domain code uses `Timestamp` and `Duration`.
- **Give each type only the instances whose laws hold for its meaning.**
  Two durations add, so `Duration` has a `Semigroup`. Two timestamps do not
  add, so `Timestamp` has none. Their relationship (timestamp minus timestamp
  is a duration, timestamp plus duration is a timestamp) is an affine space,
  which is a lawful class with a functional dependency `p → v`. Use
  `derive newtype instance` for the instances that are true, and write
  nothing for the ones that are not.
- **Hide the constructor.** Export `Percent`, not `Percent(..)`. Values enter
  through a smart constructor:

  ```purescript
  mkPercent ∷ ∀ r. Number → Either (Variant (UnitErrors r)) Percent
  ```

  Once a `Percent` exists, it is valid, and nothing checks it again.
- **A conversion with nothing left to check is total and is not named
  `mk`.** `durationToMilliseconds ∷ Duration → Milliseconds` exists so the
  constructor can stay private, not because anything is validated.
- **Never derive `Newtype` for a type with an invariant.** `wrap` is a
  public constructor by another name. For the same reason, purs warns
  `HiddenConstructors` when such a type derives `Generic`, because `to` and
  `from` hand the constructor back. Write `Show` by hand instead of deriving
  it through `Generic`.
- **Make bad input unrepresentable rather than refusing it everywhere.**
  If a function would fail on a non-positive quantity, take a `Quantity` that
  is positive by construction. The check happens once, where the number
  enters, and the error row stays out of every caller's signature.
- **Use an exact representation wherever a law must hold.** If an instance
  promises `Semigroup`, its `<>` must be associative exactly. Floating-point
  addition is not, so store money as an integer count of the smallest unit
  (cents, say, as a `BigInt` from `JS.BigInt`, which binds the language's own
  `BigInt`) and test the law with exact equality. Do not loosen the test to a
  tolerance: an instance that claims a law it does not keep is worse than no
  instance.

## Totality

Code under this discipline has no partial functions. A function that can fail
says so in its type, even when the failure cannot happen with valid input.
Crashes, `unsafePartial`, `unsafeCoerce` and `fromJust` belong only at the
program's edges: `main`, the FFI boundary and tests.

## Enforcement

Check the rules mechanically where you can:

- a script that requires every exported function in the unit modules that
  takes a raw `Number` to return `Either (Variant (... r))`;
- negative cases: small modules that must fail to compile (adding two
  timestamps, passing a `TaxRate` where a `Discount` is wanted), with a check
  that keeps them failing;
- `quickcheck-laws` over every lawful instance, with exact equality;
- a layering check that keeps partial functions out of the library modules.

## Reviewing a change

1. Does any new function close its error row, convert another module's error,
   or wrap one without adding context?
2. Is any error type split across several labels, or does any label carry a
   bare primitive instead of an error type?
3. Does any function ask for an environment field it does not read, or take
   a single application-wide `Env` record?
4. Is any new capability a type class instance rather than a value? Does any
   new class lack laws?
5. Does any new newtype export its constructor, derive `Newtype` or
   `Generic`, or derive an instance whose law does not hold for its meaning?
6. Is any raw `Number` or `String` standing in for a domain meaning?
7. Is any value validated twice, or validated where a type could have made
   the bad case unrepresentable?
8. Does any law test use a tolerance?
