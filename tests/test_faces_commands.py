# Copyright (C) 2023-2026 Pain001. All rights reserved.
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Tests for the faces commands, ``pain001.faces.list`` and ``.project``.

Faces ship in pain001 0.0.78. ``_faces_api`` is driven through
``importlib`` so the absent branches (no module, or one from before
``project_face_text``) are covered whichever pain001 is installed; the
other tests run against the real library and are skipped without it.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest
from pain001.corpus import get_file, list_files

import pain001_lsp.server as lsp_server
from pain001_lsp import _faces

SALARY_09 = get_file("de.sepa.sct-salary", "pain.001.001.09")

real = pytest.mark.skipif(
    _faces._faces_api() is None, reason="installed pain001 has no faces"
)


def _every_element_09() -> str:
    """The .09 coverage file the UK Open Banking face accepts."""
    path = next(
        f.path
        for f in list_files("coverage")
        if f.version == "pain.001.001.09"
        and f.path.name.startswith("01-transfer-every-element")
    )
    return path.read_text(encoding="utf-8")


def test_faces_api_without_the_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """An ImportError means no faces."""

    def missing(name: str) -> None:
        raise ImportError(name)

    monkeypatch.setattr(importlib, "import_module", missing)
    assert _faces._faces_api() is None


def test_faces_api_before_project_face_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A pain001.faces without the text entry point is treated as absent."""
    monkeypatch.setattr(
        importlib, "import_module", lambda name: SimpleNamespace()
    )
    assert _faces._faces_api() is None


def test_commands_report_missing_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With a pain001 that predates faces both commands say so."""
    monkeypatch.setattr(_faces, "_faces_api", lambda: None)
    expected = {"error": _faces.FACES_MISSING}
    assert _faces.faces_list() == expected
    assert _faces.faces_project({"xml": SALARY_09, "face": "x"}) == expected
    assert "0.0.78" in _faces.FACES_MISSING


def test_commands_are_registered_with_pygls() -> None:
    """Both command names are among the server's registered commands."""
    commands = set(lsp_server.server.protocol.fm.commands)
    assert {
        _faces.FACES_LIST_COMMAND,
        _faces.FACES_PROJECT_COMMAND,
    } <= commands
    assert {"pain001.faces.list", "pain001.faces.project"} <= commands


@real
def test_list_is_the_library_list() -> None:
    """Each face with its description and bindings."""
    from pain001.faces import list_supported_faces

    expected = {
        "count": len(list_supported_faces()),
        "faces": list_supported_faces(),
    }
    assert _faces.faces_list() == expected
    assert _faces.faces_list_command(object(), {"ignored": 1}) == expected


@real
def test_project_matches_the_library() -> None:
    """The command glue unwraps the first argument; the result is the library's."""
    from pain001.faces import project_face

    expected = project_face(SALARY_09, face="berlin_group").to_dict()
    request = {"xml": SALARY_09, "face": "berlin_group"}
    assert _faces.faces_project(request) == expected
    assert _faces.faces_project_command(object(), request) == expected
    assert expected["loss_report"]["unmapped_paths"]


@real
def test_project_passes_version_and_bindings() -> None:
    """A ConsentId binding turns the UK body into OBWriteDomestic2."""
    result = _faces.faces_project(
        {
            "xml": _every_element_09(),
            "face": "uk_open_banking",
            "version": "pain.001.001.09",
            "bindings": {"ConsentId": "consent-lsp-1"},
        }
    )
    assert result["version"] == "pain.001.001.09"
    assert result["payload"]["Data"]["ConsentId"] == "consent-lsp-1"


@real
def test_project_uses_the_given_version() -> None:
    """An explicit edition is honoured, not re-detected: .09 is not a .03."""
    result = _faces.faces_project(
        {
            "xml": SALARY_09,
            "face": "berlin_group",
            "version": "pain.001.001.03",
        }
    )
    assert list(result) == ["error"]
    assert "pain.001.001.03" in result["error"]


@real
@pytest.mark.parametrize(
    "request_",
    [
        None,
        {},
        {"xml": SALARY_09},
        {"face": "iso_2018"},
        {"xml": SALARY_09, "face": ""},
        {"xml": 1, "face": "iso_2018"},
        {"xml": SALARY_09, "face": 1},
    ],
    ids=[
        "none",
        "empty",
        "no-face",
        "no-xml",
        "blank-face",
        "xml-int",
        "face-int",
    ],
)
def test_project_requires_xml_and_face(request_: dict | None) -> None:
    """Missing or wrongly typed arguments are an error payload."""
    assert _faces.faces_project(request_) == {
        "error": "xml and face are required strings"
    }
    assert _faces.faces_project_command(object()) == {
        "error": "xml and face are required strings"
    }


@real
@pytest.mark.parametrize(
    ("request_", "reason"),
    [
        ({"xml": SALARY_09, "face": "uk_open_banking"}, "uk_open_banking"),
        (
            {"xml": SALARY_09, "face": "berlin_group", "bindings": {"X": 1}},
            "unknown binding",
        ),
        ({"xml": SALARY_09, "face": "nope"}, "unknown face 'nope'"),
        (
            {"xml": "/etc/passwd", "face": "iso_2018"},
            "expected the pain.001 document",
        ),
        (
            {
                "xml": '<!DOCTYPE d [<!ENTITY a "a">]><d>&a;</d>',
                "face": "iso_2018",
            },
            "refused XML",
        ),
        (
            {"xml": SALARY_09, "face": "iso_2018", "bindings": ["X"]},
            "bindings must be a JSON object",
        ),
    ],
    ids=[
        "refused",
        "binding",
        "unknown-face",
        "path",
        "entity",
        "bindings-list",
    ],
)
def test_refusals_are_error_payloads(request_: dict, reason: str) -> None:
    """A refusal is data with the face's reason, never an exception."""
    result = _faces.faces_project(request_)
    assert list(result) == ["error"]
    assert reason in result["error"]
