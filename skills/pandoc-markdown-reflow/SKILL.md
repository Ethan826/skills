---
name: pandoc-markdown-reflow
description: Reflows a Markdown file and converts straight quotes, dashes and ellipses to typographic ones with pandoc, without damaging front matter, code blocks, tables or HTML comments. Use whenever someone asks to run pandoc over Markdown, reflow or rewrap prose, add smart or curly quotes to a Markdown document, or tidy a blog post or README's typography before publishing.
license: MIT
---

# Pandoc Markdown reflow

The base command is

```bash
pandoc --from=markdown+smart --to=markdown-smart in.md -o out.md
```

Reading with `+smart` turns `"` and `'` into curly quotes, `--` into an
en dash, `---` into an em dash and `...` into an ellipsis. Writing with
`-smart` keeps those as Unicode characters, and the writer rewraps prose
at 72 columns (`--columns=N` to change it). Code spans and code blocks
are not touched by `smart`.

Run on its own, that command damages five things. Checked with pandoc
3.0.1:

| Damage | Prevention |
| --- | --- |
| YAML front matter is dropped | Split it off first and reattach it unchanged |
| A fenced block with no language becomes an indented block | Give it a language first (`text`) |
| Tabs in code blocks become spaces (Go, Makefiles, tab-indented TS) | `--preserve-tabs` |
| HTML comments come back wrapped in `` ```{=html} `` blocks, which renderers show as code | Disable `raw_attribute` on output |
| Pipe tables come back as multiline tables, which GitHub-flavored renderers do not support | Disable `multiline_tables`, `simple_tables` and `grid_tables` on output |

## Procedure

1. Copy the file somewhere outside the repository, to compare against
   later.
2. Split the front matter (everything up to and including the closing
   `---`) from the body.
3. Give every bare opening fence a language: `` ``` `` becomes
   `` ```text ``.
4. Run on the body:

   ```bash
   pandoc --from=markdown+smart \
     --to=markdown-smart-raw_attribute-multiline_tables-simple_tables-grid_tables \
     --preserve-tabs body.md -o body.out.md
   ```

5. Reattach the front matter, then run the project's formatter (for
   example Prettier) if it has one. It realigns the table columns
   pandoc leaves ragged.
6. Compare with the copy, and do not trust the result until all of
   these hold:
   - every code block is byte-identical, in the same order;
   - every HTML comment is identical, and none is inside a fence;
   - the front matter is identical;
   - the prose differs only in wrapping and typography: normalize curly
     quotes back to straight and collapse whitespace on both sides, and
     the texts match;
   - no backslash escapes appeared in the prose;
   - no closing quote opens a word and no opening quote ends one.
7. Expect the dash and ellipsis conversions in prose. If a `--` or
   `...` was meant literally, put it in a code span before running.

If a check fails, restore the affected part from the copy rather than
editing the output by hand.
