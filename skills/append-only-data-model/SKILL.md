---
name: append-only-data-model
description: Models mutable entities as an immutable identity row, append-only fact tables and a view that folds the facts into current state, so application code never issues UPDATE or DELETE. Covers snapshots versus single-fact ledgers, a syntax-tree gate with counted exceptions (test cleanup, migrations, erasure), subject and actor foreign keys for erasure, locked read-merge-append, a per-entity version that orders facts across writers, claims written before a side effect, per-tenant override rows and schema-enforced invariants. Use it when the project already keeps history this way (fact tables, resolved views, an append-only gate) and a task adds or alters a table, migration or repository, including requests to update, archive or flag a record; or when the user asks to design, evaluate or migrate to an append-only model. Not for redesigning a project that uses ordinary mutable tables. Database-neutral; examples use PostgreSQL.
license: MIT
---

# Append-only data model

Nothing stored is changed in place. Each mutable entity has an identity
row that never changes, tables of facts that only grow, and a view that
folds the facts into current state. Application code inserts; it never
issues UPDATE or DELETE.

History comes free, "who changed this and when" is a query rather than
an audit-log side table, and concurrent writers append rows instead of
overwriting each other. The cost is unfamiliar writes, and a few
problems (ordering, erasure, side effects) that need deliberate answers
a mutable schema would have hidden.

Examples use PostgreSQL 18, for illustration only. The rules apply to
any relational database.

This skill governs a project that has adopted the model, or a request
to design or evaluate one. In a project built on ordinary mutable
tables, do the update as asked; do not turn a CRUD change into a schema
redesign.

## The shape

| Layer | Holds | Mutability |
|---|---|---|
| Identity table | A primary key, and only what can never change | Immutable |
| Fact tables | One table per kind of fact, keyed to the identity | Append-only |
| Resolved view | The latest facts, folded into current state | Derived |

Current state is a fold over facts: for each kind of fact take the
latest row, then join the results to the identity. Fact tables come in
two flavours, and one entity often uses both.

- **Full-state snapshot.** Each row carries the entity's whole mutable
  state. An edit reads the current row, merges the caller's partial
  input over it and appends the result. Use it when many fields are
  edited independently, as in a profile or a configuration.
- **Single-fact ledger.** Each row records one narrow fact: a status
  change, a login, an archival. Reads take the latest row or ask whether
  any row exists. Use it for a fact with its own lifecycle.

An order might have a snapshot table for its editable details and a
ledger of status events. Archiving is a fact as well: carry an
`archived` field in the snapshot, or keep an archive ledger. Never add a
mutable flag to the identity table.

```sql
-- Illustration: a resolved view over a snapshot and a ledger.
CREATE VIEW orders_resolved AS
SELECT o.id, d.recipient, d.notes, s.status
FROM order_identities o
JOIN LATERAL (                       -- required fact: inner join
  SELECT * FROM order_details WHERE order_id = o.id
  ORDER BY version DESC LIMIT 1) d ON true
LEFT JOIN LATERAL (                  -- optional fact: left join
  SELECT status FROM order_status_events WHERE order_id = o.id
  ORDER BY version DESC LIMIT 1) s ON true;
```

- **Reads go through the view.** Repositories never read raw fact tables
  for current state, so "current" has one definition, in the schema.
- **Inner-join the facts an entity cannot lack.** A half-created entity
  then stays invisible. A left join would surface it with nulls that
  fail later, somewhere else.
- **Order by a per-entity version, never by the ID.** Each fact row
  carries `version`, allocated under the entity lock (see Ordering).
  The UUID is identity only.
- **Declare `UNIQUE (entity_id, version)` on each fact table.** Its index
  serves every "latest" lookup, and it rejects two writers that claim
  the same version. Fix slow reads with indexes or materialized views,
  never by putting a mutable column back.
- **Rebuild the view in the migration** that adds a fact column.

## The rule, and the gate that enforces it

Application code never issues UPDATE or DELETE, and that includes
`TRUNCATE` and upserts: `ON CONFLICT ... DO UPDATE` is an UPDATE.
`ON CONFLICT DO NOTHING` is an insert, and stays allowed.

An unchecked rule erodes. One deliberate UPDATE, defended in a comment,
becomes the template for the next. Enforce the rule with a test in the
normal suite:

- **Read the syntax tree, not the text.** Parse each source file. Flag
  calls to the query builder's update, delete, merge and upsert methods,
  and string or template literals containing `UPDATE ... SET`,
  `DELETE FROM`, `TRUNCATE` or `DO UPDATE`. A text search flags those
  words in a comment, and formatting defeats it, as when a call chain is
  split across lines.
- **Scan every non-test source file.** Migrations and tests sit outside
  the scan by construction.
- **Pin each exception to an exact count per file, with its reason.** A
  third delete in a file allowed two fails like a first delete anywhere
  else. A shared test helper may delete only if the gate also asserts
  that no application module imports it.
- **Check that the gate can still see.** A scanner that matches nothing
  passes forever. Assert a minimum number of files scanned and that a
  known file is among them. Run a positive probe holding every spelling
  the gate claims to catch, and assert the exact count. Run a negative
  probe (`SELECT ... FOR UPDATE`, an HTTP method list containing
  `'DELETE'`, `DO NOTHING`) and assert that nothing is flagged.

```ts
// Illustration: the exception list is data, and each entry argues for itself.
const ALLOWED = {
  "src/erasure.ts": { count: 2, reason: "Deletes identity rows; see Exceptions." },
  "src/test-support/db-cleanup.ts": { count: 4, reason: "Test cleanup shared by suites." },
} as const;
```

gate-integrity covers the general method for gates that cannot pass
vacuously.

## Exceptions

A few things must mutate. Each is listed in the gate, counted and given
a reason that would persuade a skeptic. Adding an entry is a design
decision and gets the review a schema change gets.

| Exception | Why it may mutate |
|---|---|
| Test cleanup | It is infrastructure, not application code. |
| Migrations that reshape storage | Rewriting the schema is their job. Turning a mutable column into a ledger means building the table, backfilling it, rebuilding the view and dropping the column. |
| Erasure | A ledger cannot forget, and the law or the person may require that it does. |

Nothing else may mutate. "It is only a flag" and "it is only a counter"
do not qualify; both are facts to append.

### Erasure is the hard case

When a person must be forgotten, at their request or by law, delete
their identity row and let the foreign keys cascade. No application
code runs during a cascade, so nothing above the database can make up
for a key declared wrong. Every foreign key that points at a person is
therefore a decision about erasure. Classify each one:

- **Subject: whose data this is.** The row exists because the person
  does and means nothing without them: their addresses, their own
  history, their settings. Declare it `NOT NULL ON DELETE CASCADE`.
- **Actor: who did this.** The row belongs to someone else or to the
  organization, and the reference is provenance: who approved, who
  tagged, who wrote a shared template. Declare it nullable with
  `ON DELETE SET NULL`, or retain the reference where retention law or
  policy requires it. The record stands; the link to the person goes.

Cascading an actor key deletes other people's records, and deletes rows
from ledgers meant to be permanent. Copying `CASCADE` from the
neighbouring column is how that happens.

Keep the classification in a table beside the schema, one row per key:
the column, its kind, what survives and why. Add a row with every new
key. Back it with a test that erases a person the way the erasure
procedure does, then asserts exactly what survives: each actor-keyed
row present with its substance intact and the person's ID gone, each
subject-keyed row gone. Test both directions, so a later change that
nulls everything fails as loudly as one that cascades everything.

Erasure must not:

- **rewrite other people's facts.** It removes the person and severs
  references to them. It does not edit or redact anyone else's rows.
- **leave derived copies behind.** Caches, search indexes, exports,
  analytics stores and copies at external processors hold the person's
  data too. List each beside the classification table, give it an
  erasure step, and record which steps succeeded.

Read [references/erasure.md](references/erasure.md) when adding a key
or writing the erasure test. It has a sample table and the traps:
restrictive keys that start firing, actor keys inside a grouping,
partition keys, and the erasure record that outlives its subject.

## Read, merge and append in one locked transaction

An unguarded snapshot edit loses updates. Two writers read state S0; one
appends S0 with a new name, the other S0 with a new address. The view
takes the later row, and the name change is gone. The window is a full
application round trip, wide enough for a double-submitted form.

Open a transaction, lock the identity row, and only then read:

```sql
BEGIN;
SELECT id FROM order_identities WHERE id = $1 FOR UPDATE;
SELECT * FROM order_details WHERE order_id = $1
ORDER BY version DESC LIMIT 1;
-- merge the caller's partial input over that row; it read version v
INSERT INTO order_details (id, order_id, version, recipient, notes)
VALUES ($2, $1, v + 1, $3, $4);
COMMIT;
```

A writer queued behind another merges over what the first one wrote, so
both edits survive.

- **The merge keeps every field the caller omitted.** A clearable field needs three
  states (absent, a value, null), which spreading the input over the row
  cannot distinguish.
- **Test the outcome, not the wait.** The foreign key already makes the
  insert block on a held lock, so "it blocked" proves nothing. Commit a
  write while the update waits, then assert both changes are in the
  final row.
- **A blind write skips the merge, not the lock.** When the caller
  supplies the whole state, last write wins is the intent, but the write
  still needs the next version, and "last" means last under the lock.

## Facts known only after a side effect

An email or a card charge produces a fact known only afterwards. Never
insert a placeholder and update it. Write two facts:

1. **The claim, before the act.** Its unique constraint names the act,
   for example one reminder per order per due date. Insert with
   `ON CONFLICT DO NOTHING ... RETURNING id`; only the caller that gets a
   row back may act. A read-then-act check holds only until two workers
   overlap, and a crash after the claim loses one act instead of
   repeating it.
2. **The outcome, after the act.** Append one row per result (delivered,
   failed) keyed to the claim, versioned per claim like any fact, and
   fold the latest outcome onto each claim in a view.

A claim without an outcome stays visible as one. Return what the act
needs (the claim's ID and timestamp) from the insert itself, so no query
sits between claim and act where it could fail and strand the claim.

## Ordering: a version per entity, allocated under the lock

"Latest" needs an order every writer to an entity agrees on, and the ID
cannot supply it. A time-ordered UUID such as UUIDv7 (RFC 9562) is
monotonic at best within one generator state, one session or process;
pooled connections and multiple workers are many states. Two writers in
one millisecond can commit in one order and mint IDs that sort in the
other, and the identity-row lock does not change that.
`ORDER BY id DESC` then serves the earlier write as current, and nothing
errors.

So every fact table carries a version per entity:

- **Allocate it inside the locked transaction.** Read the latest row
  under the identity-row lock and insert `version + 1`, or 1 for the
  first fact. A ledger append can compute
  `coalesce(max(version), 0) + 1` in the insert itself, after the lock.
- **Let the unique constraint catch a writer that skipped the lock.**
  Two writers computing the same version collide on
  `UNIQUE (entity_id, version)`. Retry the whole read-merge-append;
  never drop the constraint.
- **Use it everywhere "latest" is decided:** the resolved view, every
  index, the override resolver and outcome folds. A query that orders
  facts by ID or by a timestamp is a bug, however rarely it shows.
- **Keep the UUID as identity.** Where IDs double as bearer tokens
  (session IDs, reset links), sequential IDs are enumerable; the version
  is an internal ordering key, never an identifier.
- **Do not rely on a native generator for order.** As of PostgreSQL 18,
  the documentation for `uuidv7()` documents no ordering guarantee
  across sessions.
- **Test that the later write wins despite a smaller ID.** Make two
  independent generator states, give both the same injected time, and
  seed or redraw until the second write's ID sorts below the first's.
  Append both through the repository in order, assert that the IDs are
  reversed, and assert that the view shows the second write. Ordered by
  ID, the same rows show the first.

Timestamp columns hold domain time (a due date, an expiry) and do not
order writes either. Read [references/ordering.md](references/ordering.md)
when creating a fact table, writing an append or the ordering test, or
moving an existing table to versions.

## Layered overrides

Shared data sometimes needs per-tenant customization: platform-default
rows every tenant sees, and override rows only their tenant sees. Use
this only when tenants must customize shared data. A new table's default
is a non-null tenant key with a plain equality filter, which cannot
leak.

Resolve deterministically in one query, ranking the tenant above
recency:

```sql
-- Illustration: one resolved row per item for tenant $1.
SELECT DISTINCT ON (item_id) *
FROM item_settings
WHERE tenant_id = $1 OR tenant_id IS NULL   -- this tenant, plus defaults
ORDER BY item_id,                           -- must lead, for DISTINCT ON
         (tenant_id IS NULL),               -- override before default
         version DESC;                      -- then latest
```

Every part fails silently. Without the `IS NULL` branch a tenant sees
only what it has overridden; without the tenant predicate it sees other
tenants' overrides; with `version DESC` ahead of the rank, whichever
scope has written more rows wins, and re-seeding the defaults can
replace a tenant's customization.

- **The tenant is always an explicit parameter,** passed by the caller
  from the authenticated request, never read from ambient state inside
  the data layer. A method that touches tenant data without a tenant
  parameter is a bug.
- **Use one shared resolver** for every read path, never a copy per call
  site. Version rows per `(entity_id, tenant_id)` under the entity lock,
  and declare `UNIQUE NULLS NOT DISTINCT (entity_id, tenant_id, version)`
  so the default rows, whose tenant is null, are checked too.
- **Append tenant rows only.** Application code never writes a default.
  A tenant's first override merges over the default, so untouched fields
  keep the platform's values.
- **Test isolation.** Tenant A sees its override. Tenant B sees the
  default and never A's override. A default written after A's override
  does not displace it.

## Invariants the schema should enforce

An invariant the code assumes and the schema does not enforce fails
silently: a lookup that expects one match takes the first of several.

A unique index on a fact table rarely expresses uniqueness, because the
table holds every past value as well as the current one. Decide what is
unique:

- A value that never changes belongs on the identity table.
- A claim to something (an external account, a handle) belongs in a
  claim table with the unique constraint. That constraint holds for
  good, so decide up front whether a released value may be claimed
  again.
- "Unique among current values" cannot be a plain index. Check it inside
  the locked transaction that appends, under a lock keyed on the value
  (in PostgreSQL, a transaction-scoped advisory lock).

Check constraints should mirror every enumerated status, and the domain
types should mirror the check constraints.

## Checklist before committing a schema or repository change

- [ ] No UPDATE, DELETE, TRUNCATE or upsert outside the gate's pinned
      exceptions; the gate passes its own probes.
- [ ] Each new exception has an exact count and a reason.
- [ ] Each new fact table is a snapshot or a ledger by choice, with a
      `version` column and `UNIQUE (entity_id, version)`.
- [ ] Required facts are inner-joined; the view was rebuilt in the same
      migration; repository reads go through it.
- [ ] Every read-merge-append locks the identity row before reading, and
      a test shows concurrent edits both survive.
- [ ] Side effects use a unique claim and an appended outcome, never an
      updated placeholder.
- [ ] Every "latest" (views, resolvers, outcome folds) orders by the
      version, never the ID or a timestamp; the version is allocated
      under the lock, and a test shows a later write with a smaller ID
      wins.
- [ ] Every new foreign key to a person is classified in the table, and
      the erasure test covers it.
- [ ] Every new derived store of personal data has an erasure step.
- [ ] Tenant-scoped methods take the tenant explicitly, and overrides
      have isolation tests.
- [ ] Every uniqueness or shape invariant the code relies on is enforced
      by the schema.

Related: schema-migrations for applying the change safely,
multi-tenant-security-review for auditing tenant isolation, gate-integrity
for gates that cannot pass vacuously, and test-first for writing the
erasure, ordering and concurrency tests before the schema change.
