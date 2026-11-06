---
name: humanized-prose-review
description: Audits and rewrites prose so it reads as direct, natural writing by a person. Records every AI-writing tell, rewrites from that audit record, re-audits until nothing actionable remains, and finishes with an adversarial editorial review drawing on Garner, Fowler, Orwell, and Williams that keeps every fact and qualification. Use it whenever an agent writes or revises prose another person will read, such as plans, READMEs, explanatory docs, review notes, commit messages, and PR descriptions, and whenever someone asks to tighten, clean up, or de-AI a draft, even if they never say "humanize". Not for code, data, commands, or text whose exact wording must stay.
license: MIT
---

# Humanized prose review

This skill covers plans, READMEs, explanatory documents, review notes,
commit messages, PR descriptions, and similar writing. Leave code,
data, commands, and paths alone, and leave technical text alone when
the user wants its wording kept.

The detailed catalog of AI-writing patterns comes from Humanizer. If a
`humanizer` skill is installed, including a namespaced variant such as
`humanizer:humanizer`, and its metadata reports a version newer than
3.1.0, use it. Otherwise read the vendored [Humanizer 3.1.0
reference](references/humanizer-3.1.0.md). Its rules match upstream
3.1.0, but the examples in patterns 12 to 18 are original replacements
(see [NOTICE.md](NOTICE.md)), so they will not match an installed copy
word for word. Use Humanizer's guidance to find and remove the
patterns; this skill adds the audit record and the final adversarial
review.

Whichever Humanizer catalog you use, also read [additional
tells](references/additional-tells.md). It lists patterns found in review
that Humanizer 3.1.0 does not: figurative *carry* and *seam*, label
openers, mirrored scope pairs, forward-pointing closers, and
personified abstractions used as a payoff. Also read [researched
tells](references/researched-tells.md), which adds patterns from
published studies and practitioner reports and grades the evidence for
each.

`scripts/tell_lint.py` checks the catalog's listed phrases. Run it on
every draft; it needs only Python 3.9 or later. Judge each finding
yourself. An empty result shows only that those phrases are
absent, so the lint never replaces the audit. Add `--plain` when the
target is plain text, such as a commit message.

## Required workflow

1.  Read the whole source text before editing it.
2.  If the user supplies a writing sample, read it first and match its
    sentence length, word choice, punctuation, openings, transitions, and
    deliberate quirks. The sample overrides the generic cleanup rules,
    including the preference against dashes.
3.  Audit the text. For each issue, record:
    - the exact passage;
    - the pattern or tell;
    - why it weakens this text or makes the reader work harder.
4.  Rewrite from the audit record. When a paragraph's main point is buried,
    restructure the paragraph instead of patching single phrases.
5.  Audit the rewrite for tells that survived and for new problems, and
    fix them. Repeat until nothing actionable remains or the loop stops. For prose that
    matters, such as a README or a published piece, do this with the
    [clean-read loop](references/clean-loop.md): a new auditor each
    round, a fixed definition of clean, and a script that decides when to
    stop. Only the user can exempt a finding that blocks the loop. Then read the result through at speaking pace; some rhythm
    problems show up only that way.
6.  Run a final adversarial editorial review. Challenge the draft with
    the clear-style and usage principles of Bryan A. Garner, H. W.
    Fowler, George Orwell, Joseph M. Williams, and comparable
    authorities. Look for ambiguity, wordiness, unsupported claims,
    grammatical errors, needless abstraction, jargon, inconsistency, and
    anything likely to mislead this audience. Check subject-verb
    agreement, modifiers, pronoun reference, parallelism, tense,
    punctuation, word choice, and the order of sentences and
    paragraphs. Do not imitate an authority's voice or invent
    quotations or attributions, and do not change a deliberate voice
    choice merely to suit taste.
7.  Apply only the changes that make the text clearer, more correct,
    more precise, or easier to follow. Then confirm that the final
    version keeps every supported fact, name, number, date, quote,
    qualification, technical distinction, and citation, and every
    intentional part of the writer's voice. If a sentence needs a detail
    you do not have, ask for it or write a simpler sentence; an invented
    detail is an error even when it reads well.

## What to look for

Check the shape of each paragraph as well as each sentence:

- not-X-but-Y contrasts that need no contrast, and arguments against a
  view nobody holds;
- staged openings, filler, dramatic fragments, repeated one-line
  conclusions, and shallow explanations tacked onto examples;
- forced triads, repeated sentence openings, and sentences built around
  dashes;
- stacked qualifiers, vague connections, passive voice, missing actors,
  and needless nominalizations;
- inflated significance, sales language, borrowed authority, vague
  jargon, and abstract claims that never say how two things relate;
- stock AI vocabulary, decorative bold labels, and formatting that adds
  no information;
- figurative *carry* and *seam*, label openers ("One gap:"), mirrored
  scope pairs, forward-pointing closers, and abstractions personified
  for a clever ending (see the additional tells);
- participial clauses, nominalization chains, long sentences joined by
  *and*, Claude's stock phrases and word swaps, the edit-summary formula
  in commit messages, and absent specifics (see the researched tells).

At the document level, look for closers or openings repeated across
sections, a heading restated in its first sentence, narration about the
document instead of its subject, and a reply that re-explains context
the reader already supplied. Every sentence that stays should add
information, a needed qualification, or a deliberate choice of voice.

Keep a contrast when both halves matter or when the negative half
corrects a belief the reader holds. Keep uncertainty that
records a real limit. Keep technical hyphens, dashes, code, paths, and
URLs that belong to the source or its syntax.

## Detectors

You can skip the detector. If you use one, run it once after the loop
ends clean, and never rewrite to lower a score. `scripts/detect.py` can run
with a local open-source detector, a hosted one, or none. A hosted
detector sends the text to a third party, so get the user's approval for
each document first. See [detectors](references/detectors.md) for setup,
licenses, and calibration.

## Editing an author's own draft

When the user wrote the text and will publish it under their name, most
tells enter through the sentences you add.

- Make the smallest change inside the author's sentence instead of
  adding a sentence of your own.
- When the author supplies wording, use it as written; fix only typos and
  mechanics.
- For a gap the author has not written, offer a short brief unless they
  ask for prose: what the sentence must claim, what it must not
  overclaim, and the evidence. An author can write a sentence from
a brief faster than repair a drafted paragraph.
- Screen review comments, outline bullets, and commit messages too.
  Outline bullets become the author's prose.
- When the author flags a new tell, add it to the additional tells so the
  next session catches it.

## Output

For pasted prose, return the audit record and then the final rewrite,
unless the user asks for the rewrite alone. For long text, add a short
note on any patterns left in on purpose or still weak.

For a named file, apply the workflow to its prose and leave code blocks,
inline code, commands, paths, YAML metadata, data, and link targets
unchanged. Write only the final prose to the file, then give the user a
short summary. For embedded text such as a PR description or commit
message, return only the final text, unless the surrounding task has a
place for the audit record.

## Keep a record of the review

A review that leaves no record has to be repeated by the next reviewer,
who cannot tell what was already checked. When the prose lives in a
repository, record the review where it survives:

- In the commit that applies the rewrite, give the ten or so most
  significant audit entries in the body, one line each: the pattern and
  what changed. A reviewer can then check the rewrite against its reasons.
- For a document that is reviewed repeatedly, such as a README or a
  policy, keep the patterns deliberately left in (and why) in a short note
  beside it or in the project's instruction file, so the next pass does
  not undo them.
- When an agent you dispatched did the review, ask it to return the
  audit record in its report, and check the rewrite against it before you
  accept it.
- Keep the audit record out of the prose itself.
