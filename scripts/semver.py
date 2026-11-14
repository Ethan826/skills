"""Semantic Versioning 2.0.0 parsing and precedence (semver.org).

parse() accepts exactly the grammar of section 2 and 9-10 (the regular
expression is the one semver.org publishes); a leading "v" is not part
of a version and is rejected. Comparison follows section 11: numeric
fields numerically, a pre-release below its release, pre-release
identifiers compared numerically when both are numeric, by ASCII order
when both are not, numeric below alphanumeric, and a shorter list below
a longer one with the same prefix. Build metadata is ignored.
"""
from __future__ import annotations

import re
from functools import total_ordering
from typing import Iterable, Optional

# From semver.org, "Is there a suggested regular expression".
PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$")


def _identifier_key(identifier: str):
    if identifier.isdigit():
        return (0, int(identifier), "")
    return (1, 0, identifier)


@total_ordering
class Version:
    def __init__(self, major: int, minor: int, patch: int,
                 prerelease: tuple, build: tuple):
        self.major, self.minor, self.patch = major, minor, patch
        self.prerelease = prerelease
        self.build = build

    @property
    def is_prerelease(self) -> bool:
        return bool(self.prerelease)

    def _key(self):
        release = (self.major, self.minor, self.patch)
        if not self.prerelease:
            return (release, 1, ())
        return (release, 0,
                tuple(_identifier_key(i) for i in self.prerelease))

    def __eq__(self, other) -> bool:
        return isinstance(other, Version) and self._key() == other._key()

    def __lt__(self, other: "Version") -> bool:
        return self._key() < other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        text = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            text += "-" + ".".join(self.prerelease)
        if self.build:
            text += "+" + ".".join(self.build)
        return f"Version({text!r})"


def parse(text: str) -> Version:
    match = PATTERN.match(text) if isinstance(text, str) else None
    if not match:
        raise ValueError(f"not a SemVer 2.0.0 version: {text!r}")
    major, minor, patch, pre, build = match.groups()
    return Version(int(major), int(minor), int(patch),
                   tuple(pre.split(".")) if pre else (),
                   tuple(build.split(".")) if build else ())


def latest_stable(versions: Iterable[str], allow_pre: bool) -> Optional[str]:
    """The highest-precedence version, or None.

    Pre-releases count only when allow_pre is true. Strings that are not
    SemVer versions are skipped: they cannot be ordered against the anchor.
    """
    best = None
    for text in versions:
        try:
            version = parse(text)
        except ValueError:
            continue
        if version.is_prerelease and not allow_pre:
            continue
        candidate = (version, text)
        if best is None or candidate[0] > best[0] or \
                (candidate[0] == best[0] and text > best[1]):
            best = candidate
    return best[1] if best else None
