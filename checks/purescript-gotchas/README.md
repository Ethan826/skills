# purescript-gotchas check

This check compiles one small set of modules for each claim in
`skills/purescript-gotchas/SKILL.md` and compares what the compiler says
with what the skill says. It runs against the versions in the skill's
Versions table.

```bash
checks/purescript-gotchas/run.sh                 # whole check, about a minute
python3 -m unittest discover -s checks/purescript-gotchas -p 'test_*.py'
```

`run.sh` needs `bun`, `node` 22.5 or later (spago 1.0.5 requires it),
`python3` and `git`. It creates a `mktemp -d` work directory and deletes
it on exit. HOME, XDG_CACHE_HOME and bun's install cache all point into
that directory, so the purs binary download, the registry index and the
package cache end up there too. PATH holds only the work directory's
`node_modules/.bin` and links to those four tools, which keeps any global
`purs` or `spago` (for example in `~/.nvm`) out of the run. A run uses
about 370 MB of disk while it lasts. Set `PURESCRIPT_GOTCHAS_DU=1` to
print the work directory's size at the end.

## Pins

- `package.json` and `bun.lock`: purescript 0.15.17 and spago 1.0.5,
  installed with `bun install --frozen-lockfile`. `trustedDependencies`
  lets bun run purescript's postinstall, which downloads the compiler
  binary.
- `spago.yaml` and `spago.lock`: registry package set 81.0.0. `run.sh`
  runs `spago install --pure` and fails if spago rewrites the lock.
- `runner.py` reads `purs --version`, `spago --version`, the lock's
  package set, and the lock's versions of prelude, quickcheck,
  quickcheck-laws, js-bigints and bigints. It fails unless each one
  equals both the skill's Versions table (parsed with the anchors gate's
  own `parse_versions_table`) and the matching `anchors.json` entry.

## Cases

`cases.json` lists one entry per directory under `cases/`. If a directory
has no entry, or an entry has no directory, the check fails. The case
count is pinned as `expectedCases` in `cases.json`, so removing a case
along with its directory also fails; change that number only with the
owner's approval. Each entry
gives the skill section and the claim it checks. It lists the exact
errors and warnings expected, each with its code and module, and adds a
line and message fragments where those matter. A case passes only when the
compiler's diagnostics match those lists exactly. Fragments are compared
after collapsing whitespace. A missing fragment is reported as `wording
changed`, a separate failure, since the skill quotes the compiler.
`codeGuessed` marks the codes the plan was unsure of before the first run.
`control` is the case that shows the same module compiling once the
defect is removed.

Some cases also have a `run` step. `purs-graph-json` calls `purs graph`
and parses the output. The others run the compiled `main` with node:
`bigints-npm` must fail with `ERR_MODULE_NOT_FOUND` naming `big-integer`,
`js-bigints-native` must exit 0, and the two sampling cases print JSON
that the runner checks against bounds.

purs 0.15.17 leaves `moduleName` null for parse errors,
`MissingClassMember` and `NonAssociativeError`. For those the runner
reads the module name from the reported file's `module` header.

`test_runner.py` tests the runner without a compiler. It feeds the
runner hand-written `--json-errors` output from `fixtures/`. The tests cover wrong codes,
modules and lines, unexpected success, missing and extra warnings,
changed wording, exact hole counts, unparseable output, the manifest
inventory in both directions, the scan floor, version mismatches against
the table and against `anchors.json`, and a checker mutant.

## Blind spots

- Advice in the skill (what to do instead) cannot be checked, and
  neither can the "Reviewing a change" list.
- The two sampling cases (`number-add-nonassoc`, `arbitrary-number-uniform`)
  support their claims; a fixed-seed sample cannot prove them.
- Claims are matched to cases only through each case's `claim` text,
  which a reviewer checks by hand. A claim with no case goes unnoticed.
- `purs-tidy` 0.11.1 is anchored but not exercised, because no claim in
  the skill concerns it.
- The "no submodule privacy" claim is checked only as far as `purs graph`
  printing JSON. That nothing like `pub(crate)` exists is not checked.
