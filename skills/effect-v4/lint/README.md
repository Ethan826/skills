# Reference lint config

`eslint.rules.js` is an ESLint flat config for TypeScript with Effect v4 in
a decision-core application. It bans the patterns the effect-v4 skill
replaces (loops, `throw`, `try`, casts, `!`, `let`, mutation, throwing Schema
calls, `Effect.run*` outside Program, `JSON`, `Promise` and `async`), the
native array, string and `Object` methods and the null checks in core
layers, imports that cross a layer edge, inline literals in `Schema.Literals`
and `Schema.Literal`, and the names of each closed vocabulary outside the
module that defines it.

It was checked with eslint 9.39.2, @eslint/js 9.39.2, typescript-eslint
8.54.0, eslint-plugin-functional 9.0.4, TypeScript 5.9.3 and effect 4.1.4;
`checks/effect-v4-lint` in the skills repository lints must-fail fixtures
with it. Pin the same versions, or rerun that check after moving them.

## Copying it into a project

1. Copy `eslint.rules.js` to the project root. Record where it came from (the
   skills repository commit) in a comment at its top, and keep the copy
   unchanged apart from that line, so it can be compared with this one.
2. Install the five packages above at exact versions, plus `effect`.
3. Write `eslint.config.js`:

```js
import { fileURLToPath } from "node:url"
import { buildConfig } from "./eslint.rules.js"

export default buildConfig({
  tsconfigRootDir: fileURLToPath(new URL(".", import.meta.url)),
  layers: {
    domain: [],
    features: ["domain"],
    format: ["domain"],
    runtime: ["domain"],
    program: ["domain", "features", "format", "runtime"],
    facade: ["domain", "features", "format", "program"],
  },
  coreLayers: ["domain", "features", "format"],
  vocabularies: [
    { constant: "Clients", module: "src/domain/clients.ts", names: ["claude", "codex"] },
    { constant: "Roles", module: "src/domain/roles.ts", names: ["implementer", "reviewer", "corrector"] },
  ],
  aliases: { Array: ["Arr"], Schema: ["S"] },
  ignores: ["lint-fixtures/**"],
})
```

   The example is one project's settings; replace each value with yours.
4. Port `checks/effect-v4-lint/fixtures` into the project with its own
   names, and run them in its tests, so the project's copy is seen to fail
   (gate-integrity). Forbid lint-disable comments in the instruction file.

## Options

| Option | Required | Meaning |
|---|---|---|
| `tsconfigRootDir` | yes | Directory of the tsconfig for type-aware rules. |
| `layers` | yes | Layer directories under `sourceRoot`, each mapped to the layers it may import. A layer missing from another's list may not be imported by it. decision-core-architecture's onion generator (`diagram/onion.ts`) returns the same shape from `layerTable(spec)`, so a project's drift test can compare the drawing with this option. |
| `coreLayers` | yes | Layers that also ban native methods, null checks, native `Set` and `Map`, and platform imports. |
| `vocabularies` | no | `{ constant, module, names }` for each closed vocabulary. The names may appear as string literals only in `module`. Add a vocabulary's names when you add the vocabulary. |
| `aliases` | no | Names Effect modules are imported under, such as `{ Array: ["Arr"], Schema: ["S"] }`. They are exempt from the native-method ban and count as `Schema`, `Effect`, `Option` and `Result` in the other bans. |
| `sourceRoot` | no | Directory holding the layer directories; default `src`. |
| `testFiles` | no | Test globs; default `test/**/*.ts`. Tests keep the failure, asynchrony, Effect and vocabulary bans and drop the rest. |
| `platformImports` | no | Import patterns banned in core layers; default `node:*`, `bun`, `bun:*`. |
| `project` | no | tsconfig paths; default `./tsconfig.json`. |
| `ignores` | no | Extra ignore globs. |

`buildConfig` throws on a layer table that names an unknown layer and on a
vocabulary with no names.

## What it misses

Every rule group states its blind spots at the top of `eslint.rules.js`. Read
them before relying on a clean lint run.
