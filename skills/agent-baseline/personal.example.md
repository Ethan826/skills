# Personal preferences block (optional)

Copy this file out of the skill, for example to `agent-personal.md` in
your own dotfiles, edit the items, and install it beside the baseline:

```bash
baseline.sh install AGENTS.md path/to/agent-personal.md
baseline.sh check AGENTS.md path/to/agent-personal.md
```

Only the lines between the markers are installed. Each item below is set
to the skill author's defaults, and the comment under it says how to
change it. When you change an item, bump the version in the start marker
and reinstall, so every copy that still carries the old wording fails its
check.

<!-- agent-personal:start v1 -->
## Personal preferences

These preferences belong to the project owner and hold in every session
and subagent, alongside the agent baseline.

- **Text published under the owner's name:** supply the facts as bullets,
  not drafted narrative, unless the owner asks for prose. The owner
  writes the narrative; drafted paragraphs read as generated.
  <!-- To change: replace with "Draft prose freely" or limit it to named
  kinds of text, such as "blog posts and release notes". -->
- **Spelling:** American, in code, identifiers, comments, docs and commit
  messages, even where nearby text uses another variant. Mention the
  inconsistency instead of matching it.
  <!-- To change: name another variant, such as British or Canadian. -->
- **Notation:** explain in words, not mathematical notation, unless the
  notation is necessary. Then define each symbol once in plain words.
  <!-- To change: replace with "Mathematical notation is welcome" or name
  the notation that may be assumed. -->
- **Prose review:** run explanatory docs, READMEs, commit messages and PR
  descriptions through the humanized-prose-review skill before showing
  them.
  <!-- To change: name another voice or prose-review skill, or delete the
  item to skip the review. -->
<!-- agent-personal:end -->
