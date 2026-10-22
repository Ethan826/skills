# Erasure: the classification table and its traps

Read this when you add a foreign key that points at a person, change
what erasure deletes, or write the erasure test. SKILL.md states the
rules; this file holds the table format and the traps that classifying
keys tends to expose.

## The classification table

Keep it beside the schema, in the repository, with one row per foreign
key that points at a person. A neutral example:

| Column | Kind | What survives erasure | Why |
|---|---|---|---|
| `email_addresses.person_id` | Subject | Nothing | The address is the person's own data. |
| `order_identities.customer_id` | Actor | The order, with the reference nulled or retained as retention law requires | The order is also a business record. |
| `template_identities.created_by` | Actor | The shared template | Authorship is provenance, not ownership. |
| `approvals.approved_by` | Actor | The approval fact | Removing it would rewrite someone else's history. |
| `erasure_log.subject_id` | No key | The erasure record | It names an identity that no longer exists. |

Record a date when the table was last checked against the live schema,
and a test or script that lists every foreign key pointing at a person
and fails if one is missing from the table.

## Traps

- **A key that never fired starts firing.** Once an actor key stops
  cascading, rows that used to vanish together now survive. A
  restrictive key on that path (`NO ACTION` or `RESTRICT`) that never
  fired before now raises a violation and aborts the whole erasure.
  Walk every path the cascade reaches when you reclassify a key.
- **An actor key that is also part of an identity.** If a view resolves
  "latest per (thing, author)", nulling the author merges every erased
  author's rows into one. Before making a column nullable, check
  whether it appears in a `DISTINCT ON`, a unique index or a grouping
  that defines identity. If it does, replace it with a stable
  pseudonymous key or change the grouping.
- **A partition key is never an actor key.** Nulling a tenant or account
  key strands the row where no scoped query can reach it: neither
  available nor gone. Those keys cascade, and deleting a whole partition
  is its own procedure, with any retention duty met by an export taken
  first.
- **The erasure record cannot reference what it outlives.** The ledger
  row that records an erasure names an identity that is about to be
  gone. A foreign key would block the delete or, as `SET NULL`, empty
  the record of its only content. Hold opaque IDs with no foreign key,
  a check constraint on their shape, and no personal data. Insert it in
  the same transaction as the delete.
- **Generated types may not notice.** Making a column nullable changes
  what the application receives, and type generators often report view
  columns as nullable already, so nothing fails to compile. Update the
  domain mapping by hand and let the erasure test catch the rest.
- **External steps can fail after the commit.** Deleting the person at
  an external processor happens outside the transaction. Record each
  step's outcome as an appended fact keyed to the erasure record, so a
  failed step is visible and can be retried.
