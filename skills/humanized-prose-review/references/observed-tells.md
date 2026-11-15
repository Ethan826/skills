# Observed tells

This register records AI-writing tells the owner has spotted in real
drafts. A new entry takes effect on the next review, because reviewers
read it as a checklist: every entry whose status is open or
judgment-only, and the judgment remainder of every converted entry. No
code change is needed to record a tell. Converting entries into linter
rules happens in batches; SKILL.md says when and how.

Each entry has seven fields in this order, and `test_tell_lint.py`
checks that they are present. Observed gives the date (YYYY-MM-DD) and
the place the tell was seen. Example quotes the passage verbatim in a
blockquote. Why says what makes it read as machine-written. Rewrite
gives a better version that keeps every fact. Mechanizable is yes,
partly or no, with the reason. Status is `open`, `judgment-only`, or
`converted to` followed by rule ids in backticks; a rule whose `ref`
is an entry's number must appear in that entry's status. Checklist is
the question a reviewer asks of each paragraph. For a converted entry it
covers what the rules cannot see.

To record a tell, copy the last entry, give it the next O number, fill
in every field and set the status to `open`. Quote examples verbatim
inside blockquotes, so the linter lists them without blocking on them.

### O1. Status-label scaffolding

**Observed:** 2026-11-15, foreman docs. The owner reported these
spellings. They no longer appear in foreman's docs, so the fragments
below are quoted from the report.

**Example:**

> Headings ending in "(planned)" or "(built)"; bold `**built**` and
> `**planned**` labels before list items; "Planned, not built."

**Why:** The draft tags each part with its status instead of saying once
what exists. The labels repeat, and the reader has to collect them to
learn which parts have code.

**Rewrite:**

> Only the Domain types, the decoders and the pacing function have code
> so far. The rest of this page describes the design.

**Mechanizable:** partly. A heading that ends in a status in
parentheses, a bold status label used more than once in a document, and
"planned, not built" are exact spellings. A status word worked into a
sentence is not.

**Status:** converted to `status-heading`, `status-bold-repeat`,
`status-contrast`

**Checklist:** Is the status of the work stated once, in one place,
rather than tagged onto each part?

### O2. Container verb for code locations

**Observed:** 2026-11-15, foreman README.md and
skills/agent-baseline/SKILL.md.

**Example:**

> `src/runtime`, `src/program`, `src/facade`: will hold the Effect
> shell, the wiring and the CLI. They hold no code.

> The start marker holds the version.

**Why:** A directory or a marker is made the subject of a figurative
container verb. The sentence describes storage rather than saying what
goes where or what the thing records. In foreman "hold" is also the
domain noun for a block on launches; that noun is not the tell.

**Rewrite:**

> `src/runtime`, `src/program` and `src/facade` are empty. The Effect
> shell will go in `src/runtime`, the wiring in `src/program` and the
> CLI in `src/facade`.

> The start marker records the version.

**Mechanizable:** partly. A code span that names a path, followed by
"hold" or "holds", is exact; the rule skips "holds the lock" and the
noun. A pronoun or a plain noun as the subject ("They hold no code",
"The start marker holds") needs judgment.

**Status:** converted to `container-hold`

**Checklist:** Does any sentence say a file, directory, marker or field
"holds" something where "contains", "records" or "is where X goes"
would be plainer, including after a pronoun?

### O3. Colon-list summary sentence

**Observed:** 2026-11-15, foreman docs/how-it-works.md.

**Example:**

> The code is a first slice: the Domain types, the Format decoders for
> Claude and Codex output, the pure pacing function `pace` (provisional
> until the design is approved), and tests for them.

**Why:** A label clause comes first, then a colon, then a long list
with a parenthetical in the middle. The reader holds the label while
parsing the list, and the qualification about `pace` is buried.

**Rewrite:**

> Only part of the design has code. The Domain types and the decoders
> for Claude and Codex output are written and tested. So is the pure
> pacing function `pace`, which may change until the design is approved.

**Mechanizable:** no. A colon before a list is often right; the tell is
the label clause and the list's length together.

**Status:** judgment-only

**Checklist:** Does a sentence open with a label, then a colon, then a
list long enough that it should be its own sentences?

### O4. Abstraction or wrong thing as the subject

**Observed:** 2026-11-15, foreman docs/how-it-works.md.

**Example:**

> The numbers follow the design's list.

> A refusal or a created hold stops the attempt and consumes or expires
> the armed waiver, if any.

**Why:** In the first, an abstraction acts, and the reader cannot tell
which numbers or which list. The second is grammatically active, but the
subject is the wrong thing. The refusal does not stop the attempt; foreman does.

**Rewrite:**

> The step numbers in the diagram match the numbered steps in the
> design.

> When foreman refuses a launch or creates a hold, it stops the attempt.
> If a waiver was armed, foreman records it as used or expired.

**Mechanizable:** no. Telling the real actor from a stand-in needs the
meaning of the sentence.

**Status:** judgment-only

**Checklist:** Is each subject the thing that actually acts? Would the
sentence read better with the real actor named?

### O5. Flabby headings

**Observed:** 2026-11-15, foreman docs/how-it-works.md.

**Example:**

> \#\# One launch attempt

**Why:** The heading names a topic but states no point, so a reader
scanning headings learns nothing.

**Rewrite:**

> \#\# What foreman checks before it starts an agent

**Mechanizable:** no. Short headings are often right; whether one
states a point needs judgment.

**Status:** judgment-only

**Checklist:** Does each heading tell a reader scanning the page what
happens in the section, and why?

### O6. Permission sentence with an abstract subject

**Observed:** 2026-11-15, foreman docs/how-it-works.md.

**Example:**

> A launch is allowed only when the hold set is empty and no request is
> pending.

**Why:** The subject is an abstract noun and the verb is a passive
permission. The real actor (foreman) and the real object (the agent it
starts) are missing.

**Rewrite:**

> Foreman starts the next agent only when no hold is in place and no
> command from the owner is waiting to run.

**Mechanizable:** no. "Is allowed only when" is a common and often
correct construction.

**Status:** judgment-only

**Checklist:** Are each paragraph's subjects concrete actors or things,
and is the actor named where something is permitted or forbidden?

### O7. Stacked abstractions with unclear referents

**Observed:** 2026-11-15, foreman docs/how-it-works.md.

**Example:**

> A launch is allowed only when the hold set is empty and no request is
> pending. Holds are keyed by reason and several can exist at once. Each
> is removed only by its own release event, and one release removes
> only its own hold. Clock ticks and notifier timeouts never release any
> hold.

**Why:** "Hold set", "request", "release event" and "keyed by reason"
arrive in a row, each defined only by another abstraction. The reader
cannot map any of them to something concrete: what creates a hold, who
releases it, and with what command.

**Rewrite:**

> Foreman stops starting agents when something needs the owner's
> attention, and records why as a hold: a Failure hold when a step
> fails, for example, or a Protected hold when a step changed a
> protected file. Several holds can be in place at once, and each kind
> is cleared only by its own command, such as `release-protected` for a
> Protected hold.

**Mechanizable:** no. A regex cannot tell a defined term from an
undefined one.

**Status:** judgment-only

**Checklist:** Is each abstract term tied to something concrete (what
creates it, who acts on it, with what command) before the next one
arrives?

### O8. Unclear antecedents

**Observed:** 2026-11-15, foreman docs/how-it-works.md.

**Example:**

> Each is removed only by its own release event, and one release
> removes only its own hold.

**Why:** "Each", "its own" and "one release" point back to abstractions
that were never pinned down, so the reader has to guess what they refer
to.

**Rewrite:**

> Releasing one hold leaves the others in place: `release-protected`
> clears the Protected hold and nothing else.

**Mechanizable:** no. Finding a pronoun's antecedent needs a parse and
the meaning.

**Status:** judgment-only

**Checklist:** Does every pronoun and every "each", "its own" or "one"
have a clear antecedent in the sentence before?

### O9. Implementation jargon in prose

**Observed:** 2026-11-15, foreman docs/how-it-works.md.

**Example:**

> Clock ticks and notifier timeouts never release any hold.

**Why:** The sentence uses implementation vocabulary where plain words
work, so the reader has to translate it into what happens.

**Rewrite:**

> Waiting never clears a hold, and neither does an unanswered
> notification.

**Mechanizable:** no. Which terms count as jargon depends on the
audience.

**Status:** judgment-only

**Checklist:** Would a reader of this document use these words, or
would plain words say the same thing?

### O10. Left-branching gerund subject

**Observed:** 2026-11-15, foreman src/format/README.md.

**Example:**

> Turning the decoded values into Domain `Observation` values waits for
> L1 and L2.

**Why:** A long gerund phrase is the subject and the verb arrives at the
end, so the reader holds the whole clause before learning what the
sentence is about.

**Rewrite:**

> Foreman will convert the decoded values into Domain `Observation`
> values after live tests L1 and L2 confirm their shape.

**Mechanizable:** no. A gerund subject is often fine; the tell is its
length before the verb, which a regex cannot measure without a parse.

**Status:** judgment-only

**Checklist:** Does any sentence make the reader wait through a long
subject before the verb? Lead with the actor and the verb.

### O11. Figurative status verbs with an inanimate subject

**Observed:** 2026-11-15, foreman src/format/README.md.

**Example:**

> Turning the decoded values into Domain `Observation` values waits for
> L1 and L2.

> Wire tags live in `ClaudeEventTypes`, `ClaudeSystemSubtypes` and
> `CodexEventTypes`.

**Why:** "Waits for" means "is deferred until", and "lives", "sits" or
"holds" stands in for "is defined in" or "is stored in". The thing
cannot wait or live, so the verb is figurative and the actor is missing.
See O2 for "holds" with a code location.

**Rewrite:**

> No code converts the decoded values into Domain `Observation` values
> yet. That code comes after live tests L1 and L2 settle the shapes.

> `ClaudeEventTypes`, `ClaudeSystemSubtypes` and `CodexEventTypes`
> define the wire tags.

**Mechanizable:** no. "The supervisor waits for the lock" is literal,
and a regex cannot tell a process or person from a document or a task.

**Status:** judgment-only

**Checklist:** Does a task, file or value "wait", "live" or "sit"
somewhere? Name the actor, or say what is deferred or defined where.

### O12. Corporate verb used loosely

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> It will drive unmodified Claude Code and Codex CLIs through tranches
> of work on one repository.

**Why:** "Drive" is a business verb standing in for a plain one, like
"leverage", "power" or "orchestrate" used loosely. It says something
moves things along without saying what it does.

**Rewrite:**

> Foreman will run Claude Code and Codex, as their vendors ship them, on
> one repository, one tranche of work at a time.

**Mechanizable:** no. "Drive" is literal far more often than not (a
car, a nail, a disk), and "drive X through" has literal uses too.

**Status:** judgment-only

**Checklist:** Does a verb such as "drive", "leverage", "power" or
"orchestrate" stand where "run", "use" or "start" says what happens?

### O13. Qualifier that implies an unstated contrast

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> It will drive unmodified Claude Code and Codex CLIs through tranches
> of work on one repository.

**Why:** "Unmodified" implies a contrast with some modified version the
text never mentions, so the reader cannot tell what it rules out. The
meaning is that foreman runs the vendors' own command-line programs as
installed, with no patches or wrappers that change them.

**Rewrite:**

> Foreman will run the Claude Code and Codex command-line programs as
> installed, with no patches or wrappers that change them.

**Mechanizable:** no. Whether the contrast is stated nearby needs the
meaning of the paragraph.

**Status:** judgment-only

**Checklist:** Does an adjective such as "unmodified", "real" or
"proper" imply an alternative the text never names? Name it, or describe
what is there.

### O14. Cascade of prepositional phrases

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> It will drive unmodified Claude Code and Codex CLIs through tranches
> of work on one repository.

**Why:** Three prepositional phrases trail the clause ("through
tranches", "of work", "on one repository"), each modifying the one
before, so the reader has to work out what attaches to what.

**Rewrite:**

> Foreman will run Claude Code and Codex, as their vendors ship them, on
> one repository, one tranche of work at a time.

**Mechanizable:** no. Counting prepositions flags ordinary sentences
("the end of the list of names in the file"), and a rule that misfires
that often would be noise.

**Status:** judgment-only

**Checklist:** Does a clause end in a chain of three or more
prepositional phrases? Break it up or move the key one forward.

### O15. Passive hedge on what a tool does

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Foreman is meant to pace its launches against the user's subscription
> usage windows, start every step with fresh context, and keep durable
> checkpoints so a crash or restart does not lose its place.

**Why:** "Is meant to" is passive and hedges. It leaves open whether
the tool does the thing, will do it, or was only intended to.

**Rewrite:**

> Foreman will start each agent only when your plan's usage limits leave
> room for it.

**Mechanizable:** no. "Is meant to" also appears in honest statements
of intent, and the hedge depends on context.

**Status:** judgment-only

**Checklist:** Does the text say what the tool does or will do, rather
than what it "is meant to" or "is designed to" do?

### O16. Undefined actor

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Foreman is meant to pace its launches against the user's subscription
> usage windows, start every step with fresh context, and keep durable
> checkpoints so a crash or restart does not lose its place.

**Why:** "The user" could be anyone. The reader cannot tell that it
means the person who runs foreman.

**Rewrite:**

> Foreman will start each agent only when your Claude and Codex plans
> have usage to spare.

**Mechanizable:** no. Whether a role was defined earlier needs the
whole document.

**Status:** judgment-only

**Checklist:** Does each sentence name its actor, and is every role
("the user", "the owner", "the operator") defined once or replaced by
"you" in a README?

### O17. Noun stack

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Foreman is meant to pace its launches against the user's subscription
> usage windows, start every step with fresh context, and keep durable
> checkpoints so a crash or restart does not lose its place.

**Why:** "Subscription usage windows" piles three nouns together, and
the reader has to unpack which modifies which and what the whole names.

**Rewrite:**

> Your Claude plan limits usage over two windows, one that resets every
> five hours and one that resets every week. Foreman starts an agent
> only when both have room. Codex has limits too; a live test will show
> which windows it reports.

**Mechanizable:** no. Telling a noun from an adjective or a verb needs
a part-of-speech tagger, which this standard-library linter does not
have, and many three-noun compounds are ordinary ("source code review").

**Status:** judgment-only

**Checklist:** Does a phrase stack three or more nouns? Say what the
thing is in a clause.

### O18. Series of long verb phrases

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Foreman is meant to pace its launches against the user's subscription
> usage windows, start every step with fresh context, and keep durable
> checkpoints so a crash or restart does not lose its place.

**Why:** Three long verb phrases share one subject, and the last has
its own clause. The verbs ("pace", "start", "keep") are buried, and the
reader loses track of what governs each.

**Rewrite:**

> Foreman will start an agent only when your usage limits leave room.
> It will start every step as a new process, never by resuming an
> earlier session. It will record each step as it goes, so after a crash or
> restart it continues where it stopped.

**Mechanizable:** no. A series of verb phrases is often right; the
tell is the length of the items.

**Status:** judgment-only

**Checklist:** Does a sentence list several actions as long verb
phrases? Give each action its own sentence.

### O19. Ambiguous antecedent with an abstract referent

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Foreman is meant to pace its launches against the user's subscription
> usage windows, start every step with fresh context, and keep durable
> checkpoints so a crash or restart does not lose its place.

**Why:** "Its place" could belong to foreman, the crash or the launch.
"Its launches" uses an abstract noun for starting an agent.

**Rewrite:**

> After a crash or restart, foreman reads its log and continues from the
> last step it recorded.

**Mechanizable:** no. Resolving "its" needs the meaning of the
sentence.

**Status:** judgment-only

**Checklist:** Does every "it", "its", "this" and "that" have one
obvious, concrete antecedent?

### O20. Passive or stative status that hides the actors

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> The design is under adversarial review and is not approved.

**Why:** "Is under review" and "is not approved" state a condition but
leave out who reviews and who approves, which is what the reader needs
to know.

**Rewrite:**

> Independent reviewers are trying to break the design, and the owner
> has not approved it yet.

**Mechanizable:** no. The linter has no passive-voice rule, and "is
(not) approved" is often the right sentence (a pull request, a form).
Whether the actor matters depends on the subject, which a regex cannot
judge. Its tiers would also let such a rule block when it shares a
paragraph with another tell, which is too strong for a weak signal.

**Status:** judgment-only

**Checklist:** Where the text gives the status of a design, a change or
a request, does it say who reviews, approves or decides?

### O21. Modifier wedged into a verb phrase

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> The design is under adversarial review and is not approved.

**Why:** "Adversarial" splits "is under review" and makes the phrase
flabby. The owner treats it as a low-severity signal that the prose is
getting padded and applies it with judgment.

**Rewrite:**

> Reviewers are trying to break the design, and the owner has not
> approved it yet.

**Mechanizable:** no. Many modifiers inside a phrase are fine; this is
a matter of degree.

**Status:** judgment-only

**Checklist:** Does an adjective pad a stock phrase ("under active
consideration", "under adversarial review")? Say what the people are
doing instead.

### O22. Internal identifiers in reader-facing prose

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Four live tests (L1 to L4) have not been run.

**Why:** "L1 to L4" are labels from the design document. A reader of
the README has not seen them, so they add nothing but the sense of an
internal record.

**Rewrite:**

> No one has yet run foreman's four tests against real accounts. They
> check that it can read Claude usage and Codex usage windows, that its
> permission settings work, and that it recovers from a crash or
> restart.

**Mechanizable:** no. A pattern for short labels such as L1, S7 or
R-P3 also matches ordinary names (an M1 Mac, an S3 bucket, a P2
incident), and whether the reader knows a label depends
on the document's audience. Keep labels where the reader is already in
the design document.

**Status:** judgment-only

**Checklist:** Does reader-facing prose use a label (L1, S7, H1) the
reader has not been given? Name what it stands for, or drop it.

### O23. Passive with a hidden actor

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Four live tests (L1 to L4) have not been run.

**Why:** "Have not been run" hides who would run them. The tests need
the owner and real accounts, and the sentence never says so.

**Rewrite:**

> The owner has not yet run the four live tests with real Claude and
> Codex accounts.

**Mechanizable:** no. The linter has no passive-voice rule, and many
passives are right when the actor does not matter.

**Status:** judgment-only

**Checklist:** Does each sentence name its actor where the reader needs
to know who acts?

### O24. Status without stakes

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Four live tests (L1 to L4) have not been run.

**Why:** The sentence states a fact and stops. The reader cannot tell
what it means for them: what is unknown, and what might not work.

**Rewrite:**

> Nobody has yet tried foreman against real Claude and Codex accounts,
> so we don't know whether it can read your usage limits, whether its
> permission lockdown works, or whether it recovers from a crash.

**Mechanizable:** no. Whether a sentence states its consequence needs
the meaning of the paragraph.

**Status:** judgment-only

**Checklist:** Does each status or limitation sentence say what it means
for the reader?

### O25. Specialist terms with no signpost

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Decision-core architecture: a pure, total core of decisions with a
> thin shell around it. The CLI will convert input and make no
> decisions.

**Why:** "Pure" and "total" have exact meanings in functional
programming (no side effects; an answer for every input). The text uses
them as if the reader knows them, in a document meant to explain the
design. See "Write for the reader at this point" in SKILL.md.

**Rewrite:**

> At the center are functions that only compute an answer from their
> inputs. They never touch files or the network, and they return an
> answer for every possible input.

**Mechanizable:** no. Whether a term needs defining depends on the
reader and on what the text has already introduced.

**Status:** judgment-only

**Checklist:** Would a reader arriving at this paragraph from the top
understand every term? Define each specialist term where it first
appears, or use plain words.

### O26. Unexplained abstraction

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> The CLI will convert input and make no decisions.

**Why:** "Convert input" and "make no decisions" name categories
without their content. The reader cannot tell what input, converted to
what, or which decisions.

**Rewrite:**

> The command-line tool will turn what you type into plain data and pass
> it to the core. It never chooses what to do next, such as whether to
> start an agent.

**Mechanizable:** no. Whether an abstraction has been made concrete
nearby needs the meaning of the text.

**Status:** judgment-only

**Checklist:** Does each abstract claim come with the concrete thing it
stands for, shown before or right after it is named?

### O27. Label-colon fragment

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Decision-core architecture: a pure, total core of decisions with a
> thin shell around it.

**Why:** A label, a colon and a verbless definition stand in for a
sentence. The reader gets a glossary entry where the text should say
what the design does. A2 covers a stock set of such labels; this is
the open-ended form.

**Rewrite:**

> Foreman keeps every decision in a core of plain functions, and a thin
> outer layer does the reading, writing and running around it.

**Mechanizable:** no. A label and a colon are right in glossaries,
definition lists and forms, and a regex cannot tell those from prose.

**Status:** judgment-only

**Checklist:** Does a paragraph open with a label and a verbless
definition where a sentence would say what happens?

### O28. Instruction buried after its motivation

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> For sequence diagrams of a tranche and of a launch attempt, the hold
> states, a plain-words account of pacing, and what exists today, read
> docs/how-it-works.md. Each src/ layer has a README linked from there.

**Why:** A long "For X, Y, Z and W" phrase comes first and the
instruction comes last, so the reader holds every reason before learning
what to do. It is the imperative form of O10's left-branching sentence.

**Rewrite:**

> Read docs/how-it-works.md next. It has diagrams of one batch of work
> and of how foreman decides to start an agent, explains how pacing
> works, and lists what exists today. Each source directory has its own
> README, linked from that page.

**Mechanizable:** partly. A sentence that opens with "For" or "To",
runs through three or more commas, and then reaches an imperative such
as "read", "see" or "run" is a plausible pattern. It needs near misses
for sentences where the imperative comes early ("To build it, run make,
then test, then see the log"), so it waits for the next batch.

**Status:** open

**Checklist:** Does a sentence make the reader get through a list of
reasons before reaching the action? Put the action first.

### O29. Unintroduced proper noun

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> A disposable trial of Ralph 2.12.0 preceded this design. Its
> cooperative review routing worked, but the trial could not establish
> supported resume of a suspended primary loop or recovery of an
> interrupted operation.

**Why:** "Ralph 2.12.0" appears with no word on what it is or why it
matters to this reader.

**Rewrite:**

> Before designing foreman, we tried Ralph 2.12.0, an open-source tool
> that runs coding agents in a loop.

**Mechanizable:** no. Whether a name was introduced earlier, or is
known to the reader, needs the whole document and its audience.

**Status:** judgment-only

**Checklist:** Is every product, project or person named here
introduced where it first appears, with what it is and why it matters?

### O30. Hedge that merges different results

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> Its cooperative review routing worked, but the trial could not
> establish supported resume of a suspended primary loop or recovery of
> an interrupted operation.

**Why:** "Could not establish X or Y" merges two different results. The
resume failed outright (Ralph's resume command could not find the
paused run), and recovery was never tested. The reader cannot tell a
failure from an open question.

**Rewrite:**

> When we paused a run for usage limits, Ralph's documented resume
> command couldn't find the paused run. We never got far enough to test
> whether it recovers safely when a step is interrupted midway.

**Mechanizable:** no. Telling a failure from an untested case needs the
facts behind the sentence.

**Status:** judgment-only

**Checklist:** Does one hedge ("could not establish", "unclear
whether") cover results that differ? State each result separately:
failed, passed, or not tested.

### O31. Topic drift

**Observed:** 2026-11-15, foreman README.md.

**Example:**

> A disposable trial of Ralph 2.12.0 preceded this design. Its
> cooperative review routing worked, but the trial could not establish
> supported resume of a suspended primary loop or recovery of an
> interrupted operation.

**Why:** The grammatical subject moves from the trial to "its" routing
and back to the trial, so the paragraph has no stable topic. The same
passage also shows O13 ("disposable"), O17 and O25 ("cooperative review
routing"), O19 ("Its") and O24 (no stakes), and a nominalization
cascade ("supported resume of a suspended primary loop").

**Rewrite:**

> Before designing foreman, we tried Ralph 2.12.0, an open-source tool
> that runs coding agents in a loop. We ran it in a throwaway copy with
> fake agents standing in for Claude and Codex. Ralph passed work from
> implementer to reviewer and back correctly, as long as the agents
> followed its protocol. But when we paused a run for usage limits,
> Ralph's documented resume command couldn't find the paused run, and
> we never got far enough to test whether it recovers safely when a
> step is interrupted midway. Foreman needs both, so we built our own
> supervisor.

**Mechanizable:** no. Following the topic across sentences needs a
parse and the meaning.

**Status:** judgment-only

**Checklist:** Do the subjects of a paragraph's sentences stay on one
topic, or does each sentence start from something new?

### O32. Figurative noun for a design role

**Observed:** 2026-11-15, Waxwing design prose.

**Example:**

> Row polymorphism is the intended bridge to TypeScript's structural
> flexibility: functions can require part of a record while preserving
> the rest, and service requirements should compose without a new
> environment type for every combination.

**Why:** "Bridge" is a metaphor standing in for a mechanism. The reader
learns that two things are connected but not how, and the abstract
target ("structural flexibility") gives the metaphor nothing concrete
to land on. The same sentence shows O7 (stacked abstractions), O25 (an
unexplained specialist term) and O3 (a colon followed by a list).

**Rewrite:**

> Waxwing uses row polymorphism to give TypeScript programmers the
> flexibility they expect from structural types. A function can ask for
> only the fields it uses: `getName` accepts any record that has a
> `name` field, and the record it returns keeps its other fields and
> their types.

**Mechanizable:** no. Telling a figurative noun from a literal one needs
the meaning.

**Status:** judgment-only

**Checklist:** Does a metaphor stand where the text should name the
mechanism?

### O33. Hedged intent hiding status

**Observed:** 2026-11-15, Waxwing design prose (same example as O32).

**Example:**

> Row polymorphism is the intended bridge to TypeScript's structural
> flexibility

**Why:** "Intended" hides who intends it and whether it works today. The
reader can't tell a shipped feature from a plan.

**Rewrite:**

> Waxwing uses row polymorphism to give TypeScript programmers the
> flexibility they expect from structural types.

(Or, if it does not work yet: "Waxwing will use row polymorphism to…")

**Mechanizable:** partly. "the intended", "is intended to" and "is meant
to" are matchable; whether the text hides status needs the meaning.

**Status:** open

**Checklist:** Does "intended", "meant to" or "designed to" hide whether
the thing works today?

### O34. Mixed modality in one sentence

**Observed:** 2026-11-15, Waxwing design prose (same example as O32).

**Example:**

> functions can require part of a record while preserving the rest, and
> service requirements should compose without a new environment type
> for every combination.

**Why:** "Can" states a fact and "should" states a goal, joined as if
they were the same kind of claim. The reader can't tell which half
describes the system and which describes a hope.

**Rewrite:** Split the claim from the goal, and say which one is true
today: "A function can ask for only the fields it uses. Service
requirements will combine the same way, so nobody declares a new
environment type for each combination."

**Mechanizable:** no.

**Status:** judgment-only

**Checklist:** Does one sentence mix what is true ("can", "does") with
what is wanted ("should", "will")?

### O35. Conditional chain for a plan

**Observed:** 2026-11-15, Waxwing design prose.

**Example:**

> Planned inference would collect the row from the operations a
> function calls. Construction requirements and failures would be
> accounted for where a service is constructed. Adding a service or
> error family would no longer require copying its name through every
> caller. Explicit signatures would still limit what a function is
> allowed to do.

**Why:** Every sentence uses "would", so a plan reads as a hypothetical
and the paragraph hedges throughout. Four sentences in the same mood
also fall into the same rhythm. The passage also shows O1 and O4
("Planned inference" as status label and actor), O8 and O25 ("the row"
before any definition), O10 (gerund subject), O17 (noun stack) and O31
(a new abstract subject in each sentence).

**Rewrite:**

> We plan to have the compiler work out a function's requirements for
> you. It will look at the services and operations the function uses
> and add them to the function's type, in the part of the type called
> its row. When code constructs a service, the compiler will add that
> service's own requirements and possible errors to the constructing
> code's type. So when you add a new service or a new kind of error, you
> won't have to write its name into the type of every function that
> calls it. If you write a function's type yourself, the compiler still
> checks the body against it and rejects any service or error the type
> doesn't list.

**Mechanizable:** partly. Several consecutive sentences built on
"would" are countable; whether the text describes a plan needs the
meaning.

**Status:** open

**Checklist:** Does a plan read as a string of "would" sentences? State
it once ("We plan to …") and then use "will".

### O36. Vague verb with a hidden actor

**Observed:** 2026-11-15, Waxwing design prose (same passage as O35).

**Example:**

> Construction requirements and failures would be accounted for where a
> service is constructed.

**Why:** "Accounted for" names no action the reader can picture, and
the passive hides who does it. The reader can't tell what changes, or
where.

**Rewrite:**

> When code constructs a service, the compiler will add that service's
> own requirements and possible errors to the constructing code's type.

**Mechanizable:** partly. "accounted for", "taken care of", "handled"
and "addressed" in the passive are matchable; whether a concrete action
is named nearby needs the meaning.

**Status:** open

**Checklist:** Could a reader say exactly what happens, and who does
it? Replace "accounted for", "handled" and "addressed" with the action.
