# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The complexity gate catches each ceiling and holds the baseline.

``scripts/check_complexity.py`` measures every function against the
ceilings (cyclomatic 10, cognitive 15, Halstead difficulty 30, 60 lines;
500 lines per file) and compares the offenders with
``complexity-baseline.json``, which may only shrink.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """The script as a module, rooted at ``tmp_path``."""
    spec = importlib.util.spec_from_file_location(
        "check_complexity", ROOT / "scripts" / "check_complexity.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "BASELINE", tmp_path / "baseline.json")
    monkeypatch.setattr(module, "PATHS", ("pkg",))
    (tmp_path / "pkg").mkdir()
    return module


def _branchy() -> str:
    body = "".join(
        f"    if x == {i}:\n        return {i}\n" for i in range(11)
    )
    return f"def branchy(x):\n{body}    return -1\n"


def _nested() -> str:
    return (
        "def nested(rows):\n"
        "    for row in rows:\n"
        "        for cell in row:\n"
        "            for part in cell:\n"
        "                if part:\n"
        "                    if part > 1:\n"
        "                        if part > 2:\n"
        "                            return part\n"
        "    return None\n"
    )


def _long() -> str:
    body = "".join(f"    y{i} = {i}\n" for i in range(60))
    return f"def long():\n{body}    return 0\n"


def _difficult() -> str:
    # Halstead difficulty is (distinct operators / 2) * (operands /
    # distinct operands): one operand under twelve operators.
    ops = ["+", "-", "*", "/", "//", "%", "**", "<<", ">>", "&", "|", "^"]
    body = "".join(f"    c = c {op} c\n" for op in ops * 2)
    return f"def difficult(c):\n{body}    return c\n"


@pytest.mark.parametrize(
    ("source", "key", "metric", "value"),
    [
        (_branchy(), "pkg/offender.py::branchy", "cyclomatic", 12),
        (_nested(), "pkg/offender.py::nested", "cognitive", 21),
        (_long(), "pkg/offender.py::long", "lines", 62),
        (_difficult(), "pkg/offender.py::difficult", "halstead", None),
        ("x = 1\n" * 501, "pkg/offender.py", "file_lines", 501),
    ],
    ids=["cyclomatic", "cognitive", "lines", "halstead", "file-lines"],
)
def test_each_ceiling_is_caught(
    gate: ModuleType,
    tmp_path: Path,
    source: str,
    key: str,
    metric: str,
    value: float | None,
) -> None:
    path = tmp_path / "pkg" / "offender.py"
    path.write_text(source, encoding="utf-8")
    report = gate.measure_file(path)
    assert metric in report[key], report
    if value is None:
        assert report[key][metric] > gate.CEILINGS[metric]
    else:
        assert report[key][metric] == value


def test_a_function_within_every_ceiling_is_not_reported(
    gate: ModuleType, tmp_path: Path
) -> None:
    path = tmp_path / "pkg" / "fine.py"
    path.write_text("def fine(x):\n    return x + 1\n", encoding="utf-8")
    assert gate.measure_file(path) == {}


def test_the_ratchet(gate: ModuleType) -> None:
    """New or worse offenders fail; an improvement must shrink the file."""
    baseline = {"a.py::f": {"cyclomatic": 12}, "a.py::g": {"lines": 70}}
    assert gate.compare(dict(baseline), baseline) == []
    assert gate.compare(
        {**baseline, "a.py::h": {"cognitive": 16}}, baseline
    ) == ["a.py::h: cognitive 16 is over the ceiling"]
    assert gate.compare(
        {**baseline, "a.py::f": {"cyclomatic": 13}}, baseline
    ) == ["a.py::f: cyclomatic rose from 12 to 13"]
    assert gate.compare({"a.py::f": {"cyclomatic": 12}}, baseline) == [
        "a.py::g: lines improved from 70 to within the ceiling; "
        "run with --update to shrink the baseline"
    ]


def test_update_writes_the_baseline_and_main_then_passes(
    gate: ModuleType,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "pkg" / "bad.py").write_text(_branchy(), encoding="utf-8")
    gate.BASELINE.write_text("{}\n", encoding="utf-8")
    assert gate.main([]) == 1
    assert "is over the ceiling" in capsys.readouterr().err
    assert gate.main(["--update"]) == 0
    written = json.loads(gate.BASELINE.read_text(encoding="utf-8"))
    assert written == {"pkg/bad.py::branchy": {"cyclomatic": 12}}
    assert gate.main([]) == 0
    assert "1 baselined offenders, none worse" in capsys.readouterr().out


def test_the_committed_tree_holds_its_baseline() -> None:
    """The repository itself passes against complexity-baseline.json."""
    spec = importlib.util.spec_from_file_location(
        "check_complexity_tree", ROOT / "scripts" / "check_complexity.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main([]) == 0
