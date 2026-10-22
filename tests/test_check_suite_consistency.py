# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The suite-consistency check compares this tree with its own release.

The core releases first, so between the core's tag and this member's the
check must report this member as behind the suite, never this tree as
"unreleased" because it differs from the core's number.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "check_suite_consistency.py"
)


@pytest.fixture
def checker() -> types.ModuleType:
    """The script, loaded as a module."""
    spec = importlib.util.spec_from_file_location("consistency", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run(
    checker: types.ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    tree: str,
    published: dict[str, str],
) -> list[str]:
    monkeypatch.setattr(checker, "tree_version", lambda: tree)
    monkeypatch.setattr(checker, "published_version", published.get)
    problems, _ = checker.check()
    return problems


def _suite(core: str, lsp: str) -> dict[str, str]:
    versions = dict.fromkeys(
        ("pain001", "pain001-mcp", "pain001-loader-mt101"), core
    )
    versions["pain001-loader-xlsx"] = core
    versions["pain001-lsp"] = lsp
    return versions


def test_this_package_is_named_from_pyproject(
    checker: types.ModuleType,
) -> None:
    assert checker.tree_name() == "pain001-lsp"


def test_a_released_tree_is_not_reported_as_unreleased(
    checker: types.ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The core shipped 0.0.74 first; this tree is the released 0.0.72."""
    problems = _run(checker, monkeypatch, "0.0.72", _suite("0.0.74", "0.0.72"))
    assert problems == [
        "pain001-lsp: published 0.0.72, but the suite is at 0.0.74"
    ]


def test_a_bump_that_was_never_released_is_reported(
    checker: types.ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tree at the core's number, but this package never shipped it."""
    problems = _run(checker, monkeypatch, "0.0.74", _suite("0.0.74", "0.0.72"))
    assert problems == [
        "pain001-lsp: tree is 0.0.74 but PyPI has 0.0.72. Either the "
        "release was never tagged, or the tree is behind.",
        "pain001-lsp: published 0.0.72, but the suite is at 0.0.74",
    ]


def test_an_unreadable_member_is_reported(
    checker: types.ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    published = _suite("0.0.74", "0.0.74")
    del published["pain001-mcp"]
    problems = _run(checker, monkeypatch, "0.0.74", published)
    assert problems == ["pain001-mcp: could not read PyPI"]


def test_an_agreeing_suite_has_no_problems(
    checker: types.ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert not _run(checker, monkeypatch, "0.0.74", _suite("0.0.74", "0.0.74"))
