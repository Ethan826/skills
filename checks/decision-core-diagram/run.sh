#!/usr/bin/env bash
# Checks the reference onion drawing of decision-core-architecture: the
# committed diagram/onion.svg must equal the generator's output byte for byte,
# the default spec's import lists must name only its own layers, and the SVG
# must keep its dark-mode override, plain CSS (no var(), which rsvg-convert
# ignores) and no background. Needs bun on PATH; installs nothing. Works in a
# temporary directory removed on exit.
#
# Usage: run.sh [--repo DIR]
set -uo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
while [ $# -gt 0 ]; do
  case $1 in
    --repo) repo=$(cd "${2:?--repo needs a directory}" && pwd) || exit 2; shift 2 ;;
    *) echo "usage: run.sh [--repo DIR]" >&2; exit 2 ;;
  esac
done

fail() { echo "decision-core-diagram check: FAIL: $*" >&2; exit 1; }
command -v bun >/dev/null || fail "bun is not on PATH"

dir="$repo/skills/decision-core-architecture/diagram"
[ -f "$dir/onion.ts" ] || fail "no generator at $dir/onion.ts"
[ -f "$dir/onion.svg" ] || fail "no committed SVG at $dir/onion.svg"

work=$(mktemp -d "${TMPDIR:-/tmp}/decision-core-diagram.XXXXXX") || exit 2
trap 'rm -rf "$work"' EXIT

# 1. The generator runs (it throws on an import that names no layer) and its
#    output equals the committed file.
bun "$dir/onion.ts" >"$work/onion.svg" 2>"$work/err" || { cat "$work/err" >&2; fail "generator failed"; }
if ! cmp -s "$work/onion.svg" "$dir/onion.svg"; then
  diff "$dir/onion.svg" "$work/onion.svg" | head -20 >&2
  fail "committed onion.svg differs from the generator output; run: bun diagram/onion.ts > diagram/onion.svg"
fi

# 2. Every layer is labeled, and the styling stays renderable in both themes.
bun -e '
const { defaultSpec } = await import(process.argv[1])
const svg = await Bun.file(process.argv[2]).text()
const problems = []
for (const layer of defaultSpec.rings.flat()) if (!svg.includes(`>${layer.name}</`)) problems.push(`layer ${layer.name} is not labeled`)
if (!svg.includes("@media (prefers-color-scheme: dark)")) problems.push("no dark-mode override")
if (svg.includes("var(")) problems.push("uses var(), which rsvg-convert ignores")
if (svg.includes("<rect")) problems.push("has a background rect")
for (const p of problems) console.error(p)
process.exit(problems.length === 0 ? 0 : 1)
' "$dir/onion.ts" "$dir/onion.svg" || fail "diagram content"

layers=$(bun -e 'const { defaultSpec } = await import(process.argv[1]); console.log(defaultSpec.rings.flat().length)' "$dir/onion.ts")
echo "decision-core-diagram check: OK (onion.svg matches the generator, $layers layers)"
