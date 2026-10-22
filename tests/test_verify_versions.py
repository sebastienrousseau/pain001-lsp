# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Every version source agrees, and the pain001 floor is the release.

``scripts/verify_versions.py`` runs on every pull request. These tests
build a small tree where every source agrees, then move one source at a
time and expect the script to name it.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
V = "0.0.74"


@pytest.fixture
def verify() -> ModuleType:
    """The script, loaded as a module."""
    spec = importlib.util.spec_from_file_location(
        "verify_versions", ROOT / "scripts" / "verify_versions.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """A tree in which every source says 0.0.74."""
    _write(tmp_path, "pain001_lsp/__init__.py", f'__version__ = "{V}"\n')
    _write(
        tmp_path,
        "pyproject.toml",
        f'[tool.poetry]\nname = "pain001-lsp"\nversion = "{V}"\n\n'
        "[tool.poetry.scripts]\n"
        'pain001-lsp = "pain001_lsp.server:main"\n\n'
        "[tool.poetry.dependencies]\n"
        f'pain001 = ">={V},<1"\n',
    )
    _write(tmp_path, "CHANGELOG.md", f"## [{V}] - 2026-10-21\n\n## [0.0.72]\n")
    _write(tmp_path, "CITATION.cff", f'version: "{V}"\n')
    _write(tmp_path, "README.md", f"> **Latest release: v{V}**: notes\n")
    package = {"name": "pain001-lsp-json", "version": V}
    _write(tmp_path, "editors/vscode/package.json", json.dumps(package))
    lock = {**package, "packages": {"": package}}
    _write(tmp_path, "editors/vscode/package-lock.json", json.dumps(lock))
    _write(tmp_path, "editors/vscode/CHANGELOG.md", f"## {V}\n")
    _write(tmp_path, "requirements/runtime.in", f"pain001>={V},<1\npygls\n")
    _write(tmp_path, "requirements/ci.in", "-r runtime.in\npytest\n")
    return tmp_path


def test_an_agreeing_tree_passes(verify: ModuleType, tree: Path) -> None:
    assert verify.check(tree) == []


@pytest.mark.parametrize(
    ("name", "old", "new", "label"),
    [
        (
            "pyproject.toml",
            f'version = "{V}"',
            'version = "0.0.73"',
            "pyproject.toml version",
        ),
        ("CITATION.cff", V, "0.0.72", "CITATION.cff version"),
        ("README.md", V, "0.0.72", "README latest release"),
        ("CHANGELOG.md", " - 2026-10-21", "", "CHANGELOG.md dated heading"),
        (
            "editors/vscode/package.json",
            V,
            "0.0.72",
            "editors/vscode/package.json",
        ),
        (
            "editors/vscode/CHANGELOG.md",
            V,
            "0.0.72",
            "editors/vscode/CHANGELOG.md heading",
        ),
    ],
)
def test_each_drifted_source_is_named(
    verify: ModuleType, tree: Path, name: str, old: str, new: str, label: str
) -> None:
    path = tree / name
    path.write_text(path.read_text().replace(old, new), encoding="utf-8")
    problems = verify.check(tree)
    assert len(problems) == 1 and problems[0].startswith(f"{label}: ")


def test_the_lockfile_root_is_checked(verify: ModuleType, tree: Path) -> None:
    path = tree / "editors/vscode/package-lock.json"
    lock = json.loads(path.read_text())
    lock["packages"][""]["version"] = "0.0.72"
    path.write_text(json.dumps(lock), encoding="utf-8")
    assert verify.check(tree) == [
        "package-lock.json packages root: 0.0.72, expected 0.0.74"
    ]


def test_a_pyproject_floor_behind_the_release_fails(
    verify: ModuleType, tree: Path
) -> None:
    """The 0.0.72 release shipped with the floor still at 0.0.71."""
    path = tree / "pyproject.toml"
    path.write_text(path.read_text().replace(f'">={V},<1"', '">=0.0.71"'))
    assert verify.check(tree) == [
        "pyproject.toml pain001 floor: 0.0.71, expected 0.0.74"
    ]


def test_a_requirements_floor_behind_the_release_fails(
    verify: ModuleType, tree: Path
) -> None:
    path = tree / "requirements/runtime.in"
    path.write_text(path.read_text().replace(f">={V}", ">=0.0.72"))
    assert verify.check(tree) == [
        "requirements/runtime.in pain001 floor: 0.0.72, expected 0.0.74"
    ]


def test_an_unfloored_requirement_fails(
    verify: ModuleType, tree: Path
) -> None:
    _write(tree, "requirements/docs.in", "pain001[fast]\nsphinx\n")
    assert verify.check(tree) == [
        "requirements/docs.in pain001 floor: missing, expected 0.0.74"
    ]


def test_sibling_packages_are_not_the_core(
    verify: ModuleType, tree: Path
) -> None:
    _write(tree, "requirements/extra.in", "pain001-loader-mt101>=0.0.1\n")
    assert verify.check(tree) == []


def test_main_reports_and_exits(
    verify: ModuleType,
    tree: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(verify, "ROOT", tree)
    assert verify.main([]) == 0
    assert "agree on 0.0.74" in capsys.readouterr().out
    (tree / "CITATION.cff").write_text('version: "0.0.72"\n')
    assert verify.main([]) == 1
    assert "CITATION.cff version: 0.0.72" in capsys.readouterr().err


def test_a_tree_without_a_version_fails(
    verify: ModuleType, tree: Path
) -> None:
    (tree / "pain001_lsp/__init__.py").write_text("")
    assert verify.check(tree) == ["pain001_lsp/__init__.py has no __version__"]


def test_the_committed_tree_agrees(verify: ModuleType) -> None:
    assert verify.check(ROOT) == []


def test_the_script_fails_on_a_stale_floor_end_to_end(tree: Path) -> None:
    """Run as CI runs it: a floor behind the release exits non-zero."""
    import shutil
    import subprocess
    import sys

    (tree / "scripts").mkdir()
    shutil.copy(ROOT / "scripts" / "verify_versions.py", tree / "scripts")
    path = tree / "pyproject.toml"
    path.write_text(path.read_text().replace(f'">={V},<1"', '">=0.0.71"'))
    result = subprocess.run(  # nosec B603 - fixed argv
        [sys.executable, "-I", "scripts/verify_versions.py"],
        cwd=tree,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 1
    assert "pain001 floor: 0.0.71, expected 0.0.74" in result.stderr
