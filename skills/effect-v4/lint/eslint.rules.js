// Reference ESLint config for TypeScript with Effect v4 in a decision-core
// application (skills effect-v4 and decision-core-architecture). Checked by
// checks/effect-v4-lint against eslint 9.39.2, @eslint/js 9.39.2,
// typescript-eslint 8.54.0, eslint-plugin-functional 9.0.4, typescript 5.9.3
// and effect 4.1.4. README.md in this directory says how a project copies it.
//
// A project calls buildConfig with its own layer table, core layers, closed
// vocabularies and import aliases; nothing project-specific is written here.
// No rule here may be switched off by a comment: the project's instruction
// file should forbid lint-disable comments.
//
// Blind spots, by group (gate-integrity: each gate states what it misses):
//
// - Syntax bans (loops, collections, failures, asynchrony, Effect and Schema
//   bans, JSON) match the names `Schema`, `Effect`, `Option`, `Result`,
//   `JSON` and `Promise`, plus the aliases passed in `aliases`. A rename on
//   import that is not listed (`import { Schema as Sch }`) or destructuring
//   (`const { decode } = Schema`) escapes the member-access selectors; the
//   named-import ban still catches `import { decode } from "effect/Schema"`.
//   `Effect.promise` is flagged everywhere, with no allowlist.
// - Native methods in core layers: core no-restricted-properties with
//   `allowObjects`, which is name-based, not type-aware (neither
//   typescript-eslint nor eslint-plugin-functional has a rule keyed on the
//   receiver's type). A receiver whose name is an Effect module name (a
//   local `Option` holding a plain array) escapes; an Effect module imported
//   under an alias not passed in `aliases` is flagged (a false positive: add
//   the alias); a method reached without naming it (`Reflect.apply`, a
//   helper outside core) escapes; methods not in the lists below escape.
// - Null checks in core layers match the literal `null`, the identifier
//   `undefined` and `typeof x === "undefined"`; a comparison against a
//   variable that holds undefined escapes.
// - Layer imports match directory names in the specifier (`**/features/**`),
//   so a path that does not name the layer escapes, and so does a layer
//   directory outside `sourceRoot`.
// - Closed vocabularies: (1) Schema.Literals and Schema.Literal may not take
//   inline literals. This matches the callee spelled `Schema.` or a listed
//   alias only (a destructured `Literals(...)` escapes), covers elements of
//   a direct array argument but not literals built elsewhere and passed in,
//   and does not cover Schema.TaggedStruct, TaggedClass, tag or Enum. (2) The
//   names of each vocabulary in `vocabularies` may not appear as string
//   literals outside that vocabulary's module, in source or tests. This
//   matches string Literal nodes (including in type position) but not
//   identifier keys (`{ email: 1 }`), template literals or strings assembled
//   at run time, and covers only the names listed.
import js from "@eslint/js"
import functional from "eslint-plugin-functional"
import { defineConfig } from "eslint/config"
import tseslint from "typescript-eslint"

const message = (selector, text) => ({ selector, message: text })
const escapeRegExp = (text) => text.replace(/[.*+?^${}()|[\]\\/]/g, "\\$&")
const nameRegExp = (names) => `/^(${names.map(escapeRegExp).join("|")})$/`

// Every namespace the effect 4.1.4 package exports. Members of these (and of
// their aliases) are Effect functions, not native methods.
export const effectModules = [
  "Arbitrary", "Array", "BigDecimal", "BigInt", "Boolean", "Brand", "Bytes",
  "ByteSize", "Cache", "Cause", "Channel", "ChannelSchema", "Chunk", "Clock",
  "Combiner", "Config", "ConfigProvider", "Console", "Context", "Cron", "Data",
  "DateTime", "Deferred", "Differ", "Duration", "Effect", "Effectable",
  "Equal", "Equivalence", "ErrorReporter", "ExecutionPlan", "Exit", "Fiber",
  "FiberHandle", "FiberMap", "FiberSet", "FileSystem", "Filter", "Formatter",
  "Function", "Glob", "Graph", "Hash", "HashMap", "HashRing", "HashSet", "HKT",
  "Inspectable", "Iterable", "JsonPatch", "JsonPointer", "JsonSchema", "Latch",
  "Layer", "LayerMap", "LayerRef", "Logger", "LogLevel", "ManagedRuntime",
  "Match", "Metric", "MutableHashMap", "MutableHashSet", "MutableList",
  "MutableRef", "Newtype", "NonEmptyIterable", "Number", "Optic", "Option",
  "Order", "Ordering", "PartitionedSemaphore", "Path", "Pipeable",
  "PlatformError", "Pool", "Predicate", "PrimaryKey", "PubSub", "Pull", "Queue",
  "Random", "Rational", "RcMap", "RcRef", "Record", "Redactable", "Redacted",
  "Reducer", "Ref", "References", "RegExp", "Request", "RequestResolver",
  "Resource", "Result", "Runtime", "Schedule", "Scheduler", "Schema",
  "SchemaAST", "SchemaGetter", "SchemaIssue", "SchemaParser",
  "SchemaRepresentation", "SchemaTransformation", "Scope", "ScopedCache",
  "ScopedRef", "Semaphore", "SemVer", "SemVerRange", "Sink", "StandardSchema",
  "Stdio", "Stream", "String", "Struct", "SubscriptionRef", "Symbol",
  "SynchronizedRef", "Take", "Terminal", "TextDiff", "Tracer", "Trie", "Tuple",
  "TxChunk", "TxDeferred", "TxHashMap", "TxHashSet", "TxPriorityQueue",
  "TxPubSub", "TxQueue", "TxReentrantLock", "TxRef", "TxSemaphore",
  "TxSubscriptionRef", "Types", "UndefinedOr", "Unify", "Utils", "Version",
]

const nativeArrayMethods = [
  "map", "filter", "some", "every", "find", "findIndex", "findLast",
  "findLastIndex", "reduce", "reduceRight", "flatMap", "flat", "forEach",
  "includes", "indexOf", "lastIndexOf", "slice", "concat", "join", "sort",
  "toSorted", "reverse", "toReversed", "at", "fill", "splice", "toSpliced",
]
const nativeStringMethods = [
  "split", "trim", "trimStart", "trimEnd", "toLowerCase", "toUpperCase",
  "startsWith", "endsWith", "replace", "replaceAll", "padStart", "padEnd",
  "substring", "charAt", "repeat", "localeCompare", "normalize",
]

const throwingSchema = [
  "decode", "decodeSync", "decodeUnknownSync", "encodeSync", "encodeUnknownSync",
  "decodePromise", "decodeUnknownPromise", "encodePromise",
  "encodeUnknownPromise", "asserts",
]

const loops = [
  message("ForStatement", "Use Array.map / filter / Effect.forEach, not for."),
  message("ForInStatement", "Use Record.keys / Record.toEntries, not for...in."),
  message("ForOfStatement", "Use Array.map / Effect.forEach, not for...of."),
  message("WhileStatement", "Use a combinator or recursion, not while."),
  message("DoWhileStatement", "Use a combinator or recursion, not do...while."),
]

const collections = [
  message(
    "MemberExpression[computed=true][property.type='Literal'][property.value=0]",
    "Use Array.head (returns Option) instead of array[0].",
  ),
  message(
    "CallExpression[callee.property.name='push']",
    "Use Array.append / Array.appendAll instead of .push().",
  ),
  message(
    "MemberExpression[property.name='length']:not(CallExpression > .callee)",
    "Use Array.isReadonlyArrayEmpty / Array.isReadonlyArrayNonEmpty / Array.length.",
  ),
]

const failures = [
  message("TryStatement", "Use Effect.try / Effect.catchTag, not try/catch."),
  message("ThrowStatement", "Use Effect.fail with a tagged error, not throw."),
  message(
    "BinaryExpression[operator='instanceof']",
    "Use Match.tag or Schema.is, not instanceof.",
  ),
  message(
    "MemberExpression[property.name='_tag']",
    "Do not read _tag; use Match.tag or a guard such as Schema.is.",
  ),
  message(
    "BinaryExpression[operator='in'][left.value='_tag']",
    "Do not test for _tag; use Match.tag or a guard such as Schema.is.",
  ),
]

const asynchrony = [
  message("NewExpression[callee.name='Promise']", "No Promise in core code."),
  message("MemberExpression[object.name='Promise']", "No Promise in core code."),
  message("TSTypeReference[typeName.name='Promise']", "No Promise in core code."),
  message("AwaitExpression", "No await in core code."),
  message("FunctionDeclaration[async=true]", "No async function in core code."),
  message("FunctionExpression[async=true]", "No async function in core code."),
  message("ArrowFunctionExpression[async=true]", "No async function in core code."),
]

const parsing = [
  message("MemberExpression[object.name='JSON']", "JSON.parse and JSON.stringify throw; use Schema.fromJsonString."),
]

const nullish = [
  message(
    "BinaryExpression[operator=/^[!=]==?$/]:matches([left.type='Identifier'][left.name='undefined'], [right.type='Identifier'][right.name='undefined'])",
    "Comparing with undefined: use Option.fromNullishOr where the value enters core, then Option.match.",
  ),
  message(
    "BinaryExpression[operator=/^[!=]==?$/]:matches([left.type='Literal'][left.raw='null'], [right.type='Literal'][right.raw='null'])",
    "Comparing with null: use Option.fromNullishOr where the value enters core, then Option.match.",
  ),
  message(
    "BinaryExpression[operator=/^[!=]==?$/] > UnaryExpression[operator='typeof']",
    "typeof comparisons: use Option.fromNullishOr or a Predicate guard such as Predicate.isString.",
  ),
  message(
    "LogicalExpression[operator='??']",
    "?? on a nullable value: use Option.getOrElse, or Combiner/Reducer for a merge.",
  ),
  message(
    "ChainExpression",
    "Optional chaining on a nullable value: use Option.map / Option.flatMap.",
  ),
]

const nativeCollections = [
  message(
    "NewExpression[callee.name=/^(Set|Map|WeakSet|WeakMap)$/]",
    "Native Set and Map are mutable; use HashSet / HashMap, or Array.dedupe.",
  ),
]

const noRestrictedSyntax = (...groups) => ["error", ...groups.flat()]

const requireArray = (name, value) => {
  if (!Array.isArray(value) || !value.every((item) => typeof item === "string" && item !== "")) {
    throw new TypeError(`buildConfig: ${name} must be an array of non-empty strings`)
  }
  return value
}

/**
 * Builds the flat config.
 *
 * @param {object} options
 * @param {string} options.tsconfigRootDir  directory of the tsconfig used for
 *   type-aware rules (usually the directory of eslint.config.js)
 * @param {Record<string, string[]>} options.layers  layer table: each layer
 *   directory under sourceRoot, mapped to the layers it may import. A layer
 *   missing from another's list may not be imported by it.
 * @param {string[]} options.coreLayers  layers that are pure core code: they
 *   also ban native methods, null checks, native Set and Map, and platform
 *   imports
 * @param {{ constant: string, module: string, names: string[] }[]} [options.vocabularies]
 *   closed vocabularies: the named constant, the one module (path from the
 *   config's directory) that may spell the names, and the names
 * @param {Record<string, string[]>} [options.aliases]  import aliases of
 *   Effect modules, such as { Array: ["Arr"], Schema: ["S"] }
 * @param {string} [options.sourceRoot]  directory holding the layer
 *   directories (default "src")
 * @param {string[]} [options.testFiles]  globs of test files (default
 *   ["test/**\/*.ts"])
 * @param {string[]} [options.platformImports]  import patterns banned in core
 *   layers (default node:*, bun, bun:*)
 * @param {string[]} [options.project]  tsconfig paths (default
 *   ["./tsconfig.json"])
 * @param {string[]} [options.ignores]  extra ignore globs
 */
export const buildConfig = ({
  tsconfigRootDir,
  layers,
  coreLayers,
  vocabularies = [],
  aliases = {},
  sourceRoot = "src",
  testFiles = ["test/**/*.ts"],
  platformImports = ["node:*", "bun", "bun:*"],
  project = ["./tsconfig.json"],
  ignores = [],
}) => {
  const layerNames = Object.keys(layers ?? {})
  if (layerNames.length === 0) throw new TypeError("buildConfig: layers must name at least one layer")
  for (const layer of layerNames) {
    for (const allowed of requireArray(`layers.${layer}`, layers[layer])) {
      if (!layerNames.includes(allowed)) throw new TypeError(`buildConfig: layers.${layer} names unknown layer ${allowed}`)
    }
  }
  for (const layer of requireArray("coreLayers", coreLayers)) {
    if (!layerNames.includes(layer)) throw new TypeError(`buildConfig: coreLayers names unknown layer ${layer}`)
  }
  for (const v of vocabularies) {
    requireArray(`vocabulary ${v.constant} names`, v.names)
    if (typeof v.constant !== "string" || typeof v.module !== "string") {
      throw new TypeError("buildConfig: each vocabulary needs constant, module and names")
    }
  }

  const aliasesOf = (module) => aliases[module] ?? []
  const named = (module) => nameRegExp([module, ...aliasesOf(module)])
  const allowObjects = [...effectModules, ...Object.values(aliases).flat()]

  const effectBans = [
    message(
      `MemberExpression[object.name=${named("Schema")}][property.name=${nameRegExp(throwingSchema)}]`,
      "Schema.decode and the Sync, Promise and asserts forms throw or reject or are v3 names; use decodeUnknownEffect / decodeUnknownResult / decodeUnknownOption.",
    ),
    message(
      `MemberExpression[object.name=${named("Effect")}][property.name=/^(runSync|runPromise|runFork|runSyncExit|runPromiseExit|promise)$/]`,
      "Core code builds Effects; running them belongs to Program or the entrypoint. Use Effect.tryPromise, not Effect.promise.",
    ),
    message(
      `MemberExpression[object.name=${nameRegExp(["Option", "Result", ...aliasesOf("Option"), ...aliasesOf("Result")])}][property.name=/^getOrThrow/]`,
      "getOrThrow throws; use match or getOrElse.",
    ),
  ]

  const schemaCallee = `CallExpression[callee.object.name=${named("Schema")}]`
  const literalSchemas = [
    message(
      `${schemaCallee}[callee.property.name='Literals'] > ArrayExpression.arguments > :matches(Literal, TemplateLiteral).elements`,
      "Schema.Literals takes a named `as const` constant (a closed vocabulary defined once), not inline literals.",
    ),
    message(
      `${schemaCallee}[callee.property.name='Literal'] > :matches(Literal, TemplateLiteral).arguments`,
      "Schema.Literal takes a named `as const` constant, not an inline literal.",
    ),
  ]

  // One selector per vocabulary, so the message names the constant to use.
  const bareNamesExcept = (module) =>
    vocabularies
      .filter((v) => v.module !== module)
      .map((v) =>
        message(
          `Literal[value=${nameRegExp(v.names)}]`,
          `Bare closed-vocabulary string: use ${v.constant} from ${v.module}.`,
        ),
      )

  const coreGlobs = coreLayers.map((layer) => `${sourceRoot}/${layer}/**/*.ts`)
  const isCore = (file) => coreLayers.some((layer) => file.startsWith(`${sourceRoot}/${layer}/`))
  const baseGroups = [loops, collections, failures, asynchrony, effectBans, parsing, literalSchemas]
  const coreOnly = [nullish, nativeCollections]
  const testGroups = [failures, asynchrony, effectBans]

  const nativeMethods = [
    ...nativeArrayMethods.map((property) => ({
      property,
      allowObjects,
      message: `Native array method; use Array.${property === "at" ? "get" : property} or the nearest Array module function.`,
    })),
    ...nativeStringMethods.map((property) => ({
      property,
      allowObjects,
      message: "Native string method; use the String module (String.split, String.trim, ...).",
    })),
    { object: "Object", message: "Native Object functions; use the Record and Struct modules." },
  ]

  const throwingImports = {
    name: "effect/Schema",
    importNames: throwingSchema,
    message: "Throwing or v3 Schema functions are banned; see the Schema.decode rule.",
  }

  const importRule = (layer) => [
    "error",
    {
      paths: [throwingImports],
      patterns: [
        {
          group: layerNames
            .filter((other) => other !== layer && !layers[layer].includes(other))
            .flatMap((other) => [`**/${other}`, `**/${other}/**`]),
          message: `${layer} may import only ${layers[layer].join(", ") || "nothing"} from the other layers.`,
        },
        ...(coreLayers.includes(layer) && platformImports.length > 0
          ? [{ group: platformImports, message: `Core layers import no platform module (${platformImports.join(", ")}).` }]
          : []),
      ],
    },
  ]

  const modules = [...new Set(vocabularies.map((v) => v.module))]

  return defineConfig([
    { ignores: ["node_modules/**", "dist/**", ...ignores] },
    {
      files: ["**/*.ts"],
      extends: [
        js.configs.recommended,
        ...tseslint.configs.strictTypeChecked,
        ...tseslint.configs.stylisticTypeChecked,
      ],
      languageOptions: { parserOptions: { project, tsconfigRootDir } },
      plugins: { functional },
      rules: {
        "@typescript-eslint/consistent-type-assertions": ["error", { assertionStyle: "never" }],
        "@typescript-eslint/no-non-null-assertion": "error",
        "@typescript-eslint/array-type": ["error", { default: "generic", readonly: "generic" }],
        "func-style": ["error", "expression"],
        "prefer-arrow-callback": "error",
        "no-restricted-syntax": noRestrictedSyntax(...baseGroups, bareNamesExcept(null)),
        "functional/no-loop-statements": "error",
        "functional/no-throw-statements": "error",
        "functional/no-let": "error",
        "functional/immutable-data": ["error", { ignoreClasses: true }],
      },
    },
    ...layerNames.map((layer) => ({
      files: [`${sourceRoot}/${layer}/**/*.ts`],
      rules: { "no-restricted-imports": importRule(layer) },
    })),
    {
      // Core layers also ban native collection and string methods and null
      // or undefined checks (effect-v4, "Reach for the combinator").
      files: coreGlobs,
      rules: {
        "no-restricted-syntax": noRestrictedSyntax(...baseGroups, ...coreOnly, bareNamesExcept(null)),
        "no-restricted-properties": ["error", ...nativeMethods],
      },
    },
    // Each vocabulary's module may spell its own names, and no other
    // vocabulary's.
    ...modules.map((module) => ({
      files: [module],
      rules: {
        "no-restricted-syntax": noRestrictedSyntax(
          ...baseGroups,
          ...(isCore(module) ? coreOnly : []),
          bareNamesExcept(module),
        ),
      },
    })),
    {
      // Tests relax the loop, mutation, parsing, native-method and
      // null-check rules, and nothing else.
      files: testFiles,
      rules: {
        "no-restricted-syntax": noRestrictedSyntax(...testGroups, bareNamesExcept(null)),
        "no-restricted-imports": ["error", { paths: [throwingImports] }],
        "functional/no-loop-statements": "off",
        "functional/no-let": "off",
        "functional/immutable-data": "off",
      },
    },
  ])
}
