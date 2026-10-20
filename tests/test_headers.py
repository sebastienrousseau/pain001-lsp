# Copyright (C) 2023-2026 Sebastien Rousseau.
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every tracked source and Markdown file carries the suite's SPDX header.

The README once opened with ``<!-- SPDX-License-Identifier: ... OR MIT>``.
The missing ``-->`` turned the first three hundred lines into one HTML
comment, so GitHub, PyPI and the Sphinx manual rendered almost nothing
of it, and no gate noticed. These tests make the header, and its
termination, part of the build.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SPDX = "SPDX-License-Identifier: Apache-2.0 OR MIT"
MARKDOWN_HEADER = f"<!-- {SPDX} -->"
SOURCE_SUFFIXES = {".py", ".ts"}


def _tracked() -> list[Path]:
    """Return the files git tracks, or skip outside a checkout."""
    try:
        listing = subprocess.run(  # nosec B603 B607 - fixed argv
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("not a git checkout")
    return [ROOT / name for name in listing.splitlines()]


def test_source_files_carry_the_spdx_header() -> None:
    missing = [
        str(path.relative_to(ROOT))
        for path in _tracked()
        if path.suffix in SOURCE_SUFFIXES
        and SPDX
        not in "".join(path.read_text(encoding="utf-8").splitlines(True)[:3])
    ]
    assert not missing, f"no {SPDX!r} in the first 3 lines: {missing}"


def test_markdown_opens_with_a_terminated_spdx_comment() -> None:
    wrong = [
        str(path.relative_to(ROOT))
        for path in _tracked()
        if path.suffix == ".md"
        and path.read_text(encoding="utf-8").split("\n", 1)[0]
        != MARKDOWN_HEADER
    ]
    assert not wrong, f"line 1 is not {MARKDOWN_HEADER!r}: {wrong}"
