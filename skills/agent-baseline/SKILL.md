---
name: agent-baseline
description: Ships a short block of rules that must hold in every agent session and every subagent (own every failure, no escape hatches, evidence before claims, explicit staging, no push without an explicit OK, stop on a denied tool call, cost before expensive agent work, durable records for findings, no emoji), plus a script that installs it into AGENTS.md or the project's equivalent always-loaded instruction file, checks it for drift, and keeps a second always-loaded file in sync. Use it when setting up a project for agent work, when an instruction file lacks these rules, when a subagent broke a rule it never saw, after a baseline rule changes, or when a project keeps two instruction files that must agree. Skills load only when they trigger, so rules every agent needs belong in this block rather than in a skill or in memory.
license: MIT
---

# Agent Baseline

## Overview

Skills load only when their description matches the task. Whether a
subagent also inherits memory or the conversation depends on the harness
and how it was dispatched, and many subagents get only their brief and
the project's always-loaded instruction file. So a rule that has to
hold everywhere, including in a subagent launched to fix one test, has
to live in that instruction file.

This skill ships that rule set as one marked block, and a script that
installs it, checks it and keeps copies in step. The block is short on
purpose. Each rule takes a line or two, gives its reason, and names the
skill that holds the detail.

**Core principle:** one source file, generated copies, and a check that
fails on drift.

## When to Use

- You are setting up a project for agent work.
- A project's instruction file lacks these rules, or carries an older
  version of them.
- A subagent broke a rule it was never shown.
- A rule in the block changed, and every project that carries it needs
  the new wording.
- A project keeps a second always-loaded file beside AGENTS.md, because
  one harness reads its own file and not AGENTS.md, and the two must
  agree.

Don't use this block for project-specific rules: an architecture, a
naming scheme, a test command. Those go in the same instruction file,
outside the markers, where the project can edit them freely.

## What Is in the Folder

| File | What it is |
|---|---|
| `baseline.md` | The block, between `<!-- agent-baseline:start v2 -->` and `<!-- agent-baseline:end -->`. The single source. |
| `personal.example.md` | An optional second block for one owner's preferences, with each item's default and how to change it. |
| `scripts/baseline.sh` | `install`, `check`, `sync` and `check-sync`. Bash and POSIX tools only. |
| `scripts/test-baseline.sh` | The script's tests, run in a throwaway directory. |

Read `baseline.md` before installing it. It is about 40 lines, and you
are about to make every agent in the project follow it.

## The Rules in the Block

The block states each rule briefly. The reasons, in slightly more
detail:

| Rule | Why it is in every session |
|---|---|
| Own every failure | A failure that each agent treats as someone else's is never fixed. A rerun pass, a written-down limitation and a loosened tolerance each hide a failure without removing it. |
| No escape hatches | A suppression with a confident reason attached still hides the bug it suppresses. A mistake can be fixed; a rule the agent overrides on its own judgment is a rule nobody can rely on. |
| Stricter option in coding practice | Choosing strict over partial needs no ruling from your human partner. Product trade-offs do. |
| Evidence before claims | An unverified "done" costs your human partner a review to find out. See verify-before-claiming. |
| Stage explicit paths | `git add <dir>` sweeps the user's untracked drafts into a commit. |
| No push or remote action without an explicit OK | Pushes, publications and remote issues are visible to others, can be billed, and are hard to take back. See landing-a-branch. |
| Stop on a denied tool call | A denial carries a policy. Reaching the same result another way defeats it. |
| Brief subagents as if they see only this file and their brief | Whether a subagent inherits memory or the conversation depends on the harness and how it was dispatched. A rule that reaches it only by inheritance is missing wherever inheritance is off. See dispatching-agents. |
| Cost before expensive agent work | A status question should not trigger a large unrequested sweep. |
| Durable record for findings | Findings left in chat or in an agent report are lost when the session ends. See decisions-as-issues. |
| No emoji | A word such as PASS or FAIL says the same thing, and it searches and reads the same in every tool. |

## Installing

Run the script from wherever the skill is installed. `install` puts the
block in the file, or replaces an existing copy of it, and leaves every
line outside the markers alone. Running it twice changes nothing.

```bash
SKILL=path/to/agent-baseline
"$SKILL/scripts/baseline.sh" install AGENTS.md
"$SKILL/scripts/baseline.sh" check AGENTS.md
```

If the file does not exist, `install` creates it. If the file has no
block yet, the block goes at the end, after a blank line. You can move
it nearer the top so it is read first; `install` and `check` find the
block wherever it sits.

`install` refuses to touch a file whose markers are malformed (a start
with no end, an end that names another section, the same section
twice). It reports the line and exits 2. Fix the markers by hand, then
rerun it.

### The personal block

`personal.example.md` holds preferences that belong to a person rather
than a project. Its defaults are the skill author's:

- Text published under the owner's name: facts as bullets, not drafted
  narrative, unless asked.
- Spelling: American.
- Notation: words over mathematical notation, unless the notation is
  necessary.
- Prose review: the humanized-prose-review skill.

Copy the file somewhere you keep your own configuration, edit the items
(each one carries a comment saying how), and install it as a second
block:

```bash
"$SKILL/scripts/baseline.sh" install AGENTS.md ~/dotfiles/agent-personal.md
"$SKILL/scripts/baseline.sh" check AGENTS.md ~/dotfiles/agent-personal.md
```

Install it only in projects where you are the owner. In a shared
repository, one contributor's preferences would bind everyone else's
agents.

## Checking for Drift

`check <file> [block-file]` exits 0 when the file's block matches the
block file byte for byte, version line included. It exits 1 when:

- the file does not exist;
- the file has no marked sections at all;
- the block is missing;
- the block differs in any line, including an older version marker.

On a difference it prints the diff and the `install` command that
repairs it. A failing check means the block was edited in place or the
source moved on. Either way, the fix is to reinstall, not to edit the
copy until it matches.

Run `check`, and `check-sync` if there is a second file, in the
project's authoritative check: CI where the project has CI, otherwise
the documented check command that every change must pass. Drift then
fails the same way a broken test does. For example, as one step of a
check script that CI runs:

```bash
# scripts/check.sh (illustration)
set -e
tools/agent-baseline/scripts/baseline.sh check AGENTS.md
npm test
```

A git pre-commit hook may run the same check as well, to catch drift
before a commit, but only in addition. A hook can be skipped, for
example with `git commit --no-verify`, so it is never the only place the
check runs (gate-integrity covers where a gate must live):

```bash
#!/bin/sh
# .git/hooks/pre-commit (illustration; a convenience, not the gate)
exec tools/agent-baseline/scripts/baseline.sh check AGENTS.md
```

The check needs `baseline.md` at a stable path. Either install the skill
into the project, so its folder is committed, or commit the script and
`baseline.md` together under a tools directory. The check suite should
not depend on a path in one developer's home directory.

## Two Always-Loaded Files

Some projects keep a second instruction file because one harness loads
its own file and does not read AGENTS.md. The second file needs the same
marked sections, and two hand-kept copies drift.

Treat AGENTS.md as the source and the other file as a generated copy:

```bash
"$SKILL/scripts/baseline.sh" sync AGENTS.md OTHER.md
"$SKILL/scripts/baseline.sh" check-sync AGENTS.md OTHER.md
```

`sync` copies every marked section from the source into the copy,
replacing sections already there and appending new ones. Text outside
the markers in the copy, such as harness-specific notes, stays put. If
the copy holds a section the source lacks, `sync` stops and names it,
rather than delete text you may want. Add it to the source or delete it
from the copy, then rerun.

`check-sync` exits 1 when the two files disagree: a section differs, or
appears in only one file. It also fails in two cases that a plain
comparison would pass:

- **Either file has no marked sections.** Two files that both lack every
  section compare equal, and a check that only compares them passes. A
  real drift check had exactly this bug: it passed on two empty files.
- **A pinned section is missing from either file.** `--expect` names the
  sections that must be present, comma separated, and defaults to
  `agent-baseline`. If the project syncs more sections, pin all of them:

```bash
baseline.sh check-sync --expect agent-baseline,agent-personal AGENTS.md OTHER.md
```

Without the pin, deleting a section from both files at once would pass.
With it, the check fails and names the missing section.

### Adopting it where marked copies already exist

A project may already copy sections between its instruction files under
a marker scheme of its own, checked by its own drift test. Moving to this
skill's markers (`<!-- NAME:start vN -->` and `<!-- NAME:end -->`) is a
change to what loads in every session, so make it an explicit, verified
change, never a side effect of another commit:

1. Run the project's existing drift check and confirm it passes before
   you start. If it fails, fix the drift first, as its own change.
2. In one commit that does nothing else, rewrite only the marker lines
   in both files to the new format, keeping each section's name and
   content byte for byte.
3. Prove the content did not move: for each section, extract the text
   between the old markers (from the parent commit) and between the new
   ones (from your commit), and diff them. Every diff must be empty.
4. Run `check-sync --expect` with every section name pinned, and see it
   pass. Then edit one character inside a section, see it fail, and
   undo the edit.
5. Replace the old drift test with `check-sync` in the project's check
   suite, in the same commit or the next one, so that there is never a
   commit where neither check runs.

## Versioning the Block

The start marker carries the version: `<!-- agent-baseline:start v2 -->`.
When you change the block:

1. Edit `baseline.md` in the skill, and only there.
2. Bump the version: `v2` becomes `v3`.
3. Say what changed and why in the commit message, and in the skill's
   changelog if the repository keeps one. Projects pick up the change by
   reinstalling, and a human reviews the diff, so the message should
   say what each project's agents will now do differently.
4. Run `scripts/test-baseline.sh`.
5. In each project, run `install`, then `check`, then `sync` if the
   project has a second file. Review the diff before committing it.

Any change to the text already makes stale copies fail `check`. The
version adds two things: a reader can tell which rules a project carries
without diffing, and the commit history can say what each version
added.

## The Single-Source Rule

Every copy of the block is generated from one source, and a check
catches any drift:

- The source is `baseline.md` in this skill. A project's AGENTS.md
  holds an installed copy of it.
- When a project has a second file, AGENTS.md is the source for that
  file, through `sync`.
- Nobody edits a copy. A copy edited by hand is a fork that nothing
  tracks, and the next reinstall silently erases the edit.
- Each copy has a check that fails on drift, and that check runs where
  failures already stop work.

If a project needs a rule the block lacks, add it outside the markers in
that project's file. If every project needs it, change the source and
bump the version.

## Common Mistakes

| Mistake | What to do instead |
|---|---|
| Editing the installed block to suit one project | Put project rules outside the markers. Change `baseline.md` only for rules every project needs. |
| Keeping a baseline rule only in memory or in a skill | Subagents never see either. Put it in the block. |
| A drift check that compares sections without counting them | Fail on zero sections and pin the expected names, as `check-sync` does. |
| Changing the block without bumping the version | Bump it, so stale copies fail `check`. |
| Pointing the project's check at a file in your home directory | Commit the skill or the script and `baseline.md` into the project. |
| Installing the personal block in a shared repository | Keep it to projects you own. |

## Reviewing a Setup Against This Skill

1. Does the project's always-loaded file contain the block, and does
   `check` pass on it?
2. Does `check` run in the project's authoritative check (CI where the
   project has CI, otherwise its documented check command), at a path
   that exists on every machine that runs it? A pre-commit hook does not
   count unless the same check also runs there.
3. If there is a second always-loaded file, does `check-sync` pass, run
   in the same suite, and pin every synced section with `--expect`?
4. Are project-specific rules outside the markers?
5. Was the block installed by the script, not pasted by hand?
6. If the block changed, was the version bumped and the change
   described?
7. Is the personal block, if present, in a project its owner alone
   controls?
8. If the project had its own marked copies before, was the move to
   these markers a commit of its own, with section contents diffed empty
   and the old drift check replaced without a gap?
