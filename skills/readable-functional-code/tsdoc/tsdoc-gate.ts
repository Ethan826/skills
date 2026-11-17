// TSDoc gate: every exported declaration in the scanned TypeScript files
// carries a TSDoc comment (`/** ... */` with some text) as the last comment
// directly above it. Decided on the TypeScript syntax tree, not on text, so a
// "/** ... */" inside a string does not count and a commented-out export is
// not an export.
//
// What counts as an exported declaration: a statement with the `export`
// modifier (const, let, function, class, interface, type, enum, namespace),
// `export default <expression>` and `export = <expression>`, and each name in
// a local `export { a, b }` list, which needs TSDoc on its local declaration.
//
// Fails closed: a file with a syntax error, an `export { a }` naming nothing
// declared in the file, no files at all, or fewer exported declarations than
// --min is a failure with a named message, never a skip.
//
// Blind spots. Presence only: it does not judge whether a comment is
// accurate, complete or more than the name restated. Private code is not
// checked; the rule asks for TSDoc on a private helper with a rule in it,
// and that part rests on review. Re-exports (`export { a } from "./m"`,
// `export * from "./m"`) are not checked here; the declaration is checked in
// its own file when that file is scanned. Class members and interface fields
// are not checked. Each overload signature of an exported function counts as
// its own declaration, so overloads need TSDoc on each (over-matching).
// `.d.ts` files and files outside the given directories are not scanned.
//
// Usage: bun tsdoc-gate.ts [--min N] DIR...
//   Scans every *.ts and *.tsx file under each DIR (skipping .d.ts and
//   node_modules). Exit 0 when every exported declaration has TSDoc and at
//   least N were scanned (default 1); exit 1 with one line per finding.
import { readdirSync, readFileSync, statSync } from "node:fs"
import { join } from "node:path"
import ts from "typescript"

/** One problem the gate reports, as `file:line: message`. */
export interface Finding {
  readonly file: string
  readonly line: number
  readonly message: string
}

/** The result of checking one file: its findings and its export count. */
export interface FileResult {
  readonly findings: ReadonlyArray<Finding>
  readonly exported: number
}

const hasExportModifier = (node: ts.Node): boolean =>
  ts.canHaveModifiers(node) &&
  (ts.getModifiers(node) ?? []).some(
    (modifier) => modifier.kind === ts.SyntaxKind.ExportKeyword,
  )

/**
 * True when the last comment directly above `node` is a TSDoc comment with
 * some text in it. `/**\/` and `/** *\/` do not count; neither does a line
 * comment or a plain block comment, even with a TSDoc comment above it.
 */
const hasTsDoc = (node: ts.Node, text: string): boolean => {
  const ranges = ts.getLeadingCommentRanges(text, node.pos) ?? []
  const last = ranges[ranges.length - 1]
  if (last === undefined || last.kind !== ts.SyntaxKind.MultiLineCommentTrivia) return false
  const comment = text.slice(last.pos, last.end)
  if (!comment.startsWith("/**") || comment === "/**/") return false
  return comment.slice(3, -2).replace(/[\s*]/g, "").length > 0
}

const nameOf = (statement: ts.Statement): string => {
  if (ts.isVariableStatement(statement))
    return statement.declarationList.declarations.map((d) => d.name.getText()).join(", ")
  if (ts.isExportAssignment(statement)) return statement.isExportEquals ? "export =" : "default"
  const named = statement as ts.Statement & { name?: ts.Node }
  return named.name === undefined ? "default" : named.name.getText()
}

/** The top-level statement in `file` that declares `name`, if any. */
const declarationOf = (file: ts.SourceFile, name: string): ts.Statement | undefined =>
  file.statements.find((statement) => {
    if (ts.isVariableStatement(statement))
      return statement.declarationList.declarations.some((d) => d.name.getText() === name)
    if (ts.isImportDeclaration(statement) || ts.isExportDeclaration(statement)) return false
    const named = statement as ts.Statement & { name?: ts.Node }
    return named.name !== undefined && named.name.getText() === name
  })

/**
 * Checks one parsed file. Each exported declaration without TSDoc is a
 * finding named after the declaration; a local export list naming nothing
 * declared in the file is a finding too, because the gate cannot resolve it.
 */
export const checkFile = (file: ts.SourceFile, path: string): FileResult => {
  const text = file.text
  const findings: Finding[] = []
  let exported = 0
  const report = (node: ts.Node, message: string) =>
    findings.push({ file: path, line: file.getLineAndCharacterOfPosition(node.getStart(file)).line + 1, message })
  for (const statement of file.statements) {
    if (ts.isExportDeclaration(statement)) {
      if (statement.moduleSpecifier !== undefined || statement.exportClause === undefined) continue
      if (!ts.isNamedExports(statement.exportClause)) continue
      for (const element of statement.exportClause.elements) {
        exported += 1
        const local = (element.propertyName ?? element.name).getText(file)
        const declaration = declarationOf(file, local)
        if (declaration === undefined) report(element, `export { ${local} } names no declaration in this file`)
        else if (!hasTsDoc(declaration, text)) report(element, `${local}: exported without TSDoc`)
      }
      continue
    }
    if (!ts.isExportAssignment(statement) && !hasExportModifier(statement)) continue
    exported += 1
    if (!hasTsDoc(statement, text)) report(statement, `${nameOf(statement)}: exported without TSDoc`)
  }
  return { findings, exported }
}

/** Every *.ts and *.tsx file under `dir`, skipping .d.ts and node_modules. */
const sourcesUnder = (dir: string): string[] =>
  readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry)
    if (statSync(path).isDirectory()) return entry === "node_modules" ? [] : sourcesUnder(path)
    return /\.tsx?$/.test(entry) && !entry.endsWith(".d.ts") ? [path] : []
  })

/**
 * Checks every source file under `dirs`. Fails closed: a syntax error, no
 * files, or fewer than `min` exported declarations is a finding.
 */
export const checkDirs = (dirs: ReadonlyArray<string>, min: number): { findings: Finding[]; exported: number; files: number } => {
  const paths = dirs.flatMap(sourcesUnder)
  const program = ts.createProgram(paths, { noResolve: true, noLib: true, types: [], jsx: ts.JsxEmit.Preserve })
  const findings: Finding[] = []
  let exported = 0
  for (const path of paths) {
    const file = program.getSourceFile(path)
    const syntax = file === undefined ? [] : program.getSyntacticDiagnostics(file)
    if (file === undefined || syntax.length > 0) {
      findings.push({ file: path, line: 0, message: "does not parse; the gate cannot check it" })
      continue
    }
    // Program files have no parent pointers; re-parse with them for names.
    const parsed = ts.createSourceFile(path, file.text, ts.ScriptTarget.Latest, true)
    const result = checkFile(parsed, path)
    findings.push(...result.findings)
    exported += result.exported
  }
  if (paths.length === 0) findings.push({ file: dirs.join(" "), line: 0, message: "no TypeScript files to check" })
  else if (exported < min) findings.push({ file: dirs.join(" "), line: 0, message: `scanned ${exported} exported declarations, fewer than the minimum ${min}` })
  return { findings, exported, files: paths.length }
}

if (import.meta.main) {
  const args = process.argv.slice(2)
  const minAt = args.indexOf("--min")
  const min = minAt === -1 ? 1 : Number(args[minAt + 1])
  const dirs = minAt === -1 ? args : args.filter((_, i) => i !== minAt && i !== minAt + 1)
  if (dirs.length === 0 || !Number.isInteger(min) || min < 1) {
    console.error("usage: bun tsdoc-gate.ts [--min N] DIR...   (N a positive integer)")
    process.exit(2)
  }
  const { findings, exported, files } = checkDirs(dirs, min)
  for (const f of findings) console.log(`${f.file}:${f.line}: ${f.message}`)
  if (findings.length > 0) {
    console.log(`tsdoc gate: FAIL (${findings.length} findings, ${exported} exported declarations in ${files} files)`)
    process.exit(1)
  }
  console.log(`tsdoc gate: OK (${exported} exported declarations in ${files} files)`)
}
