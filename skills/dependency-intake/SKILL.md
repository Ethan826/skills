---
name: dependency-intake
description: Decides whether to take on a dependency and how, and reviews upgrades to existing ones. It covers libraries, frameworks, vendored files, installed agent skills and hosted services. It asks four questions of every candidate (what it drags in, what the import says, how much of it is wanted, whose release cycle it puts you on), prefers taking the ideas and leaving the code, writes a short review record, and sets rules for vendoring, gateways, exact pins, lockfiles and license compatibility. Use it whenever you are about to add a package, copy in third-party code or documentation, install an agent skill, wire in an external API, or bump a version, and whenever a library looks like a quick win because its types happen to fit. Use it too when asked to "just upgrade" something, because an upgrade is a review of behaviour changes as well as a version bump.
license: MIT
---

# Dependency intake

A dependency is an architectural decision. It decides what your code
imports, which release schedule you follow, which licenses you carry, and
for an agent skill, what your agent is told to do. Make the decision on
purpose, write it down, and review each upgrade as a change in behaviour.

This applies to anything you did not write and do not fully control: a
package from a registry, a framework, a file copied from another
repository, an agent skill installed from a registry, and a hosted
service your code calls.

## Order of preference

Prefer, in order:

1. the standard library;
2. a dependency the project already has (check the lockfile, since a
   transitive dependency may already be there);
3. a small local module that you write and own;
4. a new dependency, as a last resort.

Vendoring counts as option 4. It gives you more control, and it still
has to answer the questions below. A gateway (below) decides where a
dependency may be used, whichever of these you pick.

## The four questions

A type that fits is not a reason to import it. A generic library can
compile cleanly against your types and still be the wrong choice. Ask
these four questions of every candidate, and write down the answers.

1. **What does it drag in?** List its transitive dependencies. Each one
   is a decision the library makes for you. A date library that pulls in
   a serialization package has picked your serialization format before
   you chose one on its merits.
2. **What does the import say?** An import tells a reader what the
   importing module depends on. A pricing module that imports from a
   calendar library announces a dependency on calendars. Layer checks
   can enforce which direction imports go, but nothing checks whether
   they make sense.
3. **How much of it is wanted?** Compare what you will use with what you
   take on. Needing four predicates from a library of several hundred
   lines is a sign to write the forty lines yourself.
4. **Whose release cycle?** Check the version, how often it ships and
   who maintains it. A pre-1.0 library, or one with a single maintainer,
   puts its breaking changes on your schedule, including in code that
   has nothing to do with its purpose.

A candidate that passes all four might look like this. The library is already in the
tree through other dependencies, so it adds no packages. The import names
what it is (a JSON library imported by the JSON decoder). The code uses a
real share of it. It has been stable for years. Write down the
alternatives you rejected and why: one added a package, and another
brought two-way codecs the code does not need.

Apply the questions to the parts of a system that need them. In a
multi-language project the core may need strict discipline, while the
outer shell takes ordinary platform dependencies on their own merits.
Requiring every library in the shell to have bindings in the core's
language spreads one layer's rules to every layer.

## Take the ideas and leave the code

When the questions say no, you can often still use what the library got
right. Keep its conventions (half-open ranges, a constructor that rejects
invalid input, its names for things) and write the small part you need.
Record the name of the technique in a comment or the design notes, so
that the next person knows what to search for if the need grows.

Ideas and named techniques are free to use. Copied code and prose are
not (see "Licenses").

## The review record

Every change that adds a dependency carries a short review, in a
committed review file or in the pull request description, wherever the
project keeps them. Keep it to a few lines per heading:

```markdown
## <package or skill or service>

- Why: <the need, and why the standard library and existing dependencies don't meet it>
- Alternatives considered: <each one, and why it lost>
- Footprint: <transitive packages added; runtime or dev-only; size if it ships to users>
- Fit: <what the import says; how much of it is used>
- Release cycle and maintenance: <version, cadence, maintainer; upgrade effort expected>
- Security and supply chain: <install scripts, downloaded binaries, network access, permissions>
- License: <license, and whether it is compatible>
- Pinning: <exact pin or range, and why>
```

Record candidates you decline too, with the reason. A short list of
"considered and declined" saves the next person from repeating the
search, and it says what would have to change before the question is
worth reopening.

## Vendoring

Vendoring means copying third-party source into the repository instead
of resolving it through a package manager. It removes the supply-chain
and runtime-resolution risk, and in exchange you do every update by hand.

Vendor when the code is small and stable, and when you need most of what
you copy. Do not copy a large file in order to delete most of it: writing
the small part yourself is cheaper and carries no attribution duty.

Vendored code must:

- **record its origin:** the upstream repository and the exact version
  or commit it was copied from;
- **keep the license notice inside the vendored folder**, next to the
  code, so the notice travels with any copy of that folder;
- **state what was modified**, file by file, or say that nothing was;
- **keep its bytes as they arrived.** Exclude vendored folders from
  formatters and auto-fixers. A repository-wide reformat turns the next
  upstream comparison into thousands of whitespace lines that hide the
  real change.

If you rewrite a vendored file so thoroughly that it no longer tracks
upstream, treat it as your own text. Keep the attribution the license
requires, note which parts derive from the original, and accept that it
no longer follows upstream releases. Maintain it as a fork.

## Gateways for volatile systems

A gateway is an interface over an external system or protocol: an HTTP
API, a payment processor, an email provider, a queue. Use cases depend on
the interface. The implementation lives in the shell, and the core never
imports the vendor's SDK. See decision-core-architecture for where each
layer sits.

Illustration in TypeScript:

```ts
interface EmailGateway {
  sendReceipt(to: EmailAddress, receipt: Receipt): Promise<Result<void, EmailError>>;
}
```

Gateways isolate volatility, and vendoring isolates code. They solve
different problems, and a hosted service usually needs a gateway whether
or not its SDK is vendored. Replacing the provider, or a test double,
then means writing one new implementation instead of editing every
caller.

## Pins and lockfiles

- **Pin version-locked families exactly.** Some packages are released
  together and must match: a framework's core and its plugins, or a
  compiler and its runtime library. Pin each member to the same exact
  version, with no range operator. A range lets one member move ahead of
  the others, and the mismatch tends to show up at runtime, not at
  install.
- **The lockfile is the tool of record.** The package manager writes the
  lockfile and the installed tree together, so they agree by
  construction. Do not reimplement its hashes or rebuild its manifest to
  check it. Distrust it only for a specific reason. "I have not confirmed
  it myself" is not one. See verify-before-claiming, "The Tool of
  Record".
- **A stale lockfile is an incomplete commit.** Every change to a
  manifest commits the lockfile the tool wrote for it, in the same
  commit. A manifest without its lockfile builds differently on the next
  machine.
- **Reinstall after switching branches** when branches differ in their
  dependencies and share one installed tree. Otherwise imports resolve
  against the other branch's versions.

## Upgrades

When the request is "bump the versions", the deliverable is the bumped
versions plus a reviewed account of what changed in behaviour. It is not
an integrity audit of the package manager. For each package that moved:

1. Run the package manager's own upgrade command and commit what it
   writes.
2. Read the changelog or release notes for every version you skipped,
   along with any migration guide.
3. Write down each change that touches your code: renamed functions,
   stricter validation, changed defaults, renamed output fields. A
   renamed field in log or event output can silently break a dashboard
   or an alert that filters on the old name.
4. Run the full gate (see verify-before-claiming) and report the result.

For a major upgrade, three more rules apply.

- **Set the baseline on the main branch under the new install, first.**
  Install the new versions against the main branch's unchanged code and
  run lint and tests. Some warnings and failures come from the new
  dependency tree itself, not from your migration. Without this baseline
  you will "fix" them as migration bugs, or blame the migration for
  them.
- **A passing type check does not show that runtime behaviour held.** An
  upgrade can keep a name and tighten what it accepts, so a rename table
  lists it as a plain rename when it is not. Read the semantics of
  anything the guide calls a rename, and run the tests that exercise
  real data, including the property tests, whose generators may now
  produce inputs the stricter version rejects.
- **Count suppression and lint comments before and after a mechanical
  sweep.** Codemods and auto-fixes can strip trailing suppression
  comments, and some of those comments guard code the type checker
  wrongly thinks is redundant. Compare the counts across branches (for
  example, `git grep -c` on the project's suppression marker) and
  account for every one that went missing.

A migration helper's idea of "done" (often "it type-checks") may be
weaker than the project's gate. When the two differ, the project's gate
decides.

## Licenses

Check compatibility before adding anything, and check it for copied text
as well as packages.

- **Permissive licenses** (MIT, BSD, Apache-2.0) allow reuse with
  attribution. Apache-2.0 also requires you to keep its NOTICE file, if it has one, and
  to state changes in modified files.
- **Share-alike and copyleft licenses** (the GPL family, CC BY-SA, and
  for data, licenses such as ODbL) attach conditions to derived works. A
  snippet or a database extract can bring those conditions into a
  project whose own license is permissive.
- **Documentation and examples are covered too.** Code copied from a
  tutorial, a reference manual, another project's README or a
  question-and-answer site carries that source's license. Text on many
  public wikis and Q&A sites is CC BY-SA. Write your own examples, and
  borrow ideas rather than wording.
- **No stated license means no permission.** Ask the author, or leave it
  out.

## Agent skills as dependencies

An installed agent skill is a dependency that runs with your agent's
full permissions, and a change to its text changes how your agent
behaves. Hold it to the same intake as code, with these additions.

**Selection.** Apply the tests in this order. A candidate that fails an
early test is not rescued by passing a later one.

1. Does the project use the thing, at the version the skill assumes?
   Advice for the next major version of a framework is wrong for code
   still on the current one.
2. Is the source credible? A first-party vendor or a known maintainer
   outranks an aggregator that repackages documentation.
3. Is it adopted? Treat install count as a floor, not a ranking. Below
   the floor, skip an unknown author. Above it, counts stop telling
   candidates apart.
4. Does it fight the project's conventions? A skill the agent has to be
   talked out of is worse than none.
5. Is it already covered by the harness's built-in skills or by one
   already installed? A duplicate adds tokens and conflicting advice
   and no new capability.

**Pin and review.** Install project-local, record each skill's source
and version in a lockfile, and commit the installed skill bodies as
well. A skill is instructions your agent follows with full permissions,
so the reason to commit the bodies is review: every change to what the
agent is told then arrives as a diff that someone reads before it lands.
How much a lockfile alone protects you depends on the tool (some pin a
version, some a content hash they check on install), and committing the
bodies gives a reviewed diff either way. Read the diff after every
update before committing it. A skill that fetches its instructions over
the network each time it runs is unpinned by design. Note that, and
decide whether you accept it.

**Your own skills.** A skill you adapt heavily becomes your own text:
check it in, keep the upstream attribution, and stop following upstream
releases. For conventions specific to the project, write a local skill
before installing another generic one. No registry skill knows them, and
a generic skill may get them wrong. Update a local skill in the same
commit that changes the convention it describes.

**Removal.** Remove a skill whose advice contradicts the project's rules,
and a version-specific one whose job is done, such as a migration skill
after the migration lands. Remove every trace of it: the lockfile entry,
the installed folder, any links to it, and the roster entry. Re-check the
roster when a major dependency version changes.

## Review checklist

- [ ] The order of preference was followed, and the reason for skipping
      each earlier option is written down.
- [ ] The four questions have written answers.
- [ ] Anything that could be taken as ideas instead of code was.
- [ ] A review record exists, including declined alternatives.
- [ ] Vendored code records its upstream version, has its license notice
      inside its folder, lists its modifications and is excluded from
      formatters.
- [ ] A hosted or volatile system is reached only through a gateway.
- [ ] Version-locked families are pinned to one exact version.
- [ ] The lockfile written by the tool is in the same commit as the
      manifest change, and nobody re-derived its contents.
- [ ] An upgrade lists the behaviour changes found, not just the new
      versions.
- [ ] A major upgrade set its baseline on the main branch under the new
      install, counted suppression comments before and after, and did
      not stop at a passing type check.
- [ ] Licenses are compatible, including those of copied documentation,
      examples and data.
- [ ] Agent skills passed the selection tests, are pinned with their
      bodies committed, and their update diffs were read.
