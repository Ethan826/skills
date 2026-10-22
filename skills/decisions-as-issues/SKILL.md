---
name: decisions-as-issues
description: Keeps a project's decisions, findings and handoff state in durable records that a later reader, or an agent with no memory of the conversation, can trust without re-deriving them. Every decision and finding becomes an issue under an epic with a tier or a status label, every deferral states its reason, blockers name the exact open question, wrong premises are recorded, follow-ups are filed (or drafted locally until filing is authorized) rather than offered, trackers are checkpointed during the work and swept after a merge, rules that subagents need go into the instruction file, and a multi-item survey keeps a ledger in which nothing counts as captured until it has a row. Use it whenever a product or design decision is made or deferred, a review, audit, survey or agent report turns up findings, a ticket's premise proves wrong, work is blocked, handed off or about to end a session, a branch merges, or your human partner asks whether the issues are up to date, even when the item seems too small to file.
license: MIT
---

# Decisions as issues

A project's trackers exist so that someone arriving later can trust
them without re-deriving the state. That someone may be your human
partner next month, a reviewer, or an agent starting cold with no memory
of today's conversation. Each record the work leaves stale or never
writes breaks that trust. The cost lands later, on a reader who either
redoes the work or acts on something false.

The records have no failing signal. Nothing turns red when a decision
lives only in chat, an issue stays open after its work shipped, or a
backlog row still says "partial". So write each record as part of the
work, at the time the work happens.

**Iron law:** a decision or finding exists only once it has a durable
record with a status. Until then it will be lost.

Two other skills cover the edges. verify-before-claiming covers
the evidence a record needs before it says something is done, and
re-checking a ticket's claims against the running system. landing-a-branch
covers closing out the issue at merge time: walking the acceptance
criteria and reading the state back. What follows is where records go,
what they say, and how they stay current between those points.

## What outlives a session

Decide where something goes by asking what the next session will read.
A new session typically lists the open issues, which shows titles,
reads the backlog and the instruction file, and opens the one issue it
is about to work on. It does not read every comment on every issue, and
it has no access to this conversation.

| Surface | Survives? | Use it for |
|---|---|---|
| Issue title | Yes | Anything that must be picked up later. Make it self-describing. |
| Issue body | Yes, once the issue is opened | The decision or finding, its status and its reason |
| Backlog row, roadmap or checklist entry | Yes | Queue position, ordering and dependencies |
| Committed docs (design notes, decision records, product doc) | Yes | Decisions and the reasoning behind them |
| AGENTS.md or the project's equivalent instruction file | Yes, and every agent reads it | Rules any agent must follow |
| Issue comment | Only if something points at it | Evidence and detail for an issue already surfaced |
| Commit message | No | Nobody searches history for a trap they don't know about |
| Agent memory, chat, an agent's report | No | Nothing that matters later |

So file the issue with a title that says what it is, add the backlog
row, and only then put the detail in a comment.

**Which comment is the spec.** When an issue's design or acceptance
criteria live in a comment rather than the body, which is common once a
design has been revised, say so in the body: "Spec: the comment of
<date> headed 'Revised design'", or a link to it. Often it is the last
comment, but a later reader cannot know that. Without the pointer, an
agent implements the original body and the revision is lost. Decisions
that must outlive a branch go in the issue, not in a plan file that is
deleted when the branch lands.

## Structure: epics, tiers and status labels

Every product decision and every finding becomes an issue, including
the deferred and the undecided ones. A decision that sits only in a
product document or a conversation is one nobody can link to, assign or
close.

- **Epics.** Group related issues under a parent issue labelled `epic`.
  Use the tracker's sub-issue feature where it has one. Where it does
  not, the epic's body keeps a task list linking each child.
- **Tiers.** Label each issue with when it ships, such as `tier: 1` to
  `tier: 3`, matching the ranking in the product document, if there is
  one. Keep the two in step: when either changes, update the other in the
  same pass.
- **Status labels.** An issue that is not plain committed work carries
  one of these:

| Label | Meaning | The issue must say |
|---|---|---|
| `spike` | An investigation, not a build | The question it answers and what would end it |
| `deferred` | Decided: not now | Why, and what would reopen it |
| `candidate` | Found (by research, review or survey), not yet decided | Where it came from and what deciding needs |

If the project also uses milestones, keep the two ideas apart. A tier
says when an item ships. A milestone says what has to exist before it
can be built and tested. An item can be tier 1 and still wait on a later
milestone.

**A deferral states its reason.** "Deferred" with no reason looks the
same as "forgotten", and the next reader cannot tell whether the reason
still holds. Write it down, along with what would change the decision:

```
Deferred: bulk CSV export.
Reason: the one customer asking for it can use the API, and export
would need the permissions model that is planned for tier 2.
Revisit: when a second customer asks, or when the permissions model ships.
```

An idea your human partner declined for now still gets recorded as
deferred rather than dropped. The reasoning is the valuable part, and
it stops the same idea being proposed again from scratch.

**Ordering costs.** When a fix is cheap now and expensive once some
other ticket ships, say so in both tickets and order the backlog
accordingly. Nothing else records a cost that depends on sequence.

**Known failures are recorded, not hidden.** A test you know fails, a
criterion you could not meet, or a feature left out of scope goes in the
issue with a concrete next action. Leaving something out of scope is a
legitimate decision, provided the issue says so.

## Blockers name the question

A backlog row that says "blocked" or "needs review" gets skipped by the
next session as waiting on a human, often for good. Write the specific
question that is unanswered and who can answer it:

```
Blocked: does a refund on a partly shipped order reverse loyalty points
for the unshipped items only, or for the whole order? (product decision)
```

Before recording anything as blocked, check the blocker. "This would
break X" is a hypothesis until you have read X, and that is usually one
file. A blocker that turns out to be imaginary has often pushed the work
toward a weaker fix, such as disabling a check or loosening an assertion.
If the better option was available all along, say so in the issue and
take it.

## Record a wrong premise

A ticket is a claim about the system, written by someone who may have
read code rather than run it, often weeks ago. verify-before-claiming
covers checking the claim. This section covers what to do when the
claim is wrong.

Say so in an issue comment (a remote write, so it follows "Record
follow-ups instead of offering to" below: post it if authorized,
otherwise draft it locally and ask): what the ticket claimed, what you observed
and how (the request you captured, the query you ran, the test that
failed against the old code), and what the real defect is, if there is
one. Then correct the issue body or title and the backlog row so that
neither carries the false premise forward. Don't quietly close it or
implement around it. The correction is the more useful half of the
work, because the next reader who meets the same symptom will otherwise
reach the same wrong conclusion.

## Record follow-ups instead of offering to

When work turns up a real gap (an untracked trade-off, a stale document,
an issue whose body now misdescribes the work, an adjacent bug), record
it as part of the same task, then report what you did. Ending a turn
with "want me to file that?" or "not filed, your call" leaves a finding
that disappears with the conversation, and hands your human partner a
chore.

Authorization for remote writes belongs to agent-baseline: filing,
commenting on or editing an issue in a remote tracker needs an OK for
that action. Recording the finding does not wait for it.

- **Filing is authorized** when the owner's standing instruction (in
  AGENTS.md or the project's equivalent instruction file) says to file
  follow-ups, or when your human partner has given an OK for these
  issues. File them, link them and report them, without asking again.
- **Filing is not yet authorized:** write each finding durably in the
  repository first. Use the project's local record (a backlog row or
  ledger entry) where one exists; otherwise write a prepared issue
  draft to a file, with its title, body and labels ready to file
  unchanged. Then ask once, listing every draft by path and title, and
  file them all when the OK comes. That OK covers the drafts it was
  given for; a finding added afterwards needs its own.

Either way, the finding never lives only in chat. A draft on disk
survives the session; a question in a closing message does not.

If a follow-up is out of scope for the current change, recording it is
itself the scoping decision, and it leaves a record either way. Link the
issue or draft from the current issue before you close that one, rather
than mentioning it in the closing note.

Save real questions for decisions only your human partner can make: a
business call, a spend, an irreversible action, or the one filing OK
above. Whether to record something is not one of them.

## Checkpoint as you go

An agent cannot see how much budget it has left, and a session can end
mid-turn. Treat every commit, or every finished unit of work, as a
checkpoint. Before starting the next unit, bring the trackers up to
date: the backlog row, the in-progress issue's current state, and any
instruction-file change the work implied. If the session dies there,
nothing is lost.

- Update guidance files early in a session, while there is budget, not
  in a final pass that may never run.
- Don't carry uncommitted work across the start of a new issue. Commit
  or stash it first.
- When handing off mid-issue, write in the issue what is done, what
  remains, which decisions were made and which questions are open. A
  handoff kept in agent memory or in a report to the controller does not
  reach the next agent.

## Sweep every record after a merge

When work merges, or when your human partner asks whether the issues
are up to date, bring every record into step in one pass, without asking
first. Offering to do part of it hands the rest back.

Search for every mention of what changed:

- the issue itself, its epic, and related issues (search issue bodies
  and comments for the feature's name and for issue references);
- the backlog and the product document's backlog and decisions;
- AGENTS.md or the project's equivalent, where it quotes types, layers,
  commands or build order the change affected;
- READMEs and other developer docs.

Update each one, or note why it needs no change. Then report what you
updated. A stale record (a product document calling a shipped feature
unbuilt, an instruction file quoting an old type, an issue whose
criterion the new code contradicts) is the drift the records exist to
prevent.

Where the project rebase-merges, what lands is the commits, not the
pull request. A small sync or docs fix then needs no pull request of its
own. Make it a focused commit that builds and passes alone, and let the
next branch carry it. landing-a-branch covers the merge and the branch
cleanup that follows.

## Rules subagents need go into the instruction file

Subagents read AGENTS.md (or the project's equivalent). They do not read
your memory, this conversation, or a comment on some issue. A rule that
only those places know is one every agent will break, and your human
partner then has to catch each breach in review.

When your human partner sets or restates a rule that applies to the
project (a style rule, a naming convention, a command that must not be
used), write it into the instruction file in the same pass. Before
dispatching an agent, check that its brief points at the relevant
section (see dispatching-agents). Where a rule cannot yet be checked by
a tool, list it in the instruction file as one to review by eye, and
check agent output against it.

## A ledger for multi-item surveys

A survey, audit or agent report produces many findings at once. They get
summarized in chat and are lost there. Keep a ledger, a single file or
issue with one row per finding, and follow three rules:

1. **A finding is captured only once it has a row with a status.** Add
   the rows the moment the report arrives, before you reply about it. A
   finding that exists only in an agent's report or in chat has not been
   captured.
2. **Rows leave only by being shipped or dropped.** A shipped row names
   what shipped it (the issue, commit or artifact). A dropped row gives
   the owner's reason. Your own judgement that something is not worth
   doing makes it a proposal to drop, not a drop.
3. **Never delete the ledger.** Not even when its first batch has
   shipped. Its value is the history of what was found and decided.

Statuses that work well:

| Status | Meaning |
|---|---|
| SHIPPED | Done; the row names where |
| PARTIAL | Some of it shipped; the row says what remains |
| QUEUED | Accepted and waiting |
| PROPOSED | Found, not yet decided |
| DROPPED | Rejected by the owner, with the owner's reason |
| LOCAL | Valid, but belongs in a different, local or private record; the row says which |

Before you report a survey pass as complete, diff its findings against
the ledger. Every finding should appear in it. Where the ledger feeds the
issue tracker, a QUEUED or PROPOSED row becomes a `candidate` issue
under its epic.

## Red flags

- A decision or finding stated in chat with no issue or row behind it
- "Deferred" with no reason, or "blocked" with no question
- An issue whose spec lives in an unnamed comment
- About to close an issue whose premise proved wrong, without saying so
- Ending a turn with an offer to file, update or sync, with no row or draft behind it
- About to start the next task with the backlog row still stale
- A handoff written only in a report or in memory
- A rule your human partner set that is not yet in the instruction file
- Removing a ledger row because the item seemed minor
- Deleting a ledger because its contents shipped

## Rationalizations

| Excuse | Reality |
|---|---|
| "It's in the product document already" | Nobody can link to, assign or close a paragraph. File the issue. |
| "I'll record it at the end" | The end may never come. Checkpoint now. |
| "The detail is in the comments" | The next session reads titles and bodies. Point at the comment. |
| "Needs review" is clear enough | The next session will treat it as blocked on a human. Name the question. |
| "That blocker is obvious" | Read the thing it supposedly breaks. |
| "I'll just fix it and close the ticket" | Record that the premise was wrong, or the next reader repeats the mistake. |
| "I'll ask whether to file it" | Asking leaves it unrecorded. File it if filing is authorized; otherwise write the draft first, then ask once with the list. |
| "The agent will pick up the rule" | It reads the instruction file only. |
| "That finding was too small for a row" | Give it a row and propose dropping it. The owner decides. |

## Review checklist

1. Does every decision and finding from this work have an issue, under
   an epic, with a tier or a status label?
2. Does every deferral state its reason and what would reopen it?
3. Where the spec is a comment, does the issue body point at it?
4. Does every blocker name the specific question, and was the blocker
   itself checked?
5. Is every wrong premise recorded in the issue, with the body and the
   backlog row corrected?
6. Were follow-ups filed and linked, or, where filing was not authorized,
   written as local drafts and listed in one request?
7. Were the trackers current at each checkpoint, and is any handoff
   written in the issue?
8. After the merge, was every record swept, and was the list of updates
   reported?
9. Is every rule your human partner set during the work in the
   instruction file?
10. For a survey: does every finding have a ledger row with a status,
    and did any row leave other than by shipping or by the owner's drop?
