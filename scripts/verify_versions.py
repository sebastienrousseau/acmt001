#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Fail when the release version is restated differently anywhere.

Single source of truth: ``version`` in ``pyproject.toml``. The same string
must appear as:

* ``__version__`` in ``acmt001/__init__.py``;
* ``VERSION`` in ``acmt001/constants.py``;
* a ``## [X.Y.Z]`` heading in ``CHANGELOG.md``;
* the "Latest release: vX.Y.Z" callout in ``README.md``;
* the supported row of the version table in ``SECURITY.md``.

The README callout still read v0.0.1 at 0.0.9, because nothing
compared it with anything.

Standard library only, so the workflow needs no install.

Usage: python3 scripts/verify_versions.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: (file, pattern whose first group is the version restated there).
RESTATEMENTS = (
    ("acmt001/__init__.py", r'^__version__\s*=\s*"([^"]+)"'),
    ("acmt001/constants.py", r'^VERSION\s*=\s*"([^"]+)"'),
    ("README.md", r"Latest release: v(\d+\.\d+\.\d+)"),
    ("SECURITY.md", r"^\| `(\d+\.\d+\.\d+)` \| Latest released"),
)


def _read(root: Path, name: str) -> str:
    path = root / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _search(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1) if match else None


def pyproject_version(root: Path) -> str:
    """The version ``pyproject.toml`` declares: the source of truth."""
    version = _search(
        r'^version\s*=\s*"([^"]+)"', _read(root, "pyproject.toml")
    )
    if version is None:
        raise SystemExit("pyproject.toml has no version field")
    return version


def problems(root: Path = ROOT) -> list[str]:
    """Every restatement of the version that disagrees with pyproject."""
    expected = pyproject_version(root)
    out = [
        f"{name}: says {found}, pyproject.toml says {expected}"
        for name, pattern in RESTATEMENTS
        if (found := _search(pattern, _read(root, name))) != expected
    ]
    if f"\n## [{expected}]" not in "\n" + _read(root, "CHANGELOG.md"):
        out.append(f"CHANGELOG.md: no ## [{expected}] heading")
    return out


def main() -> int:
    """Compare every restatement of the version and report."""
    found = problems(ROOT)
    for problem in found:
        print(f"ERROR: {problem}")
    if found:
        return 1
    print(f"OK: every version source agrees on {pyproject_version(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
