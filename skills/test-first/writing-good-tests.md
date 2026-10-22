# Writing Good Tests

**Read this when** you write or change a test, add a mock, or add a
cleanup or helper method for tests.

## Overview

A test exists to catch a specific break. Two principles run through
everything below:

```
1. Every test names the break it catches
2. Every test exercises the real thing
```

Test-first work tends to satisfy both. A test written first and seen
failing against real code has already shown that it can fail, and it
gets a mock only when the real dependency turns out to be slow or
external. A test written after the code has to show the same thing with
a mutant (see the SKILL.md section Tests Written After the Code).

## Principle 1: Name the Break

Before writing the test body, answer this: **what production change
should make this test fail, and is that change a bug or a decision?** A
test earns its place by catching a wrong branch, a missing side effect,
a wrong argument, a boundary case or a broken contract.

**Derive expectations independently.** Use literals and hand-checked
fixtures. Table-driven tests with literal `want` values are the
preferred shape. An expectation computed by the code under test, or by
its helpers, passes whatever that code does:

```typescript
// Bad: Mirror assertion: the same builder computes both sides — always true
const expected = buildSearchQuery({ tag: 'urgent' });
expect(buildSearchQuery({ tag: 'urgent' })).toBe(expected);

// Good: Hand-derived literal
expect(buildSearchQuery({ tag: 'urgent' })).toBe('tag:"urgent"');
```

**No change detectors.** If only intentional decisions can fail a test
(a constant's value, the exact wording of a message, private structure),
it fires on every redesign and sleeps through bugs. Test the behavior
that depends on the decision. Instead of `expect(MAX_RETRIES).toBe(5)`,
check that a failing call is retried 5 times and that a 6th attempt
never happens.

**Behavior, not text.** A test that a script, skill or config contains
an exact line proves only that the source is the source. Run scripts
against controlled inputs and assert on outputs, side effects or exit
codes. Documents that instruct agents are tested by how the consuming
agent behaves (writing-skills, from superpowers). Prose for humans needs
no test at all.

**In a UI, assert on what renders.** Check the fills, text and layout
the user sees, not the data that feeds them. A component can receive the
right data and still draw the wrong color, drop a label or overlap two
elements. Query the rendered output: the text in the DOM, the computed
style, the element's position or the snapshot of a drawn canvas.

**Synthetic data must contain the hard cases.** A fixture built only
from easy values passes code that would fail on real input. Put in the
cases that break things: the empty list, the duplicate key, the value
at the boundary, the out-of-order record, the input that crosses a unit
or a day. Then **assert the whole output sequence, not only the final
value.** A running total that ends at the right number can still be
wrong at every step on the way there:

```typescript
// Bad: Only the end: a bug that applies the refund one step late still ends at 30
expect(runningTotals([10, -5, 25]).at(-1)).toBe(30);

// Good: Every step, from a fixture that includes a refund
expect(runningTotals([10, -5, 25])).toEqual([10, 5, 30]);
```

**Your code, not the framework.** Test the contract your code makes at
its boundaries: the route you register, the query you emit, the payload
you produce. Upstream mechanics are their maintainers' tests to write.
The classic case is asserting that your router invokes a registered
handler, which is the framework's test, not yours. When upstream
behavior genuinely surprised you, write one narrow characterization test
that names the assumption. The same boundary applies inside your code.

**Every new function or method is covered by a test that fails when it
breaks.** This is the one rule for trivial code; SKILL.md's checklist
points here. A constructor, getter, constant or trivial forwarding call
that validates, normalizes, defaults, derives, enforces or causes side
effects gets a test of its own. One that does none of these is covered
by the test that asserts on the first result a consumer can see that
depends on it. It needs no dedicated test, but that consumer test must
exist and must go red when the trivial code is broken. Code that no
test can reach this way is unused; delete it.

### Gate Function

```
BEFORE writing the test body:
  Name the production change that would make this test fail.

  Cannot name one            → redesign around an observable behavior
  "The source text changed"  → run the artifact and assert its effects
  Only intentional decisions → change detector; test the behavior
                               that depends on the decision

  Confirm the expected value is derived without the code under test.
  IF it reuses the code's logic or helpers:
    Replace it with a literal or hand-checked fixture
```

## Principle 2: Exercise the Real Thing

**The mock earns no assertions.** A mock assertion passes when the mock
is present and fails when it is absent. It says nothing about the
component. Assert on the real component's behavior. If the mock is what
you are checking, unmock it or delete the assertion.

```typescript
// Good: Real behavior
expect(screen.getByRole('navigation')).toBeInTheDocument();

// Bad: Mock existence
expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
```

**your human partner's correction:** "Are we testing the behavior of a
mock?"

**Pass a different value, not a mock.** When code takes its
dependencies as parameters (a clock, an output sink, a store), the test
can hand it a simple real value: a stopped clock, a buffer sink, an
in-memory store. These behave like the real thing, so nothing about the
code under test is faked, and the assertion reads the value afterward.
If the code reaches for the dependency itself, change it to take the
dependency as a parameter first; that is the dependency injection the
SKILL.md "When Stuck" table points to.

```typescript
// Bad: Mocks a function inside the module under test
vi.spyOn(tokens, 'currentTime').mockReturnValue(1_000);
expect(isExpired(token)).toBe(true);

// Good: The clock is a parameter; the test passes a stopped one
const clock = { now: () => 1_000 };
expect(isExpired(token, clock)).toBe(true);
```

**Mock at the right level.** Learn every side effect of the real method
before replacing it. Mock the slow or external operation, and keep real
whatever the test depends on. When unsure, run the test against the real
implementation first and see what actually needs to happen.

```typescript
// Bad: The mock swallows the config write that duplicate detection reads
vi.mock('ToolCatalog', () => ({
  discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
}));

// Good: Mock only the slow server startup; the config write stays real
vi.mock('MCPServerManager');
```

**Make doubles specific.** When arguments, call counts or ordering are
part of the contract, assert them; a fake that accepts anything verifies
nothing. Give each branch (success, error, malformed) its own fixture or
spy, so the wrong branch cannot satisfy the expectation.

**Mirror real data completely.** Mock the whole structure as it exists
in reality, with every documented field, not only the ones your test
reads. A partial mock fails silently when downstream code reads a field
it left out: the test passes while the integration breaks.

**Production classes carry production methods only.** Cleanup that only
tests need belongs in test utilities, never as a `destroy()` on the
production class. Ask whether the method is called only from tests, and
whether the class owns that resource's lifecycle. If the method is
test-only, or the class doesn't own the lifecycle, the method goes in a
test utility.

**Prefer real components over complex mocks.** Switch to an integration
test with real components when the mock setup outgrows the test logic,
when the mocks lack methods the real components have, or when tests
break because a mock changed. **your human partner's question:** "Do we
need to be using a mock here?"

### Gate Function

```
BEFORE adding a mock or test helper:
  Can the code take this dependency as a parameter?
    Pass a simple real value (stopped clock, buffer sink,
    in-memory store) instead of mocking.

  List the real method's side effects; keep the ones the test
  depends on real — mock the slow/external level below them.

  Mock responses mirror the complete real structure.

  A method only tests call lives in test utilities, not production.

  About to assert on the mock itself?
    Unmock it or delete the assertion.
```

## Vacuous Tests and How to Catch Them

A vacuous test passes whether or not the code is right. It usually
looks fine on the page. The faults below are the common ones, and each
has a check that exposes it.

**State each precondition as its own assertion.** A test often relies
on something being true before the real check means anything. If that
setup quietly fails, the test passes for the wrong reason. When a test
needs two values to differ, assert that they differ first:

```typescript
// Bad: If both fixtures happen to share a price, "the cache refreshed" is never tested
cache.set('sku-1', oldPrice);
clock.advance(TTL + 1);
expect(cache.get('sku-1', () => newPrice)).toBe(newPrice);

// Good: The precondition fails loudly if the fixtures collapse
expect(newPrice).not.toBe(oldPrice);
cache.set('sku-1', oldPrice);
clock.advance(TTL + 1);
expect(cache.get('sku-1', () => newPrice)).toBe(newPrice);
```

**Literals written to differ can collapse into one value.** Two values
that look different in the source can become equal once the code stores
them: rounded to two decimal places, truncated to whole milliseconds,
lowercased, trimmed or Unicode-normalized. `10.004` and `10.001` are
both `10.00` as a price. Build the second value from the first with a
step the representation preserves, and assert the difference in the
stored form:

```typescript
// Bad: Different literals, same stored price
const a = toPrice(10.004), b = toPrice(10.001);

// Good: Derived from the first by a step that survives rounding
const a = toPrice(10.00);
const b = toPrice(a.amount + 0.01);
expect(b.amount).not.toBe(a.amount);
```

**Choose operands that a weaker law cannot satisfy.** A property test
passes vacuously if its inputs also satisfy some weaker law the code
does obey. An associativity check with three equal operands,
`merge(merge(x, x), x)` against `merge(x, merge(x, x))`, passes for any
commutative `merge`, associative or not. Use distinct values, and assert
that they are distinct, so that only the law you mean can make the test
pass.

**Running a harness proves only that it runs.** A test harness, a
checker or a table of cases going green says nothing about whether each
case can fail. Mutation-test each case. Remove each guarantee in turn
(drop the validation, skip the branch, return the default) and confirm
that the case written for that guarantee goes red. A guarantee whose
removal turns nothing red is unprotected. If its own case stays green
while another case catches it, the case does not test what its name
says; fix it. Other cases may go red too: a unit test and an
integration test that both depend on the guarantee should both fail,
and that overlap is useful. Treat extra failures as a problem only when
they hide the cause, that is, when no failure message names the
guarantee that broke.

**A failure message that names the wrong values is as good as no test.**
When the test fails, its message is what the reader acts on. If it
prints the input where it should print the output, swaps expected and
actual, or carries a label copied from a neighboring case, it sends the
reader after the wrong thing. It can also hide that the assertion is
checking something other than what its name says. Read the message
every time a test goes red, during RED and during a mutant run, and
check that it names the value that is actually wrong.

## Tests Ship With the Implementation

"Complete" means the TDD cycle has run: failing test, minimal
implementation, refactor. Ship the tests the behavior needs and only
those. Trivial code is covered through its consumers, as described
under Your code, not the framework; human prose needs no test. A test
written only to satisfy process costs maintenance forever.

## The Mutation Check

Before finishing, mutate the production code, at least mentally. For
each realistic mutation, at least one test should fail:

- a wrong constant or argument;
- the wrong branch handler;
- a missing state change or side effect;
- an empty or default return;
- missing validation for zero, empty, nil, unauthorized or malformed
  input.

A mutation that no test catches means the behavior is unprotected or
the test is tautological. For a test added after the code, a mental
mutation is not enough: run the mutant in an isolated copy, as SKILL.md
describes.

## Quick Reference

| When you... | Do |
|-------------|-----|
| Write any test | Name the break it catches: a bug, not a decision |
| Build an expected value | Derive it by hand, never with the code under test |
| Test a script or document | Run it, or pressure-test its consumer; never grep its text |
| Test a UI | Assert on what renders, not the data behind it |
| Build synthetic data | Include the hard cases; assert the whole output sequence |
| Reach for a dependency test | Test your boundary contract, not their documented mechanics |
| Want to assert on a mocked element | Test the real component, or unmock it |
| Need to control a clock, sink or store | Pass a different value in; don't mock the code under test |
| Are about to mock a method | Learn its side effects; mock the slow or external level |
| Build a mock response | Mirror the real structure completely |
| Need cleanup only tests use | Put it in test utilities |
| Watch mock setup balloon | Switch to an integration test with real components |
| Rely on two values differing | Assert that they differ, in their stored form |
| Test an algebraic law | Use distinct operands and assert that they are distinct |
| Finish a harness or table of cases | Remove each guarantee in turn; its own case goes red |
| See a test fail | Read the message; it must name the wrong value |
| Finish a test file | Run the mutation check |

## Warning Signs

- Setup and assertion share the same object, guaranteeing equality
- The test can fail only through a panic, crash, or missing selector
- The test fails on every intentional change, never on accidental breakage
- Expected values are hidden behind loops, builders, or helpers
- The test greps source text, or asserts a removed symbol stays removed
- The test would still matter if only the framework remained
- The test exists for coverage, checking no side effect or outcome
- An assertion checks a `*-mock` test ID, or fails if you remove the mock
- A method is called only from test files
- Mock setup is more than half the test, or you can't explain why the mock is needed
- Mocking "just to be safe"
- A UI test asserts on props or state, never on what is drawn
- Fixtures hold only easy values, or the test checks only the last output
- A test depends on two values differing but never asserts it
- Every operand in a property test is the same value
- A harness went green, and no one has removed a guarantee to see a case go red
- A failure message names the input, a neighboring case, or the expected value as the actual one
