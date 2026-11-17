// The TSDoc gate's own tests (gate-integrity, "The gate's own gate"): inline
// must-fail and must-pass cases with exact findings, then directory runs for
// the clean fixtures (exact scan count), the dirty fixtures (exact findings),
// an unparseable file, an empty directory and a scan minimum above the count.
// Usage: bun cases.ts <tsdoc-gate.ts> <fixtures-dir>
import { mkdtempSync, rmSync } from "node:fs"
import { tmpdir } from "node:os"
import { join, relative } from "node:path"
import ts from "typescript"

const [gatePath, fixtures] = process.argv.slice(2)
if (!gatePath || !fixtures) {
  console.error("usage: bun cases.ts <tsdoc-gate.ts> <fixtures-dir>")
  process.exit(2)
}
const gate = await import(gatePath)
const problems: string[] = []
let cases = 0

const findingsOf = (text: string): string[] => {
  const file = ts.createSourceFile("case.ts", text, ts.ScriptTarget.ES2022, true)
  return gate.checkFile(file, "case.ts").findings.map((f: { message: string }) => f.message)
}
const same = (a: unknown, b: unknown) => JSON.stringify(a) === JSON.stringify(b)
const expectCase = (name: string, got: unknown, want: unknown) => {
  cases += 1
  if (!same(got, want)) problems.push(`${name}: wanted ${JSON.stringify(want)}, got ${JSON.stringify(got)}`)
}
const missing = (name: string) => `${name}: exported without TSDoc`

// Must-fail: one probe per spelling the gate claims to catch.
const mustFail: Array<[string, string, string[]]> = [
  ["no comment", "export const a = 1", [missing("a")]],
  ["a line comment", "// A.\nexport const a = 1", [missing("a")]],
  ["a file-level header only", "// Module header.\n\nexport const a = 1", [missing("a")]],
  ["a plain block comment", "/* A. */\nexport const a = 1", [missing("a")]],
  ["an empty TSDoc comment", "/** */\nexport const a = 1", [missing("a")]],
  ["a TSDoc of stars only", "/**\n *\n */\nexport const a = 1", [missing("a")]],
  ["the shortest block comment", "/**/\nexport const a = 1", [missing("a")]],
  ["a line comment between TSDoc and export", "/** A. */\n// note\nexport const a = 1", [missing("a")]],
  ["TSDoc text inside a string", 'const s = "/** A. */"\nexport const a = s', [missing("a")]],
  ["an undocumented let", "export let a = 1", [missing("a")]],
  ["an undocumented function", "export function f(): void {}", [missing("f")]],
  ["an undocumented class", "export class C {}", [missing("C")]],
  ["an undocumented interface", "export interface I { readonly x: number }", [missing("I")]],
  ["an undocumented type", "export type T = number", [missing("T")]],
  ["an undocumented enum", "export enum E { A }", [missing("E")]],
  ["an undocumented namespace", "export namespace N { export const x = 1 }", [missing("N")]],
  ["an undocumented default export", "export default 1", [missing("default")]],
  ["an undocumented export =", "const a = 1\nexport = a", [missing("export =")]],
  ["an export list of an undocumented const", "const a = 1\nexport { a }", [missing("a")]],
  ["a renamed export of an undocumented const", "const a = 1\nexport { a as b }", [missing("a")]],
  ["an export list naming nothing", "export { ghost }", ["export { ghost } names no declaration in this file"]],
  ["two undocumented exports", "export const a = 1\nexport const b = 2", [missing("a"), missing("b")]],
]
for (const [name, text, want] of mustFail) expectCase(`must fail: ${name}`, findingsOf(text), want)

// Must-pass and near misses: zero findings.
const mustPass: Array<[string, string]> = [
  ["a documented const", "/** A. */\nexport const a = 1"],
  ["a header, then TSDoc", "// header\n\n/** A. */\nexport type A = number"],
  ["a multi-line TSDoc", "/**\n * A.\n */\nexport class C {}"],
  ["an export list of a documented const", "/** A. */\nconst a = 1\nexport { a }"],
  ["a re-export (checked in its own file)", 'export { a } from "./m"\nexport * from "./m"'],
  ["a commented-out export", "// export const a = 1\nconst b = 1"],
  ["an export inside a string", 'const s = "export const a = 1"'],
  ["an undocumented private helper", "const helper = 1"],
  ["an empty export list", "export {}"],
]
for (const [name, text] of mustPass) expectCase(`must pass: ${name}`, findingsOf(text), [])

// Directory runs: exact counts and findings, failing closed on bad input.
const messages = (r: { findings: Array<{ file: string; line: number; message: string }> }) =>
  r.findings.map((f) => `${relative(fixtures, f.file)}:${f.line}: ${f.message}`)
const clean = gate.checkDirs([join(fixtures, "clean")], 9)
expectCase("clean fixtures", { findings: messages(clean), exported: clean.exported, files: clean.files }, { findings: [], exported: 9, files: 2 })
const dirty = gate.checkDirs([join(fixtures, "dirty")], 1)
expectCase("dirty fixtures", messages(dirty), [
  `dirty/mixed.ts:2: ${missing("first")}`,
  `dirty/mixed.ts:8: ${missing("third")}`,
  `dirty/mixed.ts:11: ${missing("fourth")}`,
  `dirty/mixed.ts:14: ${missing("fifth")}`,
])
const broken = gate.checkDirs([join(fixtures, "unparseable")], 1)
expectCase("unparseable file", messages(broken), [
  "unparseable/broken.ts:0: does not parse; the gate cannot check it",
  "unparseable:0: scanned 0 exported declarations, fewer than the minimum 1",
])
const empty = mkdtempSync(join(tmpdir(), "tsdoc-empty-"))
const none = gate.checkDirs([empty], 1).findings.map((f: { message: string }) => f.message)
rmSync(empty, { recursive: true })
expectCase("empty directory", none, ["no TypeScript files to check"])
const floor = gate.checkDirs([join(fixtures, "clean")], 10).findings.map((f: { message: string }) => f.message)
expectCase("scan minimum above the count", floor, ["scanned 9 exported declarations, fewer than the minimum 10"])

for (const p of problems) console.error(`FAIL  ${p}`)
if (problems.length > 0) process.exit(1)
console.log(`${cases} cases`)
