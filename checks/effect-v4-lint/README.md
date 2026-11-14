# effect-v4-lint check

Lints the fixtures in `fixtures/` with the reference ESLint config,
`skills/effect-v4/lint/eslint.rules.js`, at the versions in `package.json`
and `bun.lock` (eslint 9.39.2, @eslint/js 9.39.2, typescript-eslint 8.54.0,
eslint-plugin-functional 9.0.4, TypeScript 5.9.3, effect 4.1.4).
typescript-eslint 8.54.0 accepts TypeScript below 6.0, so this check pins
TypeScript 5.9.3, while `checks/effect-v4` compiles the skill's examples with
7.0.2.

```bash
checks/effect-v4-lint/run.sh        # the check; needs bun 1.3.6 on PATH
checks/effect-v4-lint/test-run.sh   # the check's own tests (planted defects)
```

`run.sh` installs into a temporary directory, with bun's cache inside it, and
removes the directory on exit. `fixtures/eslint.config.js` calls
`buildConfig` with an example layer table and four example vocabularies. The
check fails when:

- `package.json` pins a range; a pin differs from its `anchors.json` `tool`
  entry (`check` `checks/effect-v4-lint`), or, for `effect`, from the
  `effect-v4/effect` entry; or the installed version differs from the pin;
- `bun install --frozen-lockfile` fails;
- the config's `effectModules` list differs from the namespaces that
  `effect/src/index.ts` exports;
- a `.ts` file under `fixtures/src` or `fixtures/test` is missing from
  `expected.json`, or listed twice, or listed but absent;
- a must-fail fixture lacks any expected report, matched by rule id and a
  substring of the message (the native-method fixtures list each method, so
  dropping one method from the config fails);
- a clean control reports anything, or any fixture has a parse error.

`test-run.sh` plants a defect per case, in the config or in a copy of the
check, and requires the named failure: a rule removed, a native method
removed, the `Schema.Literals` ban removed, aliases ignored, a vocabulary
module allowed to spell every vocabulary, the null-check ban removed, a layer
edge opened, the vocabulary ban dropped from tests, an Effect module missing
from or added to `effectModules`, an unlisted fixture, a dirty control, a
parse error, and each kind of version disagreement.

## Adding a rule or a fixture

A new rule group needs a must-fail fixture and an `expected.json` entry in the
same change. A new option of `buildConfig` needs a fixture that fails when the
option is ignored.

## What it does not catch

- Code a rule should reject but no fixture contains. The fixtures show each
  group can fail; they do not show a list is complete.
- Every blind spot listed at the top of `eslint.rules.js`.
- A project's own copy of the config drifting from this one.
- The preset rules from `@eslint/js`, `strictTypeChecked` and
  `stylisticTypeChecked`, beyond the ones a fixture happens to trip.
