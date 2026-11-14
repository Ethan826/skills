// The reference config with the example parameters the fixtures are written
// against. run.sh copies skills/effect-v4/lint/eslint.rules.js to the parent
// of this directory.
import { fileURLToPath } from "node:url"
import { buildConfig } from "../eslint.rules.js"

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
    { constant: "Channels", module: "src/domain/channels.ts", names: ["email", "sms"] },
    { constant: "Priorities", module: "src/domain/priorities.ts", names: ["low", "normal", "urgent"] },
    { constant: "Kinds", module: "src/format/kinds.ts", names: ["result", "failure"] },
    { constant: "Sources", module: "src/format/sources.ts", names: ["file", "pipe"] },
  ],
  aliases: { Array: ["Arr"], Schema: ["S"] },
})
