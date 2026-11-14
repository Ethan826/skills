// Checks that the reference config's effectModules list (the receivers the
// native-method ban allows) is exactly the set of namespaces the installed
// effect package exports from its index (`export * as X from ...`). A module
// missing from the list makes every call on it a false positive; a name in
// the list that effect does not export lets a local variable of that name
// escape the ban.
// Usage: bun modules.ts <eslint.rules.js> <node_modules>
import { readFileSync } from "node:fs"
import { join, resolve } from "node:path"

const [rulesPath, modules] = process.argv.slice(2)
if (!rulesPath || !modules) {
  console.error("usage: bun modules.ts <eslint.rules.js> <node_modules>")
  process.exit(2)
}
const { effectModules } = await import(resolve(rulesPath))
const index = readFileSync(join(modules, "effect", "src", "index.ts"), "utf8")
const exported = [...index.matchAll(/^export \* as (\w+) from /gm)].map((m) => m[1])
const listed: string[] = effectModules
const missing = exported.filter((m) => !listed.includes(m))
const extra = listed.filter((m) => !exported.includes(m))
if (exported.length === 0) console.error("found no namespace exports in effect/src/index.ts")
for (const m of missing) console.error(`effect exports ${m}, which effectModules does not list`)
for (const m of extra) console.error(`effectModules lists ${m}, which effect does not export`)
if (exported.length === 0 || missing.length > 0 || extra.length > 0) process.exit(1)
console.log(`effectModules matches effect's ${exported.length} namespace exports`)
