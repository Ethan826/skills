// Extracts every ```ts block of a Markdown file into <outdir>/<prefix>-NN.ts,
// prefixed by preludes/<prefix>-NN.ts (stubs for undeclared names) if present.
// Usage: bun extract.ts <file.md> <prefix> <outdir>. Prints the block count.
// Fences are tracked as CommonMark does (``` or ~~~, up to three spaces of
// indent, closed by the same character at least as long). It fails on an
// unterminated fence, and on a fence tagged typescript, tsx, js, javascript,
// mts or cts, because only `ts` blocks are extracted and checked.
import { existsSync, readFileSync, writeFileSync } from "node:fs"
import { join } from "node:path"

const [skill, prefix, outdir] = process.argv.slice(2)
if (!skill || !prefix || !outdir) {
  console.error("usage: bun extract.ts <file.md> <prefix> <outdir>")
  process.exit(2)
}
const unchecked = new Set(["typescript", "tsx", "js", "javascript", "mts", "cts"])
const lines = readFileSync(skill, "utf8").split("\n")
let n = 0
let fence: { char: string; length: number; line: number; body: string[] | null } | null = null
lines.forEach((line, i) => {
  if (fence === null) {
    const open = /^ {0,3}(`{3,}|~{3,})\s*([^\s`]*)/.exec(line)
    if (open === null) return
    const info = open[2].toLowerCase()
    if (unchecked.has(info)) {
      console.error(`untyped-checked fence: ${skill} line ${i + 1} (${info})`)
      process.exit(1)
    }
    fence = { char: open[1][0], length: open[1].length, line: i + 1, body: info === "ts" ? [] : null }
    return
  }
  const close = /^ {0,3}(`{3,}|~{3,})\s*$/.exec(line)
  if (close !== null && close[1][0] === fence.char && close[1].length >= fence.length) {
    if (fence.body !== null) {
      n += 1
      const id = String(n).padStart(2, "0")
      const preludePath = join(import.meta.dir, "preludes", `${prefix}-${id}.ts`)
      const prelude = existsSync(preludePath) ? readFileSync(preludePath, "utf8") : ""
      writeFileSync(join(outdir, `${prefix}-${id}.ts`),
        `${prelude}// ---- ${skill} block ${id}, starting at line ${fence.line + 1} ----\n${fence.body.join("\n")}\n\nexport {}\n`)
    }
    fence = null
    return
  }
  if (fence.body !== null) fence.body.push(line)
})
if (fence !== null) {
  console.error(`unterminated fence: ${skill} line ${(fence as { line: number }).line}`)
  process.exit(1)
}
console.log(n)
