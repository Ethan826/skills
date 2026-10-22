# Ethan Kent's Agent Skills

A set of agent skills distilled from my personal side projects and
experiments, built on my own time and published under my name with an
MIT license. Each one is a plain `SKILL.md` folder, and none depends on
a particular model or harness.

Usefulness varies. Some are general habits any coding agent benefits
from; others carry opinions from specific projects and only pay off in
that kind of work. Each skill below is labelled:

- **Broad**: useful in most agent work.
- **Situational**: pays off in the right kind of task.
- **Niche**: opinionated or narrow.

## Install

The installer is [`skills`](https://github.com/vercel-labs/skills).

```bash
npx skills add Ethan826/skills --list                     # browse
npx skills add Ethan826/skills --skill agent-baseline     # one skill
npx skills add Ethan826/skills --skill '*'                # all of them
```

Add `-g` to install for your user account instead of the current
project, and `-a <agent>` to target a particular agent.

Start with `agent-baseline`. A skill loads only when its trigger fires,
so the rules every session needs (own every failure, no escape hatches,
no unrequested pushes) can't live in a skill alone. Installing the skill
copies its folder; it does not yet change what agents read. To activate
the rules, put the block into the project's always-loaded instruction
file and add the drift check to the project's checks. Ask the agent to
"install and check the agent-baseline block in AGENTS.md", or run the
script yourself from wherever the skill was installed:

```bash
SKILL=path/to/agent-baseline
"$SKILL/scripts/baseline.sh" install AGENTS.md
"$SKILL/scripts/baseline.sh" check AGENTS.md
```

[`agent-baseline`](skills/agent-baseline/SKILL.md) covers where the
check belongs and how to keep a second instruction file in step.

Some skills carry an architecture or a house style rather than a
general habit: `append-only-data-model`, `decision-core-architecture`,
`readable-functional-code` and `purescript-rows-and-newtypes`. They
govern only a project that has adopted that approach, or a request to
design or evaluate it, and their descriptions say so. Installing them
with the rest should not turn an ordinary change in another project into
a redesign. If you don't want them at all, install by name instead of
with `'*'`.

Each folder's scripts are self-contained, but some skills hand off to
others by name, and a missing one leaves that step without its detail.
The workflow skills are meant to be installed together. One dependency
is on a file: `inline-plan-execution` sends its final review out with
`requesting-review`'s `code-reviewer.md`, so install `requesting-review`
with it. It also loads `test-first`, `verify-before-claiming`,
`root-cause-debugging`, `isolated-workspaces` and `landing-a-branch` by
name. It does not need `subagent-plan-execution`.

The forks below replace their superpowers originals. Don't install both
sets in the same place: a fork and its original trigger on the same
situations and give conflicting instructions. One superpowers skill is
not forked, and the forks work alongside it:

```bash
npx skills add obra/superpowers@writing-skills
```

## The skills

### Forked from superpowers

Twelve skills adapted from Jesse Vincent's
[obra/superpowers](https://github.com/obra/superpowers) (MIT, credited in
each folder). They keep its workflow (design, plan, execute task by task,
review, land), and they tighten its rules on evidence, on delegation and
on landing a branch.

| Skill | Usefulness | What it does |
|---|---|---|
| [`verify-before-claiming`](skills/verify-before-claiming/SKILL.md) | Broad | Run the command that proves a claim before making it, and report every failure seen. |
| [`root-cause-debugging`](skills/root-cause-debugging/SKILL.md) | Broad | Find the cause before writing a fix. A test that passes on rerun is still a failure. |
| [`test-first`](skills/test-first/SKILL.md) | Broad | Write the test first for new behavior; prove a test written afterwards by putting the bug back. |
| [`requesting-review`](skills/requesting-review/SKILL.md) | Broad | Get a read-only review of a whole diff, with a three-way verdict. |
| [`receiving-review`](skills/receiving-review/SKILL.md) | Broad | Weigh review findings against the code before acting on them. |
| [`dispatching-agents`](skills/dispatching-agents/SKILL.md) | Broad | What a subagent's brief has to contain, and how to check what it reports. |
| [`design-brainstorming`](skills/design-brainstorming/SKILL.md) | Situational | Find out what is actually wanted, then write and approve a design before building. |
| [`implementation-planning`](skills/implementation-planning/SKILL.md) | Situational | Turn an approved design into small tasks with exact interfaces and tests. |
| [`subagent-plan-execution`](skills/subagent-plan-execution/SKILL.md) | Situational | Run a plan with a fresh agent and a review per task, tracked in a ledger that survives context compaction. |
| [`inline-plan-execution`](skills/inline-plan-execution/SKILL.md) | Situational | Run a plan yourself, with one review of the whole branch at the end. |
| [`landing-a-branch`](skills/landing-a-branch/SKILL.md) | Situational | Rebase and fast-forward, close out the issue, and push only with an explicit OK. |
| [`isolated-workspaces`](skills/isolated-workspaces/SKILL.md) | Situational | Set up a git worktree without touching your own uncommitted files. |

### Working rules and records

Original skills for how an agent works in any project.

| Skill | Usefulness | What it does |
|---|---|---|
| [`agent-baseline`](skills/agent-baseline/SKILL.md) | Broad | Rules every session must follow, as a block for the always-loaded instruction file, with a script to install it and check it for drift. |
| [`gate-integrity`](skills/gate-integrity/SKILL.md) | Broad | Make checks trustworthy: gates that are seen to fail, checkers with their own tests, every exemption inventoried, and stated limits. |
| [`dependency-intake`](skills/dependency-intake/SKILL.md) | Broad | Decide whether to take on a library, vendored file, agent skill or service, and how; review upgrades. |
| [`decisions-as-issues`](skills/decisions-as-issues/SKILL.md) | Situational | Keep decisions, findings and handoff state in records a reader with no memory of the conversation can trust. |

### Data and operations

Four original skills for services that store data and serve more than one
customer.

| Skill | Usefulness | What it does |
|---|---|---|
| [`append-only-data-model`](skills/append-only-data-model/SKILL.md) | Situational | Model mutable entities as immutable facts folded into current state, including erasure, ordering and per-tenant overrides. |
| [`schema-migrations`](skills/schema-migrations/SKILL.md) | Situational | Write, lock and roll out schema changes, with real rollbacks locally and roll-forward in production. |
| [`launch-readiness-audit`](skills/launch-readiness-audit/SKILL.md) | Situational | Audit readiness to launch with every row tied to code or live evidence, rechecked each pass. |
| [`multi-tenant-security-review`](skills/multi-tenant-security-review/SKILL.md) | Situational | Review tenant isolation and authorization across roles, routes and writes. Not a full security audit. |

### Design review

Original skills for work that involves algorithms, interfaces or claims
of correctness. The planning skills above invoke the first two.

| Skill | Usefulness | What it does |
|---|---|---|
| [`compose-published-primitives`](skills/compose-published-primitives/SKILL.md) | Situational | Build each algorithmic part from a published or widely used source, and flag anything invented. |
| [`adversarial-procedure-review`](skills/adversarial-procedure-review/SKILL.md) | Situational | Try to break a proposed algorithm, and the claims about it, before approving it. |
| [`public-api-argument-shape`](skills/public-api-argument-shape/SKILL.md) | Situational | Shape public signatures so a wrong call fails to compile, and gate it with an assignability check that proves itself. |
| [`proof-dossier`](skills/proof-dossier/SKILL.md) | Niche | Derive new theory statements-first, machine-check it with its axioms reported and gated, and run parallel proofs against one interface. |

### Architecture and languages

Four original skills, opinionated and narrower than the rest. One is
about architecture in any language; three are for functional code, and
two of those are for PureScript only.

| Skill | Usefulness | What it does |
|---|---|---|
| [`decision-core-architecture`](skills/decision-core-architecture/SKILL.md) | Niche | Keep a pure core of decisions under a thin shell that holds no logic. Language-neutral, but functional in outlook. |
| [`purescript-rows-and-newtypes`](skills/purescript-rows-and-newtypes/SKILL.md) | Niche | Track a PureScript function's dependencies and errors in its type. PureScript only. |
| [`purescript-gotchas`](skills/purescript-gotchas/SKILL.md) | Niche | PureScript compiler and tooling traps that cost a compile cycle to discover, pinned to the versions they were checked against. |
| [`readable-functional-code`](skills/readable-functional-code/SKILL.md) | Niche | Readability rules for functional code, with budgets and names a lint can check, plus Effect for TypeScript idioms. |

### Writing

| Skill | Usefulness | What it does |
|---|---|---|
| [`humanized-prose-review`](skills/humanized-prose-review/SKILL.md) | Broad | Audit and rewrite prose to remove AI-writing tells, ending with an editorial pass. Builds on the open-source humanizer skill (MIT, credited). Good for READMEs, PR descriptions and docs. |

## Settings the skills read from your project

The skills look in `AGENTS.md`, or the project's equivalent instruction
file, for three things.

**Where specs and plans live.** `design-brainstorming`,
`implementation-planning` and the two plan executors read one line:

```
Plans: docs/plans/      # specs and plans are committed files in this directory
Plans: issues           # the spec is an issue; the plan is a working file
```

If the line is missing, they act as if it said `issues`. The spec is then
the issue (the skills name the comment that holds it), and the plan is a
git-ignored working file under `.superpowers/plans/`. Decisions that have
to outlive the branch go in the issue.

**Whether CI costs money.** `landing-a-branch` looks for any statement
that CI or deploys are billed or expensive, such as `CI is billed per
run`. When it finds one, it commits as it goes and pushes only when you
ask.

**Who approves proof work.** `proof-dossier` reads one line naming the
approvals a formal proof effort needs:

```
Proof approvals: two                # statements before proving, dossier before adoption
Proof approvals: one (dossier)      # only the finished dossier is reviewed
Proof approvals: <named reviewer>   # that person approves in place of you
```

If the line is missing, it uses two.

## Forks and the originals they replace

Upstream superpowers skills still refer to the original names. When one
says `superpowers:subagent-driven-development`, use the fork listed
beside it here. Each fork's description also ends with the name it
replaces, so an agent can make the match.

| Fork | Replaces superpowers' |
|---|---|
| [`design-brainstorming`](skills/design-brainstorming/SKILL.md) | `brainstorming` (without its visual companion) |
| [`implementation-planning`](skills/implementation-planning/SKILL.md) | `writing-plans` |
| [`verify-before-claiming`](skills/verify-before-claiming/SKILL.md) | `verification-before-completion` |
| [`root-cause-debugging`](skills/root-cause-debugging/SKILL.md) | `systematic-debugging` |
| [`test-first`](skills/test-first/SKILL.md) | `test-driven-development` |
| [`dispatching-agents`](skills/dispatching-agents/SKILL.md) | `dispatching-parallel-agents` |
| [`subagent-plan-execution`](skills/subagent-plan-execution/SKILL.md) | `subagent-driven-development` |
| [`inline-plan-execution`](skills/inline-plan-execution/SKILL.md) | `executing-plans` |
| [`requesting-review`](skills/requesting-review/SKILL.md) | `requesting-code-review` |
| [`receiving-review`](skills/receiving-review/SKILL.md) | `receiving-code-review` |
| [`landing-a-branch`](skills/landing-a-branch/SKILL.md) | `finishing-a-development-branch` |
| [`isolated-workspaces`](skills/isolated-workspaces/SKILL.md) | `using-git-worktrees` |

## Keeping the forks in sync with upstream

Each fork's `NOTICE.md` records the superpowers commit it was last synced
with. To see what upstream has changed since then:

```bash
git clone https://github.com/obra/superpowers /tmp/superpowers
git -C /tmp/superpowers diff <pinned-commit> HEAD -- skills/<original-name>
```

The forks were rewritten rather than patched, so upstream changes can't
be applied as diffs. Port each change by hand, then update the commit in
`NOTICE.md` and `THIRD_PARTY.md`.

## License

MIT; see `LICENSE`. The forked skills and the vendored humanizer
reference are modified copies of MIT-licensed work. Each one carries the
original notice in its own `NOTICE.md`, and `THIRD_PARTY.md` lists them
all.
