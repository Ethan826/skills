// Checks that package.json pins exact versions, that every anchors.json `tool`
// entry whose check is checks/effect-v4 names a package pinned here at the
// same version, and that the installed packages are the pinned versions.
// Usage: bun versions.ts <anchors.json> <package.json> <node_modules>
import { readFileSync } from "node:fs"
import { join } from "node:path"

const [anchorsPath, packagePath, modules] = process.argv.slice(2)
if (!anchorsPath || !packagePath || !modules) {
  console.error("usage: bun versions.ts <anchors.json> <package.json> <node_modules>")
  process.exit(2)
}
const problems: string[] = []
const pkg = JSON.parse(readFileSync(packagePath, "utf8"))
const pins: Record<string, string> = { ...pkg.dependencies, ...pkg.devDependencies }
for (const [name, pin] of Object.entries(pins)) {
  if (!/^\d+\.\d+\.\d+$/.test(pin)) problems.push(`package.json pins ${name} to "${pin}", not an exact version`)
}
type Anchor = { id: string; kind: string; package?: string; version?: string; check?: string }
const anchors: Anchor[] = JSON.parse(readFileSync(anchorsPath, "utf8")).anchors
const mine = anchors.filter((a) => a.kind === "tool" && a.check === "checks/effect-v4")
if (mine.length === 0) problems.push("anchors.json has no tool entry whose check is checks/effect-v4")
for (const a of mine) {
  const pin = a.package === undefined ? undefined : pins[a.package]
  if (pin === undefined) problems.push(`anchors.json ${a.id} names ${a.package}, which package.json does not pin`)
  else if (pin !== a.version) problems.push(`anchors.json ${a.id} says ${a.version}, package.json pins ${pin}`)
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
