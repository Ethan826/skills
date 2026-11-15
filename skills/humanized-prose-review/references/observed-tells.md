# Observed tells

This register records AI-writing tells the owner has spotted in real
drafts. A new entry takes effect on the next review, because reviewers
read it as a checklist: every entry that has no linter rule, and the
checklist question of every entry that has one. No
code change is needed to record a tell. Converting entries into linter
rules happens in batches; SKILL.md says when and how. For what to
write in place of a tell, see [good patterns](good-patterns.md).

Each entry has seven fields in this order, and `test_tell_lint.py`
checks that they are present. Observed gives the date (YYYY-MM-DD) and
the place the tell was seen. Example quotes the passage verbatim in a
blockquote. Why says what makes it read as machine-written. Rewrite
gives a better version that keeps every fact. Mechanizable is yes,
partly or no, with the reason. Status is `open`, `judgment-only`, or
`converted to` followed by rule ids in backticks; a rule whose `ref`
is an entry's number must appear in that entry's status. Checklist is
the question a reviewer asks of each paragraph. For an entry with rules,
it covers what the rules cannot see.

Record the cause of each tell (a missing actor, an undefined term, a
missing example) along with its words. A writer trained the same way
reaches for a near synonym once one phrase is caught, and a reviewer who
checks for the cause catches the synonym too.

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
> pacing function `pace`, which may change until the owner approves the
> design.

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
> protected file. Several holds can be in place at once, and the owner
> clears each kind only with its own command, such as
> `release-protected` for a Protected hold.

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
> values after the first two live tests, which run against real
> accounts, confirm their shape.

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

> Foreman has no code yet that converts the decoded values into Domain
> `Observation` values. We will write it after the first two live
> tests, which run against real accounts, confirm the shapes of those
> values.

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
> five hours and one that resets every week. Foreman will start an agent
> only when both windows have room. Codex has limits too; a live test will show
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

> After a crash or restart, foreman will read its log and continue from
> the last step it recorded.

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

> At the center of foreman are functions that only compute an answer
> from their inputs. They never read or write files or use the network,
> and they return an answer for every possible input.

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
> it to the core. It will never choose what to do next, such as whether
> to start an agent.

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

> In foreman, a core of plain functions makes every decision. A thin
> outer layer reads and writes files and runs the agents.

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

**Mechanizable:** partly. The rule matches a sentence that opens with
"For" or "To", runs at least 80 characters before its first imperative
("read", "see", "run" and a few others), and passes three or more commas
on the way. It skips "For example" and sentences whose imperative comes
early ("To build it, run make, then test, then see the log"). A shorter
lead-in, or one without commas, needs judgment.

**Status:** converted to `buried-instruction`

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
> step is interrupted midway. Foreman needs both a working resume and
> safe recovery, so we built our own supervisor.

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

> A Waxwing function can ask for only the fields it uses: `getName`
> accepts any record that has a `name` field, and the record it returns
> keeps its other fields and their types. Typing records this way is
> called row polymorphism, and it gives TypeScript programmers the
> flexibility they expect from structural types.

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

**Status:** converted to `hedged-intent`

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
today: "A function can ask for only the fields it uses. A function's
service requirements will combine the same way, so you won't have to
declare a new environment type for each combination."

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

**Status:** converted to `would-chain`

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

**Status:** converted to `passive-vague-verb`

**Checklist:** Could a reader say exactly what happens, and who does
it? Replace "accounted for", "handled" and "addressed" with the action.

### O37. Staged hypothesis with a second hedge

**Observed:** 2026-11-15, Waxwing design prose.

**Example:**

> The hypothesis is that these features can make dependencies and
> errors compose without a new environment type, error union or
> transformer stack for every combination.

**Why:** "The hypothesis is that" frames the claim instead of making
it, with an abstraction as subject and no owner. "Can" adds a second
hedge, so the reader can't tell how confident the writer is. A
hypothesis stated without its test is only a hedge. The sentence also
shows O8 ("these features"), O9 and O25 ("compose").

**Rewrite:**

> We expect inferred rows to let you call functions that need
> different services, or that fail in different ways, without writing
> any glue types to combine them. We'll test that expectation by [name
> the test].

**Mechanizable:** partly. "The hypothesis is that", "The idea is that"
and "The goal is to" are matchable as staged openers; the second hedge
needs the meaning.

**Status:** converted to `staged-claim`

**Checklist:** Is a claim framed ("The hypothesis is …") instead of
made? Does it hedge twice? Does it say how it will be tested?

### O38. Benefit stated only as what it avoids

**Observed:** 2026-11-15, Waxwing design prose (same example as O37).

**Example:**

> without a new environment type, error union or transformer stack for
> every combination.

**Why:** The reader learns what won't be needed, in another
ecosystem's jargon ("environment type", "error union", "transformer
stack" from Haskell and Effect), but not what they will be able to do.
The three terms also form a forced triad.

**Rewrite:**

> … without writing any glue types to combine them. In Haskell, each
> new combination usually means a new environment record, a new error
> union, or another layer of monad transformers.

**Mechanizable:** no.

**Status:** judgment-only

**Checklist:** Is a benefit stated only as an absence? Say what the
reader can do, and explain any outside jargon used for contrast.

### O39. Vague relational verb with a figurative object

**Observed:** 2026-11-15, Waxwing design prose.

**Example:**

> Koka, Unison and Effekt inform the effect system's lineage.

**Why:** "Inform" and "lineage" say that an influence exists without
saying what came from where. The reader can't name one idea Waxwing took
from any of the three. The three names are also never introduced (O29).

**Rewrite:**

> In Koka, a research language, a function that prints to the console
> and can throw an exception has the type `() -> <console,exn> int`.
> The `<console,exn>` part says that the function may print and may
> throw. Unison and Effekt, two other research languages, also list a
> function's side effects in its type, and so do Waxwing's types.

**Mechanizable:** partly. "inform(s) the", "shape(s) the", "lineage",
"heritage" and "DNA" are matchable as notes; whether the sentence says
what was borrowed needs the meaning.

**Status:** converted to `vague-influence`

**Checklist:** Does a verb like "inform", "shape" or "underpin" stand
where the text should say what was taken, from where?

### O40. Moralizing verb for a design decision

**Observed:** 2026-11-15, Waxwing design prose.

**Example:**

> Dependencies, expected failures, external interaction, state and
> divergence deserve precise descriptions instead of one catch-all IO.

**Why:** "Deserve" casts a design choice as a moral claim, and hides who
decides and why. The five-item subject also buries the verb (O18), and
"divergence" and "catch-all IO" are unexplained (O25).

**Rewrite:**

> A function's type will list five kinds of effect: the services it
> needs, the errors it can return, whether it reads or writes outside
> the program, whether it changes state, and whether it might run
> forever. Haskell gives all five the single type `IO`.

**Mechanizable:** partly. "deserve(s)" with a non-person subject is
matchable as a note.

**Status:** converted to `deserves`

**Checklist:** Does "deserves", "merits" or "calls for" stand in for a
decision someone made? Say who decided what.

### O41. One pronoun, different antecedents in adjacent sentences

**Observed:** 2026-11-15, Waxwing design prose.

**Example:**

> Their effect systems make different promises. Waxwing's stronger
> purity and effect-kind contracts still need design; their guarantees
> do not follow from its existing effect rows or from another
> language's proofs.

**Why:** The first "their" means the three languages from two sentences
earlier; the second "their" means the contracts. A reader who keeps the
first referent in mind misreads the second sentence.

**Rewrite:** Name the referent in each sentence: "The published proofs
for each of the three languages cover that language's own effect types
and say nothing about Waxwing's rules. We still have to write
Waxwing's rules for pure functions and for these five kinds of effect,
and prove what they guarantee."

**Mechanizable:** no.

**Status:** judgment-only

**Checklist:** When the same pronoun appears in neighboring sentences,
does it refer to the same thing both times?

### O42. Comparative with no baseline

**Observed:** 2026-11-15, Waxwing design prose (same example as O41).

**Example:**

> Waxwing's stronger purity and effect-kind contracts still need design

**Why:** "Stronger" invites the question "than what?", and the text
doesn't answer. The noun stack ("purity and effect-kind contracts") and
the stative "still need design" (O20) add to the fog.

**Rewrite:**

> We still have to write Waxwing's rules for pure functions and for
> these five kinds of effect, and prove what they guarantee.

**Mechanizable:** no.

**Status:** judgment-only

**Checklist:** Does every comparative ("stronger", "better", "simpler")
name what it is compared with?

### O43. Verb split from its object

**Observed:** 2026-11-15, the coordinator's own rewrite of O39.

**Example:**

> three research languages that record in a function's type what the
> function may do.

**Why:** A prepositional phrase ("in a function's type") sits between
the verb and its object, so the object arrives last and dangles. The
object itself ("what the function may do") is still abstract.

**Rewrite:**

> In Koka, a function that prints to the console and can throw an
> exception has the type `() -> <console,exn> int`. The `<console,exn>`
> part says that the function may print and may throw.

**Mechanizable:** no.

**Status:** judgment-only

**Checklist:** Does a phrase separate a verb from its object? Does the
sentence show a concrete instance, or only describe one?

### O44. Figurative verb for a logical relation

**Observed:** 2026-11-15, the coordinator's own rewrite of O41.

**Example:**

> The three languages guarantee different things, so Waxwing can't
> inherit their results.

**Why:** "Inherit their results" dresses a logical point (their proofs
don't apply to Waxwing's rules) as a family metaphor, and "different
things" names nothing. The "so" asserts a causal link the sentence
doesn't show.

**Rewrite:**

> The published proofs for each of the three languages cover that
> language's own effect types and say nothing about Waxwing's rules.

**Mechanizable:** no.

**Status:** judgment-only

**Checklist:** Does a metaphor ("inherit", "carry over", "build on")
stand for a logical relation the text should state plainly?

### O45. Gerunds as a parallel flourish

**Observed:** 2026-11-15, the coordinator's own rewrite of O43.

**Example:**

> the type itself lists the printing and the throwing.

**Why:** "The printing and the throwing" turns two verbs into gerund
nouns for a neat parallel. The result is vaguer than saying what the
type says, and "itself" adds emphasis with no content.

**Rewrite:**

> The `<console,exn>` part says that the function may print and may
> throw.

**Mechanizable:** partly. "the X-ing and the Y-ing" is matchable as a
note.

**Status:** converted to `gerund-pair`

**Checklist:** Has a pair of verbs been turned into "the X-ing and the
Y-ing"? Say what happens instead.

### O46. Summarizing demonstrative after a long list

**Observed:** 2026-11-15, the coordinator's own rewrite of O40.

**Example:**

> … whether it changes state, and whether it might run forever, instead
> of putting all of that under one IO type as Haskell does.

**Why:** "All of that" points back at a five-item list, so the reader
has to reassemble the list to know what "that" means. The contrast
also hides at the tail of an already long sentence.

**Rewrite:**

> A function's type will list five kinds of effect: the services it
> needs, … whether it changes state, and whether it might run forever.
> Haskell gives all five the single type `IO`.

**Mechanizable:** partly. "all of that", "all of this" and "all this"
are matchable as notes; whether the referent is a long list needs the
meaning.

**Status:** converted to `headless-summary`

**Checklist:** Does "that", "this" or "every one of these" point back
at a list or a long passage? Give the demonstrative a head noun:
either name the category before the list ("five kinds of effect: …")
and refer back with it ("all five"), or attach the noun where you
refer back ("every one of those effect types"). A demonstrative with
no head noun ("these", "those") is still a gap.

### O47. Figurative "touch" and "carry" for editing and containing

**Observed:** 2026-11-15, the coordinator's chat text.

**Example:**

> It won't touch your verbatim examples.

> since several of mine carried tells you caught

**Why:** "Touch" stands for "edit" and "carried" for "contained", so
the reader translates each verb into the action it means. "It" has no
clear antecedent (O8), and "mine" leaves the reader to supply the noun
(the rewrites). Figurative "carry" is already A1 in the additional
tells; its rule, `figurative-carry`, now matches "carried" as well.

**Rewrite:**

> The agent will not edit any entry's Example field, which quotes the
> original text exactly.

> … because you found tells in several rewrites I wrote.

**Mechanizable:** partly. "Touch" after a negative ("won't touch",
"does not touch", "never touch") is matchable as a non-blocking
finding; the rule skips physical objects such as a screen or a stove.
R8's `verb-no` rule already flags "touches no". A positive use ("the
patch touches the parser") needs judgment.

**Status:** converted to `touch-change`

**Checklist:** Does "touch", "carry" or "hold" stand where "edit",
"contain" or "record" would say what happens? Does a possessive pronoun
("mine", "yours") leave the reader to supply its noun?

### O48. Contrast tails used out of habit

**Observed:** 2026-11-15, the coordinator's chat text.

**Example:**

> …, rather than editing the file under it

> …cross-reference instead of duplicating

**Why:** Each tail says what is not done, as a beat of rhythm more than
as information. One "rather than" can be the clearest way to state a
choice; several close together read as a habit, even when each is
grammatical. "Under it" also places one file below another as
shorthand for a relation the sentence never names.

**Rewrite:** State the action, and name the alternative only when the
reader needs it to understand the choice. For the second example:
"Cross-reference the existing entry."

**Mechanizable:** partly. The `rather-than` rule (§1) already flags
each "rather than" as a weak tell. The `contrast-density` rule adds a
non-blocking finding when "rather than" or "instead of" appears twice
within 1,200 characters (about 200 words), across paragraph breaks.
Whether a given contrast helps the reader, and what a spatial word such
as "under" stands for, need judgment.

**Status:** converted to `contrast-density`

**Checklist:** Do "rather than" and "instead of" recur within a few
paragraphs? Keep the one the reader needs to understand a choice, and
elsewhere state the action alone. Does a spatial word ("under",
"behind", "on top of") stand for a relation the text should name?

### O49. Imitated expert manner

**Observed:** 2026-11-15, the coordinator's chat text.

**Example:**

> a note when the phrase repeats within a short span. That beats
> blocking every single use.

> The core failure, a term used without its real meaning, stays a
> judgment item, with two questions on the checklist

> Nothing in that section lands until you approve it.

**Why:** The writer copies the manner of someone who knows the field,
brisk and casual, and uses its terms without their meanings. The owner
compared it to a person with no medical training who talks to a doctor
in an invented quasi-medical patois that a trained ear hears as
unfamiliar. It has three parts. First, borrowed words used loosely: "a
note" and "blocking" sound like the linter's terms, but the linter
reports a blocking or a non-blocking finding, and "within a short span"
sounds like a measure without being one. "Stays a judgment item" uses
the register's status field as if it were plain English, with a
figurative "stays". "Lands" is git shop talk for "is committed" or
"is merged"; the landing-a-branch skill defines the term, but here it
appears without that definition, in a negative frame around a simple
action. Second, a casual claim that one option is better,
with no reason ("That beats", and the intensifier "every single").
Third, clipped syntax: a fragment with no main verb, and a bare "That"
with no head noun (O46).

**Rewrite:**

> The rule reports a non-blocking finding when "rather than" or
> "instead of" appears twice within 1,200 characters, about 200 words.
> It will not block a single use, because one "rather than" is often
> the clearest way to state a choice.

> No rule can reliably detect a term used without its real meaning, so
> reviewers check for it by reading, using two questions.

> I won't commit any text from that section until you approve it.

**Mechanizable:** partly. Casual claims of preference ("that beats",
"every single", "is the way to go", "a no-brainer", "wins out", "hands
down") are matchable as non-blocking findings. Whether a term has its
real meaning needs a reader who knows the field. A rule for "land" with
a subject that is not an aircraft would flag too many ordinary
sentences, so reviewers check for it by reading.

**Status:** converted to `unreasoned-preference`

**Checklist:** Does each technical-sounding term have the field's
actual meaning and, where it suggests a measure, a definite value? When
the text says one option is better, does it say why?

## Worked example: one paragraph, many tells

The owner annotated this paragraph from the coordinator's chat text on
2026-11-15. It shows how many entries can apply to one short passage.

Original:

> What that means for the register. The tells aren't random noise.
> They're fingerprints of optimizing for how prose appears at a glance.
> A register plus a linter applies counter-pressure in exactly the places
> the training pushed. It works best when it targets the underlying
> failures (the hidden actor, the missing example, borrowed jargon)
> rather than individual words, because the model will produce new
> surface variants of the same habit.

The owner's annotations, in order:

- "What that means for the register." is a label fragment with a
  headless "that" (O27, O46).
- "aren't random noise. They're" denies a view nobody stated, then
  asserts, and "random noise" is a cliché.
- "fingerprints" is a metaphor standing for a mechanism (O32).
- "optimizing for how prose appears" is a gerund abstraction with no
  actor (O10).
- "counter-pressure" and "pushed" are physics metaphors for a logical
  relation (O44), and "exactly" is an intensifier.
- "the training" is personified.
- "It" has three candidate antecedents (O8).
- "works best" is a claim with no evidence.
- "targets" is a corporate verb (O12), and "underlying" is filler.
- The parenthetical list is a forced triad.
- "rather than" is a contrast tail (O48).
- "surface variants" is pseudo-technical (O49), and "habit" is
  personified.
- The last clause is an aphoristic close that asserts an effect nobody
  measured.

Rewrite:

> The register should record why each passage reads badly, such as a
> missing actor or an undefined term, as well as the words it used. A
> rule that matches one phrase stops that phrase, but a model trained
> the same way will often reach for a near synonym: "instead of" in
> place of "rather than". A reviewer who checks for the cause catches
> the synonym too. My evidence for this claim is only the examples from
> 2026-11-15, where the same causes kept appearing in new words.
