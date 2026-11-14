# Skill updates: drift detection and the skill-update skill

2026-11-14. Status: DRAFT for the owner's approval. Nothing is built.

## Problem

Skills here go stale in three ways:

1. **Forks of upstream skills.** Twelve skills are rewritten forks of
   obra/superpowers at `2ce8aa1`; `humanized-prose-review` carries
   blader/humanizer 3.1.0. The pinned commit lives in each `NOTICE.md`
   and in `THIRD_PARTY.md`. The README's sync section says how to diff
   by hand, but nothing notices when upstream moves.
2. **Skills that state facts about tool versions.** `effect-v4` is
   checked against effect 4.1.1; `purescript-gotchas` lists nine tool and
   package versions. A new release can make a claim false.
3. **Third-party skills installed unmodified** (`writing-skills`,
   `find-skills`, the Trail of Bits property-testing skill and others).
   Their lock lives on the owner's machine, outside this repository.

## Decisions already made

- Monthly cadence (owner, 2026-11-14).
- A scheduled job looks for drift and asks for approval before anything
  changes (owner, 2026-11-14).
- The report goes wherever is most portable (owner, 2026-11-14): a
  GitHub issue in this repository, readable and answerable from any
  device.

## Design

### Anchors

One file, `anchors.json`, records what each skill is anchored to and
the check that proves the anchor still holds. Three kinds of entry:

| Kind | Fields | Example |
|---|---|---|
| `fork` | skill, upstream repo, upstream path, commit | test-first <- obra/superpowers `skills/test-driven-development` @ `2ce8aa1` |
| `vendored` | skill, upstream repo, file, tag or commit | humanized-prose-review <- blader/humanizer 3.1.0 |
| `tool` | skill, ecosystem, package, version, check command | effect-v4 <- npm `effect` 4.1.1, check `checks/effect-v4` |

A fourth kind, `none`, is for a skill with nothing external to track
(an original skill that states no tool facts). It carries a one-line
reason.

**Every skill must be registered** (owner, 2026-11-14). A new skill
directory without an `anchors.json` entry fails the gate on push. A
skill with a "Versions" section, a `NOTICE.md`, or a row in
`THIRD_PARTY.md` cannot be registered as `none`. So adding a skill
forces a decision about how it will be kept current, and a `tool`
entry must name a check that exists. The gate decides from the
directory listing and those parsed files, not from matched prose.

`anchors.json` is the single source. A gate that runs on every push
fails when a `NOTICE.md`, `THIRD_PARTY.md` row or a skill's "Versions"
section disagrees with it. That gate gets its own must-fail fixtures.

### Detection

A script with no model calls. For each anchor:

- **fork / vendored:** a shallow, blob-less fetch of the upstream repo,
  then the commits since the anchor that touch the anchored path. Moves
  elsewhere in the upstream repo are ignored.
- **tool:** the registry's latest stable version (npm for effect and
  spago; GitHub releases for purs; the PureScript registry for package
  sets and packages). Pre-releases are ignored unless the anchor itself
  is a pre-release.

The detection also looks the other way, for skills that are new rather
than changed:

- **New upstream skills.** A skill added to a tracked upstream (for
  example, a new superpowers skill) appears as a drift item until it is
  forked, installed unmodified, or declined. The decline is recorded in
  `anchors.json` with its reason, so it is not reported again.
- **Unregistered local skills.** The push gate already blocks these. The
  monthly run repeats the check, so a skill added outside the normal
  path (a direct push, an edit on GitHub) still shows up in the issue.

Output is a list of drift items: skill, kind, from, to, and a link to the
upstream diff or release notes.

### The scheduled workflow

A GitHub Actions workflow in this repository: monthly, plus a manual
trigger. It runs the detection script, then opens one issue labeled
`skill-drift`, or updates the open one in place, with a checklist item
per drift item. Its token has `contents: read` and `issues: write` and
nothing else. Third-party actions are pinned to a commit SHA.

It never edits the repository, never runs a model and spends no Claude
or Codex allowance. Running an agent in CI would need an API key; the
owner's subscription login is for the owner's own use of the clients.

### Approval and updates

The owner ticks the items to take, in the issue. Later, in an ordinary
session, an agent asked to "do the approved skill updates" reads the
issue and works through the ticked items with the `skill-update` skill,
on a branch, landed the usual way. An unticked item stays in the issue
until upstream moves again or the owner closes it as declined, with the
reason recorded.

### The skill-update skill

What it tells an agent, by kind:

- **fork:** walk the upstream diff since the anchor change by change.
  Port, adapt or decline each one against the fork's deliberate
  departures, and log the decision per change in the issue. Then move the
  anchor in `anchors.json`, `NOTICE.md` and `THIRD_PARTY.md` together.
- **vendored:** the same walk, plus the license check from
  dependency-intake.
- **tool:** install the new version in the skill's check, run it, and fix
  every claim that fails. Record names that changed meaning in the
  skill's "wrong in an older version" list. Move the anchor only after
  the check passes, including its must-fail controls.
- **new skill, here or upstream:** register it. Choose its kind and
  write its check, or record why it has none; for an upstream skill,
  decide whether to fork it, install it unmodified, or decline it. The
  same steps apply when someone writes a new skill in this repository,
  so the skill also triggers on "add a skill".
- **third-party, unmodified:** a dependency upgrade, handed to
  dependency-intake's upgrade review.

It refers to `dependency-intake`, `gate-integrity`, `verify-before-
claiming` and `landing-a-branch` rather than repeating them.

### Checks in the repository

`checks/effect-v4/` takes the typecheck harness from the 2026-11-14
session: the block extractor, stubs, the must-fail and type controls,
the `Effect.promise` runtime check, exact pins and `bun.lock`. CI runs it
on any change to `effect-v4` or its anchor. `checks/purescript-gotchas/` is new: one
small module per claim, compiled with the pinned purs, spago and package
set, with modules that must fail where the skill says something is
rejected.

## Out of scope for the first version

- Running agents automatically on approval.

## Rulings on the former open questions (owner, 2026-11-14)

- Third-party skills installed unmodified are tracked in the first
  version. A fifth kind, `installed`, records the source repository,
  skill path and the commit or folder hash, copied by hand from the
  owner's skills lock (`~/.agents/.skill-lock.json`). Detection reports
  upstream commits that touch that path.
- `purescript-gotchas` gets a check harness in this work, not at its
  first drift item.

## Build order (after approval)

1. `anchors.json` with an entry for every existing skill, and the
   consistency and registration gate, with must-fail fixtures (a skill
   with no entry, a `none` entry on a skill with a Versions section, a
   `tool` entry whose check is missing).
2. `checks/effect-v4/`, moved from the session scratch folder, and its CI
   job.
3. `checks/purescript-gotchas/` and its CI job.
4. The detection script, with tests against recorded upstream fixtures.
5. The scheduled workflow and issue writer.
6. The `skill-update` skill, a README row and an update to the README's
   sync section.
