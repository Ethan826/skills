// Lints fixtures/ with the reference config and compares the result with
// expected.json. Fails when a fixture is unlisted or listed but missing, when
// a must-fail fixture lacks any expected (rule, message) pair, when a native
// method is not reported by name, when a clean control reports anything, or
// when any file has a parse error (a message with no rule).
// Usage: bun lint.ts <fixtures-dir> <expected.json>
import { readFileSync, realpathSync } from "node:fs"
import { relative } from "node:path"
import { ESLint } from "eslint"

const [rootArg, expectedPath] = process.argv.slice(2)
if (!rootArg || !expectedPath) {
  console.error("usage: bun lint.ts <fixtures-dir> <expected.json>")
  process.exit(2)
}
type Pair = [string, string]
const expected: {
  nativeMethods: Record<string, string[]>
  mustFail: Record<string, Pair[]>
  clean: string[]
} = JSON.parse(readFileSync(expectedPath, "utf8"))

const wants: Record<string, Pair[]> = { ...expected.mustFail }
for (const [file, methods] of Object.entries(expected.nativeMethods)) {
  wants[file] = [
    ...(wants[file] ?? []),
    ...methods.map((m): Pair => ["no-restricted-properties", `'${m}' is restricted`]),
  ]
}

// Real paths on both sides: a temporary directory under a symlink (macOS
// /var) would otherwise give paths that do not share a prefix.
const root = realpathSync(rootArg)
const eslint = new ESLint({ cwd: root })
const results = await eslint.lintFiles(["src/**/*.ts", "test/**/*.ts"])
const linted = new Map(results.map((r) => [relative(root, realpathSync(r.filePath)), r]))
const problems: string[] = []

const listed = [...Object.keys(wants), ...expected.clean]
const duplicates = listed.filter((f, i) => listed.indexOf(f) !== i)
for (const f of duplicates) problems.push(`listed twice in expected.json: ${f}`)
for (const f of linted.keys()) if (!listed.includes(f)) problems.push(`fixture not in expected.json: ${f}`)
for (const f of listed) if (!linted.has(f)) problems.push(`listed but not linted: ${f}`)

for (const [file, pairs] of Object.entries(wants)) {
  const messages = linted.get(file)?.messages ?? []
  for (const [rule, text] of pairs) {
    if (!messages.some((m) => m.ruleId === rule && m.message.includes(text))) {
      problems.push(`${file}: expected ${rule} "${text}", got ${JSON.stringify(messages.map((m) => `${m.ruleId}: ${m.message}`))}`)
    }
  }
}
for (const file of expected.clean) {
  for (const m of linted.get(file)?.messages ?? []) {
    problems.push(`clean control ${file}: ${m.ruleId}: ${m.message} (line ${m.line})`)
  }
}
for (const [file, r] of linted) {
  for (const m of r.messages) if (m.ruleId === null) problems.push(`parse error in ${file}: ${m.message}`)
}

if (problems.length > 0) {
  for (const p of problems) console.error(p)
  process.exit(1)
}
const nMustFail = Object.keys(wants).length
const nPairs = Object.values(wants).reduce((n, ps) => n + ps.length, 0)
console.log(`${nMustFail} must-fail fixtures (${nPairs} expected reports), ${expected.clean.length} clean controls`)
