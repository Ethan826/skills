---
name: landing-a-branch
description: Lands finished work on a branch. Verifies the full check, closes out the issue and every record the change made stale, then offers your human partner a fixed menu (rebase and fast-forward onto the base locally, push and open a pull request, or keep the branch) and carries out the choice without merge commits and without any push they have not approved. Use it whenever implementation is complete and the tests pass, whenever someone says the work is done, ready, or ready to merge, ship or land, and before any push, PR, merge or branch cleanup, even when the next step seems obvious. Replaces superpowers' finishing-a-development-branch.
license: MIT
---

# Landing a Branch

## Overview

**Core principle:** Verify the check, detect the environment, close out the records, present the options, carry out the choice, clean up.

**Announce at start:** "I'm using the landing-a-branch skill to complete this work."

Two rules run through every step. History stays linear, so the base only ever fast-forwards and this skill never creates a merge commit. And nothing is pushed without your human partner's explicit OK for that particular push, because a push is the point where local, recoverable work becomes shared and starts CI runs and deploys.

## Step 1: Verify the Full Check

Run the project's full check for every platform it targets: tests, type-check, lint and build, whatever the project defines as its check (`npm test` / `cargo test` / `pytest` / `go test ./...`). A green suite on one platform says nothing about another.

**If the check fails**, report the failures and stop. The menu comes after a green check:

```
Tests failing (<N> failures). Must fix before completing:

[Show failures]
```

**If the check passes,** continue to Step 2.

## Step 2: Detect the Environment

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
# Capture now, while still inside the workspace: Step 6 changes directory
# before cleanup (Step 7) needs this value
WORKTREE_PATH=$(git rev-parse --show-toplevel)
```

The result decides which menu to show and how cleanup works:

| State | Menu | Cleanup |
|-------|------|---------|
| `GIT_DIR == GIT_COMMON` (normal repo) | Standard 3 options | No worktree to clean up |
| `GIT_DIR != GIT_COMMON`, named branch | Standard 3 options | Provenance-based (see Step 7) |
| `GIT_DIR != GIT_COMMON`, detached HEAD | Reduced 2 options (no local landing) | Externally managed: leave in place |

## Step 3: Determine the Base Branch

The base branch is the one this work forked from. The plan, the conversation or the branch's upstream usually names it. If none of them does, ask: "This branch split from <your best guess>. Is that correct?" Confirm before landing, because landing on the wrong base is expensive to undo.

## Step 4: Close Out the Records

Do this before presenting the menu, so your human partner chooses with the records already up to date. Skip the parts that don't apply: a change with no issue has no issue comment.

1. **Comment on the issue.** Walk its acceptance criteria one by one, and give the evidence for each: the test, the command and its output, the commit. Say plainly which criteria you could not verify and why. A comment that only says "done" leaves the reviewer to redo your verification. Posting it is a remote write: post it if authorized, otherwise draft it locally and include it in the one request for an OK (decisions-as-issues, "Record follow-ups instead of offering to").
2. **Read the issue state back from the tracker.** Check that the comment posted and that the state, labels and links are what you expect. Don't trust that a write landed until you have read it back.
3. **Sweep every record the change made stale.** Look at the backlog, product docs, AGENTS.md or the project's equivalent instruction file, READMEs, and related issues. Update each one, or say why it needs no change.
4. **Record out-of-scope follow-ups.** When you find work that belongs outside this branch, file the issue and link it if filing is authorized. If it is not, write a prepared issue draft or a backlog row locally, and list the drafts in one request for the OK. decisions-as-issues, "Record follow-ups instead of offering to", has the full rule. An offer with nothing written down only hands your human partner a chore.
5. **Collect the rulings list.** If a plan executor recorded rulings it made along the way, gather them for your human partner, and copy any that must outlive the branch into the issue.
6. **Retire the plan file.** If the plan lived in `.superpowers/plans/` (the working-file location used when the project keeps plans in issues), it is deleted when the branch lands: at the end of Option 1, or when the pull request merges. Options 2 and 3 keep it until then.

## Step 5: Present the Options

**Normal repo and named-branch worktree.** Present exactly these 3 options:

```
Implementation complete. What would you like to do?

1. Rebase and fast-forward onto <base-branch> locally
2. Push <branch> and open a Pull Request (<what the push and PR trigger>)
3. Keep the branch as-is (I'll handle it later)

Which option?
```

**Detached HEAD.** Present exactly these 2 options:

```
Implementation complete. You're on a detached HEAD (externally managed workspace).

1. Push as a new branch and open a Pull Request (<what the push and PR trigger>)
2. Keep as-is (I'll handle it later)

Which option?
```

Fill in what the push triggers from the project's CI configuration (`.github/workflows/` or its equivalent): which checks run on a branch push, which on a pull request, and whether anything deploys. If the configuration doesn't say, write "CI unknown". See "Pushing" below.

Present the menu as written, keeping it short and taking every option from the list above. Discarding the work happens only when your human partner asks for it explicitly (see "If your human partner asks to discard the work" below). Wait for their answer, because the integration decision is theirs.

## Step 6: Carry Out the Choice

### Option 1: Rebase and Fast-Forward onto <base> Locally

The base moves only by fast-forward, so it never gets a merge commit, and every commit on it has passed the full check. Work through these steps in order.

```bash
# 1. Fetch. Don't pull: a pull merges into whatever tree is checked out,
#    dirty or not.
git fetch origin

# 2. Rebase the branch onto the base, from the worktree.
#    Use origin/<base-branch> if the fetch shows the remote ahead and the
#    local <base-branch> has no commits of its own.
git -C "$WORKTREE_PATH" rebase <base-branch>
```

If the local base and the remote base have both moved, stop and ask your human partner which one to land on. If the rebase stops on a conflict, resolve it in the worktree, or abort with `git rebase --abort` and report.

3. **Run the full check again in the worktree,** for every platform, even after a clean rebase. A rebase without conflicts can still drop an import or leave a stale dependency list.
4. **Commit any fix in the worktree before fast-forwarding.** `merge --ff-only` moves commits, not a working tree's uncommitted edits, so a fix left uncommitted never reaches the base. Stage files by explicit path, never a directory, and before committing compare `git status --short` with the snapshot taken at the start of the session (see isolated-workspaces), so your human partner's own untracked files are left alone.
5. **Fast-forward the base:**

```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"

# If <base-branch> is checked out in the main checkout:
git merge --ff-only <feature-branch>

# If <base-branch> is not checked out anywhere:
git push . <feature-branch>:<base-branch>
```

Both commands refuse a non-fast-forward. If one refuses, the base moved after your rebase: go back to step 2. Never fall back to a plain `git merge`.

6. **Run the full check again on the base,** in the main checkout. In a normal repo with no worktree, the base isn't checked out yet: run `git checkout <base-branch>` first. Its tree is now identical to the branch tip, so the checkout changes no files.

If the check fails on the base, stop. Leave the worktree and branch in place and investigate. Nothing has been pushed, so the result is local and recoverable.

Once the base is green, delete the plan file if Step 4 calls for it, clean up the worktree (Step 7), then delete the branch:

```bash
git branch -d <feature-branch>
```

Landing locally pushes nothing. Pushing the base afterwards is a push to the base branch, and it needs its own OK (see "Pushing").

### Option 2: Push and Open a Pull Request

Choosing this option is the OK for this one push, as described in the menu. It does not cover later pushes.

```bash
git push -u origin <feature-branch>
# From a detached HEAD, name the new branch on the remote:
# git push origin HEAD:refs/heads/<new-branch>
```

Then open the pull or merge request against <base-branch> with the forge's tooling: its CLI if one is available, or the creation URL most forges print when you push. Follow the repo's PR template and conventions if it has them, and report the URL to your human partner.

Keep the worktree, because your human partner iterates on PR feedback there. Each later push of review fixes needs its own OK. When several fixes are ready, offer one push for the batch.

### Option 3: Keep As-Is

Report: "Keeping branch <name>. Worktree preserved at <path>."

### If your human partner asks to discard the work

This path exists only in response to an explicit request to throw the work away. Confirm first:

```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

Wait for that exact confirmation. When it arrives:

```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"
```

Then clean up the worktree (Step 7) and force-delete the branch:

```bash
git branch -D <feature-branch>
```

## Step 7: Clean Up the Workspace

**This runs for Option 1 and for confirmed discards.** Options 2 and 3 always keep the worktree. Both callers have already changed directory to the main repo root, since worktree removal has to run from outside the worktree, and they use the `GIT_DIR`, `GIT_COMMON` and `WORKTREE_PATH` values captured in Step 2, before that change of directory.

**If `GIT_DIR == GIT_COMMON`:** this is a normal repo with no worktree to clean up. You're done.

**If `WORKTREE_PATH` is under `.worktrees/` or `worktrees/`:** the isolated-workspaces skill created this worktree, so cleanup is yours:

```bash
git worktree remove "$WORKTREE_PATH"
git worktree prune  # Self-healing: clean up any stale registrations
```

**If removal is refused** (`contains modified or untracked files`): the worktree holds files that exist nowhere else, such as uncommitted plans, notes or scratch work. Never reach for `--force` on your own initiative. Show your human partner what is at stake and ask:

```bash
git -C "$WORKTREE_PATH" status --porcelain -uall
```

```
Worktree removal refused. These files were never committed:

<file list>

1. Commit them to <branch> before cleanup
2. Move them into <main repo root>
3. Delete them (unrecoverable)

Which?
```

Carry out the choice, then remove the worktree.

**Otherwise,** the host environment owns this workspace. Leave it in place, and use your platform's workspace-exit tool if it has one.

## Pushing

A push publishes work and can start CI runs and deploys, and none of that can be taken back the way a local commit can. CI runs can also cost your human partner money. So:

- **Defer every push when CI or deploys are billed.** If AGENTS.md (or the project's equivalent instruction file) says CI, CD or deploys cost money, are billed per run or are expensive, do not offer pushes as you go. Commit, say what is committed and unpushed, and wait until your human partner asks for a push. Batching ten commits into one push costs one run instead of ten.
- **Get an explicit OK for each push.** An earlier OK covers the push it was given for and nothing after it.
- **"Commit" means commit.** It does not mean push.
- **Name the push before offering it.** Say whether it is a branch push, a pull request, or a push to the base branch, and what CI runs and deploys it triggers, if the project's workflows say. Pushing a branch often runs little or nothing; opening a PR usually runs CI; pushing to the base may deploy.
- **Offer one push for a batch.** When several commits are ready, offer to push them together.
- **Treat drift reports as information.** A status line such as "3 commits unpushed" tells you the state. It doesn't ask you to push.
- **Don't force-push to fix a rejection.** A rejected push means the remote moved. Investigate, and force-push only when your human partner asks for it.

## Small Follow-Up Fixes

A small fix found after a branch lands (a typo, a missed rename, a one-line correction) goes in as its own commit on the next branch. It doesn't get a pull request of its own. History is what has to stay clean, and a separate commit keeps it clean; PR scope can be looser.

## Pruning Merged Branches

Delete a branch only after `git cherry` confirms its commits are on the base:

```bash
git cherry <base-branch> <branch>
```

No output, or only lines starting with `-`, means every commit has an equivalent on the base. Any line starting with `+` is a commit the base lacks, so the branch stays. A rebased branch can fail `git branch -d` even when `git cherry` is clean, because its commits were copied rather than merged. Use `-D` only once `git cherry` has shown that.

Delete the branch you just landed yourself. For bulk local cleanup, give your human partner a command to run rather than deleting in bulk yourself. This one lists the branches whose commits are all on the base:

```bash
base=<base-branch>
for b in $(git for-each-ref --format='%(refname:short)' refs/heads/); do
  [ "$b" = "$base" ] && continue
  git cherry "$base" "$b" | grep -q '^+' || echo "$b"
done
```

They review the list and delete what they choose with `git branch -D <name>...`.

## Quick Reference

| Option | Rebase + fast-forward | Push | Keep worktree | Delete branch |
|--------|-----------------------|------|---------------|---------------|
| 1. Rebase and fast-forward locally | yes | - (a later push needs its own OK) | - | yes |
| 2. Push and open PR | - | yes, this push only | yes | - |
| 3. Keep as-is | - | - | yes | - |
| Discard (explicit request only) | - | - | - | yes (force) |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Tests passed earlier this session" | Run the check on the tree you are about to land. A green run only proves the tree it ran on. |
| "It passes on one platform, so it passes" | Run every platform's full check. A pass on one platform doesn't cover the others. |
| "The rebase was clean, so the check can wait" | A conflict-free rebase can still drop an import or leave a stale dependency list. Run the full check. |
| "I'll fix it on the base after the fast-forward" | Commit the fix in the worktree first. `merge --ff-only` moves commits, not uncommitted edits. |
| "`--ff-only` refused, a normal merge will do" | Never create a merge commit. Rebase onto the moved base and run the check again. |
| "`git pull` is the quick way to update the base" | A pull merges into the checked-out tree, dirty or not. Fetch, then rebase. |
| "They obviously want it merged" | Integration is your human partner's decision. Present the menu and wait. |
| "They OK'd a push earlier" | That OK covered that push. Ask again for this one. |
| "They said commit, and pushing is the obvious next step" | Commit doesn't mean push. |
| "The status line says commits are unpushed" | That is information, not an instruction. |
| "The issue comment can just say it's done" | Walk the acceptance criteria against evidence, and name what you could not verify. |
| "I'll offer to file the follow-up" | File it and link it if filing is authorized; otherwise write the draft first, then ask once with the list. |
| "This small fix deserves its own PR" | Put it in the next branch as its own commit. History needs to stay clean; PR scope doesn't. |
| "These old branches are obviously merged" | Check with `git cherry`, and give your human partner the bulk-cleanup command to run. |
| "They seem done with this feature, so I'll offer to discard it" | The menu is complete as written. Discard happens only when your human partner asks for it in so many words. |
| "'Yeah, get rid of it' counts as confirmation" | Only the typed word `discard` authorizes deletion. |
| "The PR is up, so the worktree is clutter now" | PR feedback gets fixed in that worktree. It stays until the work lands. |
| "This other worktree looks stale, so I'll clean it too" | Clean up only worktrees under `.worktrees/` or `worktrees/`. Everything else belongs to the host. |
| "Removal was refused, and `--force` just finishes the cleanup" | The refusal means files exist only in that worktree. `--force` destroys them permanently. Show your human partner and ask. |
| "The failure on the base is probably flaky" | A failing check on the base stops everything. Branch and worktree stay put while you investigate. |
| "The base branch is obviously main" | Confirm the fork point or ask. Landing on the wrong base is expensive to undo. |
| "The push was rejected, so force-push will fix it" | A rejected push means the remote moved. Investigate, and force-push only on your human partner's explicit request. |
