# decision-core-diagram check

Checks the reference onion drawing in `skills/decision-core-architecture/diagram/`.

```bash
checks/decision-core-diagram/run.sh        # needs bun on PATH; installs nothing
checks/decision-core-diagram/test-run.sh   # the check's own tests (planted defects)
```

It fails when:

- `onion.svg` differs by a single byte from what `onion.ts` prints;
- an import list in the default spec names a layer the spec does not have;
- a layer is not labeled in the SVG;
- the SVG loses its `@media (prefers-color-scheme: dark)` override, uses
  `var()` (which `rsvg-convert` ignores), or gains a background `<rect`.

`test-run.sh` plants each of those defects and requires the named failure.

The skill states no tool version, so `anchors.json` keeps
`decision-core-architecture` as `none`; the anchors gate registers only
checks that back a `tool` entry. This check runs in its own workflow,
`check-decision-core-diagram.yml`.

## What it does not catch

- Whether the default import lists match the import table in `SKILL.md`. That
  table is prose; the two were compared by hand when the generator was
  written.
- Overlapping or clipped text. Render both themes with `rsvg-convert` and look
  after changing a note, a name or the geometry.
- A project's copy of the generator. The project's own drift test covers it.
