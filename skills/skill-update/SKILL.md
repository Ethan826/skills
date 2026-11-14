---
name: skill-update
description: Carries out approved skill updates in a repository whose skills are anchored in anchors.json (upstream forks, vendored files, tool versions, unmodified installs), and registers new skills there. Use it whenever asked to "do the approved skill updates", to work through ticked items in the skill-drift issue, to port upstream changes into a fork, to bump a version a skill was checked against, or to move a pinned upstream commit, a NOTICE.md or a THIRD_PARTY.md row. Use it too whenever someone asks to add, write, fork or install a skill in a repository that keeps an anchors.json, or the gate reports UNREGISTERED, because every new skill there must be registered before it lands.
license: MIT
---

# Skill update

A skill that was true when it was written can go stale in three ways:
its upstream moves, the tools it describes release a new version, or an
installed copy falls behind its source. In this repository each skill's
anchor (what it was taken from, or checked against) is recorded in
`anchors.json`. A gate keeps that record consistent on every push, a
monthly job reports what moved upstream in one GitHub issue, and the owner
ticks the items to take. This skill covers what happens next: acting on
the ticked items, declining the others, and registering new skills.

```
NOTHING MOVES AN ANCHOR BEFORE ITS CHECK PASSES
```

An anchor is a claim: "this skill matches upstream at this commit", or
"every claim here holds under this version". Moving it without the check
that backs it records a claim nobody tested.

This skill points to these instead of repeating them: dependency-intake for
upgrade reviews, license checks and agent skills as dependencies;
gate-integrity for any change to a gate or a check, including its
must-fail cases; verify-before-claiming for what a green run lets you
report; landing-a-branch for landing the batch; isolated-workspaces for
the branch it is done on.

## The records

| File | What it holds |
|---|---|
| `anchors.json` | One entry per anchor, keyed by `id`, and a `declined` list. The single source. |
| `skills/<name>/NOTICE.md` | For a fork or vendored file: the first paragraph names the upstream, the 7-character commit and the release or version. |
| `THIRD_PARTY.md` | One table row per fork or vendored file, with the same commit or version. |
| A skill's `## Versions` table | For a `tool` anchor: one row per anchored package, version first. |
| `checks/<name>/` | The harness a `tool` entry names, run by `checks/<name>/run.sh`. |

The kinds, and the fields each needs (the gate rejects unknown keys):

| Kind | Fields | Used for |
|---|---|---|
| `fork` | `repo`, `path`, `commit` (40 hex), `release` | A skill rewritten from an upstream skill. |
| `vendored` | `repo`, `path`, `local`, `version`, `commit`; optional `tag` | An upstream file copied in with changes. |
| `tool` | `ecosystem`, `package`, `version`, `row`, `check` | A skill that states facts about a tool version. |
| `installed` | `repo`, `path`, `folderHash`; optional `commit`, `basis` | A third-party skill installed unmodified on the owner's machine. |
| `none` | `reason` | An original skill with nothing external to track. |

Every entry also has `id`, `skill` and `kind`. `declined` entries take one
of two shapes: `{repo, path, reason}` for an upstream skill not adopted,
and `{anchor, to, reason}` for one drift item not taken.

The commands, run from the repository root:

```bash
python3 scripts/anchors_gate.py                  # registration and consistency gate
python3 scripts/detect_drift.py --out <scratch>/drift.json  # what moved (network)
python3 -m unittest discover -s scripts          # the scripts' own tests
checks/<name>/run.sh                             # a tool entry's harness
```

Read the module docstrings of `scripts/anchors_gate.py` and
`scripts/detect_drift.py` for their rules and blind spots before relying
on a green result. The gate cannot tell whether an anchor is true, only
whether the records agree.

## Starting from the issue

1. Find the open issue: `gh issue list --label skill-drift --state open`.
   There should be one. Read it with `gh issue view <number>`.
2. Take only ticked items (`- [x]`). An unticked item is not approved,
   however small it looks. A line that says "approval cleared: target
   moved" is unticked on purpose: the owner approved a different diff.
3. Each line ends with a key comment, `<!-- key:<id> to:<to> -->`, with
   both values percent-encoded (an id can hold spaces). The `id` is the
   `anchors.json` entry; `to` is the commit (7 characters) or version the
   approval covers. If upstream has moved past it, update only as far
   as the approved target and leave the rest for the next run.
4. Do the whole batch on one branch (isolated-workspaces) and land it
   with landing-a-branch. One commit per item keeps each decision
   reviewable.

Do not edit the region between `<!-- skill-drift:start -->` and
`<!-- skill-drift:end -->` by hand; the monthly job rewrites it and reads
back only the ticks. Record decisions in comments on the issue instead.
An item leaves the issue on the first run after its anchor moves on the
default branch, or after a matching decline lands there.

## fork

A fork was rewritten rather than patched, so upstream diffs cannot be
applied. Each upstream change is a decision.

1. Clone upstream into a scratch directory, blob-less like the detector:

   ```bash
   git clone --filter=blob:none --bare https://github.com/<repo> <scratch>/up.git
   git -C <scratch>/up.git log --reverse --format='%h %s' <commit>..<to> -- <path>
   ```

   `<commit>` is the entry's anchor and `<to>` the approved target.

2. Learn the fork's deliberate departures before judging any change.
   Compare the fork with the original at the anchor
   (`git -C <scratch>/up.git show <commit>:<path>/SKILL.md`), and read
   the fork's README row, the README's "Forks and the originals they
   replace" table and the fork's `NOTICE.md`. A departure is anything the
   fork changed on purpose: a rule tightened, a section dropped, a step
   renamed.

3. Walk the commits oldest first, one at a time
   (`git -C <scratch>/up.git show <sha> -- <path>`). For each change,
   decide one of three things:
   - Port it when it applies as written, rewriting it in the fork's
     style.
   - Adapt it when the idea applies but meets a departure: keep the
     departure and take what is compatible.
   - Decline it when it conflicts with a departure or the fork already
     covers it, and say which.

4. Log the decisions as one comment on the issue, a row per change:
   upstream commit, what it changed, the decision, the reason, and where
   it landed in the fork. Use `gh issue comment <number> --body-file
   <file>`.

5. Move the anchor in three places together, in the same commit:
   - `anchors.json`: `commit` (all 40 characters, from
     `git -C <scratch>/up.git rev-parse <to>`) and `release`. For
     `release`, `git -C <scratch>/up.git describe --tags --abbrev=0 <to>`
     gives the newest tag reachable from the commit; if the commit is
     past that tag, say so in the issue comment.
   - `NOTICE.md`, first paragraph: the 7-character commit and
     `(vX.Y.Z)`. The gate parses this paragraph with a fixed grammar;
     change only those two spans.
   - `THIRD_PARTY.md`: the row's `@ <commit>`.

   Move it even when every change was declined. The anchor records how
   far upstream has been reviewed, whether or not anything was copied.

6. Run `python3 scripts/anchors_gate.py`. For a fork, the check is the
   gate plus the review in step 3; nothing else shows the port is right.

Delete the scratch clone when done.

## vendored

Walk the diff as for a fork, then do three more things.

Read the upstream license at `<to>` and run dependency-intake's license
check. If the license changed, stop and ask the owner.

Vendor at a release where you can. Detection lists the newest SemVer tag
in the item's detail ("latest release: v4.0.0"); if the approved `to` is
not a tagged commit, ask whether to use the tag instead. Record
`version`, `tag` and `commit` in `anchors.json`, and the version in
`NOTICE.md` ("version X.Y.Z") and the `THIRD_PARTY.md` row.

If the local file's name includes the version
(`references/humanizer-3.1.0.md`), rename it with `git mv` and update
`local` in `anchors.json`, the code span in `NOTICE.md`, the
`THIRD_PARTY.md` row, and every link to it from the skill
(`git grep -n -F '<old file name>'`).

Keep the modifications listed in `NOTICE.md` true. If upstream changed a
passage the local copy had replaced, decide again whether the replacement
stands.

## tool

A `tool` entry says every claim in the skill holds under that version, and
its check is what shows it.

1. Read the release notes for every version between `version` and the
   approved `to`, as in dependency-intake's upgrade section. Note each
   rename, removal and change of meaning.

2. Change the pin in the check's own files. Let the package manager write
   the lockfile, in a scratch copy of the check directory, and copy only
   the lockfile back; never edit a lockfile by hand.
   - `checks/effect-v4`: `package.json`, then `bun install` to rewrite
     `bun.lock`.
   - `checks/purescript-gotchas`: purs and spago in `package.json` and
     `bun.lock`; the package set in `spago.yaml`
     (`workspace.packageSet.registry`), then `spago install` to rewrite
     `spago.lock`. The anchored packages (prelude, quickcheck and the
     rest) come from the package set, so they move only when the set
     does. If no set contains the new version yet, leave the item for a
     later run or decline it.

3. In the same working tree, change `version` in `anchors.json` and the
   row in the skill's Versions table. Both harnesses compare their pins
   with both records and fail on any difference, so the three move
   together. "Moving the anchor" means committing that change, and the
   commit waits for step 8.

4. Pins shared between skills move together. `checks/effect-v4` checks
   every `tool` entry that names it, so an `effect` or `typescript` bump
   moves `effect-v4` and `readable-functional-code` in one change.

5. Run the check: `checks/<name>/run.sh`. Fix every failure.
   - Fix a failing claim in the skill: rewrite it to say what the new
     version does, or remove it. Leave the check as it is.
   - The must-fail controls count. In `checks/effect-v4`, the errors
     `mustfail-raw/must-fail.ts` must produce are listed in
     `expected.json` by line and code; in `checks/purescript-gotchas`,
     each case in `cases.json` lists its exact errors and quoted
     fragments. A control that changes is reviewed like any claim: update
     the expectation only when the skill's statement still holds for the
     stated reason. A "wording changed" failure means the skill quotes
     the compiler, so update the quote in the skill as well.
   - Any other change to a check, beyond its pins and expectations, is a
     gate change: follow gate-integrity, and run the check's own tests
     (`checks/effect-v4/test-run.sh`;
     `python3 -m unittest discover -s checks/purescript-gotchas -p 'test_*.py'`).

6. Record every name that changed meaning in the skill's list of names
   that are wrong in an older version (in effect-v4, "v3 names that are
   wrong in v4"), with the versions it was checked in. If the skill has
   no such list and a name changed, add one.

7. Update the version strings no gate sees: the skill's description
   and prose (effect-v4's "Checked against effect <version>"), its README
   row, and the check's `README.md`. Find them with
   `git grep -n -F '<old version>'` and read each hit; not every hit is
   this anchor.

8. Commit only after `run.sh` exits 0, the gate passes, and the check's
   own tests pass if you touched the check.

An anchor its check does not exercise (`purs-tidy`, listed in
`checks/purescript-gotchas/README.md`'s blind spots) gets a green run that
proves nothing about it. Move it after reading its release notes, and say
in the issue that no check covers it.

## installed

An unmodified third-party skill is a dependency. Its upgrade is
dependency-intake's upgrade review, with that skill's section on agent
skills: read the upstream diff on the path from the item's `from` to `to`
before anything is installed, since the text is instructions the agent
will follow.

The installed copy lives on the owner's machine, so the owner (or an
agent with the owner's explicit go-ahead) updates it with the installer
that put it there. Then record the new anchor:

- `folderHash`: the new `skillFolderHash` from `~/.agents/.skill-lock.json`.
- An entry that also records `commit` (`installed/humanizer`,
  `installed/writing-skills`): set `commit` to the installed commit, and
  `folderHash` to that commit's tree at the path
  (`git -C <scratch>/up.git rev-parse <commit>:<path>`; for a skill at
  the repository root, `<commit>:`). Detection reports the entry as
  anchor-missing when they disagree.
- `basis`: how the values were obtained, with the date.

The gate cannot compare `installed` entries with the real lock, which is
not in the repository. Copy the values; do not retype them.

## New skills

Every directory under `skills/` needs an `anchors.json` entry, or the gate
fails with `UNREGISTERED`. Register a skill in the commit that adds it.

**A skill written here.** Choose its kind:

- It states facts about a tool version (a Versions table, version-specific
  names, compiler messages): `tool`, one entry per Versions row, each
  naming a check under `checks/<name>/` with an executable `run.sh`.
  Write the check with gate-integrity: it must fail when a claim is
  false, with must-fail controls for what the skill says is rejected. A
  placeholder `run.sh` that exits nonzero with "check not built yet"
  holds the place while the check is written; it backs no claim.
- It is derived from upstream text: `fork` or `vendored`, with
  `NOTICE.md` and a `THIRD_PARTY.md` row, after dependency-intake's
  license check.
- Neither: `none`, with a one-line reason. If the prose mentions a
  version as an illustration, the reason says so (see the existing
  entries). The gate refuses `none` for a skill with a Versions section,
  a `NOTICE.md` or a `THIRD_PARTY.md` row.

Then add the README row in the right table, with a usefulness label.

**A skill new upstream** (a `new-upstream-skill/<owner>/<repo>/<name>`
item). Detection watches the `skills/` directory of each repository that
has a fork entry. The owner decides one of three things:

- fork it: write the skill, then register it as `fork` as above;
- install it unmodified: dependency-intake's selection tests, then an
  `installed` entry;
- decline it: a `declined` entry `{"repo": ..., "path": "skills/<name>",
  "reason": ...}`.

The reason is the owner's words. Do not supply one.

**An `unregistered/<skill>` item** means a skill reached the default
branch without an entry. Register it as above.

## anchor-missing

Detection could not find the anchor: the commit is not on the default
branch (a force-push), the path is missing (at the anchor, or at HEAD
for an installed entry), a `folderHash` names something other than a
tree, or an installed entry's `commit` and `folderHash` disagree. The
item's detail gives the reason. The other anchors were still
checked.

Find out what happened before changing anything, and keep the evidence:
the upstream history around the commit, the path's history
(`git -C <scratch>/up.git log --format='%h %s' --stat -- <path>`), or the
release that renamed it. Bring the evidence to the owner with a proposed
new `repo`, `path` or `commit`. A repointed anchor needs the same review as
any other move: for a fork or vendored file, walk the diff from the old
content to the new.

## Declining

Declining an item is a recorded decision, made by the owner, with the
owner's reason.

- To decline one drift item, add `{"anchor": "<id>", "to": "<to>",
  "reason": "<owner's reason>"}` to `declined`. `to` is exactly the item's target,
  decoded from the key comment (7 characters for a commit, the version
  for a tool). Detection drops the item while upstream stays at that
  target and reports it again once upstream moves past it.
- To decline an upstream skill, add `{"repo", "path", "reason"}`, as in
  New skills. It stays declined until the entry is removed.

Run the gate after editing `declined`; it checks the shape, that
`anchor` names an existing entry, and that `to` has the form detection
writes (7 lowercase hex, or SemVer for a tool). Land declines like any other change.

## Finishing

Before landing, run, one at a time:

```bash
python3 scripts/anchors_gate.py
python3 -m unittest discover -s scripts
checks/<name>/run.sh        # for each check whose pins or skill changed
```

Then land with landing-a-branch. Report per item what moved, what was
ported, adapted or declined, and which checks ran, under
verify-before-claiming. After the branch reaches the default branch, the
next monthly run (or a manual run of the `skill-drift` workflow, if the
owner asks for one) drops the finished items from the issue.

## Checklist

- [ ] Only ticked items were taken, each to the `to` its approval covers.
- [ ] Each fork or vendored change has a port, adapt or decline decision
      logged on the issue.
- [ ] `anchors.json`, `NOTICE.md` and `THIRD_PARTY.md` moved together.
- [ ] Each `tool` anchor was committed only after its check passed,
      must-fail controls included.
- [ ] Changed names are in the skill's older-version list, and the
      version strings no gate sees were updated.
- [ ] Each installed upgrade had dependency-intake's review, and its
      hash came from the lock.
- [ ] Each new skill is registered, with a check or a reason.
- [ ] Each decline records the owner's reason.
- [ ] The gate and the affected checks were run, and the branch landed
      with landing-a-branch.
