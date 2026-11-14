// Compares tsc's output for tsconfig.mustfail.json with expected.json: the
// number of `error TS` lines must equal mustFailErrors, and the errors, as
// "line:code" in mustfail-raw/must-fail.ts, must equal mustFailAt exactly
// (same multiset). A total alone could stay the same while the errors moved.
// Usage: bun mustfail.ts <tsc-output> <expected.json>
import { readFileSync } from "node:fs"

const [outputPath, expectedPath] = process.argv.slice(2)
if (!outputPath || !expectedPath) {
  console.error("usage: bun mustfail.ts <tsc-output> <expected.json>")
  process.exit(2)
}
const expected = JSON.parse(readFileSync(expectedPath, "utf8"))
const want: string[] = [...expected.mustFailAt].sort()
if (want.length !== expected.mustFailErrors) {
  console.error(`expected.json is inconsistent: mustFailErrors is ${expected.mustFailErrors}, mustFailAt lists ${want.length}`)
  process.exit(1)
}
const errorLines = readFileSync(outputPath, "utf8").split("\n").filter((l) => l.includes("error TS"))
if (errorLines.length !== want.length) {
  console.error(`expected ${want.length} must-fail errors, found ${errorLines.length}`)
  process.exit(1)
}
const got = errorLines.map((l) => {
  const m = /^mustfail-raw\/must-fail\.ts\((\d+),\d+\): error (TS\d+):/.exec(l)
  return m === null ? `unparsed: ${l}` : `${m[1]}:${m[2]}`
}).sort()
if (got.join("\n") !== want.join("\n")) {
  const missing = want.filter((w) => !got.includes(w))
  const unexpected = got.filter((g) => !want.includes(g))
  console.error(`must-fail errors differ: missing [${missing.join(", ")}], unexpected [${unexpected.join(", ")}]`)
  console.error(`expected ${want.join(", ")}; found ${got.join(", ")}`)
  process.exit(1)
}
console.log(`${got.length} must-fail errors, at ${got.join(", ")}`)
