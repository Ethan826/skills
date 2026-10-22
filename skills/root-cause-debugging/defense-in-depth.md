# Defense in Depth by Construction

## Overview

Once you have found the root cause of a bug caused by a bad value, it is
tempting to add a check wherever that value travels. Resist that. Checks
scattered through the inner layers drift apart, get skipped by mocks and
new code paths, and leave every reader wondering which ones still
matter.

Defense in depth comes from construction:

1. **Parse once at the boundary** into a type that cannot hold the bad
   value.
2. **Guard the environment at the runtime edge**, where a dangerous
   operation actually touches the world.
3. **Instrument** the dangerous operation so the next failure leaves
   evidence.

What it does not mean is re-validating at each layer. If inner code
feels it must re-check a shape, the boundary that handed the value over
is the thing to fix.

## 1. Parse at the Boundary

Turn untrusted input (a string from a test fixture, a request body, a
config file) into a type that can only hold a valid value. Do it once,
where the value enters. A smart constructor is the usual tool: the only
way to get the type is through a function that checks, so any value of
that type that exists is valid.

```typescript
declare const brand: unique symbol;
export type ProjectDir = string & { readonly [brand]: 'ProjectDir' };

export function parseProjectDir(raw: string): ProjectDir {
  const trimmed = raw.trim();
  if (trimmed === '') {
    throw new Error('project directory is empty');
  }
  const absolute = resolve(trimmed);
  if (!existsSync(absolute) || !statSync(absolute).isDirectory()) {
    throw new Error(`project directory is not a directory: ${absolute}`);
  }
  return absolute as ProjectDir;
}
```

Code further in takes the type, not the raw string, and does not check
again:

```typescript
function createWorkspace(dir: ProjectDir, sessionId: string) {
  // No emptiness check here: a ProjectDir cannot be empty.
  // ... proceed
}
```

The cast inside `parseProjectDir` is the one place that asserts the
type, and it sits directly after the checks that justify it. Nowhere
else may build a `ProjectDir` by casting. If a caller can't get one, it
has a raw value that has not been parsed, and the fix belongs at that
caller's boundary.

Where the language supports it, prefer a sum type or a closed set of
cases to a flag or a sentinel. A value that cannot be represented never
needs a check.

## 2. Guard the Environment at the Runtime Edge

Some dangers depend on context rather than on the value's shape. A
correctly typed directory is still the wrong place for `git init` if it
is the repository under test. Put that guard at the point where the
operation runs, because only there is the context known.

```typescript
async function gitInit(directory: ProjectDir) {
  // In tests, refuse git init outside temp directories
  if (process.env.NODE_ENV === 'test') {
    const normalized = normalize(resolve(directory));
    const tmpDir = normalize(resolve(tmpdir()));

    if (!normalized.startsWith(tmpDir)) {
      throw new Error(
        `Refusing git init outside temp dir during tests: ${directory}`
      );
    }
  }
  // ... proceed
}
```

This guard does not repeat the boundary's check. It asks a different
question, "is this safe here?", which no type answers.

## 3. Instrument the Dangerous Operation

Log the context just before the operation, so a failure that slips
through anyway can be traced.

```typescript
async function gitInit(directory: ProjectDir) {
  const stack = new Error().stack;
  logger.debug('About to git init', {
    directory,
    cwd: process.cwd(),
    stack,
  });
  // ... proceed
}
```

## Applying the Pattern

When you find a bug caused by a bad value:

1. **Trace the data flow** to where the bad value originates. See
   [root-cause-tracing.md](root-cause-tracing.md).
2. **Fix the source.** The bug came from somewhere specific. Fix that
   first.
3. **Find the boundary** where the raw value enters the code that
   trusts it, and introduce the type there. Change the inner signatures
   to take the type, and let the compiler show you every caller that
   still passes a raw value.
4. **Remove the inner re-checks** the type now makes redundant.
5. **Add an environment guard** where the operation is dangerous in some
   contexts, and **instrument** it.
6. **Test the boundary**: the constructor rejects each bad input, and
   the guard refuses the dangerous context.

## Example: The Empty projectDir

**Bug:** an empty `projectDir` caused `git init` to run in the source
tree.

**Data flow:**
1. Test setup produced an empty string.
2. `Project.create(name, '')`
3. `WorkspaceManager.createWorkspace('')`
4. `git init` ran in `process.cwd()`, because an empty `cwd` means the
   current directory.

**Root cause:** the test read `context.tempDir` at module load, before
`beforeEach` had set it. The fix at the source made `tempDir` a getter
that throws if it is read too early.

**Defense, by construction:**
- `Project.create()` parses its argument into a `ProjectDir`. An empty
  or missing directory is rejected there, once.
- `WorkspaceManager` and `WorktreeManager` take a `ProjectDir`, so they
  cannot receive an empty string, and their own emptiness checks go
  away.
- `gitInit` refuses to run outside the temp directory during tests.
- `gitInit` logs its directory, cwd and stack before running.

With the type in place, a new code path or a mock that tries to pass a
raw string fails to compile instead of running `git init` in the wrong
place. That is the property the scattered checks were trying to buy.
