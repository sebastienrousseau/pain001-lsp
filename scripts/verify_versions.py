#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Verify that every restatement of the pain001-lsp version agrees.

The release version is ``pain001_lsp.__version__``. The same string must
appear in:

* ``pyproject.toml`` (``[tool.poetry] version``);
* ``CHANGELOG.md`` (a dated ``## [X.Y.Z] - YYYY-MM-DD`` heading);
* ``CITATION.cff`` (``version``);
* ``README.md`` (the ``Latest release: vX.Y.Z`` line);
* ``editors/vscode/package.json`` and the root of its lockfile (the
  extension ships at the suite's version), and an ``## X.Y.Z`` heading in
  ``editors/vscode/CHANGELOG.md``.

The suite releases in lockstep, the core first, so the ``pain001`` floor
in ``pyproject.toml`` and in every ``requirements/*.in`` that names it must
equal the release version too. The 0.0.72 changelog said the floor had
moved to 0.0.72 while ``pyproject.toml`` still said 0.0.71, and nothing
noticed.

Exit status 0 on agreement, 1 otherwise.

Usage:
    python scripts/verify_versions.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VERSION = r"(\d+\.\d+\.\d+)"

#: (label, file, pattern whose first group is the version).
TEXT_SOURCES = (
    (
        "pyproject.toml version",
        "pyproject.toml",
        rf'^version\s*=\s*"{VERSION}"',
    ),
    ("CITATION.cff version", "CITATION.cff", rf'^version:\s*"?{VERSION}"?'),
    ("README latest release", "README.md", rf"Latest release: v{VERSION}"),
)

#: The pain001 floor, in pyproject.toml and in a requirements file.
FLOOR_PYPROJECT = rf'^pain001\s*=\s*"?>=\s*{VERSION}'
FLOOR_REQUIREMENT = rf"^pain001(?:\[[^\]]*\])?\s*>=\s*{VERSION}"


def _read(root: Path, name: str) -> str:
    """The text of ``name`` under ``root``, or "" when it is missing."""
    path = root / name
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _first(pattern: str, text: str) -> str | None:
    """The first group of the first multiline match, or None."""
    match = re.search(pattern, text, re.MULTILINE)
    return match.group(1) if match else None


def package_version(root: Path) -> str | None:
    """``__version__`` as written in ``pain001_lsp/__init__.py``."""
    text = _read(root, "pain001_lsp/__init__.py")
    return _first(rf'^__version__\s*=\s*"{VERSION}"', text)


def _extension_versions(root: Path) -> dict[str, str | None]:
    """The VS Code extension's manifest, lockfile and changelog versions."""
    found: dict[str, str | None] = {}
    for label, name in (
        ("editors/vscode/package.json", "editors/vscode/package.json"),
        (
            "editors/vscode/package-lock.json",
            "editors/vscode/package-lock.json",
        ),
    ):
        text = _read(root, name)
        found[label] = str(json.loads(text).get("version")) if text else None
    lock = _read(root, "editors/vscode/package-lock.json")
    root_package = (
        json.loads(lock).get("packages", {}).get("", {}) if lock else {}
    )
    found["package-lock.json packages root"] = root_package.get("version")
    return found


def sources(root: Path, version: str) -> dict[str, str | None]:
    """Every restatement of the version, keyed by where it lives."""
    found = {
        label: _first(pattern, _read(root, name))
        for label, name, pattern in TEXT_SOURCES
    }
    changelog = _read(root, "CHANGELOG.md")
    dated = rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$"
    found["CHANGELOG.md dated heading"] = (
        version if re.search(dated, changelog, re.MULTILINE) else None
    )
    ext_changelog = _read(root, "editors/vscode/CHANGELOG.md")
    heading = rf"^## {re.escape(version)}$"
    found["editors/vscode/CHANGELOG.md heading"] = (
        version if re.search(heading, ext_changelog, re.MULTILINE) else None
    )
    found.update(_extension_versions(root))
    return found


def floors(root: Path) -> dict[str, str | None]:
    """The pain001 floor in pyproject.toml and each requirements/*.in."""
    found = {
        "pyproject.toml pain001 floor": _first(
            FLOOR_PYPROJECT, _read(root, "pyproject.toml")
        )
    }
    for path in sorted((root / "requirements").glob("*.in")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"^pain001\b(?!-)", text, re.MULTILINE):
            label = f"requirements/{path.name} pain001 floor"
            found[label] = _first(FLOOR_REQUIREMENT, text)
    return found


def check(root: Path) -> list[str]:
    """Every disagreement with ``__version__`` under ``root``."""
    version = package_version(root)
    if version is None:
        return ["pain001_lsp/__init__.py has no __version__"]
    found = {**sources(root, version), **floors(root)}
    return [
        f"{label}: {value or 'missing'}, expected {version}"
        for label, value in found.items()
        if value != version
    ]


def main(argv: list[str] | None = None) -> int:
    """Report every source that disagrees with ``__version__``."""
    del argv
    problems = check(ROOT)
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(
        f"OK: every version source and the pain001 floor agree on "
        f"{package_version(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
