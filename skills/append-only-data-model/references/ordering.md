# Ordering facts: the per-entity version

Read this when you create a fact table, write the code that appends to
one, or write the ordering test. SKILL.md states the rule; this file
holds a complete schema, the append statements and the tests.

## Why the ID cannot order writes

A time-ordered UUID such as UUIDv7 (RFC 9562) sorts by the clock of the
process that minted it, then by that generator's own counter or random
bits. Monotonicity, where a generator offers it at all, holds only for
one generator state: one session, one process, one connection. A
deployment with a connection pool or more than one worker has many
generator states, and they do not coordinate.

The identity-row lock serializes the writes to one entity. It does not
make their IDs sort in that order. Two writers in the same millisecond,
on different connections, can commit in one order and mint IDs that sort
in the other. Clock skew between hosts widens the window from a tie to
seconds. `ORDER BY id DESC` then serves the earlier write as current.
Nothing errors.

As of PostgreSQL 18, the documentation for the built-in `uuidv7()`
promises a millisecond timestamp with a sub-millisecond fraction and
documents no ordering guarantee across sessions. Application-side
generators are no better placed: each has its own state.

## The schema

Each fact table carries `version`, a positive integer allocated per
entity. The unique constraint makes a duplicate version an error, and
its index serves every "latest" lookup.

```sql
CREATE TABLE order_identities (
  id uuid PRIMARY KEY
);

CREATE TABLE order_details (
  id        uuid PRIMARY KEY,
  order_id  uuid NOT NULL REFERENCES order_identities (id) ON DELETE CASCADE,
  version   bigint NOT NULL CHECK (version > 0),
  recipient text NOT NULL,
  notes     text,
  UNIQUE (order_id, version)
);

CREATE TABLE order_status_events (
  id       uuid PRIMARY KEY,
  order_id uuid NOT NULL REFERENCES order_identities (id) ON DELETE CASCADE,
  version  bigint NOT NULL CHECK (version > 0),
  status   text NOT NULL CHECK (status IN ('open', 'shipped', 'cancelled')),
  UNIQUE (order_id, version)
);

CREATE VIEW orders_resolved AS
SELECT o.id, d.recipient, d.notes, s.status
FROM order_identities o
JOIN LATERAL (
  SELECT * FROM order_details WHERE order_id = o.id
  ORDER BY version DESC LIMIT 1) d ON true
LEFT JOIN LATERAL (
  SELECT status FROM order_status_events WHERE order_id = o.id
  ORDER BY version DESC LIMIT 1) s ON true;
```

Each fact table numbers its own rows; versions in `order_details` and
`order_status_events` are unrelated. The view never compares them.

## Appending

Create the entity and its first required fact in one transaction, with
version 1:

```sql
BEGIN;
INSERT INTO order_identities (id) VALUES ($1);
INSERT INTO order_details (id, order_id, version, recipient, notes)
VALUES ($2, $1, 1, $3, $4);
COMMIT;
```

A snapshot edit reads the latest row under the lock and appends the
next version:

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

A ledger append reads nothing else, so it can allocate in the insert:

```sql
BEGIN;
SELECT id FROM order_identities WHERE id = $1 FOR UPDATE;
INSERT INTO order_status_events (id, order_id, version, status)
SELECT $2, $1, coalesce(max(version), 0) + 1, $3
FROM order_status_events WHERE order_id = $1;
COMMIT;
```

Take the lock before computing the version. Under READ COMMITTED a
writer that waited for the lock sees the previous writer's committed
row when its next statement runs, so it allocates the following number.
A writer that skips the lock can compute a version another writer is
also inserting; the unique constraint then rejects one of them. Treat
that error as a retry of the whole read-merge-append, never as a reason
to drop the constraint.

Where the application never reads `version` back, a database sequence
drawn after the lock is an alternative: with the default `CACHE 1`, a
value drawn while holding the entity lock is greater than any value
drawn by a writer that committed before. A larger cache hands each
session its own block of numbers, which breaks that. It orders correctly only when every writer to the entity takes
the lock first, and nothing in the schema checks that. The per-entity
version with its unique constraint fails loudly instead.

## The tests

**Later write wins despite a smaller ID.** Simulate two independent
generator states: two generator instances, or the injected-clock
variant called with the same instant from two fresh states. Seed the
random source, or draw until a pair comes out reversed, so the second
write's ID sorts below the first's. Append through
the real repository code, in order, and assert the resolved view shows
the second write. Assert as well that the two IDs really are reversed,
so the test cannot pass by luck of the draw.

```sql
-- Fixed IDs stand in for two generator states at the same millisecond.
INSERT INTO order_identities (id)
VALUES ('01900000-0000-7000-8000-00000000000a');
INSERT INTO order_details (id, order_id, version, recipient)
VALUES ('01900000-0000-7000-8000-ffffffffffff',
        '01900000-0000-7000-8000-00000000000a', 1, 'first');
INSERT INTO order_details (id, order_id, version, recipient)
VALUES ('01900000-0000-7000-8000-000000000001',
        '01900000-0000-7000-8000-00000000000a', 2, 'second');

SELECT recipient FROM orders_resolved
WHERE id = '01900000-0000-7000-8000-00000000000a';   -- expect 'second'
```

Ordered by `id DESC`, the same rows return `first`.

**Concurrent edits both survive.** Hold the lock in one connection and
append; start a second connection's edit, which waits; commit the
first; let the second finish. Assert the final row carries both changes
and the versions are consecutive.

**An unlocked duplicate fails.** Insert two rows with the same entity
and version and assert a unique violation, so a later migration that
drops the constraint fails the suite.

## Overrides

Layered override rows take a version per `(entity_id, tenant_id)`
scope, allocated under the entity lock in the same way. The resolver
ranks the tenant first and orders by `version DESC` within the scope.
A plain unique constraint treats every null tenant as distinct, so
declare it `UNIQUE NULLS NOT DISTINCT (item_id, tenant_id, version)`
(PostgreSQL 15 and later), or the default rows go unchecked.

## Moving an existing table to versions

Add the column as nullable, backfill it with
`row_number() OVER (PARTITION BY entity_id ORDER BY <best existing order>)`,
then set it `NOT NULL`, add the unique constraint and rebuild the view,
in one migration. The backfill can only be as right as the order it
reads: if the old order was by ID across several writers, some history
may already be misordered, and the migration cannot recover the truth.
Say so in the migration rather than claim the history is exact.
