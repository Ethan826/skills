---
name: isolated-workspaces
description: Sets up an isolated workspace before feature work. It detects isolation that already exists, prefers the harness's native worktree tool, and falls back to a git worktree in an ignored directory. It then snapshots the working tree for safe staging, checks that the new worktree starts at the intended base, installs dependencies and runs a clean baseline. Use it whenever you start feature work, a bug fix or a plan execution that should not touch the current checkout, before dispatching agents that need their own copy of the repo, and whenever you are unsure whether you are already in a worktree. Replaces superpowers' using-git-worktrees.
license: MIT
---

# Isolated Workspaces

## Overview

Make sure work happens in an isolated workspace. Prefer a native worktree tool or command, if your harness has one, and fall back to a manual git worktree only when it doesn't.

**Core principle:** Detect existing isolation first. Then use the native tool. Then fall back to git. Never fight the harness.

**Announce at start:** "I'm using the isolated-workspaces skill to set up an isolated workspace."

## Step 0: Snapshot and Detect Existing Isolation

**Snapshot the working tree first.** At the start of the session, before you change anything, record the output of:

```bash
git status --short
```

Keep it in your notes or in a scratch file outside the repo. Stage files by explicit path, never a directory, and before committing compare `git status --short` with this snapshot, so your human partner's own untracked files are left alone.

**Before creating anything, check whether you are already in an isolated workspace.**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**Submodule guard:** `GIT_DIR != GIT_COMMON` is also true inside a git submodule. Before concluding that you are already in a worktree, check that you are not in a submodule:

```bash
# If this returns a path, you're in a submodule, not a worktree: treat as normal repo
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**If `GIT_DIR != GIT_COMMON` (and not a submodule):** you are already in a linked worktree. Skip to Step 2 (Project Setup), and don't create another worktree.

Report the branch state:
- On a branch: "Already in isolated workspace at `<path>` on branch `<name>`."
- Detached HEAD: "Already in isolated workspace at `<path>` (detached HEAD, externally managed). Branch creation needed at finish time."

**If `GIT_DIR == GIT_COMMON` (or in a submodule):** you are in a normal repo checkout.

Has your human partner already stated a worktree preference in your instructions? If not, ask before creating a worktree:

> "Would you like me to set up an isolated worktree? It protects your current branch from changes."

Honor a preference they have already declared without asking. If they decline, work in place and skip to Step 2.

## Step 1: Create the Isolated Workspace

**There are two mechanisms. Try them in this order.**

### 1a. Native Worktree Tool (preferred)

Your human partner has agreed to an isolated workspace (Step 0). Check whether your harness gives you a native worktree tool or command: a dedicated worktree tool, a `/worktree` command or a `--worktree` flag, for example. If it does, use it and go on to the base check below.

A native tool handles directory placement, branch creation and cleanup itself. Running `git worktree add` when one exists creates phantom state that your harness can't see or manage.

Go to Step 1b only if no native worktree tool is available.

### 1b. Git Worktree Fallback

**Use this only if Step 1a does not apply,** because no native worktree tool is available. Create the worktree by hand with git.

#### Directory Selection

Follow this order of priority. An explicit preference from your human partner always beats what you find on the filesystem.

1. **Check your instructions for a declared worktree directory.** If your human partner has named one, use it without asking.

2. **Check for an existing project-local worktree directory:**
   ```bash
   ls -d .worktrees 2>/dev/null     # Preferred (hidden)
   ls -d worktrees 2>/dev/null      # Alternative
   ```
   If you find one, use it. If both exist, `.worktrees` wins.

3. **If nothing else guides you,** default to `.worktrees/` at the project root.

#### Safety Verification (project-local directories only)

**Verify that the directory is ignored before creating the worktree:**

```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**If it is not ignored,** add it to .gitignore, commit that change, then go on. An unignored worktree directory lets the worktree's whole contents be committed into the repository by accident.

#### Create the Worktree

```bash
# Determine path based on chosen location
path="$LOCATION/$BRANCH_NAME"

git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

**Sandbox fallback:** if `git worktree add` fails with a permission error (a sandbox denial), tell your human partner that the sandbox blocked worktree creation and that you are working in the current directory instead. Then run setup and the baseline tests in place.

### Check the Starting Commit

A newly created worktree, from a native tool or from git, may start at the default branch rather than the branch you meant to work from. Check before you start:

```bash
git log -1 --oneline
```

If that is not the intended base, reset the new worktree to it. The worktree holds no work yet, so nothing is lost:

```bash
git reset --hard <intended-base>
```

Run this only in a worktree you just created and have not worked in.

## Step 2: Project Setup

Detect the project type and run the matching setup:

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
if [ -f pyproject.toml ]; then poetry install; fi

# Go
if [ -f go.mod ]; then go mod download; fi
```

## Step 3: Verify a Clean Baseline

Run the tests to make sure the workspace starts clean:

```bash
# Use project-appropriate command
npm test / cargo test / pytest / go test ./...
```

**If tests fail:** report the failures and ask whether to proceed or investigate.

**If tests pass:** report that the workspace is ready.

### Report

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Workspaces You Don't Own

**A long-lived scratch worktree belongs to the host.** Your human partner may keep a worktree for experiments that outlives any one branch. Never clean it up or remove it. When a test needs a particular commit, point the scratch worktree at that commit (`git -C <scratch-worktree> checkout --detach <commit>`) instead of creating a new one.

**Copies made for agents go in scratch space, without build caches.** When an agent needs its own copy of the repo rather than a worktree, put the copy in the harness's scratch or temporary directory, not inside the repo. Leave out build caches and build output (compiler caches, `target/`, `dist/`, `.cache/` and the like). They are often the largest part of a checkout, and the agent can rebuild what it needs.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Session start | Snapshot `git status --short` (Step 0) |
| Already in linked worktree | Skip creation (Step 0) |
| In a submodule | Treat as normal repo (Step 0 guard) |
| Native worktree tool available | Use it (Step 1a) |
| No native tool | Git worktree fallback (Step 1b) |
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check instruction file, then default `.worktrees/` |
| Directory not ignored | Add to .gitignore + commit |
| Permission error on create | Sandbox fallback, work in place |
| New worktree at the wrong commit | `git reset --hard <intended-base>` before any work |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |
| Host's long-lived scratch worktree | Never clean up; check out the commit you need |
| Copy for an agent | Scratch space, no build caches |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'm obviously not in a worktree, so there's no need to check" | Run Step 0. Harness-created isolation and submodules both fool a glance; the detection commands settle it. |
| "`git worktree add` is quicker than hunting for a native tool" | A native worktree tool owns placement, branching and cleanup. Bypassing it is the most common mistake here, and it creates phantom state your harness can't see or manage. |
| "The worktree directory is surely ignored already" | Run `git check-ignore`. An unignored worktree directory commits the whole tree into the repo. |
| "Any directory name works" | Explicit instructions beat an existing project-local directory, which beats the `.worktrees/` default. |
| "The new worktree is on the right branch, surely" | Check `git log -1`. A new worktree may start at the default branch. |
| "`git add .` is fine, it's my worktree" | Stage by explicit path and compare with the session-start snapshot. Your human partner's untracked files are not yours to commit. |
| "That scratch worktree looks abandoned" | A long-lived scratch worktree belongs to the host. Leave it, and point it at the commit you need. |
| "Copying the whole directory is simplest" | Build caches are often most of the size. Leave them out, and put the copy in scratch space. |
| "The workspace is fresh, so baseline tests can wait" | A dirty baseline makes every later failure ambiguous. Run the tests now; proceeding past failures is your human partner's call. |
