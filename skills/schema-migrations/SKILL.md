---
name: schema-migrations
description: Guides database schema changes through a migration runner, from scaffolding to production. It covers the local loop (write up and a real down, apply, regenerate generated types, commit both), rolling back locally versus rolling forward in production, locking applied migrations with content hashes, rebuilding views and other derived objects, replacing functions with a down that restores the prior body, additive changes with backfills in expand, migrate and contract steps, filename ordering, what to do when a deploy fails partway through a migration, and keeping destructive scripts off non-local databases. Tool-neutral, with PostgreSQL as illustration. Use it whenever adding or changing a table, column, index, view, constraint or database function, whenever generated database types look stale or a column seems not to exist, whenever a migration fails, or a deploy or rollback involves the schema, and before editing any file in a migrations directory, even for a one-line fix.
license: MIT
---

# Schema migrations

A migration is a change to every database that will ever run it,
including ones that already exist and ones that do not exist yet. The
rules below keep those databases on the same schema. They hold for any
migration runner. The examples are illustrations in PostgreSQL SQL. The
PostgreSQL behavior they rely on was tested on 14.17. For version 17, the
view and function restrictions are confirmed by the PostgreSQL 17
documentation for `CREATE VIEW` and `CREATE FUNCTION`; nothing here was
tested at runtime on 17.

For what shape the tables themselves should take, see
append-only-data-model. For pushing the deploy that carries a migration,
see landing-a-branch.

## The loop

1. **Scaffold** the file with the runner's own command, so the name gets
   a correctly ordered prefix (see "Filenames sort, and order is
   permanent").
2. **Write `up` and a real `down`.** The down undoes exactly what the up
   did. "Rolling back: local versus production" says why it must be real
   even though production never runs it.
3. **Apply it locally,** against a local database named explicitly (see
   "Local database hygiene").
4. **Prove the down:** roll back one step, then apply again. Both
   directions must succeed, and the schema after the second apply must
   match the first.
5. **Regenerate the generated types,** if the project generates
   application types from the live schema.
6. **Commit the migration and the regenerated types together,** with the
   migration's hash recorded in the lock (see "Applied migrations are
   immutable").

Many projects also run a drift check that compares the committed
generated types with the live schema, often in a pre-commit hook or in
CI. That check is a safety net. Run the generator yourself as step 5. A
drift check can only catch what the generator sees, and it often runs
only when a database is reachable.

When a column "does not exist" right after you added it, ask the runner
which migrations are applied before you debug anything else. "The
migration never ran" and "the types are stale" look the same from the
application, and the runner's status command tells them apart in one
step.

## Rolling back: local versus production

**Local and CI: down must be real and tested.** Iterating on a schema
means applying, finding a mistake, rolling back and applying again. A
down that is missing or wrong blocks that loop, or leaves the local
database in a state no other database has. Test it the way step 4 says:
back one, forward again. In CI, apply every migration to an empty
database, roll the newest back, and apply it again.

**Production: roll forward, never back.** Fix a bad migration with a new
migration that corrects it. Two facts make a production down dangerous:

- If migrations run when the application starts, rolling back the
  deployed image does not undo them. The older code comes back up in
  front of the newer schema, so check that the two are compatible before
  you roll the image back.
- Data written since the migration ran may depend on the new shape. A
  down that drops a column drops every value written to it since the
  deploy.

**Mark a destructive down.** When the down destroys data (it drops a
column, a table, or rows the up created), say so in a comment at the top
of the migration, and never run it against production:

```sql
-- DESTRUCTIVE DOWN: drops orders.discount_code and every value in it.
-- Local and CI only. In production, fix forward with a new migration.
```

**Separate deploying code from migrating the schema.** Where you can,
make every migration compatible with the release before it, and change
the schema in expand, migrate and contract steps (see "Additive by
default"). Then the code can roll back without the schema having to.
Running migrations as a separate deploy step, before new code starts,
also surfaces a failure before any new code serves traffic. If they must
run at start-up, the compatibility rule is what keeps an image rollback
safe.

### When a deploy fails partway through a migration

1. **Stop.** Do not rerun the deploy, and do not run a down. Neither is
   safe until you know what state the database is in.
2. **Find out what applied.** Read the runner's history table in that
   environment, and inspect the schema itself. Runners usually record a
   migration only after it commits, so the last row is the last
   migration that fully applied.
3. **Work out what the failed migration left behind.** If the runner
   wrapped it in a transaction and the database has transactional DDL
   (PostgreSQL does), it left nothing. Without a transaction (MySQL,
   which commits each DDL statement implicitly; a runner set to run
   without one; or a statement such as
   PostgreSQL's `CREATE INDEX CONCURRENTLY`, which cannot run inside
   one), some of its statements may have taken effect. Check each one.
   Runners that apply a batch of migrations in one go differ on whether
   the earlier ones in the batch committed, so check those as well.
4. **Restore service.** If the database is back on the previous schema,
   the previous image matches it and is safe to redeploy. If the
   database is partly migrated, confirm that the previous code works
   against it before rolling back.
5. **Fix forward.** A runner that stops at the first failure will hit
   the same failure on every start, and a later migration cannot run
   first. That leaves two fixes:
   - Change the database so the migration succeeds, for example by
     correcting the data it trips on. Do it as a reviewed manual step,
     record it where the team will find it, and repeat it in any other
     environment that holds the same data.
   - Correct the failed migration itself. That counts as editing a
     migration, so two conditions must both hold. First, the history
     table of every persistent database shows the migration never
     applied; check each environment's table, not your memory. Second,
     you have inspected and reconciled whatever the failed run left
     behind (step 3) in every environment where it ran: each partial
     effect is reversed, or the corrected migration is written to expect
     it. A clean history row does not mean a clean schema. Make the change
     and its one lock entry a commit of its own that says why.
6. **Verify the schema,** including every view and derived object the
   migration touched, before you call the incident over.

## Applied migrations are immutable

Runners record applied migrations by name, not by content. Editing a
migration that has already run changes what a fresh database gets and
does nothing to the databases that ran the old version. The two diverge
for good, with no error and no warning, and no later migration
reconciles them unless someone notices.

Suppose, for illustration, that a migration that has already deployed
is edited in place to rename a column. Every fresh database, including
the one the tests run against, gets the new name; production keeps the
old one. If the code that writes the column is best-effort, say an audit
log whose errors are caught and dropped, every insert fails quietly and
the tests still pass. Nothing reports the gap until someone goes looking
for rows that were never written.

So the fix for a wrong migration is another migration. Enforce this with
a content-hash lock, a committed file that maps each migration's name to
a hash of its bytes, checked in CI:

- **No missing file:** every migration has a recorded hash.
- **No orphaned entry:** every recorded name still has a file. Deleting
  an applied migration is the same defect as editing one, since the
  databases that ran it keep its effects.
- **Byte-identical:** every file hashes to its recorded value.
- **Fail on an empty directory.** A wrong path or a broken glob would
  otherwise find nothing and pass every check.
- **Record new files only.** The command that updates the lock adds
  hashes for files it has not seen, and refuses if any recorded hash no
  longer matches. Offer no command that rewrites every hash. That command
  would become the way people silence the check.

When the byte check fails, revert the edit and write a new migration
that reconciles the difference. The only exception is the one in step 5
of "When a deploy fails partway through a migration", and it needs the
same evidence. A sketch of the check is in
[references/hash-lock.md](references/hash-lock.md). Read it when
setting up the lock in a project that has none.

## Migrations do not depend on application code

A migration must run the same way years from now, against whatever
schema exists by then. Do not import generated database types, ORM
models or domain modules into it. Those describe the schema as it is
today, and a migration written against them stops compiling, or changes
meaning, when the schema moves on. Use plain SQL or the runner's untyped
schema builder, and copy any constant the migration needs into the
migration itself.

## Views and other derived objects are rebuilt explicitly

Adding a column to a table does not add it to any view over that table.
PostgreSQL expands `SELECT *` into a fixed column list when it creates
the view, and `CREATE OR REPLACE VIEW` can add columns only at the end of
that list (tested on 14.17; the PostgreSQL 17 `CREATE VIEW` documentation
states the same). A column added to the table but
never surfaced in the view is a silent no-op as far as the application
can tell.

Drop the view and create it again, in the same migration or the next
one:

```sql
DROP VIEW order_summaries;
CREATE VIEW order_summaries AS
  SELECT o.id, o.customer_id, o.total, o.discount_code
  FROM orders o;
```

If other views depend on the one you drop, PostgreSQL refuses. Drop the
dependents first and recreate everything in dependency order, within
one migration. Avoid `DROP ... CASCADE`: it removes the dependents
with no more than a notice, and nothing reminds you to recreate them.
Materialized views need the same treatment.

## Replacing a function

`CREATE OR REPLACE FUNCTION` swaps the body in place, and anything that
calls the function, such as a column default or a trigger, uses the new
body at once. Nothing needs rebuilding. (Tested on 14.17, and stated in
the PostgreSQL 17 `CREATE FUNCTION` documentation: it cannot
change the return type, and different argument types create a second
function instead of replacing the first.)

The down is where this goes wrong. The database keeps no previous
version to restore, and a down that drops the function breaks every
default and trigger that calls it. Paste the previous body into the down, unchanged:

```sql
-- up
CREATE OR REPLACE FUNCTION normalize_email(e text) RETURNS text
  LANGUAGE sql IMMUTABLE AS $$ SELECT lower(trim(e)) $$;

-- down: the body as it was before this migration, verbatim
CREATE OR REPLACE FUNCTION normalize_email(e text) RETURNS text
  LANGUAGE sql IMMUTABLE AS $$ SELECT lower(e) $$;
```

Roll back and forward to prove both bodies install. A function body is
invisible to type generation, so the drift check will not notice a
mistake in one. Give the function's behavior a test of its own.

## Additive by default

- **New columns are nullable or have a default.** A `NOT NULL` column
  without one fails on any table that has rows. In PostgreSQL 11 and
  later, adding a column with a non-volatile default does not rewrite
  the table.
- **Backfill inside the change.** When no running code depends on the
  old shape, one migration can create the new structure, copy the data
  across and then remove the old structure. Dropping a column on its own
  is a breaking change. It belongs in the step that finishes moving the
  column's data elsewhere.
- **Expand, migrate, contract.** When running code does depend on the
  old shape, use separate releases:
  1. *Expand:* add the new column or table. Code writes both shapes and
     reads the old.
  2. *Migrate:* backfill, then switch reads to the new shape.
  3. *Contract:* drop the old shape, once no running code reads it and
     no release you might roll back to needs it.
- **Know what your runner wraps in a transaction.** Some operations
  refuse to run inside one, such as PostgreSQL's
  `CREATE INDEX CONCURRENTLY`. If a runner wraps every migration, those
  operations need a deliberate change to how that migration runs, not a
  keyword added quietly.

## Filenames sort, and order is permanent

Runners apply migrations in lexical order of filename. A timestamp
prefix from the scaffolder gives that order for free. If you write a
prefix by hand, make it sort after every existing migration.

Never add a file that sorts before one already applied. Depending on the
runner, an existing database either refuses it, skips it, or runs it out
of order, while a fresh database runs it in sequence. Any of the three
leaves environments that disagree. Check after every rebase: a
migration on your branch can end up sorting before one that landed on
the main branch in the meantime. Rename yours to sort last, and move its
lock entry with it. That is safe only because it has not yet run
anywhere persistent. The lock's record-new command can enforce the rule
by refusing a file that sorts before the newest recorded one.

## Local database hygiene

- **Name the connection target explicitly.** A connection string left
  in your shell, aimed at a container hostname or at another
  environment, silently redirects every command that reads it. Give local
  commands a pinned local target, or variants that ignore the ambient
  value. A default that falls back to a port with nothing listening shows
  up as "connection refused", which is a configuration problem, not a
  database one.
- **Destructive scripts check the host first.** Anything that deletes,
  truncates or resets checks the target against a short allowlist
  (`localhost`, the local container's service name) and refuses
  everything else, whatever flags it is given.
- **Treat production access as read-only.** Inspect production to
  diagnose. Change it through migrations, or through a reviewed and
  recorded manual step during an incident.
- **Take migration status from the runner.** "Is it applied?" is a fact
  the runner owns (see verify-before-claiming). Ask it rather than
  inferring the answer from the schema or from memory.

## Checklist

1. Was the file scaffolded, or hand-named so it sorts after every
   existing migration, including after a rebase?
2. Does it have a real down? Was it rolled back and applied again
   locally?
3. If the down destroys data, does the migration say so, and say it is
   never for production?
4. Is the change additive? Do new columns allow nulls or have a default?
   Is any drop part of a finished backfill?
5. Will the release before this one run correctly against the new
   schema, so that an image rollback is safe?
6. Was every view and derived object over a changed table dropped and
   recreated in dependency order, without `CASCADE`?
7. Does a replaced function's down restore its previous body verbatim?
   Does the function have its own test?
8. Is the migration free of imports from generated types and application
   code?
9. Were the generated types regenerated and committed with the
   migration?
10. Was the new hash recorded with the record-new command, and does the
    lock check pass, with every existing hash unchanged?
11. Was no applied migration edited, renamed or deleted?
12. Did every command run against an explicitly named local database?
