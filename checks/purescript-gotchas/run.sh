#!/usr/bin/env bash
# Compile one small module set per purescript-gotchas claim against the
# pinned toolchain (see README.md). Everything is installed into a mktemp
# work directory, removed on exit; HOME and the caches point inside it, so
# nothing global is read or written. Needs bun, node (>= 22.5, for spago),
# python3 and git on PATH.
# Exit 0 prints "purescript-gotchas check: OK (N cases)".
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

# Only these tools are visible; a global purs or spago (for example in
# ~/.nvm) stays off PATH.
mkdir -p "$work/bin" "$work/home" "$work/cache" "$work/project"
for tool in bun node python3 git; do
  found="$(command -v "$tool")" || { echo "run.sh: $tool not found" >&2; exit 1; }
  ln -s "$found" "$work/bin/$tool"
done
export PATH="$work/project/node_modules/.bin:$work/bin:/usr/bin:/bin"
export HOME="$work/home" XDG_CACHE_HOME="$work/cache"
export BUN_INSTALL_CACHE_DIR="$work/bun-cache"

cp "$here/package.json" "$here/bun.lock" "$here/spago.yaml" "$here/spago.lock" \
  "$work/project/"
cd "$work/project"
bun install --frozen-lockfile >/dev/null

for tool in purs spago; do
  case "$(command -v "$tool")" in
    "$work"/*) ;;
    *) echo "run.sh: $tool resolves outside the work directory" >&2; exit 1 ;;
  esac
done

# --pure installs from spago.lock as committed; the cmp catches a rewrite.
spago install --pure >"$work/spago-install.log" 2>&1 ||
  { cat "$work/spago-install.log" >&2; exit 1; }
cmp -s spago.lock "$here/spago.lock" ||
  { echo "run.sh: spago install changed spago.lock" >&2; exit 1; }
mv output "$work/out"

status=0
python3 "$here/runner.py" --project "$work/project" --out "$work/out" \
  --repo "$repo" || status=$?
if [ -n "${PURESCRIPT_GOTCHAS_DU:-}" ]; then
  du -sh "$work" >&2
fi
exit "$status"
