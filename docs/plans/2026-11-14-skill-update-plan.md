# Skill updates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-plan-execution (recommended) or inline-plan-execution to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record what every skill here is anchored to, gate that record on every push, move the Effect v4 typecheck harness into the repository, build a PureScript claim harness, detect drift monthly into one GitHub issue, and write the `skill-update` skill that acts on approved items.

**Architecture:** `anchors.json` at the repository root is the single source. A stdlib-only Python gate (`scripts/anchors_gate.py`) parses the skill directories, `anchors.json`, every `NOTICE.md`, the `THIRD_PARTY.md` table and each skill's `## Versions` table, and fails on any disagreement. Two harnesses under `checks/` back the tool-version claims, each behind a `run.sh` that works in a throwaway directory. A detection script with injected sources (network in production, recorded fixtures in tests) produces drift items; an issue writer turns them into one `skill-drift` issue, updated in place. Three GitHub workflows run the gate and harnesses on push and PR, and detection monthly.

**Tech Stack:** Python 3.9+ stdlib with `unittest` (gate, detection, issue writer, PureScript runner); bash (`run.sh` entry points and harness tests, as in `skills/agent-baseline/scripts`); bun 1.3.6 with TypeScript 5.9.3, effect 4.1.1, @effect/vitest 4.1.1, vitest 5.1.0 (Effect harness, as already locked); purs 0.15.16, spago 1.0.4, registry package set 81.0.0 (PureScript harness); `git` and `gh` CLIs; GitHub Actions on `ubuntu-24.04`.

**Spec:** `docs/plans/2026-11-14-skill-update-design.md` (commit d940162). Its status line still reads "DRAFT for the owner's approval"; the commit message and the caller say approved. Task 6 does not edit the design, so fix the status line only if the owner asks.

**Why Python for the gate and detection:** the repo's only tested scripts in a general-purpose language are `skills/humanized-prose-review/scripts/*.py`, stdlib-only and run with `python3 -m unittest discover -s scripts`. Python parses JSON without dependencies, runs on the stock macOS python3 (3.9.6 here) and on the Actions runner without a setup action, and so adds no third-party action to pin. Bash (the agent-baseline convention) cannot parse JSON or Markdown tables without `jq` or worse. TypeScript under bun would need a lockfile and a setup action for the gate. Code must run on Python 3.9: no `match`, no `X | Y` in runtime annotations (use `from __future__ import annotations`).

## Global Constraints

- Cadence: monthly scheduled run, plus a manual trigger (design, "Decisions already made").
- The scheduled job never edits the repository, never runs a model, and spends no Claude or Codex allowance.
- Drift workflow token: `permissions: contents: read` and `issues: write`, nothing else. The push/PR workflows: `contents: read` only.
- Every third-party action is pinned to a full 40-character commit SHA, with the tag in a trailing comment.
- One open issue labeled `skill-drift`, updated in place; runs are idempotent (same detection result and same issue state: no API write).
- `anchors.json` is the single source; `NOTICE.md`, `THIRD_PARTY.md` rows and `## Versions` tables must agree with it.
- Every directory under `skills/` is registered. `none` is refused for a skill with a `## Versions` section, a `NOTICE.md`, or a `THIRD_PARTY.md` row. A `tool` entry names a check that exists.
- The gate decides from parsed files, never matched prose; every gate carries the gate-integrity standard block.
- Detection is testable offline against recorded fixtures; network only in the scheduled (or manually triggered) run.
- Kinds: `fork`, `vendored`, `tool`, `installed`, `none`. Declines of upstream skills are recorded in `anchors.json` with a reason.
- Pins exact; lockfiles committed (`bun.lock`, `spago.lock`). Effect harness: effect 4.1.1, @effect/vitest 4.1.1, vitest 5.1.0, typescript 5.9.3. PureScript harness: purs 0.15.16, spago 1.0.4, package set 81.0.0, and the package versions in `skills/purescript-gotchas/SKILL.md` "Versions".
- Local disk is tight (about 10 to 13 GB free). Every install goes into a `mktemp -d` work directory removed on exit, with bun's and spago's caches pointed inside it. No global installs. Record `du -sh` of the work directory once per harness in the task report.
- Stage explicit paths only; never `git add <dir>`, `-A` or `.`. Compare `git status --short` with the session-start snapshot before each commit (the owner keeps untracked `*.local.md` files at the root).
- No push without the owner's explicit OK. No merge commits.
- New prose uses American spelling. README and SKILL.md prose gets a humanized-prose-review pass.
- If a tool call is denied, stop that line and report it.

## Provenance

- Registration and consistency gate: structural checks over parsed JSON and Markdown (CommonMark fenced-code and table rules), faithful to gate-integrity's standard block. No novel algorithm.
- Fork drift: `git log <anchor>..<head> -- <path>` over a blob-less clone (git's own range and pathspec semantics), faithful.
- Installed drift: comparison of git tree object IDs (`git rev-parse <commit>:<path>`) against the lock's `skillFolderHash`, faithful to git's object model, **provided** `skillFolderHash` is the git tree ID of the skill folder. Task 4 Step 1 verifies that before anything relies on it.
- Latest stable version: Semantic Versioning 2.0.0 precedence (semver.org, section 11), pre-releases excluded unless the anchor is one. Faithful; implemented in stdlib in about 30 lines, with tests from the spec's own examples.
- Issue reconciliation: keyed upsert of checklist lines by an HTML-comment key. Routine; no source needed.

## Review Focus

1. A skill directory added with only a `README.md` and no `SKILL.md`, or a stray file under `skills/`: the gate must fail with a named message, not skip it (Task 1, `test_directory_without_skill_md_fails`).
2. Upstream force-push or a deleted anchor commit (`git log` exits non-zero on an unknown revision): detection must emit an item of kind `anchor-missing` for that anchor and keep going with the others, never crash the run or drop the anchor silently (Task 4, `test_unknown_anchor_commit_reports_anchor_missing`).
3. The owner edits the issue body by hand (adds a note, reorders lines): the writer must keep text outside its marked region and keep tick state by key (Task 5, `test_text_outside_region_survives` and `test_reordered_lines_keep_ticks`).
4. Registry or GitHub API unavailable or rate-limited mid-run: the run must fail visibly (non-zero exit, nothing written to the issue) rather than post a partial "no drift" body that would close the issue (Task 5, `test_source_error_writes_nothing`).
5. A `## Versions` heading inside a fenced code block, or a near-miss heading such as `## Versioning the Block` (agent-baseline has exactly this): neither counts as a Versions section (Task 1, spelling and near-miss probes).

---

## Design questions this plan had to settle

Each is a choice made here, not a ruling. The owner should confirm or overrule them at plan review; the tasks name where each lands.

- **D1 `writing-skills` has no lock entry.** The design lists it as third-party, installed unmodified, and the README installs it from `obra/superpowers@writing-skills`, but `~/.agents/.skill-lock.json` has no entry for it and no plugin record was found. Task 1 cannot copy a folder hash. Proposal: register it as `installed` from `obra/superpowers`, path `skills/writing-skills`, anchored to commit `2ce8aa1` (the commit the forks track) with `"anchorBasis": "assumed; no lock entry"`. Owner to confirm or supply the installed copy.
- **D2 `installed` anchors are tree hashes, not commits.** The lock records `skillFolderHash`. Detection compares it with the tree at upstream HEAD and, on a difference, finds the newest upstream commit whose tree matches, to give a "since" for the commit list. Depends on the Task 4 Step 1 verification.
- **D3 Which `installed` skills.** From the lock: `find-skills` (vercel-labs/skills), `property-based-testing` (trailofbits/skills), `react-native-best-practices` (callstackincubator/agent-skills), `humanizer` (blader/humanizer). The 28 entries from `Ethan826/skills` are this repository and are excluded. `ynab-budget` (in `~/.claude/skills`, not in the lock) and the superpowers plugin skills are not tracked.
- **D4 New-upstream-skill detection covers only `obra/superpowers`**, the one upstream with forks. Watching every skill added to `trailofbits/skills` or `vercel-labs/skills` would be noise. The first run would otherwise report every superpowers skill neither forked nor installed (for example `using-superpowers`); Task 1 lists them at `2ce8aa1` and asks the owner for each decline reason before writing `declined` entries.
- **D5 effect-v4's Versions section is prose.** A gate cannot read it without matching prose. Task 1 adds a table at the top of that section (`| Tool or package | Version |`, as purescript-gotchas has) and keeps the prose. This edits a published skill.
- **D6 Every `tool` entry needs a Versions table row.** The design says the gate fails when a Versions section disagrees; this plan also requires that each `tool` entry's skill state that version in a Versions table, in both directions. So `readable-functional-code` (whose `typescript.md` blocks the Effect harness compiles against effect 4.1.1 and TypeScript 5.9.3) gets a short `## Versions` section in its `SKILL.md`. Its `tool` entries point at `checks/effect-v4`, whose name is the design's.
- **D7 What effect-v4 anchors.** One `tool` entry per Versions row: `effect`, `@effect/vitest`, `typescript`. `vitest` 5.1.0 is in the harness lockfile as a peer, but the skill states no claim about it, so it is not anchored. The skill also mentions effect 3.19.15 in another section; that is a historical reference, not an anchor.
- **D8 `purs-tidy` 0.11.1** is in purescript-gotchas' Versions table but no claim in the skill concerns it. It is anchored (`tool`, npm) so detection reports it, and its harness does not exercise it. The `check` for that entry is the same `checks/purescript-gotchas`; the gap is listed in the harness's blind spots.
- **D9 Commits are stored in full.** `anchors.json` stores 40-character SHAs; `NOTICE.md` and `THIRD_PARTY.md` keep the 7-character form, and the gate requires it to be a prefix. Fork entries also carry `release` (`v7.0.1`), which the gate compares with the NOTICE.
- **D10 NOTICE.md is parsed with a fixed grammar.** NOTICE files are prose. The gate parses the first paragraph after the `# Notice` heading into its inline code spans and links, in order, and requires the exact sequence for its kind (fork: code span `<upstream skill name>`, link `[owner/repo](https://github.com/owner/repo)`, code span `<short sha>`, then `(vX.Y.Z)`; vendored: code span `<local file>`, link, then `version X.Y.Z`). A first paragraph that does not fit the grammar fails as unparseable. All 13 current NOTICE files fit it (checked by reading them).
- **D11 Blob-less, not shallow.** The design says "a shallow, blob-less fetch". A shallow clone of fixed depth may not contain the anchor, and `git log anchor..HEAD -- path` then fails. Detection uses `git clone --filter=blob:none --no-checkout --bare`; history is complete, blobs are not fetched. obra/superpowers is small.
- **D12 Tick state across moves.** The issue key is the anchor `id`. When an item's target (`to`) changes between runs, its tick is cleared and the line notes the old target, because an approval covered a specific diff. Owner to confirm.
- **D13 Declining a drift item.** The design says an unticked item stays "until upstream moves again or the owner closes it as declined, with the reason recorded". With one shared issue, "closes it" can only mean the item. This plan records a declined drift item as a `declined` entry in `anchors.json` (`anchor id`, `to`, `reason`), written in an ordinary session through the skill-update skill. Detection skips an item whose `to` matches a decline, and reports it again once upstream moves past it.
- **D14 No drift.** When detection finds nothing and an issue is open, the writer replaces the region with "No drift found." and closes the issue. When nothing is open, it does nothing.
- **D15 Placeholders before the harnesses exist.** The gate requires `checks/<name>/run.sh` for every `tool` entry, and Task 1 registers the tool entries before Tasks 2 and 3 build them. Task 1 commits a placeholder `run.sh` for each that exits 2 with `check not built yet (plan task N)`. No CI job runs them until their own task adds the workflow.
- **D16 Path-filtered workflows.** Path filtering is per workflow in GitHub Actions, so each harness gets its own workflow file instead of a third-party paths-filter action. A path-filtered workflow does not report on PRs that skip it, so neither should be made a required status check.
- **D17 Gate location.** The gate, detection and issue writer are repository infrastructure, not part of any skill, so they live in a root `scripts/` directory with tests beside them, following humanized-prose-review's layout.
- **D18 Description and README version strings.** effect-v4's frontmatter description and its README row both say "Checked against effect 4.1.1". The gate does not check them (blind spot); the skill-update skill lists them in its anchor-move step.

---

## File structure

```
anchors.json                                   single source of anchors and declines
scripts/anchors_gate.py                        registration and consistency gate (+ workflow pin check)
scripts/test_anchors_gate.py                   gate tests: standard block
scripts/fixtures/gate/<case>/                  must-fail and pass fixture trees (mini repos)
scripts/semver.py                              SemVer 2.0.0 parse and precedence
scripts/detect_drift.py                        drift detection, sources injected
scripts/sources.py                             NetworkSources and the Sources protocol
scripts/test_detect_drift.py, test_semver.py   detection tests
scripts/fixtures/detect/                       recorded registry responses, git repo builders
scripts/drift_issue.py                         issue body rendering and reconciliation
scripts/test_drift_issue.py                    writer tests with a fake client
checks/effect-v4/                              moved harness (see Task 2)
checks/purescript-gotchas/                     new harness (see Task 3)
.github/workflows/gates.yml                    push/PR: script tests + gate
.github/workflows/check-effect-v4.yml          push/PR, path-filtered
.github/workflows/check-purescript-gotchas.yml push/PR, path-filtered
.github/workflows/skill-drift.yml              monthly + manual
skills/skill-update/SKILL.md                   the skill
```

Modified: `skills/effect-v4/SKILL.md` (Versions table, D5), `skills/readable-functional-code/SKILL.md` (Versions section, D6), `README.md` (row, sync section, a "Checks" note), `THIRD_PARTY.md` (writing-skills sentence if D1 changes it).

### `anchors.json` schema (version 1)

```json
{
  "version": 1,
  "anchors": [
    {"id": "test-first", "skill": "test-first", "kind": "fork",
     "repo": "obra/superpowers", "path": "skills/test-driven-development",
     "commit": "<40 hex>", "release": "v7.0.1"},
    {"id": "humanized-prose-review", "skill": "humanized-prose-review", "kind": "vendored",
     "repo": "blader/humanizer", "path": "SKILL.md",
     "local": "references/humanizer-3.1.0.md", "version": "3.1.0", "commit": "<40 hex>"},
    {"id": "effect-v4/effect", "skill": "effect-v4", "kind": "tool",
     "ecosystem": "npm", "package": "effect", "version": "4.1.1",
     "row": "effect", "check": "checks/effect-v4"},
    {"id": "installed/find-skills", "skill": "find-skills", "kind": "installed",
     "repo": "vercel-labs/skills", "path": "skills/find-skills",
     "folderHash": "76a98a285cb0434f3d39e1a873823556330e398b"},
    {"id": "gate-integrity", "skill": "gate-integrity", "kind": "none",
     "reason": "Original skill; states no tool versions."}
  ],
  "declined": [
    {"repo": "obra/superpowers", "path": "skills/using-superpowers", "reason": "<owner's>"},
    {"anchor": "effect-v4/effect", "to": "4.2.0", "reason": "<owner's>"}
  ]
}
```

Ecosystems: `npm` (effect, @effect/vitest, typescript, spago, purs-tidy), `github-release` (`package` is `purescript/purescript` for purs), `purescript-package-set`, `purescript-package` (prelude, quickcheck, quickcheck-laws, js-bigints, bigints). `row` is the exact first-column label of the skill's Versions table (`purs`, `registry package set`, ...). Unknown keys fail the gate.

---

### Task 1: `anchors.json` and the registration and consistency gate

**Files:**
- Create: `anchors.json`, `scripts/anchors_gate.py`, `scripts/test_anchors_gate.py`, `scripts/fixtures/gate/**` (fixture files, each staged by path), `checks/effect-v4/run.sh` and `checks/purescript-gotchas/run.sh` (placeholders, D15), `.github/workflows/gates.yml`
- Modify: `skills/effect-v4/SKILL.md` (Versions table only, D5), `skills/readable-functional-code/SKILL.md` (new `## Versions`, D6)

**Interfaces:**
- Produces: `load_anchors(path: Path) -> Anchors` (validated; raises `GateError(code, message)`); `check_repo(root: Path) -> list[Finding]` where `Finding = (code: str, subject: str, message: str)`; `parse_versions_table(skill_md: str) -> dict[str, str] | None`; `parse_notice(text: str, kind: str) -> NoticeFacts`; `parse_third_party(text: str) -> dict[str, ThirdPartyRow]`; `check_workflow_pins(root: Path) -> list[Finding]`. CLI: `python3 scripts/anchors_gate.py [--root DIR]`, exit 0 with `anchors gate: N skills, M anchors, OK`, else exit 1 printing one `CODE subject: message` per finding. Finding codes used by later tasks: `UNREGISTERED`, `NO_SUCH_SKILL`, `NONE_FORBIDDEN`, `CHECK_MISSING`, `NOTICE_MISMATCH`, `NOTICE_UNPARSEABLE`, `THIRD_PARTY_MISMATCH`, `VERSIONS_MISMATCH`, `VERSIONS_UNANCHORED`, `SCHEMA`, `DUPLICATE_ID`, `NOT_A_SKILL_DIR`, `UNPINNED_ACTION`.

Rules the gate enforces, each from parsed input:
1. Every entry under `skills/` is a directory containing `SKILL.md` (`NOT_A_SKILL_DIR` otherwise) and has at least one non-`installed` anchor (`UNREGISTERED`).
2. Every non-`installed` anchor names an existing skill directory (`NO_SUCH_SKILL`); an `installed` anchor must not (`SCHEMA`, collision with a local skill).
3. A `none` entry is the skill's only entry, and the skill has no `## Versions` heading, no `NOTICE.md`, no `THIRD_PARTY.md` row (`NONE_FORBIDDEN`). Headings are found by a line scan that tracks fenced code blocks (``` and ~~~, per CommonMark), and only an ATX heading whose text is exactly `Versions` at level 2 counts.
4. `fork` and `vendored` entries agree with `NOTICE.md` under the D10 grammar and with the `THIRD_PARTY.md` table, both directions: a NOTICE or a row with no matching entry also fails (D9 prefix rule).
5. Each `tool` entry: `check` is a directory with an executable `run.sh` (`CHECK_MISSING`); the skill's Versions table has a row whose first cell equals `row` and whose second cell's first whitespace-separated token equals `version` (`VERSIONS_MISMATCH`); every Versions table row has a `tool` entry (`VERSIONS_UNANCHORED`).
6. `id` unique; `commit` 40 lowercase hex; required keys by kind; no unknown keys (`SCHEMA`, `DUPLICATE_ID`).
7. Every line in `.github/workflows/*.yml` whose first non-space token is `uses:` or `- uses:` names `owner/repo[/path]@<40 hex>` or a local `./` path (`UNPINNED_ACTION`). This is a text check that over-matches by design (a `uses:` inside a block scalar would also be checked; it cannot miss a step).

Blind spots, written in the gate's module docstring: whether an anchor is true (that the fork really came from that commit); whether a check exercises its skill's claims; version strings in descriptions and README prose (D18); NOTICE text after the first paragraph; `installed` entries against the owner's real lock file (it is not in the repository); the workflow's `permissions` block (no YAML parser in the stdlib; reviewed by hand in Task 5).

- [ ] **Step 1: Build fixture repositories.** Each fixture under `scripts/fixtures/gate/<case>/` is a minimal tree: `anchors.json`, `skills/…`, `THIRD_PARTY.md`, optionally `checks/…` and `.github/workflows/…`. `pass-minimal` has one fork skill, one tool skill with a Versions table and an executable `checks/x/run.sh`, one `none` skill. Each must-fail fixture copies `pass-minimal` and plants one defect. Generate the copies in a test helper from `pass-minimal` plus a per-case patch, rather than committing 20 near-identical trees; commit only `pass-minimal` and the cases that need distinct files.

- [ ] **Step 2: Write the failing tests** in `scripts/test_anchors_gate.py` (unittest, same header style as `test_tell_lint.py`, `ANCHORS_GATE_PATH` env var swaps the checker for the mutant run). One test per row; each asserts exit status and the exact finding code and subject:

| Test | Fixture defect | Expected |
|---|---|---|
| `test_pass_minimal` | none | exit 0, `3 skills` |
| `test_skill_without_entry_fails` | add `skills/new/SKILL.md` | `UNREGISTERED new` |
| `test_none_on_skill_with_versions_fails` | `none` skill gains `## Versions` | `NONE_FORBIDDEN` |
| `test_none_on_skill_with_notice_fails` | `none` skill gains `NOTICE.md` | `NONE_FORBIDDEN` |
| `test_none_on_skill_with_third_party_row_fails` | row added for the `none` skill | `NONE_FORBIDDEN` |
| `test_tool_check_missing_fails` | delete `checks/x/run.sh` | `CHECK_MISSING` |
| `test_tool_check_not_executable_fails` | chmod 644 | `CHECK_MISSING` |
| `test_versions_value_mismatch_fails` | table says 4.1.2 | `VERSIONS_MISMATCH` |
| `test_versions_row_without_anchor_fails` | extra table row | `VERSIONS_UNANCHORED` |
| `test_notice_commit_mismatch_fails` | NOTICE `2ce8aa2` | `NOTICE_MISMATCH` |
| `test_notice_release_mismatch_fails` | NOTICE `(v7.0.2)` | `NOTICE_MISMATCH` |
| `test_notice_unparseable_fails` | first paragraph reworded | `NOTICE_UNPARSEABLE` |
| `test_notice_without_entry_fails` | NOTICE on the tool skill | `NOTICE_MISMATCH` |
| `test_third_party_mismatch_fails` | row commit differs | `THIRD_PARTY_MISMATCH` |
| `test_third_party_row_without_entry_fails` | extra row | `THIRD_PARTY_MISMATCH` |
| `test_unknown_key_fails` / `test_duplicate_id_fails` / `test_short_commit_in_anchors_fails` | schema defects | `SCHEMA` / `DUPLICATE_ID` / `SCHEMA` |
| `test_installed_named_like_local_skill_fails` | collision | `SCHEMA` |
| `test_directory_without_skill_md_fails` | `skills/stray/README.md` | `NOT_A_SKILL_DIR stray` (Review Focus 1) |
| `test_unpinned_action_fails` | `uses: actions/checkout@v5` | `UNPINNED_ACTION` |
| `test_unparseable_anchors_fails` | invalid JSON | `SCHEMA`, exit 1, no traceback |
| `test_empty_skills_dir_fails` | `skills/` empty, anchors empty | exit 1, `SCHEMA no skills` (declared inventory: at least one) |
| `test_versions_in_code_fence_ignored` | `## Versions` only inside a fence on the `none` skill | exit 0 (Review Focus 5) |
| `test_near_miss_heading_ignored` | `## Versioning the Block` on the `none` skill | exit 0 (Review Focus 5) |
| `test_spelling_probes` | Versions heading as `## Versions`, `##  Versions `, closing-hash form `## Versions ##` | each counted exactly once |
| `test_live_repo_scan_floor` | the real repository root | exit 0, at least 31 skills and 31 non-`installed` anchors, and the scan includes `purescript-gotchas` with 9 Versions rows and `test-first` as `fork` |
| `test_checker_mutant` | rerun the suite with `ANCHORS_GATE_PATH` pointing at a copy whose `NONE_FORBIDDEN` branch is deleted | the suite fails |

Case mutants (standard block item 8): for each must-fail case, the helper also builds the case with its defect reverted and asserts exit 0, in the same test, so each fixture fails for its own reason.

- [ ] **Step 3: Run the tests to see them fail.** Run: `cd /Users/ethan/Desktop/skills && python3 -m unittest discover -s scripts -p 'test_anchors_gate.py' -v`. Expected: every test errors with `No such file` or `ModuleNotFoundError` for `anchors_gate`.

- [ ] **Step 4: Implement `scripts/anchors_gate.py`** to the Interfaces above. Markdown tables: a table is a header row, a delimiter row (`|---|`), then rows, outside fences; cells split on unescaped `|` and stripped. `THIRD_PARTY.md` "Skill" cell: the first whitespace-separated token is the skill; the "Derived from" cell is parsed as `<owner/repo> `<name>` @ `<sha>`` for forks and `<owner/repo> <version>` for vendored.

- [ ] **Step 5: Run the fixture tests.** Same command; expected PASS except `test_live_repo_scan_floor` (no `anchors.json` yet).

- [ ] **Step 6: Write `anchors.json` for the repository.** 31 skill directories today (listed by `ls skills`): 12 `fork` (commit: resolve `2ce8aa1` to its full SHA with `git ls-remote https://github.com/obra/superpowers` or the commits API page; `release: v7.0.1`; `path: skills/<original name>` from the README "Forks and the originals" table), 1 `vendored` (humanized-prose-review; resolve whether `3.1.0` is a tag of blader/humanizer with `git ls-remote --tags`, and record the commit it points to; if no tag exists, stop and ask, D-list item), `tool` entries for effect-v4 (3, D7), readable-functional-code (2, D6) and purescript-gotchas (9, D8), and `none` for the other 15 with a one-line reason each. Add the four `installed` entries from the lock (D3) and the `writing-skills` entry (D1). For D4, list `skills/` at the full `2ce8aa1` (`gh api repos/obra/superpowers/contents/skills?ref=<sha> --jq '.[].name'`), subtract the 12 forked and `writing-skills`, and **stop to ask the owner** for each remaining decline reason; write them into `declined` only with the owner's words.

- [ ] **Step 7: Add the Versions tables (D5, D6).** In `skills/effect-v4/SKILL.md`, insert under `## Versions` a table with rows `effect | 4.1.1`, `@effect/vitest | 4.1.1`, `typescript | 5.9.3`, keeping the prose. In `skills/readable-functional-code/SKILL.md`, add a `## Versions` section with rows `effect | 4.1.1` and `typescript | 5.9.3` and one sentence saying the `typescript.md` examples compile against them, checked by `checks/effect-v4`.

- [ ] **Step 8: Add placeholders (D15).** `checks/effect-v4/run.sh` and `checks/purescript-gotchas/run.sh`, executable, body: print `check not built yet (plan task 2)` (or 3) to stderr and `exit 2`.

- [ ] **Step 9: Find and verify the `actions/checkout` SHA, and write `gates.yml`.** For each action this plan uses (here `actions/checkout`; Task 2 adds `oven-sh/setup-bun`, Task 3 `actions/setup-node`):
  1. `gh api repos/<owner>/<repo>/releases/latest --jq '.tag_name,.published_at'`; take the latest release at least 14 days old (else the previous one).
  2. `gh api repos/<owner>/<repo>/git/ref/tags/<tag> --jq '.object.type,.object.sha'`; if the type is `tag`, dereference with `gh api repos/<owner>/<repo>/git/tags/<sha> --jq .object.sha`.
  3. Independently: `git ls-remote https://github.com/<owner>/<repo> refs/tags/<tag> 'refs/tags/<tag>^{}'`; the peeled line must equal step 2's commit.
  4. `gh api repos/<owner>/<repo>/commits/<sha> --jq .sha` returns the same 40 characters (the commit exists in that repository, not a fork).
  5. Write `uses: <owner>/<repo>@<sha> # <tag>` and record the four outputs in the task report.
  `gates.yml`: `on: [push, pull_request]`, `permissions: contents: read`, one job on `ubuntu-24.04`: checkout, `python3 --version`, `python3 -m unittest discover -s scripts -v`, `python3 scripts/anchors_gate.py`, and `cd skills/humanized-prose-review && python3 -m unittest discover -s scripts` and `skills/agent-baseline/scripts/test-baseline.sh` (existing checker suites, which nothing runs in CI today).

- [ ] **Step 10: Run everything.** `python3 -m unittest discover -s scripts -v` (all pass, including the scan floor) and `python3 scripts/anchors_gate.py` (expected `anchors gate: 31 skills, … anchors, OK`). Then plant one defect by hand in a scratch copy of the repo (`cp -R` to the scratchpad, remove `anchors.json`'s `gate-integrity` entry) and confirm `UNREGISTERED gate-integrity`; delete the copy.

- [ ] **Step 11: Commit.** Stage each created and modified path explicitly (list the fixture files with `git status --short scripts/fixtures` and add them one by one), then:
```bash
git commit -m "anchors: register every skill, gate the record against NOTICE, THIRD_PARTY and Versions"
```

---

### Task 2: `checks/effect-v4/` from the session harness, and its CI job

**Files:**
- Create from `/private/tmp/claude-501/-Users-ethan-Desktop-waxwing/d6631703-6b46-4991-b861-2d62fce2d27a/scratchpad/effect-typecheck`: `checks/effect-v4/extract.ts`, `package.json`, `bun.lock`, `tsconfig.json`, `tsconfig.mustfail.json`, `preludes/*.ts` (9 files), `controls/{must-fail,types,vitest-names}.ts`, `mustfail-raw/must-fail.ts`, `runtime/promise-rejection.ts`. Not copied: `blocks/` (generated, and the `block-0N.ts` files are stale), `idioms/` and `tsconfig.idioms.json` (they check `effect-ts-idioms.md`, a file that commit 74ccde5 folded into effect-v4; their content is covered by the effect-v4 blocks and controls). Stop and ask if the owner wants `idioms/` kept.
- Replace: `checks/effect-v4/run.sh` (placeholder from Task 1)
- Create: `checks/effect-v4/expected.json`, `checks/effect-v4/test-run.sh`, `checks/effect-v4/README.md` (short: what it checks, how to run, blind spots), `.github/workflows/check-effect-v4.yml`

**Interfaces:**
- Consumes: `anchors.json` entries `effect-v4/*` and `readable-functional-code/*` with `check: checks/effect-v4` (Task 1).
- Produces: `checks/effect-v4/run.sh [--repo DIR]`, exit 0 and last line `effect-v4 check: OK (9 + 2 blocks, 7 must-fail errors, runtime claim holds)`; non-zero with a named message otherwise. `--repo` defaults to the repository root and is how `test-run.sh` points it at planted copies.

`run.sh` does, in order, inside `work=$(mktemp -d)` with `trap 'rm -rf "$work"' EXIT` and `BUN_INSTALL_CACHE_DIR="$work/bun-cache"`:
1. Copy the check's tracked files into `$work`; `bun install --frozen-lockfile`.
2. Extract blocks into a fresh `$work/blocks/` (so no stale block survives) from `<repo>/skills/effect-v4/SKILL.md` (prefix `effect-v4`) and `<repo>/skills/readable-functional-code/typescript.md` (prefix `typescript`).
3. Compare with `expected.json` (`{"effect-v4": 9, "typescript": 2, "mustFailErrors": 7}`): a block count that differs fails `expected 9 effect-v4 blocks, found N`; a `preludes/<prefix>-NN.ts` with no block NN fails `orphan prelude`; a fence whose info string is `typescript`, `tsx`, `js` or `javascript` in either file fails `untyped-checked fence` (the extractor reads only `ts`).
4. `tsc --noEmit -p tsconfig.json` must exit 0.
5. `tsc --noEmit -p tsconfig.mustfail.json` must report exactly 7 `error TS` lines, one on each of the 7 statement lines of `mustfail-raw/must-fail.ts` (parse `file(line,col): error TSnnnn`), not merely 7 in total.
6. `bun runtime/promise-rejection.ts` must print `CLAIM HOLDS` and exit 0.

`extract.ts` changes: write into a directory given as its third argument; exit non-zero on an unterminated fence. Keep the rest.

- [ ] **Step 1: Write `test-run.sh`** in the agent-baseline style (`expect WANT NAME CMD...`, a scratch dir, a pass/fail tally). Cases, each against a scratch copy of the repo's two skill files under a fake `--repo` tree:

| Case | Planted defect | Expected exit and message |
|---|---|---|
| `clean` | none | 0, `effect-v4 check: OK` |
| `v3-name-in-block` | add `Effect.catchAll` to block 01 | non-zero, `tsc` error naming `blocks/effect-v4-01.ts` |
| `block-removed` | delete the last `ts` block of SKILL.md | `expected 9 effect-v4 blocks, found 8` |
| `typescript-fence` | change one fence to ```` ```typescript ```` | `untyped-checked fence` |
| `orphan-prelude` | add `preludes/effect-v4-10.ts` | `orphan prelude` |
| `mustfail-line-fixed` | in a copy of the check, change `Effect.catchAll` to `Effect.catch` in `mustfail-raw` | `expected 7 must-fail errors, found 6` |
| `runtime-claim` | in a copy of the check, swap `Effect.promise(rejecting)` for `Effect.tryPromise({…})` in the first case | `CLAIM FAILS` |
| `typescript-md-block-removed` | delete one block of `typescript.md` | `expected 2 typescript blocks, found 1` |

Each failing case also runs with its defect reverted and expects 0 (case mutant). `test-run.sh` runs `run.sh` up to 16 times; to save time and disk, make `run.sh` accept `--deps DIR` to reuse one installed `node_modules` across cases, with the default still a fresh install.

- [ ] **Step 2: Run it to see it fail.** `checks/effect-v4/test-run.sh`; expected: `clean` fails with `check not built yet (plan task 2)`.

- [ ] **Step 3: Copy the harness files and write `run.sh`, `expected.json`, the `extract.ts` changes** as above.

- [ ] **Step 4: Run the check and its tests.** `checks/effect-v4/run.sh` then `checks/effect-v4/test-run.sh`; expected OK and all cases pass. Record `du -sh` of the work dir (print it from `run.sh` under `--verbose`). Confirm `ls ~/.bun/install/cache` did not grow.

- [ ] **Step 5: Pin `oven-sh/setup-bun`** with the Task 1 Step 9 procedure, and write `check-effect-v4.yml`: `on: push` and `pull_request` with `paths: [skills/effect-v4/**, skills/readable-functional-code/typescript.md, checks/effect-v4/**, anchors.json, .github/workflows/check-effect-v4.yml]`, `permissions: contents: read`, steps checkout, setup-bun with `bun-version: 1.3.6`, `checks/effect-v4/run.sh`, `checks/effect-v4/test-run.sh`. Then `python3 scripts/anchors_gate.py` (expected OK; the pins pass `UNPINNED_ACTION`).

- [ ] **Step 6: Commit** each file by path:
```bash
git commit -m "checks/effect-v4: compile every effect-v4 and typescript.md block, with must-fail and runtime controls"
```

---

### Task 3: `checks/purescript-gotchas/` and its CI job

**Files:**
- Create: `checks/purescript-gotchas/package.json` (devDependencies `purescript: 0.15.16`, `spago: 1.0.4`, `trustedDependencies: ["purescript"]` for its binary download), `bun.lock`, `spago.yaml` (workspace, `packageSet.registry: 81.0.0`, dependencies `prelude`, `console`, `effect`, `quickcheck`, `quickcheck-laws`, `js-bigints`, `bigints`, `tuples`, `orders`), `spago.lock`, `cases.json`, `cases/<case>/*.purs` (and `*.js` runners where noted), `runner.py`, `test_runner.py`, `run.sh` (replaces the placeholder), `README.md`
- Create: `.github/workflows/check-purescript-gotchas.yml`

**Interfaces:**
- Consumes: the purescript-gotchas Versions table via `parse_versions_table` from `scripts/anchors_gate.py` (Task 1).
- Produces: `checks/purescript-gotchas/run.sh`, exit 0 with `purescript-gotchas check: OK (N cases)`. `runner.py` functions: `load_cases(path) -> list[Case]`; `classify(result_json: dict) -> Outcome` where `Outcome = (status: "ok"|"error", errors: list[(code, message)], warnings: list[(code, message)])`; `check_case(case, outcome) -> list[str]` (empty when it matches); `check_versions(versions_table, spago_lock, tool_versions) -> list[str]`.

How a case runs: `spago install` once fetches the set into the work dir. For each case, `purs compile --json-errors --output <work>/out/<case> $(spago sources) cases/<case>/*.purs`, parsing the JSON from stderr. Decide on `errorCode` and on the module and line it points at, never on message text alone. Where the skill quotes the compiler, the case also lists `messageIncludes` fragments; a mismatch there is reported as `wording changed`, a separate failure class, since the skill makes that claim too.

Cases (one per claim; `expect` is `ok`, `error <code>` or `warning <code>`; codes marked * are the plan's belief about purs 0.15.16, and Step 4 confirms them. If the compiler gives a different code for the same construct, that is a finding about the plan or the skill: stop and report it, and do not edit the expectation to match):

| Case | Skill claim (section) | Expect |
|---|---|---|
| `reexport-individual` | individually imported name cannot be re-exported | error `UnknownExport`*, includes `Cannot export unknown type Thing` |
| `facade-hides-ctor` | facade without `(..)` hides constructor | error `UnknownName`*, includes `Unknown data constructor Cents` |
| `facade-keeps-type-and-fn` | caller gets `Cents` and `fromInt` | ok |
| `export-forms` | `T`, `T(..)`, `T(A, B)` | ok; plus `export-forms-hidden` error `UnknownName`* using a constructor left out of `T(A)` |
| `purs-graph-json` | `purs graph` prints JSON | runner calls `purs graph`, parses stdout as JSON with the case's module as a key |
| `cycle-point-free` | point-free member of a recursive group | error `CycleInDeclaration`, includes `The value of one is undefined here` |
| `cycle-fixed` | `go es = concatMap one es` | ok |
| `cycle-nonrecursive` | point-free compiles while the group is not recursive | ok |
| `orphan-instance` | no orphans | error `OrphanInstance` |
| `newtype-derive-inner` | needs the inner instance | error `NoInstanceFound`, includes `Eq Cents` |
| `generic-hidden-ctor` | warning, not error | ok with warning `HiddenConstructors` |
| `constrained-ctor` | no constrained data constructors | error `ErrorParsingModule`*, includes `=>` |
| `semigroup-number` / `semigroup-int` | no Semigroup for Number, Int | error `NoInstanceFound`, includes `Semigroup Number` / `Semigroup Int` |
| `additive-wrapper` | `Data.Monoid.Additive` works | ok |
| `semiring-four-members` | Semiring is add, zero, mul, one | error `MissingClassMember`* for an instance giving only `add` and `zero` |
| `between-explicit` | explicit import shadows with a warning | ok with warning `ScopeShadowing` |
| `between-open` | open import makes use a conflict | error `ScopeConflict` |
| `abs-not-in-prelude` | `abs` unknown with only Prelude | error `UnknownName`, includes `abs` |
| `abs-from-data-ord` | importing `Data.Ord (abs)` compiles | ok |
| `no-tuple-syntax` | `(a, b)` does not parse | error `ErrorParsingModule`*, includes `,` |
| `number-add-nonassoc` | addition on Number not associative, between a sixth and a quarter | compile ok, then `node` runs the compiled `main` over 100,000 triples from a fixed-seed generator at magnitudes 1, 1e3, 1e6, 1e9; prints the fraction per magnitude; the runner asserts each fraction is in [1/6, 1/4] |
| `quickcheck-chain` | `===` and `<?>` cannot be chained | error `NonAssociativeError` |
| `quickcheck-types` | `(x === y) <?> "msg"` is a type error | error `TypesDoNotUnify`* |
| `bigints-npm` | `Data.BigInt` needs `big-integer` at runtime | compile ok; running the output with `node` (no `big-integer` installed) fails with `ERR_MODULE_NOT_FOUND` naming `big-integer` |
| `js-bigints-native` | `JS.BigInt` runs without npm dependencies | compile ok, runs and exits 0 |
| `laws-gen-variant` | `checkSemigroupGen :: Gen s -> Effect Unit` | ok, with that annotation on a binding |
| `laws-proxy-needs-arbitrary` | `checkSemigroup` needs `Arbitrary s` | error `NoInstanceFound`, includes `Arbitrary` |
| `arbitrary-number-uniform` | `Arbitrary Number` is in `[0.0, 1.0)` | compile ok; `node` samples 10,000 values with a fixed seed; runner asserts all in [0, 1) and min < 0.01 and max > 0.99 (supports the claim; a sample cannot prove it) |
| `hole-one-decl` | holes in one declaration reported together | exactly 2 `HoleInferredType` errors |
| `hole-two-decls` | holes in separate declarations one compile at a time | exactly 1 `HoleInferredType` error |

`check_versions` asserts: `purs --version` = the `purs` row's first token; `spago --version` = `spago`; `spago.yaml` package set = `registry package set`; for each of `prelude`, `quickcheck`, `quickcheck-laws`, `js-bigints`, `bigints`, `spago.lock` resolves exactly the table's version. `purs-tidy` is not exercised (D8, listed in the README's blind spots).

Blind spots in `README.md`: claims about advice (what to do instead) are not checkable; the "Reviewing a change" list is not checked; sampling claims are supported, not proved; claims with no bold lead-in are matched to cases only through `cases.json`'s `claim` field, which a reviewer checks by hand.

- [ ] **Step 1: Write `test_runner.py` first** (unittest; recorded `--json-errors` outputs in `checks/purescript-gotchas/fixtures/` written by hand from the purs JSON error format, so the runner is testable without purs):
  - `test_expected_error_matches`, `test_wrong_code_fails` (message names case, wanted and got), `test_unexpected_success_fails`, `test_warning_expected_but_absent_fails`, `test_wording_changed_is_reported_separately`;
  - `test_manifest_inventory_both_ways`: a `cases/` directory not in `cases.json` fails, and a `cases.json` entry with no directory fails;
  - `test_empty_manifest_fails`; `test_scan_floor`: the real `cases.json` has at least 32 cases and contains `cycle-point-free`;
  - `test_versions_mismatch_fails` (lock says prelude 6.0.1) and `test_versions_match_passes`, using the real SKILL.md table;
  - `test_unparseable_compiler_output_fails` (stderr not JSON);
  - `test_checker_mutant`: with `RUNNER_PATH` pointing at a copy whose `check_case` ignores `errorCode`, the suite fails.
- [ ] **Step 2: Run to see them fail.** `cd checks/purescript-gotchas && python3 -m unittest test_runner -v`; expected: import errors.
- [ ] **Step 3: Implement `runner.py` and `run.sh`.** `run.sh` uses `work=$(mktemp -d)`, trap removal, `BUN_INSTALL_CACHE_DIR=$work/bun-cache`, and runs `spago` with `HOME=$work/home XDG_CACHE_HOME=$work/cache` so the registry index and package cache land in the work dir. It installs with `bun install --frozen-lockfile` and puts `$work/node_modules/.bin` first on PATH, so the global `purs` and `spago` in `~/.nvm` are not used. Verify in Step 4 that bun runs the `purescript` package's postinstall (the binary download); if it does not, switch the check to `npm ci` with a committed `package-lock.json` and say so in the report.
- [ ] **Step 4: Write the cases and run.** `checks/purescript-gotchas/run.sh`; expected `OK (32 cases)`. Record the work dir's peak `du -sh` and confirm `~/.cache/spago-nodejs`, `~/Library/Caches/spago-nodejs` and `~/.bun/install/cache` did not grow. If a case's claim does not hold at the pinned versions, stop: report the case, the compiler output and the skill line, and change neither the skill nor the expectation without the owner.
- [ ] **Step 5: Case mutants.** For each error case, a sibling run with the defect removed (for example `reexport-individual` with `module Facade (module Other)`) must compile; add these as `ok` cases suffixed `-control` only where Step 4's table does not already have one, and say which in the report.
- [ ] **Step 6: CI.** Pin `actions/setup-node` (Task 1 Step 9 procedure). Node version: an exact current LTS release at least 14 days old, recorded in the workflow (`node-version: 24.x.y`); check `purescript@0.15.16`'s and `spago@1.0.4`'s `engines` fields on the npm registry page first. The workflow also uses setup-bun (Task 2's pin). `paths: [skills/purescript-gotchas/**, checks/purescript-gotchas/**, anchors.json, .github/workflows/check-purescript-gotchas.yml]`, `permissions: contents: read`, steps: checkout, setup-node, setup-bun, `python3 -m unittest discover -s checks/purescript-gotchas -p 'test_*.py'`, `checks/purescript-gotchas/run.sh`. Then `python3 scripts/anchors_gate.py`.
- [ ] **Step 7: Commit** each file by path:
```bash
git commit -m "checks/purescript-gotchas: one compiled case per claim, pinned to the skill's Versions table"
```

---

### Task 4: drift detection, offline-tested

**Files:**
- Create: `scripts/semver.py`, `scripts/test_semver.py`, `scripts/sources.py`, `scripts/detect_drift.py`, `scripts/test_detect_drift.py`, `scripts/fixtures/detect/*.json` (trimmed recorded responses), `scripts/fixtures/detect/upstream.py` (helper that builds throwaway git repos in a temp dir for fork, vendored and installed cases)

**Interfaces:**
- Consumes: `load_anchors` and `check_repo` from `scripts/anchors_gate.py` (Task 1).
- Produces:
  - `semver.parse(s: str) -> Version`, `semver.latest_stable(versions: list[str], allow_pre: bool) -> str | None`.
  - `class Sources(Protocol)`: `clone(repo: str) -> Path` (blob-less bare clone, D11), `npm_versions(pkg) -> list[str]`, `github_releases(repo) -> list[Release(tag, prerelease, draft, url)]`, `package_sets() -> list[str]`, `purescript_package_versions(pkg) -> list[str]`. `NetworkSources(token: str | None, workdir: Path)` implements it with `git` and `urllib`; tests use `FixtureSources(fixture_dir, repos: dict[str, Path])`.
  - `detect(root: Path, sources: Sources) -> list[DriftItem]`, where `DriftItem = {"id", "skill", "kind", "from", "to", "link", "detail"}` and `kind` is one of `fork`, `vendored`, `tool`, `installed`, `new-upstream-skill`, `unregistered`, `anchor-missing`.
  - CLI: `python3 scripts/detect_drift.py --root . --out drift.json`; exit 0 with the items written (including when empty); exit 1 on any source error, writing nothing (Review Focus 4).

Behavior per kind:
- fork, vendored: `git -C <clone> log --format=%H%x09%s <anchor>..HEAD -- <path>`. Non-empty: item with `from` = anchor short SHA, `to` = HEAD short SHA, `link` = `https://github.com/<repo>/compare/<anchor>...<head>`, `detail` = the commit subjects. Vendored also reports a newer release tag when one exists. Unknown anchor revision: `anchor-missing` (Review Focus 2).
- installed: `git rev-parse HEAD:<path>` against `folderHash`. On a difference, walk `git log --format=%H -- <path>` until a commit whose tree at `<path>` equals `folderHash`; `from` is that commit or `unknown`; `detail` lists the commits after it (D2).
- tool: the latest stable version from the source for its ecosystem; an item when it is greater than `version` by SemVer precedence. purs: the newest non-draft, non-prerelease GitHub release, tag without its `v`. Package sets: the newest set version.
- new-upstream-skill: for each repo with `fork` entries (D4), the directory names under `skills/` at HEAD minus fork paths, `installed` paths and `declined` paths.
- unregistered: `check_repo` findings with code `UNREGISTERED`, one item each.
- declines: an item whose (`id`, `to`) matches a `declined` entry is dropped (D13).

Before Step 1, confirm two premises and record the evidence in the task report (network allowed for this step only, read-only):
- **Step 0a, D2 premise:** in a scratch dir, `git clone --filter=blob:none --bare https://github.com/vercel-labs/skills` and check whether some commit's `git rev-parse <c>:skills/find-skills` equals `76a98a285cb0434f3d39e1a873823556330e398b`. If none does, stop: `installed` drift needs a different anchor, and that is a question for the owner. Delete the clone.
- **Step 0b, endpoints:** confirm the PureScript registry sources by reading the purescript/registry repository's README (package sets are files under `package-sets/`, metadata under `metadata/<package>.json` with `published` versions). Record one trimmed response per endpoint as a fixture: npm `effect`, GitHub releases for `purescript/purescript`, the package-set list, `metadata/prelude.json`. The GitHub contents API lists at most 1,000 entries per directory, so if `package-sets/` has more, use the git trees API instead and say so.

- [ ] **Step 1: Write `test_semver.py`** from SemVer 2.0.0 section 11's examples: `1.0.0-alpha < 1.0.0-alpha.1 < 1.0.0-alpha.beta < 1.0.0-beta < 1.0.0-beta.2 < 1.0.0-beta.11 < 1.0.0-rc.1 < 1.0.0`, and `1.9.0 < 1.10.0 < 1.11.0`; `latest_stable(["4.1.1", "4.2.0-beta.1"], False) == "4.1.1"`; `latest_stable(["4.2.0-beta.1", "4.2.0-beta.2"], True) == "4.2.0-beta.2"`; build metadata ignored for precedence; `parse("v1")` raises.
- [ ] **Step 2: Write `test_detect_drift.py`** with `FixtureSources` and repos built by `upstream.py` (a bare repo with an anchor commit, then commits touching the path and commits elsewhere):
  - `test_fork_no_change`, `test_fork_change_on_path_reported` (subjects in `detail`, compare link exact), `test_fork_change_elsewhere_ignored`;
  - `test_unknown_anchor_commit_reports_anchor_missing` (and the other anchors are still checked);
  - `test_installed_same_tree_no_item`, `test_installed_changed_tree_reports_since_commit`, `test_installed_hash_not_in_history_reports_unknown_from`;
  - `test_tool_npm_newer_stable`, `test_tool_npm_prerelease_ignored`, `test_tool_prerelease_anchor_sees_prerelease`, `test_purs_release_draft_and_prerelease_ignored`, `test_package_set_newer`;
  - `test_new_upstream_skill_reported`, `test_declined_upstream_skill_not_reported`, `test_declined_drift_target_not_reported_until_upstream_moves`;
  - `test_unregistered_local_skill_reported`;
  - `test_source_error_exits_1_and_writes_nothing` (Review Focus 4);
  - `test_output_is_stable` (same inputs give byte-identical `drift.json`; items sorted by `id`);
  - `test_checker_mutant` (`DETECT_DRIFT_PATH` swapped for a copy whose fork branch drops the pathspec; the suite fails).
- [ ] **Step 3: Run to see them fail.** `python3 -m unittest discover -s scripts -p 'test_*.py' -v`; expected: import errors for `semver`, `detect_drift`.
- [ ] **Step 4: Implement** `semver.py`, `sources.py`, `detect_drift.py` to the Interfaces. `NetworkSources` sends `Authorization: Bearer <token>` when given, a generic `User-Agent: skills-drift-check`, and clones into its `workdir`.
- [ ] **Step 5: Run the tests**; expected all pass, no network (run once with networking off, for example by setting `HTTPS_PROXY=http://127.0.0.1:9`, to confirm).
- [ ] **Step 6: One live dry run (manual, read-only network).** `python3 scripts/detect_drift.py --root . --out <scratchpad>/drift.json`; paste the item list into the task report. Expected: no `anchor-missing`, no `unregistered`; any real drift listed. Delete the clones.
- [ ] **Step 7: Commit** each file by path:
```bash
git commit -m "scripts: detect skill drift against forks, vendored files, tools and installed skills"
```

---

### Task 5: the issue writer and the scheduled workflow

**Files:**
- Create: `scripts/drift_issue.py`, `scripts/test_drift_issue.py`, `.github/workflows/skill-drift.yml`

**Interfaces:**
- Consumes: `drift.json` items (Task 4).
- Produces: `render(items, previous_body: str | None) -> str`; `reconcile(items, client: IssueClient) -> Action` where `Action` is one of `none`, `create`, `update`, `close`; `class IssueClient(Protocol)`: `find_open(label) -> Issue | None`, `create(title, body, label)`, `update(number, body)`, `close(number, comment)`, `ensure_label(name, color, description)`. `GhClient` implements it with `gh api` (env `GH_TOKEN`); tests use a `FakeClient` that records calls. CLI: `python3 scripts/drift_issue.py drift.json`.

Body format: free text above and below is the owner's. The writer owns only the region between `<!-- skill-drift:start -->` and `<!-- skill-drift:end -->`. Each item is one line `- [ ] **<skill>** (<kind>): <from> -> <to>. [diff](<link>) <!-- key:<id> -->`, followed by its `detail` lines indented. Tick state is read from the previous body by key; it is kept when `to` is unchanged and cleared, with `(approval cleared: target moved from <old> to <new>)` appended, when `to` changed (D12). Items absent from detection are dropped. No timestamps in the body, so an unchanged result renders byte-identically. Title: `Skill drift`.

- [ ] **Step 1: Write `test_drift_issue.py`:**
  - `test_no_open_issue_creates_one_with_label`, `test_label_created_if_missing`;
  - `test_existing_issue_updated_in_place` (no `create` call);
  - `test_idempotent_second_run_makes_no_write` (same items, body from the first run: Action `none`, no client write calls);
  - `test_ticks_kept_by_key`, `test_reordered_lines_keep_ticks`, `test_text_outside_region_survives` (Review Focus 3);
  - `test_tick_cleared_when_target_moves` (D12);
  - `test_no_items_closes_open_issue` and `test_no_items_no_issue_does_nothing` (D14);
  - `test_missing_region_markers_appends_region` (owner deleted them; the old text is kept and a fresh region added below);
  - `test_two_open_drift_issues_fails` (exit 1 naming both numbers, no write; the writer never guesses which one is the issue);
  - `test_source_error_writes_nothing` (no `drift.json`, or it is invalid: exit 1, no client calls);
  - `test_checker_mutant` (`DRIFT_ISSUE_PATH` copy that ignores previous ticks; the suite fails).
- [ ] **Step 2: Run to see them fail**: `python3 -m unittest discover -s scripts -p 'test_drift_issue.py' -v`.
- [ ] **Step 3: Implement `drift_issue.py`.**
- [ ] **Step 4: Run all script tests**: `python3 -m unittest discover -s scripts -v`; expected pass.
- [ ] **Step 5: Write `skill-drift.yml`:**
```yaml
on:
  schedule: [{cron: "17 6 1 * *"}]
  workflow_dispatch: {}
permissions:
  contents: read
  issues: write
concurrency: {group: skill-drift, cancel-in-progress: false}
```
  One job on `ubuntu-24.04`: checkout (Task 1 pin), `python3 scripts/detect_drift.py --root . --out "$RUNNER_TEMP/drift.json"` with `GITHUB_TOKEN: ${{ github.token }}`, then `python3 scripts/drift_issue.py "$RUNNER_TEMP/drift.json"` with `GH_TOKEN: ${{ github.token }}`. No other actions, no secrets, no write to the repository. Review the `permissions` block by reading it (the gate cannot parse YAML; this is its stated blind spot).
- [ ] **Step 6: Gate and live check.** `python3 scripts/anchors_gate.py` (pins OK). The first `workflow_dispatch` run needs the branch on GitHub, which needs a push: ask the owner for that OK, then trigger with `gh workflow run skill-drift.yml --ref <branch>` and run it twice. Expected: the first run creates or updates the issue; the second reports Action `none` in its log. If the owner does not want a push yet, record that the live run is pending.
- [ ] **Step 7: Commit** each file by path:
```bash
git commit -m "skill-drift: monthly detection into one issue, updated in place"
```

---

### Task 6: the `skill-update` skill and the README

**Files:**
- Create: `skills/skill-update/SKILL.md`
- Modify: `anchors.json` (register `skill-update` as `none`: "Original skill; states no tool versions."), `README.md` (a row in "Working rules and records", a rewritten "Keeping the forks in sync with upstream" section, a short "Checks" paragraph naming `anchors.json`, the gate, the two harnesses and the monthly issue)

**Interfaces:**
- Consumes: everything above, by name: `anchors.json` fields, `scripts/anchors_gate.py`, `checks/<name>/run.sh`, the `skill-drift` issue format and its key comments, `declined` entries.

Content the skill must carry (the design's "The skill-update skill" section, by kind), with frontmatter `name: skill-update`, `license: MIT`, and a description that triggers on "do the approved skill updates", a `skill-drift` issue, "add a skill", and moving a pinned version or upstream commit:
- Start: read the open `skill-drift` issue; take only ticked items; one branch for the batch (isolated-workspaces), landed with landing-a-branch.
- fork: walk `git log <anchor>..<new> -- <path>` change by change; port, adapt or decline each against the fork's deliberate departures; log each decision as a comment on the issue; move `commit` and `release` in `anchors.json`, the NOTICE first paragraph and the `THIRD_PARTY.md` row together; run the gate.
- vendored: the same, plus dependency-intake's license check; rename the local file if its name carries the version.
- tool: change the pin in the check's lockfile, run `checks/<name>/run.sh`, fix every claim that fails, record names that changed meaning in the skill's "wrong in an older version" list, then move `version` in `anchors.json` and the Versions table only after the check passes, including its must-fail controls; update the description and README strings the gate cannot see (D18).
- installed: a dependency upgrade under dependency-intake's upgrade review; then copy the new `skillFolderHash` from the lock.
- new skill (here or upstream): register it (choose a kind, write its check or the reason it has none); for an upstream skill, fork, install unmodified, or record a decline with the owner's reason.
- declined drift item: add a `declined` entry (D13).
- Refers to dependency-intake, gate-integrity, verify-before-claiming and landing-a-branch rather than repeating them.

- [ ] **Step 1: Failing check first.** Create `skills/skill-update/` with an empty `SKILL.md` and run `python3 scripts/anchors_gate.py`; expected `UNREGISTERED skill-update`. Then add the `none` entry; expected OK.
- [ ] **Step 2: Write `SKILL.md`.** Read `writing-skills` (obra/superpowers, installed) for skill structure and description guidance first, and match the frontmatter and section style of `skills/gate-integrity/SKILL.md`.
- [ ] **Step 3: Write the README changes.** The sync section now says: anchors live in `anchors.json`; the monthly workflow files the `skill-drift` issue; tick items there, then ask an agent to "do the approved skill updates"; the hand-diff command stays as the manual path.
- [ ] **Step 4: Prose pass.** Run humanized-prose-review (its `scripts/tell_lint.py` and the editorial pass) on `skills/skill-update/SKILL.md` and the changed README sections, keeping every fact; American spelling.
- [ ] **Step 5: Run everything once:** `python3 -m unittest discover -s scripts -v`, `python3 scripts/anchors_gate.py`, `checks/effect-v4/run.sh`, `checks/purescript-gotchas/run.sh` (one at a time, not in parallel, for disk and memory). Expected: all pass.
- [ ] **Step 6: Commit** by path:
```bash
git add skills/skill-update/SKILL.md anchors.json README.md
git commit -m "skill-update: the skill that acts on approved drift items; README sync section"
```

---

## Order, parallelism and cost

| Task | Depends on | Shares files with | Could run in parallel with | Rough tokens (one implementer, before review) |
|---|---|---|---|---|
| 1 anchors + gate | none | `anchors.json` (6), `checks/*/run.sh` placeholders (2, 3) | none; everything consumes it | 120K |
| 2 effect-v4 check | 1 | `checks/effect-v4/run.sh` (1) | 3, 4 | 70K |
| 3 purescript check | 1 | `checks/purescript-gotchas/run.sh` (1); imports the gate's table parser | 2, 4 | 150K (32 cases and a toolchain) |
| 4 detection | 1 | `scripts/` (1, 5): separate files | 2, 3 | 120K |
| 5 issue + workflow | 4 | `scripts/` | 2, 3 (after 4) | 80K |
| 6 skill + README | 1 to 5 | `anchors.json` (1), `README.md` | none | 60K |

Tasks 2, 3 and 4 touch disjoint files and can run as parallel subagents in separate worktrees after Task 1 lands on the branch. Each needs only Task 1's interfaces. Running Tasks 2 and 3 at the same time doubles peak disk (two dependency installs, perhaps 1 GB together); with about 10 GB free that fits, but run their `run.sh` one at a time. Task 3 Step 4 and Task 4 Step 0 stop for the owner if a premise fails, so start them early.

Implementer total about 600K tokens. Subagent execution: 6 tasks × about 3 dispatches plus one branch review, about 19 dispatches and 1.2M to 1.5M tokens. Inline: 1 dispatch, about 700K to 900K tokens, as this session's context grows across six tasks. Both are above the implementation-planning skill's 500K threshold and need the owner's yes.

Owner input needed during execution: D1 (writing-skills anchor), D4 (decline reasons for unforked superpowers skills, Task 1 Step 6), the push for the live workflow run (Task 5 Step 6), and any claim that fails in Task 3 Step 4.
