# Additional tells

These patterns come from an author's corrections of agent-written drafts.
Humanizer 3.1.0 does not list them. Check for them whichever Humanizer
catalog you use. Each one names its nearest Humanizer pattern, so you can
tell an extension from a new pattern.

### A1. Figurative "carry" and "seam"

**Watch for:** *carry* in any form used figuratively ("the word carries the
number", "this example carries the section", "the types carry the
architecture", "the colour carries information"); *seam* for a boundary
("the seam between the two layers", "decoded at the seam"); the stock
phrases "worth being precise about", "it's worth seeing why", "the part
worth being honest about", and *precisely* or *exactly this* used as an
intensifier ("So the guarantee is exactly this").
**Problem:** Each is a metaphor where a plain word would do, and models use
them far more often than people. One sighting is enough for an author who
has learned to spot them. Extends §12.
Use the literal word: *has*, *holds*, *says*, *enforces*, *decides*, *is
what makes*; *boundary*, *interface*, *where A meets B*. Keep *carry* when
something is literally carried (a bridge, a load, a signal, a remainder in
arithmetic) and *seam* for the textile or geological sense.
**Before:**
> The word "endpoint" carries the number, so keep it. The decoder sits at the
> seam between the client and the service.
**After:**
> The word "endpoint" is what makes the number right, so keep it. The decoder
> sits at the boundary between the client and the service.

### A2. Label openers

**Watch for:** a noun phrase and a colon opening a sentence or paragraph
before an ordinary point: "One gap:", "One caveat:", "The catch:", "The
upshot:", "Short version:", "The fix:", "Net effect:".
**Problem:** It is a staged run-up (§4) compressed into a label. The reader
learns what kind of statement is coming before the statement itself. Make
the point, and let its content show that it is a caveat. Keep a label in a
form, a changelog, or a list whose format calls for one.
**Before:**
> One gap: the request can still fail before the schema runs.
**After:**
> The request can still fail before the schema runs.

### A3. Mirrored scope pair

**Watch for:** two short sentences of the same shape, the second negating
the first's scope: "It handles X. It does nothing about Y."; "The check
covers A. It does not cover B."; "The type tracks errors. It does not track
time."
**Problem:** A relative of the split contrast in §1. The symmetry sets the
rhythm, and the limit reads as a flourish rather than as information. State
the limit once, in whatever shape the sentence needs. Keep both halves when
the reader really needs both, but break the mirror.
**Before:**
> The schema handles malformed data. It does nothing about a network that's
> down.
**After:**
> The schema only covers bad data; a failed request still rejects the
> promise.

### A4. Tidy forward-pointing closer

**Watch for:** a closing sentence that promises the resolution will come
later, phrased as a neat summary ("Effect, below, puts both kinds of failure
in the same channel."; "We'll see how the next section closes that gap.");
a tie-a-bow return ("Which brings it back around to..."); a closing
parenthetical that restates the paragraph.
**Problem:** A relative of §2. The paragraph ends on a bow instead of a
fact, and a forward promise is a claim about a later passage that the
reader cannot yet check. Cut it. If the reader really needs to know where
something continues, give the location plainly ("Part 2 covers network
failures.").
**Before:**
> A failed request still rejects the promise. Effect, below, puts both kinds
> of failure in the same channel.
**After:**
> A failed request still rejects the promise.

### A5. Personified abstraction as the payoff

**Watch for:** an abstraction made the actor and given a clever verb,
usually at the end of the sentence where the point should land: "or wait
for one to escape", "the error slips through", "the bug hides in the
retry", "the type quietly lies".
**Problem:** The reader has to translate the image back into the event.
The wit is the agent's, and the author did not ask for it. Name the real
actor and use the literal verb. Personification the author wrote on purpose
(a function "telling lies", or one "working on this with its therapist") is
their voice; leave it. The tell is the agent adding it.
**Before:**
> To learn which exceptions can occur, we read the code all the way down, or
> wait for one to escape.
**After:**
> To figure it out, we have to trace code all the way down, or observe what
> errors actually occur at runtime.
