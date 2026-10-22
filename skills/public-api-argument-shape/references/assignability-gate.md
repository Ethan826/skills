# An assignability gate for argument shape, in TypeScript

Read this when you are writing the gate described in SKILL.md. It is an
illustration of the method, not a drop-in tool: adapt the entry modules, the
runner and the floor to the project.

It needs TypeScript 5.4 or later, the first release whose `typescript.d.ts`
declares `checker.isTypeAssignableTo` as public. The code below, with its
tests, was run against TypeScript 5.4.2 and 5.9.3 on Node 26's built-in
test runner, which strips the type annotations itself, and it type-checks
under `tsc --strict`. Any runner works.

## The analysis

It reports Rule 1 (two parameters where either type is assignable to the
other) and Rule 2 (positional optionals and positional booleans) over the
public callable surface, and nothing else. It does not walk syntax looking
for function-shaped nodes, because there are too many: a declaration, an
exported arrow or function expression, a renamed or default export, a
method, a function-typed property, a call or construct signature, a
constructor, a class field holding an arrow. It asks the checker instead.
For each export of the entry modules it takes the export's type (and, for
a class, interface or type alias, its declared type), reads every call and
construct signature of that type, then does the same for each public
member declared in the project, and for the function type of each
parameter, which is an injected callback. Function bodies are never
entered, so internal closures and unexported helpers stay exempt, as
SKILL.md's scope says.

It refuses to run over a program with compiler errors. A syntax error or
an unresolved type would otherwise leave a signature unread or typed as
`any`, and the gate would pass on code it could not see. It counts every
signature it reads, so a test can put a floor under that count.

```ts
import ts from "typescript";

export interface Report {
  readonly findings: ReadonlyArray<string>;
  readonly signaturesRead: number;
}

const kinds = [ts.SignatureKind.Call, ts.SignatureKind.Construct] as const;

const isHidden = (member: ts.Symbol): boolean =>
  member.getName() === "prototype" ||
  member.getName().startsWith("#") ||
  (member.declarations ?? []).some(
    (d) => (ts.getCombinedModifierFlags(d) & (ts.ModifierFlags.Private | ts.ModifierFlags.Protected)) !== 0,
  );

// Assignability gate over the public callable surface: the exports of the
// entry modules, every call and construct signature of their types, the
// public members of those types, and the callback types in their parameters.
// Nothing inside a function body is visited, so internal closures are exempt.
export const analyze = (program: ts.Program, entries: ReadonlyArray<string>): Report => {
  const errors = ts.getPreEmitDiagnostics(program).filter((d) => d.category === ts.DiagnosticCategory.Error);
  if (errors.length > 0) {
    throw new Error(ts.formatDiagnostics(errors, {
      getCanonicalFileName: (f) => f,
      getCurrentDirectory: () => process.cwd(),
      getNewLine: () => "\n",
    }));
  }
  const checker = program.getTypeChecker();
  const findings: Array<string> = [];
  const seen = new Set<ts.Signature>();
  const isOurs = (node: ts.Node | undefined): boolean => {
    const file = node?.getSourceFile();
    return file !== undefined && !program.isSourceFileDefaultLibrary(file) && !program.isSourceFileFromExternalLibrary(file);
  };
  const at = (node: ts.Node | undefined): string => {
    if (node === undefined) return "?";
    const file = node.getSourceFile();
    return `${file.fileName}:${file.getLineAndCharacterOfPosition(node.getStart()).line + 1}`;
  };

  const check = (signature: ts.Signature, where: string): void => {
    const declaration = signature.getDeclaration() as ts.SignatureDeclaration | undefined;
    if (seen.has(signature) || !isOurs(declaration)) return;
    seen.add(signature);
    const params = signature.getParameters().map((symbol) => ({
      symbol,
      node: symbol.valueDeclaration as ts.ParameterDeclaration | undefined,
      name: symbol.getName(),
      type: checker.getTypeOfSymbol(symbol),
    }));
    const label = `${at(declaration)} ${where}`;
    params.forEach((a, i) =>
      params.slice(i + 1).forEach((b) => {
        if (checker.isTypeAssignableTo(a.type, b.type) || checker.isTypeAssignableTo(b.type, a.type)) {
          findings.push(`${label}: ${a.name} and ${b.name} are interchangeable`);
        }
      }),
    );
    params.forEach(({ node, name, type }) => {
      if (node !== undefined && checker.isOptionalParameter(node)) {
        findings.push(`${label}: ${name} is a positional optional`);
      }
      if ((type.flags & ts.TypeFlags.BooleanLike) !== 0) {
        findings.push(`${label}: ${name} is a positional boolean`);
      }
      // A parameter's own function type is an injected callback: check it too.
      kinds.forEach((kind) =>
        checker.getSignaturesOfType(type, kind).forEach((s) => check(s, `${where} callback ${name}`)),
      );
    });
  };

  const signaturesOf = (type: ts.Type, where: string): void =>
    kinds.forEach((kind) =>
      checker.getSignaturesOfType(type, kind).forEach((s) =>
        check(s, kind === ts.SignatureKind.Construct ? `new ${where}` : where),
      ),
    );

  // A type's own signatures, then those of each public member declared in this project.
  const surface = (type: ts.Type, where: string): void => {
    signaturesOf(type, where);
    checker.getPropertiesOfType(type)
      .filter((member) => !isHidden(member) && (member.declarations ?? []).some(isOurs))
      .forEach((member) => signaturesOf(checker.getTypeOfSymbol(member), `${where}.${member.getName()}`));
  };

  entries.forEach((entry) => {
    const source = program.getSourceFile(entry);
    if (source === undefined) throw new Error(`not in program: ${entry}`);
    const moduleSymbol = checker.getSymbolAtLocation(source);
    if (moduleSymbol === undefined) throw new Error(`not a module (no exports): ${entry}`);
    checker.getExportsOfModule(moduleSymbol).forEach((exported) => {
      const symbol = (exported.flags & ts.SymbolFlags.Alias) !== 0 ? checker.getAliasedSymbol(exported) : exported;
      const where = exported.getName();
      if ((symbol.flags & ts.SymbolFlags.Value) !== 0) surface(checker.getTypeOfSymbol(symbol), where);
      if ((symbol.flags & ts.SymbolFlags.Type) !== 0) surface(checker.getDeclaredTypeOfSymbol(symbol), where);
    });
  });
  return { findings, signaturesRead: seen.size };
};

// Builds a one-file program from inline source, for the probes.
export const analyzeInline = (source: string): Report => {
  const file = "probe.ts";
  const options: ts.CompilerOptions = { strict: true, noEmit: true };
  const host = ts.createCompilerHost(options);
  const readFromDisk = host.getSourceFile;
  host.getSourceFile = (name, version) =>
    name === file ? ts.createSourceFile(file, source, version, true) : readFromDisk(name, version);
  return analyze(ts.createProgram([file], options, host), [file]);
};
```

## The test, with its self-checks

There is one planted violation per supported form, each an alias beside
its base type, which a written-type gate would miss, so the probe proves
the gate's kind as well as its detector. The near miss holds two
distinct brands of one base type, a record whose fields share a type, an
internal closure with two `number` parameters inside an exported
function, a private method and an unexported helper; all are legal under
the rules, and the probe also asserts how many signatures were read, so
it fails if the exempt ones start being counted. Two more probes show
that a syntax error and an unresolved type fail the gate. The last test
runs the analysis over the real API and puts a floor under the number of
signatures read. Set the floor near the real count and raise it as the
API grows.

```ts
import assert from "node:assert/strict";
import { test } from "node:test";
import ts from "typescript";
import { analyze, analyzeInline } from "./argument-shape.ts";

// One planted violation per supported form. An alias beside its base type,
// which a written-type gate would miss, so the probe proves the gate's kind too.
const planted: ReadonlyArray<readonly [string, string]> = [
  ["function declaration", `export function f(a: Note, b: string): void {}`],
  ["exported arrow", `export const f = (a: Note, b: string): void => {};`],
  ["function expression", `export const f = function (a: Note, b: string): void {};`],
  ["renamed export", `const g = (a: Note, b: string): void => {}; export { g as f };`],
  ["default export", `export default (a: Note, b: string): void => {};`],
  ["interface method", `export interface I { m(a: Note, b: string): void }`],
  ["function-typed property", `export interface I { readonly m: (a: Note, b: string) => void }`],
  ["call signature", `export interface I { (a: Note, b: string): void }`],
  ["construct signature", `export interface I { new (a: Note, b: string): object }`],
  ["function type alias", `export type F = (a: Note, b: string) => void;`],
  ["constructor", `export class C { constructor(a: Note, b: string) {} }`],
  ["class method", `export class C { m(a: Note, b: string): void {} }`],
  ["static method", `export class C { static m(a: Note, b: string): void {} }`],
  ["arrow class field", `export class C { readonly m = (a: Note, b: string): void => {}; }`],
  ["object of functions", `export const api = { m: (a: Note, b: string): void => {} };`],
  ["callback parameter", `export const f = (run: (a: Note, b: string) => void): void => {};`],
];

planted.forEach(([form, source]) =>
  test(`planted violation, ${form}: exactly one finding`, () => {
    const { findings } = analyzeInline(`type Note = string;\n${source}`);
    assert.equal(findings.length, 1, findings.join("\n"));
  }),
);

test("near miss: brands, records, private members and internal closures give none", () => {
  const { findings, signaturesRead } = analyzeInline(`
    type OrderId = string & { readonly __brand: "OrderId" };
    type ShelfId = string & { readonly __brand: "ShelfId" };
    export interface Orders {
      move(order: OrderId, shelf: ShelfId): void;
      swap(pair: { readonly first: OrderId; readonly second: OrderId }): void;
    }
    export const total = (prices: ReadonlyArray<number>): number => {
      const add = (a: number, b: number): number => a + b;
      return prices.reduce(add, 0);
    };
    export class Ledger { private merge(a: string, b: string): void {} }
    function helper(a: string, b: string): void {}
  `);
  assert.deepEqual(findings, []);
  assert.equal(signaturesRead, 3); // move, swap, total
});

test("a parse error or an unresolved type fails the gate instead of passing it", () => {
  assert.throws(() => analyzeInline(`export const f = (a: string, b: string => {};`));
  assert.throws(() => analyzeInline(`export const f = (a: Missing): void => {};`));
});

test("the public API has no findings, and enough signatures were read", () => {
  const entries = ["src/api.ts"];
  const { findings, signaturesRead } = analyze(
    ts.createProgram(entries, { strict: true, noEmit: true }),
    entries,
  );
  assert.deepEqual(findings, []);
  assert.ok(signaturesRead >= 2, `read only ${signaturesRead} signatures`);
});
```

Before trusting the gate, break it on purpose: replace the
assignability condition with `false` and check that every planted probe
fails, then put back a transposable signature in the real API and check
that the last test names it. Done to the code above, the first step fails
all sixteen planted probes and leaves the near miss, the error probes and
the real-API test passing.

When adding a form the project uses (a getter returning a function, a
namespace two levels deep), add its planted probe first and watch it
fail. The earlier version of this sketch matched four syntax node kinds
and read zero signatures for an exported arrow, a function expression, a
call or construct signature, a constructor, a renamed or default export,
an arrow class field and an object of functions, while still reporting
other interfaces, so a signature floor met elsewhere hid the gap.

## Behavior worth knowing

- **Callback types are visited.** A function type in a parameter or a
  public member is checked as its own signature, so an injected
  `(owner, member) => ...` callback is covered. Each signature is read
  once however many routes reach it.
- **Members are read one level deep.** `export const api = { m }` is
  covered; `api.orders.move` is not. Export nested surfaces directly, or
  extend `surface` and plant a probe for it.
- **Private and protected members, `#` fields and `prototype` are
  skipped,** as are signatures and members declared in the default
  library or in `node_modules`, so `export const names = ["a"]` does not
  pull in every `Array` method. An implicit constructor has no
  declaration and is not counted.
- **Any compiler error in the program fails the gate,** including errors
  outside the entry modules. If that is too broad, filter the diagnostics
  to the files the gate covers, but keep failing on syntax errors and
  unresolved names there.
- **`any` and `unknown` parameters collide with everything.** Every type
  is assignable to `unknown`, and `any` is assignable both ways. In a
  public signature that is usually a finding worth having. If the
  project disagrees, exclude them explicitly and say so beside the rule.
- **A generic signature `f<T>(a: T, b: T)` collides,** because both
  parameters have the same type. Two unrelated type parameters `T` and
  `U` do not.
- **A branded ID beside its own base type collides** (`OrderId` beside
  `string`), because the brand is assignable to the base. Brand the
  other parameter or use a record.
- **An optional boolean is reported once, as an optional.** Its type is
  `boolean | undefined`, which does not carry the boolean flag. Both
  fixes are the same: a record field.
- **Unannotated parameters** get whatever type the checker infers, often
  `any`. Projects that run this gate usually also require annotations
  on exported signatures.
