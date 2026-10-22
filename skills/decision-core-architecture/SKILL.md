---
name: decision-core-architecture
description: "Design, extend or review an application built as a pure, total core of decisions under a thin facade that holds no logic, with every technology concern (UI, persistence, OS, IO, formats) kept outside the core. Use when the project has already adopted this architecture (its docs or layout name Domain, Features, a facade and a shell) and the task adds a feature, places a piece of logic, or designs a module boundary, error type or dependency there; or when the user asks to design a new application this way or to evaluate whether it fits. Not for ordinary changes in projects built on a different architecture. Not tied to any language or framework."
license: MIT
---

# A decision core under a technology shell

The architecture separates decisions from technology. A decision is a choice
the product's user would recognize and could disagree with: what to show,
whether an invoice is overdue, when to send a reminder, how a figure is
rounded. Technology is how a decision reaches the world: pixels, markup,
gestures, storage, the network, the OS. Decisions live in the core and
technology lives in the shell. The facade between them contains no decisions.

The line does not fall between frontend and backend. A drag or a key press
can lead to a decision, and that decision still belongs in the core.

These rules govern implementation only in a project that has adopted the
architecture, or when the user asks to design or evaluate one. In a project
built another way, follow its existing structure. Proposing a move to this
one is a separate decision for the user, not part of an ordinary task.

Code sketches below use a Haskell-like notation. `∀ r` means "for any `r`",
and `| r` leaves a record or row open to further fields. For the same rules
written out in PureScript, with rows, `Variant` errors and newtypes, see
purescript-rows-and-newtypes.

## The layers

Name each layer for what would make it change. A name that only gives a
position in a diagram, such as "Core", "Services" or "Infrastructure", cannot
tell you where a new module goes.

    Domain     the subject's own model: value types, invariants, the pure
               maths. Changes when the domain changes.
    Features   use cases built from Domain: state transitions, the decisions
               a user would recognize. Changes when the product changes.
    Format     translation to and from foreign formats (parse in, serialize
               out). Pure, and total where the format allows.
    Runtime    implementations of the capabilities Domain declares (file IO,
               the log sink, the clock). Changes when the engine or OS does.
    Program    the composition root, which builds the environment and wires
               the layers together. Changes when the wiring does.
    ---------- facade: plain-data wrappers over Features, no logic ----------
    App shell  UI, navigation, persistence, every piece of state that must
               outlive the process.
    Native     platform integrations the shell can't reach on its own.

The list is not the dependency graph. Each layer may import only these:

    Domain     nothing outside Domain. It declares capabilities as types
               but never imports Features, Format, Runtime or anything later.
    Features   Domain.
    Format     Domain, and the value types Features returns (the layout a
               renderer serializes). Domain and Features never import Format.
    Runtime    Domain, to implement the capabilities it declares. Never
               Features: the core does not know which engine runs it.
    Program    Domain, Features, Format and Runtime. It wires
               implementations to the code that needs them.
    facade     Features and Format through what Program builds, plus Domain
               types for conversion. It is the only way into the core.
    App shell  the facade and Native. Never a core layer directly.
    Native     the platform's own SDKs. Nothing from the core or the shell.

So a use case in Features may import a Domain type, but a Domain module
that imports a Features helper or the Runtime clock is a violation, as is
a shell screen that imports Features instead of calling the facade.
Enforce these edges with a script in the check suite, because a rule that only the documentation states gets
broken without anyone noticing. If the language cannot make a subtree
private, the import check does that too. Every import across that boundary
goes in a named list with the reason for it, so the shared surface grows only
when someone decides it should.

A module that will not fit in one layer usually straddles two. Split it and
keep the rule. Laying out a document, for example (where each line breaks,
which heading starts a new page), is a decision, while writing that layout as
HTML or as PDF is a format. The decision returns the layout as a value, and
each renderer serializes it.

## Where a piece of logic goes

Ask whether the user would recognize the choice, or care if it changed.

If so, it goes in Features or Domain as a pure, total function over plain
state, even when a UI event triggers it. Dragging a meeting to a new slot
leads to a decision about whether it clashes with another meeting, and
pressing Send on an invoice leads to a decision about whether the invoice is
complete. Both decisions live in the core.

If the code only converts an event or a value into the shape a decision
takes or returns (pointer coordinates into a time slot, a key press into a
command, a value into markup), it goes in the shell or in Format.

A UI framework or a rendering format is never a reason to keep a decision out
of the core. Do not make up for it by building a second functional discipline
in the shell. Move the logic to the core, where the tooling already enforces
that discipline.

## The core is pure and total

- Domain and Features contain no partial functions. Anything that can fail
  returns the failure as a value. Crashes, throws and unchecked casts are
  allowed only at the edges.
- Smart constructors establish invariants once, so any value that exists is
  valid. When bad input could either be refused with an error that every
  caller must carry or made unrepresentable by a type, use the type. A line
  item's quantity, for example, should be positive by construction rather
  than a number checked wherever it is used.
- Use an exact representation wherever a law must hold. If amounts must add
  associatively, store an integer count of the smallest unit, not floats
  whose sums depend on the order of addition.
- A type class is justified when it has laws you can state and test, or when
  it must dispatch on a type that appears only in the result (`mempty`,
  `pure`), which a record cannot do. Two instances are enough to justify a
  lawful class. No number of instances justifies a class without laws.

## State: the shell holds it, the core transforms it

Every stateful use case is a step function:

    step : Settings → Context → State → Input → Result (State, Output)

- `State` is plain data, so the shell can keep it, persist it and pass it
  back. The core holds no state between calls.
- `step` validates the state it receives, just as it validates the input.
- After a crash or relaunch, the shell rebuilds the state by folding the
  persisted inputs through the same `step`. There is no separate recovery
  path.
- Tests need no fakes. Fold a recorded input sequence through `step` and
  assert on the whole output sequence, not only the final value. Build the
  hard cases on purpose: an edit undone and then redone, two edits that
  arrive out of order, a session that stops halfway through a command.
- Related watchers, such as reminders or validation warnings, have the same
  shape. Each sits beside the main step and reads its output rather than
  recomputing it.

Compute each derived quantity in one place. If several views depend on one
underlying number, derive every view from that number. Never add a second
computation to cover a timing gap, because the two will disagree.

## Dependencies are values, not type classes

Inject each capability (clock, logger, HTTP client) as a record in an
environment, and make each function ask for exactly the part it reads, never
for one application-wide environment:

    type Clock     = { now : Effect Timestamp }
    type Logging r = { logger : LogSink, clock : Clock | r }
    render : ∀ r. Needs (Logging r) → Paths → Effect Unit

- Capabilities compose as ordinary functions: a `LogSink → LogSink` filters
  by level, and an `Http → Http` adds retries.
- A test passes a different value, not a different monad: a sink that
  writes to a buffer, or a stopped clock so that timestamps can be compared
  for equality.
- A function's signature states everything it depends on, and the compiler
  holds it to that. When signatures grow unwieldy, widen an existing part of
  the environment before naming a new combination.
- A capability has no laws, so by the rule above it is not a type class. Use
  a class only where a record cannot dispatch.

Inputs that arrive as data, such as key presses, received messages or
imported rows, are not capabilities. The shell passes them to `step`, so the
core never has to ask for them.

Choose environment-specific implementations at the composition root, and
nowhere else. Production, test and development differ by which values
Program builds, not by flags the code checks. A line such as
`if (isProduction)` or `let live = true` inside a layer is a decision about
wiring made in the wrong place: tests can no longer reach the other branch,
and the branch the tests skip is the one that ships. Program builds the live
implementations; a test builds fakes and calls the same entry point.

### Example: a feedback shell over the real core

A second shell is a cheap way to try the product before the main one is
built: a small web page, a command-line tool or a notebook that calls the
same facade the real app will call. Because it runs the real core, what you
see in it is what the product will decide.

- The feedback shell imports only the facade. It holds no decisions of its
  own, for the same reason the app shell holds none.
- Where a feature the core does not have yet is needed to try something,
  the shell uses a stand-in, and each stand-in names the issue that will
  replace it (`// stand-in until #42: fixed tax rate`). Stand-ins live in
  the feedback shell only, never in the facade or the core, so nothing
  shipped can come to depend on one.
- When a stand-in's issue lands, delete the stand-in. A search for the
  marker lists what is still faked.

## Errors are open rows, combined like the environment

A fallible function returns `Either (Variant row) a` with the row left open,
and composing two functions merges their rows without converting either
one. In TypeScript the equivalent is a union of tagged error types, which is
how Effect's error channel combines them.

- Give each error type one label, not one label per failure. The label
  carries the whole error type.
- Leave rows open in the core. Close them only where errors are handled: at
  the boundary that reports them (the facade, a CLI) and in tests.
- Wrap an error only to add context it lacks, such as which row of an import
  or which line of a config file failed. The wrapper carries that context and
  the inner error, which is still a row. Otherwise errors pass through
  unwrapped.
- Never report a failure that can only be a bug as an ordinary outcome such
  as "no match". If you do, a bug looks the same as bad input.

## The facade

- Only plain data crosses. Records, arrays, numbers and strings cross
  unchanged. Sum types cross as discriminated unions `{ type, value }`.
  Optional values cross as the host language's `undefined` or `null`, never
  as the core's `Maybe` or `Option`. Inside the core, absence stays a
  `Maybe` or `Option`; the facade converts in both directions. Where a
  language guide asks for `Option` in payloads, that applies to internal
  payloads, and this rule wins at the facade.
- A core value that is too rich to cross (it holds big integers, closures or
  internal invariants) goes in a private field of an opaque handle, which
  shows nothing to serializers, reflection or loggers. Never persist a
  handle. Persist the source and rebuild the value on launch.
- The facade contains no logic. If facade code branches on what a value
  means, that branch is a decision and belongs in Features.
- The facade has a typed declaration for every core export it calls, and a
  contract test checks those declarations against the build, so no cast is
  ever needed.

## Decode a boundary value once

A value that crosses a real boundary (storage, a file, the network, a
bundled fixture, the facade) is `unknown` until a schema decodes it. After
that it is typed and trusted. If code further in wants to check the value's
shape again, fix the boundary that handed it over.

## Round each figure once, in the core

The core returns each figure twice: the exact value, for computation, and a
reading for display, made of a whole count, its number of decimal places and
its unit. A renderer places the decimal point where the reading says and
writes the digits it was given. Nothing after the facade rounds again.
Platform number formatters round differently from one another, so a renderer
that rounded for itself could show a different figure from another renderer
of the same value.

## Enforcement

Check every rule above mechanically where you can. The check suite should
include:

- the import-direction check, and any subtree-privacy check;
- the facade contract test, which confirms that each declared name exists
  and is the kind of value declared;
- a ban on escape hatches in shell and facade code: lint-disable comments,
  type-checker suppressions, type assertions, non-null assertions, skipped
  or focused tests, and calls to partial functions;
- for every new test, a run showing it fail without its fix, before anyone
  relies on it.

Never switch a check off in place, because a disabled check stops guarding
every later change too. If a rule seems wrong for a case, stop and raise it
with whoever owns the rules. When a check could report every case or only the
cases a heuristic can follow, write the one that reports every case.

## Deliberately deferred

- Do not abstract over a second variant until it exists. Write the second
  reader or adapter concretely, then extract what the two share. This does
  not apply to lawful abstractions, which their laws justify.
- Do not give the core a graph when it needs a line. If the domain
  sometimes branches, select a single path first and give the core that
  path.

## Reviewing a change against this skill

1. Does any new decision live in the shell or the facade? Move it into
   Features.
2. Does any import fall outside the allowed edges, or reach into a
   private subtree? Does the check catch it?
3. Does any new fallible function close its error row, convert another
   module's error, or wrap one without adding context?
4. Does any new capability arrive as a type-class instance instead of a
   value?
5. Does any core-specific value cross the facade, or does any handle get
   persisted?
6. Is any value decoded twice, or any figure rounded twice?
7. Is there now a second computation of a quantity that already has one?
8. Was any check weakened so that the change would pass?
9. Does any layer other than Program branch on the environment (a flag, an
   environment variable, a mode) instead of receiving a different value?
10. Does any stand-in from a feedback shell appear in the facade or core,
    or lack the issue that will replace it?
