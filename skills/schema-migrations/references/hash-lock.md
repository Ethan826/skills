# A content-hash lock for migrations

Read this when a project has no lock yet. The sketch is TypeScript on
Node, for illustration. Port it to the project's language and test
runner, and keep the behavior.

The lock is a committed JSON file beside the migrations, mapping each
filename to the SHA-256 of its bytes:

```json
{
  "20260301120000_create-orders.sql": "9f2c...",
  "20260305093000_add-discount-code.sql": "41ab..."
}
```

## The check (runs in CI)

```ts
// check-lock.ts
import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const dir = "migrations";
const lockPath = join(dir, "migration-lock.json");

export const migrationNames = (): string[] =>
  readdirSync(dir).filter((n) => n.endsWith(".sql")).sort();

export const hashOf = (name: string): string =>
  createHash("sha256").update(readFileSync(join(dir, name))).digest("hex");

export function checkLock(): string[] {
  const names = migrationNames();
  const lock: Record<string, string> = JSON.parse(readFileSync(lockPath, "utf8"));
  const problems: string[] = [];

  // A wrong path or glob finds nothing, and nothing would then fail.
  if (names.length === 0) problems.push(`no migrations found in ${dir}`);

  for (const n of names) {
    if (!(n in lock)) problems.push(`not recorded: ${n}`);
    else if (lock[n] !== hashOf(n)) problems.push(`changed after recording: ${n}`);
  }
  for (const n of Object.keys(lock)) {
    if (!names.includes(n)) problems.push(`recorded but missing: ${n}`);
  }
  return problems;
}
```

Wire `checkLock()` into the test suite or a CI step that fails when the
list is not empty. Put the reason in the failure message: a changed file
means "revert the edit and write a new migration", never "update the
hash".

## Recording new files (run by hand when adding a migration)

```ts
// record-new.ts
import { readFileSync, writeFileSync } from "node:fs";
import { hashOf, migrationNames } from "./check-lock";

const lockPath = "migrations/migration-lock.json";
const lock: Record<string, string> = JSON.parse(readFileSync(lockPath, "utf8"));

// Refuse to run while any recorded file has changed.
for (const [name, hash] of Object.entries(lock)) {
  if (hashOf(name) !== hash) throw new Error(`changed after recording: ${name}`);
}

// New files must sort after every recorded one.
const newest = Object.keys(lock).sort().at(-1) ?? "";
for (const name of migrationNames()) {
  if (name in lock) continue;
  if (name < newest) throw new Error(`${name} sorts before ${newest}`);
  lock[name] = hashOf(name);
}

writeFileSync(lockPath, JSON.stringify(lock, null, 2) + "\n");
```

The script only adds entries. It has no mode that rewrites existing
ones. The rare legitimate change to an existing entry (a migration that
has applied in no persistent database, or a rename after a rebase) is a
hand edit to that one line, made in its own commit that gives the
reason, so a reviewer sees it.

`hashOf` throws if a recorded file has been deleted. That stops the
script, as it should. The check reports the deletion by name.

Hashing raw bytes means a checkout that rewrites line endings changes
every hash. Mark the migrations directory as binary or LF-only in
`.gitattributes` (for example `migrations/** -text`) so every clone sees
the same bytes.
