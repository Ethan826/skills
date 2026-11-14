// Checks that package.json pins exact versions; that every anchors.json `tool`
// entry whose check is checks/effect-v4-lint names a package pinned here at
// the same version; that every other pin here equals the version of an
// effect-v4 tool entry for that package (effect is anchored by
// checks/effect-v4 and must not drift apart here); and that the installed
// packages are the pinned versions.
// Usage: bun versions.ts <anchors.json> <package.json> <node_modules>
import { readFileSync } from "node:fs"
import { join } from "node:path"

const [anchorsPath, packagePath, modules] = process.argv.slice(2)
if (!anchorsPath || !packagePath || !modules) {
  console.error("usage: bun versions.ts <anchors.json> <package.json> <node_modules>")
  process.exit(2)
}
const check = "checks/effect-v4-lint"
const problems: string[] = []
const pkg = JSON.parse(readFileSync(packagePath, "utf8"))
const pins: Record<string, string> = { ...pkg.dependencies, ...pkg.devDependencies }
for (const [name, pin] of Object.entries(pins)) {
  if (!/^\d+\.\d+\.\d+$/.test(pin)) problems.push(`package.json pins ${name} to "${pin}", not an exact version`)
}
type Anchor = { id: string; skill: string; kind: string; package?: string; version?: string; check?: string }
const anchors: Anchor[] = JSON.parse(readFileSync(anchorsPath, "utf8")).anchors
const mine = anchors.filter((a) => a.kind === "tool" && a.check === check)
if (mine.length === 0) problems.push(`anchors.json has no tool entry whose check is ${check}`)
for (const a of mine) {
  const pin = a.package === undefined ? undefined : pins[a.package]
  if (pin === undefined) problems.push(`anchors.json ${a.id} names ${a.package}, which package.json does not pin`)
  else if (pin !== a.version) problems.push(`anchors.json ${a.id} says ${a.version}, package.json pins ${pin}`)
}
for (const [name, pin] of Object.entries(pins)) {
  if (mine.some((a) => a.package === name)) continue
  const shared = anchors.filter((a) => a.kind === "tool" && a.skill === "effect-v4" && a.package === name)
  if (shared.length === 0) problems.push(`package.json pins ${name}, which no effect-v4 tool entry anchors`)
  else if (!shared.some((a) => a.version === pin)) {
    problems.push(`package.json pins ${name} ${pin}, anchors.json ${shared.map((a) => a.id).join(", ")} says ${shared.map((a) => a.version).join(", ")}`)
  }
}
for (const [name, pin] of Object.entries(pins)) {
  let installed: string
  try {
    installed = JSON.parse(readFileSync(join(modules, name, "package.json"), "utf8")).version
  } catch {
    problems.push(`${name} is not installed`)
    continue
  }
  if (installed !== pin) problems.push(`installed ${name} is ${installed}, package.json pins ${pin}`)
}
if (problems.length > 0) {
  for (const p of problems) console.error(p)
  process.exit(1)
}
console.log(`versions agree: ${mine.length} anchors, ${Object.keys(pins).length} pins`)
