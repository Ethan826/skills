---
name: launch-readiness-audit
description: Audits whether a product or service is ready to launch, or to move up a launch tier such as closed beta, soft launch or public launch. Every row in the audit carries an evidence level observed in this pass (verified in code, verified live, unverified, confirmed gap, confirmed blocker), with the date and the method used. Each pass re-checks rows against the deployed environment instead of carrying them forward, sorts blockers into bands with defined meanings, runs the restore, rollback and alert drills, checks infrastructure claims against deployed state, and files every unresolved row as an issue in the launch milestone. The output is an audit table, a blocker list and a tier verdict. Use it whenever someone asks whether a system is ready to ship, go live, open signups, take payment or onboard real users, when writing or updating a go-live checklist or gap analysis, before a launch-tier change, and whenever an earlier readiness document is about to be trusted as current.
license: MIT
---

# Launch readiness audit

A launch audit answers one question: what is true of the running system
today, and is it enough for the next tier? Readiness documents tend to
answer an easier one, what was true when someone last looked, and they
drift. A row marked fixed whose fix never landed, a row still marked as a
blocker weeks after the fix shipped, and a summary that disagrees with
its own body are all common, and each comes from carrying a row forward
instead of checking it again.

This skill applies verify-before-claiming to a whole system at once. The
claims are about deployed state, and the audit records how each one was
observed.

## The iron law

```
A ROW'S LEVEL IS WHAT THIS PASS OBSERVED, NOT WHAT THE LAST PASS RECORDED
```

An earlier pass is a lead. It tells you where to look and what you
expect to find, and it is never the finding.

## Evidence levels

Give every row exactly one level.

| Level | Meaning | Typical method |
|---|---|---|
| VERIFIED IN CODE | The code or configuration source does what the row requires. Nothing was run against production. | Reading the source; a passing test in CI |
| VERIFIED LIVE | Observed in the running production environment in this pass. | A request against the public endpoint; a read of deployed resources; a query on the production database |
| UNVERIFIED | Not yet observed, in code or live. A suspicion goes here, with the suspicion written in the notes. | None yet; name the check that would settle it |
| CONFIRMED GAP | Observed to be missing or wrong, and it does not block the target tier. | Any of the above |
| CONFIRMED BLOCKER | Observed to be missing or wrong, and the target tier cannot be reached until it is fixed. | Any of the above |

Two rules apply to every level.

- **Code evidence is not live evidence.** Code that sets a header, a
  retention period or a feature flag says what should happen. Only the
  deployed system shows what does, because a deploy can lag, a parameter
  can be overridden, and an environment can hold another environment's
  values. Write "verified in code; live check not done" when that is the
  state, and leave the row there.
- **A failed lookup is not evidence.** If a probe errors, times out, hits
  the wrong name or returns nothing, the row stays UNVERIFIED. Two lookups
  that both fail compare as equal, which can make a missing value look
  like a match. Check that each side of a comparison returned a real
  value before comparing them.

## The row format

Each row states what it checks well enough that someone else can repeat
the check and get the same answer.

```
- [ ] Short name of the requirement
      What:    the property that must hold, in terms a user would notice
      How:     the exact check: command, request, query or manual steps
      Failure: what the check shows when the property does not hold
      Level:   VERIFIED LIVE, 2026-05-14, by <method>; <what was observed>
      Issue:   <link>, if the row is anything other than verified
      Was:     earlier levels, kept when a row changes, with their dates
```

Keep the history line. A row that went from CONFIRMED BLOCKER to
VERIFIED LIVE tells the next reader what broke and how it was proven
fixed. When an item turns out not to have been the problem it was filed
as, say so in the row, and do not quietly mark it closed. A wrong premise
says something about how earlier passes were run, and the next pass
needs to know it.

Head the document with the date of the last pass, who ran it, how they
reached the environment (which accounts, which read paths), and the
version or commit that was deployed at the time. A level means little
without knowing what it was observed against.

## Re-auditing

A re-audit re-checks every open row and every verified row that a change
since the last pass could have touched. When it is unclear what a change
could have touched, re-check everything. For each row:

1. Read the previous level as a hypothesis.
2. Run the row's How against the environment as it is now.
3. Record the new level, the date and the method, even when nothing
   changed. "Re-checked 2026-05-14, unchanged" is a finding, and a blank
   is not.
4. Where the level changed, move the old one to the Was line.
5. Where you cannot reach the evidence, write down why (a credential an
   agent cannot use, an action that needs a real card or a real
   identity, a read path that is broken) and who can reach it. Then the
   row has an owner, and the gap does not read as an oversight.

Keep a single source of truth for status. If the document has a summary
table above the detailed rows, derive the summary from the rows on every
pass, or drop it. A summary that says closed above a body that still
says blocker is a common way these documents mislead.

Check that ordinary tooling still reaches the environment. A path used
only during incidents, such as the operator's route into the production
database, can break with nobody noticing, because nothing routine uses
it. The audit may be the only time it runs outside an incident.

## Blocker bands

Sort open rows into bands, and write the meaning of each band at the top
of the blocker list so a reader can argue with the sorting. These
defaults suit most products that take money or hold personal data:

| Band | Meaning |
|---|---|
| P0 | The core transaction cannot happen at all: users cannot sign up, pay, or do the one thing the product is for. |
| P1 | The core transaction has never been proven end to end in production. It might work, and nobody has seen it work. |
| P2 | A promise already published to users (terms, privacy policy, marketing copy, a status page) that the system does not yet keep. |
| P3 | Product quality with some legal or reputational exposure, such as accessibility or error handling on secondary paths. |
| Not a blocker | Real, recorded and deliberately deferred. List these by name with the reason, so a reader can see each deferral was decided. |

A band is a statement about risk, not a measure of how much effort the
fix takes. State plainly which bands could slip and on what condition.
For example, P2 can ship only if your human partner is willing to say
out loud which promise is not yet kept.

**A row that names an issue puts that issue in the launch milestone.**
The milestone, or whatever the tracker uses to group launch work, is the
authority, and the audit document is its reading order. An issue that
the audit depends on but that has no milestone is invisible to anyone
working from the milestone. On every pass, check that each issue named in a row is in the milestone, and add
any that are missing.

Note any ordering between blockers that costs something when it goes
wrong: a test that destroys the account or data another test needs, or a
drill that spends real money. Write the order into both rows.

## Launch tiers

Define tiers before auditing, so the verdict compares the system with a
written standard. Each tier includes everything in the tier below. A
typical ladder:

| Tier | Audience | Must be true, at minimum |
|---|---|---|
| Closed beta | Invited, known users who expect breakage | Legal documents substantive enough for what users are asked to agree to. The core transaction tested end to end in a sandbox. External uptime monitoring whose alert has been fired on purpose and received. A backup restore drilled once. Transactional email reaching arbitrary inboxes. |
| Soft launch | Public signup, limited outreach | Every applicable security and data-integrity row VERIFIED LIVE. Rate limits on expensive and unauthenticated endpoints. Structured production logs with a stated retention. Alarms on service and database health. An incident runbook. A rollback rehearsed. |
| Public launch | Marketing and paid acquisition | A load test at a stated multiple of expected load. A restore drilled at production scale. Accessibility audited on the core flows. Security headers verified on the live hosts. Every published claim checked against the system (see below). |

Adjust the conditions to the product, and write the adjusted list into
the audit. Some rows apply only when a release touches a given area,
such as authentication, billing or stored results. Say which areas
trigger which sections, and treat any failing row in an applicable
section as a blocker. A security row that returns success where it
should refuse is a blocker in every tier, whichever section it sits in.
For the multi-tenant and authorization rows, see
multi-tenant-security-review.

## Drills

Some properties can be shown only by exercising them. Configuration that
claims to provide them is not evidence.

- **Backup restore.** Restore into a fresh instance, then count what
  arrived and compare it with production: databases, tables, views, row
  counts for the tables that matter, and the latest applied migration.
  Spot-check content in a few rows. An empty restore starts, accepts
  connections and passes a health check, and it often finishes faster
  than a real one, so speed and health say nothing. A retention setting
  describes a policy, not the history that exists. After an instance is
  replaced, the backup history can start over while the setting reports
  the same number of days. Check the age of the newest backup against
  the instance's creation time.

  ```sql
  -- Illustration, PostgreSQL: run on both the restored and the live
  -- instance, and compare.
  SELECT table_schema, table_type, count(*)
  FROM information_schema.tables
  WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
  GROUP BY 1, 2;
  ```

- **Rollback.** Rehearse it, and record what it does not undo. An image
  rollback usually leaves schema migrations in place. Rolling back to a
  mutable tag can deploy something other than the build that was tested.
  Prefer pinning an immutable build identifier, and check which one is
  running.
- **Alerts.** Trigger each alert on purpose (stop a health endpoint,
  breach a threshold in a safe way) and confirm that the message reached
  the person who will act on it. An alert wired to an unread inbox or an
  unconfirmed subscription is the same as having no alert.
- **Recovery paths.** Run the runbook's commands, not your memory of
  them. A runbook step that names a renamed resource fails during the
  incident it was written for.

## Infrastructure claims

Check infrastructure against what is deployed, never against the
declared configuration alone. Read the live resource: the running task
definition, the DNS record as resolvers return it, the parameter's
current value, the headers on a real response. Infrastructure-as-code,
environment files and console screenshots describe intent. Take the
answer from the tool of record (see verify-before-claiming).

Probe for content, not status. A catch-all route that serves the app's
index page with a success code for every unknown path makes a missing
file look present. Check what the response contains.

Compare environments value by value where they must differ (live and
sandbox credentials, webhook secrets, price or plan identifiers), and
record that each lookup returned a value before comparing.

## Security and privacy claims in published text

Terms, privacy policies, security pages, marketing copy and sales
answers make claims about the system: data is encrypted, deleted on
request, retained for so many days, never shared. Before any such text
is published or approved, find the row that verifies each claim. If
there is no row, add one. A published claim the system does not keep is
a P2 blocker, and it can become a legal problem as soon as it ships.

Watch for the reverse as well. When the code does something the policy
does not authorize, such as deleting accounts or emailing users, either
the policy changes or the code does.

## The "what am I missing?" pass

After the rows, answer these questions in prose. Each answer either
names a row that already covers it or becomes a new row.

1. **What fails silently?** Look for errors caught and logged while the
   caller is told it succeeded, retries that eventually give up with no
   alarm, and jobs that skip records they cannot process.
2. **Which assumption is load-bearing but untested?** That an alert
   reaches someone, that the smallest database tier copes, that a proxy
   rewrites paths the way the code expects.
3. **What is the likeliest first incident?** Write it as a short story:
   what fires, what fails, what the user sees, and how long until someone
   notices.
4. **What breaks at ten times current load?** Quotas, sandbox limits on
   outbound email, connection pools, unindexed queries and rate limits
   set for a demo.
5. **What would a new operator not know?** Which command is the only
   way in, which rollback does not undo migrations, which setting reports
   a policy rather than a fact. Whatever the answer, it belongs in the
   runbook.
6. **What surprised you?** Anything unexpected found while reading the
   code or the environment is a lead.

## Every unresolved row becomes an issue

Before the audit ends, every row not at VERIFIED LIVE or VERIFIED IN CODE
(where code evidence is all the tier requires) has an issue, linked from
the row, in the launch milestone, with the band as its priority. The
same holds for each answer to the questions above that names a real
risk. A gap recorded only in the audit document is lost the moment
someone works from the tracker instead. Tell people to work the issues,
not the document's row numbers. See decisions-as-issues for how to write
them.

## The output

Return three things, in this order.

1. **The audit table:** every row with its level, date, method and
   issue link, grouped by section.
2. **The blocker list:** open rows by band, each with one line on why it
   is in that band and who can do the work (an agent, your human
   partner, a third party). Above the list, give the band definitions and
   the count per band. Below it, list what is deliberately not a blocker
   and why.
3. **The tier verdict:** the highest tier whose conditions are all met,
   the rows standing between it and the next tier, and the critical path
   through them. Give one verdict, with its reason in a sentence or two.

After those three, report what changed since the last pass in a short
section of its own: rows that changed level, issues added to the
milestone, premises found to be wrong. Recompute every figure in that
section from the rows, and do not copy it from the previous report.

## Red flags

- A row's level matches last pass's, and no check was run this pass.
- "Verified" with no date or method.
- A comparison that passed when one side came back empty.
- A restore judged by how fast it finished or whether it accepted
  connections.
- An alert that has never fired.
- A summary that disagrees with the rows.
- An infrastructure row verified from the declared configuration.

## Reviewing an audit against this skill

1. Does every row carry one evidence level, with a date and method from
   this pass?
2. Is code evidence kept separate from live evidence, and does each tier
   get the kind it requires?
3. Were the restore, rollback and alert drills actually run, and did the
   restore check counts and content?
4. Are infrastructure rows checked against deployed state?
5. Are the blocker bands defined, and does each open row's band fit its
   definition?
6. Is every issue named in a row in the launch milestone, and does every
   unresolved row have an issue?
7. Is every security or privacy claim in published text backed by a
   row?
8. Were the "what am I missing?" questions answered, with each answer
   tied to a row?
9. Does the output end with one tier verdict and the critical path to
   the next tier?
