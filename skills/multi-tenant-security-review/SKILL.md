---
name: multi-tenant-security-review
description: Reviews a multi-tenant application for tenant isolation and authorization, meaning whether one tenant can read or change another tenant's data and whether a user can act beyond their role. It checks where authorization decisions live, requires the tenant as an explicit parameter on every data access, runs a route sweep derived from the API definition (anonymous, every role, and a user of a second tenant, against an expected-status table), tests every write path with another tenant's IDs, and works through a checklist of common cross-tenant leaks. Use it whenever you add or change routes, roles, permissions, sessions, queries or background jobs in software that serves more than one customer organization, before a launch or a release that touches authentication, and whenever someone asks whether tenants are isolated. It is not a full security audit, and it says what it leaves out.
license: MIT
---

# Multi-tenant security review

## What this review is for

The threat model is narrow. In a system that serves several tenants
(customer organizations whose data shares one deployment), the review
asks two questions. Can a user of one tenant read or change another
tenant's data, by any route, query, job, cache or log? And can a user
act beyond their role inside their own tenant: a member doing an
admin's work, an admin doing a platform operator's? The attacker is
assumed to hold a valid account somewhere in the system, to be able to
craft any request, and to know or guess other tenants' identifiers.

## What it does not cover

This is not a comprehensive security audit, and its report must not
read like one. It does not cover:

- infrastructure hardening: network exposure, TLS configuration,
  container and host hardening, cloud permissions, security headers;
- supply chain: dependencies, build pipelines, provenance (see
  dependency-intake);
- cryptography: algorithm choice, key management, password hashing
  parameters, token formats;
- penetration testing by people trying to break in, which finds
  classes of problem a structured review does not;
- denial of service beyond the limits in the leak checklist, and
  secrets management.

For those, use a dedicated review, a published verification standard
such as the OWASP Application Security Verification Standard, or a
professional penetration test. launch-readiness-audit covers the wider
go-live picture. Name each excluded area in the report so nobody reads
a clean isolation review as a clean bill of health.

## Where authorization lives

Authentication establishes who the caller is. Authorization decides
whether that caller may do this thing to this record. Parsing and
validation are neither. A request body that decodes into a well-typed
command says only that the request is well formed. It does not say the
caller may issue it. Parsing is not authorization.

Put the layers where they belong:

| Layer | Its job | Not its job |
|---|---|---|
| Entrypoint (route handler, message consumer) | Coarse checks: is there a valid session, is the tenant resolved, is the request well formed | Deciding whether this caller may act on this record |
| Use case | The authorization decision, made explicitly, with the caller, the tenant and the target record in hand | Parsing raw input |
| Domain | Pure policy helpers the use case calls, such as "may this role edit this kind of record" | I/O, or looking up the caller itself |

A coarse check at the entrypoint is not authorization. "Signed in"
says nothing about which records the caller may touch. Middleware that
requires an admin role on a route group is coarse too: it does not know
which tenant's record the request names. Keep the real decision in one
explicit, central place per use case, so a reviewer can find it and a
test can reach it.

Signs it has drifted:

- an ownership check written inline in a handler, and missing from its
  sibling handlers;
- a use case that trusts an ID because "the route already checked it";
- a role check in the user interface with no counterpart on the server;
- a refusal that throws an unhandled error and surfaces as a 500, which
  means the check exists but nobody designed what happens when it fails.

## The tenant is an explicit parameter

Every function that reads or writes tenant-scoped data takes the tenant
as a required argument. The data layer never pulls the tenant from
ambient state: a request-local global, a thread-local, a connection
setting nobody can see at the call site. Ambient tenant context fails
silently. A background job, a retry or a test runs without it, and the
query either fails open or quietly uses whichever tenant was left
behind.

Illustration, in TypeScript:

```ts
// Ambient: nothing at the call site says which tenant this reads.
findInvoice(invoiceId)

// Explicit: the tenant is part of the query, and the type requires it.
findInvoice(tenantId, invoiceId)
//   SELECT ... FROM invoices WHERE tenant_id = $1 AND id = $2
```

Rules that follow from this:

- **Filter by tenant in the query itself,** even when IDs are globally
  unique. "The ID is a UUID, so it cannot collide" is true and beside
  the point. The attacker supplies the ID on purpose.
- **Resolve the tenant once, at the boundary, from a trusted source**
  (the session, or a verified host mapping), and pass it down. Never
  take it from a request field the caller controls.
- **Test the tenant resolution itself.** If the tenant comes from a
  `Host` or forwarded-host header behind a proxy, test which header
  wins and what happens
  when it is missing or names no tenant.
- **Layered data needs the same care.** Where platform defaults are
  overlaid with per-tenant overrides, the override layer is keyed by
  tenant explicitly, and a read must not fall through to another
  tenant's overrides. append-only-data-model covers layered overrides.

## The route sweep

A route sweep sends one request to every route the application serves,
under each kind of caller, and checks each status against a table of
expectations. It catches what handler-level tests cannot see: routing
that misses, middleware not wired to a new route, and a refusal path
that faults.

### Derive the routes from the API definition

Read the list of routes from the same API definition the server is
built from: the router, the schema, the OpenAPI document. Never keep a
hand list. A hand list goes stale the day someone adds a route, and the
new route is exactly the one that needs checking. Pin the count of
route groups (or routes) in an assertion, so a discovery bug that
returns nothing fails loudly instead of passing an empty sweep. Adding
a group then means updating the pin on purpose, in the same change.

### Sweep under every kind of caller

Run the full sweep as:

1. an anonymous caller;
2. each role in the system, one session per role, all in tenant A;
3. each role in tenant B, one session per role, aiming at tenant A's
   real records.

The cross-tenant pass is the one that tests isolation. Point its
requests at IDs that exist in tenant A. A request for an ID that names
nothing tests only the not-found path.

Run the cross-tenant pass under every role, not only B's most privileged
one. Handlers often branch on role, and each branch can build its own
query: a handler can scope its admin branch to the caller's tenant and
forget the tenant filter in its member branch. A sweep that sends only
B's admin across the boundary passes against that handler while any B
member can read A's records. By default, the sweep is the full matrix of
every role in every tenant. Collapse two cells into one only with
evidence that they exercise the same authorization and query path, such
as a handler with no role branch, and record that evidence beside the
table so a later branch reopens the cell.

Consider a hypothetical sweep that runs three sessions, an anonymous
caller and two of A's roles, and no cross-tenant pass. It leaves every
other role, and the tenant boundary itself, to hand-run checks that
drift out of date. This skill requires both: every role in tenant A,
and every role of the second tenant.

### The expected-status table

Write the expectation for every route and caller before running the
sweep:

| Route | Anonymous | Member | Admin | Tenant B member | Tenant B admin |
|---|---|---|---|---|---|
| `GET /invoices` | 401 | 200, own only | 200, all of A's | 200, none of A's | 200, none of A's |
| `GET /invoices/:id` (member's own) | 401 | 200 | 200 | 404 | 404 |
| `GET /invoices/:id` (a colleague's) | 401 | 403 | 200 | 404 | 404 |
| `PATCH /invoices/:id` | 401 | 403 | 200 | 404 | 404 |
| `PATCH /admin/users/:id` (a user of A) | 401 | 403 | 200 | 404 | 404 |

The example is illustrative. A cell stands for one fully specified
scenario: the route, the caller, the target record and the request
payload are all fixed, so the scenario has exactly one right answer.
A status alone proves little, so each cell also names two more
assertions, and the test checks all three:

- **The payload.** What the response body may contain: for a list, which
  records and none of another tenant's; for a refusal, no record data in
  the error body.
- **The side effects.** What must and must not have changed: after a
  refused write, the record reads back unchanged and no event, email or
  job was emitted; after an allowed write, exactly the intended change
  happened.

Rules for the table:

- **Each scenario expects exactly one status.** "403 or 404" is not an
  expectation. A route that no longer exists answers 404, so an
  either-or cell passes while testing nothing. Choose per route. If you
  answer 404 to hide another tenant's records, prove the route exists
  with a control in the same test (the owner's request succeeds).
- **An empty 200 is not a refusal.** When a request names a target
  (an ID in the path, a subject in a filter), a handler that ignores it
  and returns the caller's own records, or nothing, looks identical to
  one that held the boundary. Seed the target with data,
  leave the caller with none, and expect a refusal status.
- **Pair every refusal with a control.** The same request from a caller
  who is allowed must succeed. Without it, a handler that refuses
  everyone, or that crashes, looks correct. Choose the control's role
  from the use case's actual rule. If only admins may act, a plain
  member is not the control.
- **Send a valid request.** A malformed body is refused at parsing,
  before the authorization check runs. A 400 in a role or cross-tenant
  cell means "not tested", not "refused". Build a well-formed payload
  for each write route, using IDs that work for the control.
- **Pin what is allowed on purpose.** A read that a lower role may
  legitimately make belongs in the table as an expected 200, so that a
  later over-tightening fails the sweep too.
- **No 5xx anywhere.** A refusal is a 4xx. A 500 on a refusal path is
  a finding.

### Lists checked in both directions

A sweep keeps short lists of exceptions: routes that are public to
anonymous callers, and groups where no session can reach a success
(token-only flows, platform-operator routes). Check each list both
ways:

- every route not on the public list refuses an anonymous caller; and
- every route on the public list really does answer an anonymous
  caller, so an entry left behind after a route was locked down gets
  removed instead of implying an open door.

The same goes for the no-success list. A group on it that starts
succeeding fails the check, and so does a group off it that never
succeeds. Each entry carries a one-line reason.

### Routes that end the session

A logout or revoke route kills the session the sweep is holding, and
every later route then answers 401. Skip it in the sweep and assert it
in a test of its own, with a fresh session: before logout the session
works, and afterwards it answers 401. The route is still checked, only
outside the sweep.

### Keeping the sweep honest

A 200 where the table says 403, or any success where it expects a
refusal, is a release blocker. It does not get
recorded as a known issue, retried until it passes, or fixed by
loosening the expectation. Changing an expectation is a decision made
with your human partner, recorded with its reason. gate-integrity
covers keeping a check like this from being weakened to get green.

## Insecure direct object references on writes

Most isolation testing stops at reads. Test every write path as well:
create, update, delete, archive, attach, assign, invite, export.

- Issue each write as a tenant B user with tenant A's ID, wherever the
  ID appears: path, query string, body field, or a nested reference
  (an own-tenant parent with a foreign child).
- Expect the refusal from the table, then read the record back as its
  owner and confirm nothing changed. A refusal status after a partial
  write is still a leak.
- Within a tenant, try fields that change authority: a role, an admin
  flag, an owner, a "submit on behalf of" field. A user must not be
  able to promote themselves or act as someone else by naming them.
- Pair each refusal with a control: the same body, from the owner or
  with the field naming the caller, succeeds.

## The usual cross-tenant leaks

Work through this list in every review. These failures sit outside
the main data path, where the route sweep does not look.

| Leak | What to check |
|---|---|
| Rate limits keyed on a spoofable address | A limiter keyed on `X-Forwarded-For` taken at face value lets a caller pick a fresh key per request. Take the client address only from the hop your own proxy sets, and test that rotating a forged header does not reset the count. |
| Missing body and field length limits | Every request has a body size cap, and every string field a maximum length, enforced before the work starts. One tenant must not be able to exhaust what all tenants share. |
| Development origins allowed in production | CORS in production allows only production origins. Test that a localhost origin gets no allow header. |
| CSRF on cookie-authenticated writes | Every state-changing route that accepts a cookie session checks the Origin or a CSRF token. Test with a foreign origin. |
| Sessions not revoked on password reset | A reset revokes every other session for that user. Test with two sessions. |
| Unauthenticated logout | Logout requires the session it ends. A route that revokes a session by ID without authentication lets anyone sign anyone out. |
| Tokens or personal data in logs | Request logging redacts cookies, authorization headers, reset and invite tokens, and personal fields. Error bodies do not echo another tenant's IDs or names. |
| Guessable IDs used as bearer secrets | A sequential or guessable ID must never be the only thing protecting a resource (a share link, an invite, a download). Bearer secrets are long and random, and expire. |
| Caches and search indexes keyed without the tenant | Every cache key and every search query includes the tenant. Test by warming a cache as tenant A and reading as tenant B. |
| Background jobs that drop the tenant | Jobs, queues, scheduled tasks and webhooks carry the tenant in their payload and pass it explicitly to every data call. A job that runs "for all tenants" iterates over tenants and does not query across them. |

## Minting test sessions

Create test sessions through the data layer, not through the login
route. Insert the user, their role and a live session record directly
in test setup, and send the resulting cookie or token. A sweep issues
one request per route for every caller. If each caller logs in first,
the login rate limiter trips, the sweep runs with no session, and every
route reports 401, which looks like a wiring fault and is not one. Test
the real login path, rate limiter included, once and on its own.

Keep the helper honest: it must write exactly what the real login
writes (expiry, role, disabled flag), or the sweep tests a session the
application never issues.

## The output

Return the report in three parts.

**1. Findings,** each with a severity:

- **Critical:** a cross-tenant read or write, privilege escalation, or
  any 200 where the table expects a refusal. A release blocker.
- **Important:** a leak-checklist item that fails, a refusal that
  answers 5xx, an authorization decision outside the use case, or a
  data access without an explicit tenant.
- **Minor:** hardening that reduces exposure without closing a known
  path, such as an error message that names a record type it need not.

Give each finding the route or code location, the request that shows
it, the observed and expected result, and the fix.

**2. The sweep results:** the route and group counts, the callers swept
(every role in each tenant, with the evidence for any collapsed cell),
the expected-status table with each mismatch marked, both directions of
each exception list, and every cell recorded as "not tested" with the
reason.

**3. Out of scope:** the areas from "What it does not cover" that this
review did not examine, plus anything in scope that could not be tested
and why. verify-before-claiming applies to every "isolated" or "passes"
in the report.

## Review checklist

1. Is the threat model stated, and does the report say what is out of
   scope?
2. Is every authorization decision in a use case, with entrypoints
   doing only coarse checks?
3. Does every tenant-scoped data access take the tenant explicitly and
   filter by it in the query?
4. Is the route list derived from the API definition, with the count
   pinned?
5. Were all routes swept as anonymous, as every role, and as every role
   of a second tenant against real records? Is each collapsed
   cross-tenant cell backed by recorded evidence that it exercises the
   same authorization and query path as the cell kept?
6. Does every fully specified scenario expect exactly one status, with
   its payload and side-effect assertions, and is every refusal paired
   with a control? Does every concealing 404 have a control proving the
   route exists?
7. Are the exception lists checked in both directions, each entry with
   a reason?
8. Was every write path tested with another tenant's IDs, and the
   record read back unchanged?
9. Was every item in the leak checklist checked?
10. Were test sessions minted through the data layer, with the real
    login tested separately?
11. Is every 200-where-403-expected reported as Critical and treated as
    a release blocker?
