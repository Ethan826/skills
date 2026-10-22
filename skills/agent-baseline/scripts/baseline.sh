#!/usr/bin/env bash
# Install, check and sync marked sections in an always-loaded agent
# instruction file (AGENTS.md or the project's equivalent).
#
# A marked section is the lines from a start marker to its end marker,
# both at the start of a line:
#
#   <!-- NAME:start vN -->
#   ...
#   <!-- NAME:end -->
#
# NAME is lowercase letters, digits and hyphens. The " vN" version is
# optional in the syntax and recommended in practice.
#
# Usage:
#   baseline.sh install <instruction-file> [block-file]
#   baseline.sh check <instruction-file> [block-file]
#   baseline.sh sync [--expect a,b] <source> <copy>
#   baseline.sh check-sync [--expect a,b] <source> <copy>
#
# block-file defaults to ../baseline.md beside this script. It must hold
# exactly one marked section; text outside the markers is not installed.
#
# --expect pins the section names that both files must contain, comma
# separated. It defaults to agent-baseline. check and check-sync fail
# when either file has no marked sections at all, so two files that both
# lack the block can never pass.
#
# Exit status: 0 on success, 1 on a failed check, 2 on bad usage or a
# malformed file.
set -euo pipefail

prog=baseline.sh
here=$(cd "$(dirname "$0")" && pwd)
default_block="$here/../baseline.md"
default_expect=agent-baseline

die() {
  echo "$prog: $*" >&2
  exit 2
}

fail() {
  echo "$prog: FAIL: $*" >&2
}

usage() {
  grep '^#   baseline.sh ' "$0" | sed 's/^#   /usage: /' >&2
  exit 2
}

tmp=$(mktemp -d "${TMPDIR:-/tmp}/baseline.XXXXXX")
trap 'rm -rf "$tmp"' EXIT

# extract FILE DIR: write each marked section of FILE, markers included,
# to DIR/NAME, and the section names in file order to DIR/.names.
# Exits 2 on nested, unmatched, unterminated or duplicate markers, and on
# a line that starts like a marker but is not well formed.
extract() {
  local file=$1 dir=$2
  mkdir -p "$dir"
  : >"$dir/.names"
  awk -v dir="$dir" -v prog="$prog" '
    function bad(msg) {
      printf "%s: %s:%d: %s\n", prog, FILENAME, FNR, msg > "/dev/stderr"
      err = 1
      exit 2
    }
    function marker_name(line, kind,    n) {
      n = line
      sub(/^<!-- /, "", n)
      sub(":" kind ".*$", "", n)
      return n
    }
    {
      sub(/\r$/, "")
      is_start = ($0 ~ /^<!-- [a-z0-9][a-z0-9-]*:start( v[0-9]+)? -->[ \t]*$/)
      is_end = ($0 ~ /^<!-- [a-z0-9][a-z0-9-]*:end -->[ \t]*$/)
      if (!is_start && !is_end && $0 ~ /^[ \t]*<!--[ \t]*[A-Za-z0-9_-]+:(start|end)/)
        bad("malformed section marker: " $0)
      if (is_start) {
        if (open != "") bad("start of \"" marker_name($0, "start") "\" inside open section \"" open "\"")
        open = marker_name($0, "start")
        if (open in seen) bad("section \"" open "\" appears twice")
        seen[open] = 1
        out = dir "/" open
        print open >> (dir "/.names")
        print $0 > out
        next
      }
      if (is_end) {
        name = marker_name($0, "end")
        if (open == "") bad("end of \"" name "\" with no open section")
        if (name != open) bad("end of \"" name "\" does not match open section \"" open "\"")
        print $0 > out
        close(out)
        open = ""
        next
      }
      if (open != "") print $0 > out
    }
    END {
      if (err) exit 2
      if (open != "") {
        printf "%s: %s: section \"%s\" has no end marker\n", prog, FILENAME, open > "/dev/stderr"
        exit 2
      }
    }
  ' "$file" || exit 2
}

count() {
  wc -l <"$1/.names" | tr -d ' '
}

# replace_or_append FILE NAME SECTION_FILE: put SECTION_FILE in place of
# section NAME in FILE, or append it after a blank line if FILE has no
# such section. Creates FILE if it does not exist.
replace_or_append() {
  local file=$1 name=$2 section=$3 out="$tmp/rewrite"
  if [ ! -e "$file" ]; then
    cat "$section" >"$file"
    result=created
    return
  fi
  result=replaced
  if grep -q "^<!-- $name:start\( v[0-9][0-9]*\)\{0,1\} -->" "$file"; then
    # Keep the file's final-newline state: awk ends every line it prints
    # with a newline, so a file whose last line has none would otherwise
    # gain one on every install, even when the section is unchanged.
    # emit() writes each line's newline before the next line instead, and
    # END writes the last one only if the original file had it.
    local final_newline=1
    if [ -n "$(tail -c 1 "$file")" ]; then
      final_newline=0
    fi
    awk -v name="$name" -v section="$section" -v final_newline="$final_newline" '
      function emit(s) {
        if (started) printf "\n"
        printf "%s", s
        started = 1
      }
      BEGIN { skipping = 0; started = 0 }
      {
        line = $0
        sub(/\r$/, "", line)
        if (!skipping && line ~ ("^<!-- " name ":start( v[0-9]+)? -->[ \t]*$")) {
          while ((getline s < section) > 0) emit(s)
          close(section)
          skipping = 1
          next
        }
        if (skipping) {
          if (line ~ ("^<!-- " name ":end -->[ \t]*$")) skipping = 0
          next
        }
        emit($0)
      }
      END { if (started && final_newline) printf "\n" }
    ' "$file" >"$out"
  else
    result=appended
    cat "$file" >"$out"
    if [ -s "$file" ]; then
      if [ -n "$(tail -c 1 "$file")" ]; then
        printf '\n' >>"$out"
      fi
      if [ -n "$(tail -n 1 "$file" | tr -d ' \t\r')" ]; then
        printf '\n' >>"$out"
      fi
    fi
    cat "$section" >>"$out"
  fi
  if cmp -s "$out" "$file"; then
    result=unchanged
    return
  fi
  cat "$out" >"$file"
}

# load_block BLOCK_FILE DIR: extract the block file and print its single
# section name.
load_block() {
  local block=$1 dir=$2
  [ -f "$block" ] || die "block file $block does not exist"
  extract "$block" "$dir"
  local n
  n=$(count "$dir")
  [ "$n" -eq 1 ] || die "block file $block must hold exactly one marked section; it holds $n"
  head -n 1 "$dir/.names"
}

cmd_install() {
  [ $# -ge 1 ] && [ $# -le 2 ] || usage
  local file=$1 block=${2:-$default_block} name
  name=$(load_block "$block" "$tmp/block")
  if [ -e "$file" ]; then
    extract "$file" "$tmp/target"
  fi
  replace_or_append "$file" "$name" "$tmp/block/$name"
  echo "$prog: section \"$name\" in $file: $result"
}

cmd_check() {
  [ $# -ge 1 ] && [ $# -le 2 ] || usage
  local file=$1 block=${2:-$default_block} name
  name=$(load_block "$block" "$tmp/block")
  if [ ! -f "$file" ]; then
    fail "$file does not exist"
    exit 1
  fi
  extract "$file" "$tmp/target"
  if [ "$(count "$tmp/target")" -eq 0 ]; then
    fail "$file has no marked sections at all"
    exit 1
  fi
  if [ ! -f "$tmp/target/$name" ]; then
    fail "$file has no \"$name\" section"
    exit 1
  fi
  if ! cmp -s "$tmp/block/$name" "$tmp/target/$name"; then
    fail "section \"$name\" in $file differs from $block"
    diff "$tmp/block/$name" "$tmp/target/$name" >&2 || true
    echo "$prog: rerun: $prog install $file $block" >&2
    exit 1
  fi
  echo "$prog: PASS: section \"$name\" in $file matches $block"
}

# parse_sync_args "$@": sets expect, src, copy.
parse_sync_args() {
  expect=$default_expect
  local positional=()
  while [ $# -gt 0 ]; do
    case $1 in
      --expect)
        [ $# -ge 2 ] || usage
        expect=$2
        shift 2
        ;;
      --expect=*)
        expect=${1#--expect=}
        shift
        ;;
      -*) usage ;;
      *)
        positional+=("$1")
        shift
        ;;
    esac
  done
  [ ${#positional[@]} -eq 2 ] || usage
  src=${positional[0]}
  copy=${positional[1]}
  [ -n "$expect" ] || die "--expect needs at least one section name"
  case $expect in
    *[!a-z0-9,-]* | ,* | *, | *,,*) die "bad --expect list: $expect" ;;
  esac
}

# require_sections LABEL FILE DIR: fail unless DIR holds at least one
# section and every expected name. Prints failures; returns 1 on any.
require_sections() {
  local file=$1 dir=$2 status=0 name
  if [ "$(count "$dir")" -eq 0 ]; then
    fail "$file has no marked sections at all"
    return 1
  fi
  for name in $(printf '%s\n' "$expect" | tr ',' ' '); do
    if [ ! -f "$dir/$name" ]; then
      fail "$file has no \"$name\" section (pinned by --expect)"
      status=1
    fi
  done
  return $status
}

cmd_sync() {
  parse_sync_args "$@"
  [ -f "$src" ] || die "$src does not exist"
  extract "$src" "$tmp/src"
  require_sections "$src" "$tmp/src" || exit 1
  if [ -e "$copy" ]; then
    extract "$copy" "$tmp/copy"
    local stale=0 name
    while IFS= read -r name; do
      if [ ! -f "$tmp/src/$name" ]; then
        fail "$copy has section \"$name\", which $src lacks; add it to $src or delete it from $copy"
        stale=1
      fi
    done <"$tmp/copy/.names"
    [ $stale -eq 0 ] || exit 1
  fi
  local name
  while IFS= read -r name; do
    replace_or_append "$copy" "$name" "$tmp/src/$name"
    echo "$prog: section \"$name\" in $copy: $result"
  done <"$tmp/src/.names"
  echo "$prog: synced $(count "$tmp/src") section(s) from $src into $copy"
}

cmd_check_sync() {
  parse_sync_args "$@"
  local f status=0 name
  for f in "$src" "$copy"; do
    if [ ! -f "$f" ]; then
      fail "$f does not exist"
      status=1
    fi
  done
  [ $status -eq 0 ] || exit 1
  extract "$src" "$tmp/src"
  extract "$copy" "$tmp/copy"
  require_sections "$src" "$tmp/src" || status=1
  require_sections "$copy" "$tmp/copy" || status=1
  while IFS= read -r name; do
    if [ ! -f "$tmp/copy/$name" ]; then
      fail "section \"$name\" is in $src but not in $copy"
      status=1
    elif ! cmp -s "$tmp/src/$name" "$tmp/copy/$name"; then
      fail "section \"$name\" differs between $src and $copy"
      diff "$tmp/src/$name" "$tmp/copy/$name" >&2 || true
      status=1
    fi
  done <"$tmp/src/.names"
  while IFS= read -r name; do
    if [ ! -f "$tmp/src/$name" ]; then
      fail "section \"$name\" is in $copy but not in $src"
      status=1
    fi
  done <"$tmp/copy/.names"
  if [ $status -ne 0 ]; then
    echo "$prog: edit $src, then run: $prog sync --expect $expect $src $copy" >&2
    exit 1
  fi
  echo "$prog: PASS: $(count "$tmp/src") section(s) match between $src and $copy"
}

[ $# -ge 1 ] || usage
sub=$1
shift
case $sub in
  install) cmd_install "$@" ;;
  check) cmd_check "$@" ;;
  sync) cmd_sync "$@" ;;
  check-sync) cmd_check_sync "$@" ;;
  -h | --help | help) usage ;;
  *) usage ;;
esac
