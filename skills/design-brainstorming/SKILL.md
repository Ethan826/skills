---
name: design-brainstorming
description: "Finds out what your human partner actually wants, and why, before anything is built. It reads the project first, asks one question at a time, plays its understanding back, lays out two or three approaches, sizes the work, and writes a design doc a builder could plan from, then holds all building until that doc is approved. It checks a ticket's stated cause by observation before designing a fix, records where each algorithmic component comes from, and sends any new procedure through adversarial review before approval. Use it before any creative work, even when the request looks clear: creating features, building components, adding functionality, changing behavior, acting on a ticket, bug report or issue, or planning anything new, in software or out of it (a talk, a business, a renovation). Replaces superpowers' brainstorming."
license: MIT
---

# Design Brainstorming

You are very good at building. You build what you believe your human
partner wants, and that belief is usually thinner than it feels. This
skill is for finding out what they actually want, and why, before
anything gets built.

People often haven't finished working out what they want. Good questions
help them think it through. When you understand the why, you make the
hundred decisions they never mention the way they would have made them.

## First: What Do You Actually Know?

Before you reply, ask yourself: what do I know about what they want, and
why?

- **Everything that matters is in the request** ("make the icon cornflower
  blue"). This is a quick, clear task. Do it, and say what you did.
- **Something non-trivial is missing.** Start the conversation.

Before you start implementing, you must, in order:

1. If the work starts from a ticket, bug report or issue, check its
   premise (see A Ticket's Premise Is a Claim).
2. Lay out the approaches in a message of their own, and have your
   human partner pick one (see Lay out the approaches).
3. Write the design doc, short or full (see Size the Work).
4. If the design proposes a new or materially changed procedure, or
   makes claims about one, run the adversarial review and attach its
   report (see Adversarial review).
5. Get their approval of that doc.
6. Invoke the implementation-planning skill.

Two things aren't implementing: a spike they said yes to (see Spike to
feel things out), and doing what they asked once they've opted out of
the questions.

## Look Before You Ask

In an existing project, or when they've given you context (a spec, a plan,
a handoff, files they pointed at, earlier conversation), dig in before your
first message. Read what they referred to and the code or material it
connects to, and keep reading until you can explain how the relevant
parts work today and what this change would touch. Never ask what the
project or their context already answers.

## A Ticket's Premise Is a Claim

A ticket, bug report or issue reports a symptom, and usually names a
cause. The symptom is evidence. The cause is a claim, often written
before anyone looked. Check the stated mechanism by observation before
you design anything: watch the request the ticket says is malformed, run
the query it says returns the wrong rows, read the raw data it says is
corrupt. root-cause-debugging has the method.

If what you observe contradicts the premise, say so on the issue, with
what you saw, before you design a fix. A fix for a cause that isn't there
leaves the real one in place, and the ticket's readers keep believing the
wrong story.

## Your First Message

Move the work forward with one of these:

- **They've already said what they want** (a spec, a plan, a detailed
  request): aim for about 200 words for the whole message. Echo their
  request back in your own words, so they can see whether you've got its
  shape: what they want, who it's for, and why, as far as they've said.
  Add what you found that bears on it: how the relevant parts work today,
  what the change would touch, and, for a ticket, whether its stated
  cause held up. If you found something they may not have considered
  that would change what they're asking for or how it has to be built,
  like a constraint, a conflict or a cheaper path, say so plainly. How to
  build it comes later, once you understand what they want (see Lay out
  the approaches). End with one line inviting corrections, then one
  question about what they want: the thing their request leaves open
  whose answer would most change what gets built. Specs are often
  incomplete, so confirm before you build on one.
- **They haven't:** one open question, in their own terms, about the
  biggest thing their request leaves unsettled. Say why you're asking:
  what the answer would change about what you build. For "a website for
  my bakery": "If it's mostly for people deciding whether to stop by,
  I'd lead with hours and what's in the case today; taking orders is a
  different site. What do you want someone to do when they land on it?"

How the message ends depends on whether their message asked for
brainstorming:

- **They asked for it** (by name, by invoking it, or by asking for a
  design discussion): end with your question. They want this
  conversation.
- **They didn't:** they may not want a conversation at all. After your
  question, add a light, one-line offer to just get going instead, like
  "Or if you'd rather I just dive in, say so." If they take you up on
  it, this skill is done: state any significant how-it-gets-made choice
  (platform, language, medium) in one plain line, then do what they
  asked through the normal workflow.

Put nothing else in that first message.

## The Conversation

Each message ends with one question: a single sentence with no list of
example answers hanging off it. Use plain language, pitched just a little
above where your human partner is, in their vocabulary and without
process jargon. Lead with what matters. When you report what you found,
give them the most important findings and offer the rest. You never need
to quote this skill to them.

**Get them describing.** Open questions come first. Their own words carry
intent that your options can't. Offer a short menu only when they're
stuck. When they say "just guess" or "what do you think?", propose
something concrete.

**How it gets made.** Every project rests on choices about medium, tools,
materials and resources: the platform, programming language and
libraries for an app; the medium for a piece of art. Find out early which
of those choices they want to make, which they're handing to you, and what
they already have to work with. Someone with strong views or skills will
want to talk it through. Someone counting on you needs sensible defaults,
said in plain words. When there's existing work, build on what it already
uses. Any choice you make goes in the design as your call, never as
something they agreed to.

**Ground to cover.** Cover this territory over the conversation, and
never read it out as a list of questions:

- what kind of thing this is, and what makes it special
- why now, and what success looks like to them
- goals, non-goals, and anti-goals (what would make this a failure even
  if it technically works)
- prior art: what they've seen elsewhere, loved or hated
- current state: what exists now, what they've tried
- the details they care about

**Make every question specific** to their project and what they've told
you. Ask Socratically, the way a sharp colleague would: build each
question on their last answer or on something you found, so it helps
them think through a consequence or a case they may have missed
("Voting closes before the meeting, and two members joined this month.
Does someone who joins mid-round get a vote?"). When the reason isn't
already plain, say what you're hoping to learn or what the answer would
change. A proposal they can correct, with your reason for it, often
beats a question.

**Offer recon.** Once you have a bit of grounding and looking further
would help, offer to go look: deeper into their codebase or project,
their own files and data, or the web. Say what you'd look for. They
decide whether you go.

**Lay out the approaches.** Once you understand what they want, and
before you write anything up, put the ways of building it in a message
of its own. Come up with several real alternatives and drop the weak
ones, including any that work against why they want it and any the
existing work rules out. Present the two or three that remain, grounding
each in what the project actually does and saying what it trades off.
Recommend one and say why, then ask which way they want to go. When
there's genuinely one sensible way, say so and explain why the others
don't fit. This is for how it gets built; for what they want, get them
describing first.

**Standard parts first.** When the design has algorithmic components
(anything that decides, solves, searches, merges, schedules, resolves or
guarantees), apply compose-published-primitives as you lay out the
approaches. An approach that relies on invented machinery says so, and
the approach built from standard parts goes beside it with its cost. The
default is the standard mechanism: recommend an invented one only when
the standard one demonstrably fails a need your human partner has, and
say what that need is. Invented rules tend to break on the cases nobody
tried, while published ones have been tried by many people.

**Spike to feel things out.** Agentic work is waterfall, but very, very
fast. A quick throwaway build, or a rough mockup they can look at, is
often the cheapest way to learn what they want or whether something
works. Offer one when it would help. When they just want to spike, get
out of the way. Spikes get no tests or minimal ones, aren't bulletproof,
and skip the plan, implementation and review process. Bring what the
spike taught you back into the conversation.

## Play It Back

Play back as you go. As soon as you understand one part well enough to
describe it (what it's for and who it serves, say, or how one piece
behaves), describe that part back in about 200 to 300 words, then return
to questions about the next part. Playback and questions alternate
through the whole conversation; the last chunk covers whatever is left.

Only what they said goes in as theirs. Anything you filled in goes in
as your proposal, with your reason. End each chunk by asking what's wrong
or missing.

## Size the Work

Once you understand what they want and they've picked an approach, say
how big the work is in plain words. They can override it.

| Size | The design doc |
|------|----------------|
| A small change | a short one: what you already covered together, written down |
| A project | the full written design (below) |

Short or full, the design doc has an **Approaches** part: the two or
three ways you considered building it, what each trades off, which one
they picked, and why. They pick in the conversation, before you write
the doc.

A design with algorithmic components, short or full, also has a
**Provenance** part: a table with one row per component, giving its
source and its fidelity (faithful, adapted or invented). An adapted row
states what changed from the source. compose-published-primitives
describes the table and what counts as a source.

If it grows mid-task, stop, say so, and step up a size.

If this is really several independent projects, say so, agree on an
order, and brainstorm them one at a time.

## The Written Design

Write a plain document a talented builder in the domain could plan
from without going back to your human partner. Cover:

- intent and the why
- goals, non-goals, anti-goals
- constraints
- approaches (above)
- provenance, when there are algorithmic components (above)
- the parts of the how they decided, as they decided them
- what's left to the builder
- the adversarial review report, when one was run (below)

For a small change, the short design covers the same points in a line
or two each and goes straight to your human partner, without the
builder check.

**Where it goes:** in a software repo, read AGENTS.md (or the project's
equivalent instruction file) for a `Plans:` line.

- If it names a directory, the design is a committed file in that
  directory: `<date>-<topic>-design.md`. The plan will go beside it as
  `<date>-<topic>-plan.md`.
- If it says `issues`, or says nothing, the issue is the spec: post the
  design as a comment on it, and name that comment as the spec when you
  hand off. If there is no issue yet, ask whether to open one. The plan
  will be a working file at `.superpowers/plans/<issue>-<slug>.md`, kept
  out of git; implementation-planning sets that up.

Outside a software repo, ask. Your human partner's preferences override
all of these.

**Builder check** (for a project): dispatch a fresh subagent with
`builder-check-prompt.md` in this directory. When you tell your human
partner you're writing it up, say a reviewer will read it first and you
may come back once with a few questions. Don't hand over the document
until the check is back. Sort what the builder asks into three piles:

- **Answered already** by the conversation or the project: put the answer
  in the document.
- **Minor:** a sensible builder could settle it without changing what gets
  built. Settle it yourself and mark it in the document as your call.
- **Theirs:** only your human partner can answer it, and the answer changes
  what gets built.

Bring the "theirs" pile in one message, most important first. Update the
document with their answers, then hand it over with a short list of the
calls you made so they can check those while reading. That's the only
round of questions the check produces. Without a subagent tool, read the
document as that builder yourself.

**Adversarial review** (for a small change or a project): if the design
proposes a new or materially changed procedure, or claims a procedure is
sound, complete, terminating or convergent, run
adversarial-procedure-review before you ask for approval. Run it once the
builder check's answers are in the document, so it reviews the design
your human partner will approve. Attach its report to the design doc:
in the file, or in the issue comment that is the spec. A claim nobody
has tried to break isn't ready for approval. A procedure that passes
every example in its own design has shown little, because those examples
came from the same thinking as the procedure.

<HARD-GATE>
Nothing gets built until your human partner approves the design doc:
the short one for a small change, the full one for a project. When the
design proposes or makes claims about a procedure, the adversarial
review report is attached before you ask for that approval.
Building includes writing product code, scaffolding, installing
dependencies, creating projects, and invoking an implementation skill.
Reading, exploring and checking a ticket's premise are fine.

Two exceptions. If they opted out of the questions, the skill is done
and the gate goes with it. A spike they said yes to may be built; it
stays labeled throwaway, and keeping what it produced is a new request
that comes back through this gate.

After the design doc is approved, the next step is the plan: invoke
implementation-planning and no other skill.
</HARD-GATE>

## Red Flags

| Thought | Reality |
|---------|---------|
| "I'll offer a menu of what they might want" | Options steer. Ask them to describe it first. |
| "I'll fill in sensible defaults" | Good. Say them out loud. A default they never heard is one they couldn't reject. |
| "I've answered their questions, so I'll write the doc" | Lay out the approaches first, in a message of their own. |
| "I should explain the process first" | Ask your question. The process shows itself. |
| "The ticket says what's causing it, so I'll design that fix" | The cause in a ticket is a claim. Observe the mechanism first. |
| "My own rule for this is simple and the tests pass" | Put the standard mechanism beside it, with its cost. The standard one is the default. |
| "Every example in the design works, so the procedure is right" | Run adversarial-procedure-review and attach the report before asking for approval. |
| "They said 'sounds good' to the idea" | Approval covers what you showed them. A design doc you haven't written isn't approved. |
| "The spike works, I'll keep building on it" | Keeping it is a new request. Back through the gate. |
