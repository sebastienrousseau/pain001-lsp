# Copyright (C) 2023-2026 Pain001. All rights reserved.
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Tests for the example-corpus commands.

The corpus ships in pain001 0.0.67 and the lockfile may pin an older
library, so the helpers are driven through a stub ``pain001.corpus``
module for both the present and the absent branch, and once against the
real library when it has the corpus.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

import pain001_lsp.server as lsp_server


@dataclass
class _File:
    kind: str
    version: str
    path: Path
    scenario_id: str | None = None
    country: str | None = None
    family: str | None = None
    variant: str | None = None


_FILES = [
    _File(
        "market",
        "pain.001.001.03",
        Path("gb.chaps.property-purchase.pain.001.001.03.xml"),
        "gb.chaps.property-purchase",
        "GB",
        "priority-payment",
    ),
    _File(
        "market",
        "pain.001.001.03",
        Path(
            "gb.chaps.property-purchase__gb.example.priority.pain.001.001.03.xml"
        ),
        "gb.chaps.property-purchase",
        "GB",
        "priority-payment",
        "gb.example.priority",
    ),
    _File(
        "market",
        "pain.001.001.09",
        Path("se.bankgiro.supplier.pain.001.001.09.xml"),
        "se.bankgiro.supplier",
        "SE",
        "bankgiro-credit",
    ),
    _File("coverage", "pain.001.001.13", Path("set-01.xml")),
]


def _stub_corpus() -> SimpleNamespace:
    def list_files(kind=None):
        return [f for f in _FILES if kind in (None, f.kind)]

    def get_file(scenario_id, version, variant=None):
        for f in _FILES:
            if (f.scenario_id, f.version, f.variant) == (
                scenario_id,
                version,
                variant,
            ):
                return f"<Document>{f.path.name}</Document>"
        raise FileNotFoundError(
            f"no market file for {scenario_id} in {version}"
        )

    def provenance(scenario_id, version, variant=None):
        get_file(scenario_id, version, variant)
        return {"scenario": scenario_id, "message_type": version}

    return SimpleNamespace(
        list_files=list_files, get_file=get_file, provenance=provenance
    )


@pytest.fixture
def stub(monkeypatch):
    """Make ``pain001.corpus`` resolve to the stub."""
    fake = _stub_corpus()
    real = importlib.import_module

    def fake_import(name, package=None):
        if name == "pain001.corpus":
            return fake
        return real(name, package)

    monkeypatch.setattr(lsp_server.importlib, "import_module", fake_import)
    return fake


@pytest.fixture
def absent(monkeypatch):
    """Make ``pain001.corpus`` unimportable."""
    real = importlib.import_module

    def fake_import(name, package=None):
        if name == "pain001.corpus":
            raise ImportError("No module named 'pain001.corpus'")
        return real(name, package)

    monkeypatch.setattr(lsp_server.importlib, "import_module", fake_import)


def test_corpus_list_returns_every_file_with_metadata(stub):
    """No filter lists market and coverage files alike."""
    out = lsp_server.corpus_list()
    assert out["count"] == 4
    assert out["files"][1]["variant"] == "gb.example.priority"
    assert out["files"][-1] == {
        "kind": "coverage",
        "scenario_id": None,
        "version": "pain.001.001.13",
        "country": None,
        "family": None,
        "variant": None,
        "file": "set-01.xml",
    }


def test_corpus_list_filters(stub):
    """Kind, country (any case) and version filters combine."""
    assert lsp_server.corpus_list({"kind": "coverage"})["count"] == 1
    assert lsp_server.corpus_list({"country": "gb"})["count"] == 2
    se = lsp_server.corpus_list(
        {"kind": "market", "version": "pain.001.001.09"}
    )
    assert [f["scenario_id"] for f in se["files"]] == ["se.bankgiro.supplier"]
    assert lsp_server.corpus_list({"country": "CH"})["count"] == 0


def test_corpus_get_returns_xml_and_sidecar(stub):
    """The generic file and the bank variant are distinct, each with a sidecar."""
    generic = lsp_server.corpus_get(
        {
            "scenario_id": "gb.chaps.property-purchase",
            "version": "pain.001.001.03",
        }
    )
    variant = lsp_server.corpus_get(
        {
            "scenario_id": "gb.chaps.property-purchase",
            "version": "pain.001.001.03",
            "variant": "gb.example.priority",
        }
    )
    assert generic["variant"] is None and "__" not in generic["xml"]
    assert (
        variant["variant"] == "gb.example.priority" and "__" in variant["xml"]
    )
    assert generic["provenance"]["scenario"] == "gb.chaps.property-purchase"


def test_corpus_get_errors(stub):
    """Missing arguments and unknown files are error payloads."""
    assert (
        "required"
        in lsp_server.corpus_get({"version": "pain.001.001.03"})["error"]
    )
    assert "required" in lsp_server.corpus_get(None)["error"]
    out = lsp_server.corpus_get(
        {
            "scenario_id": "gb.chaps.property-purchase",
            "version": "pain.001.001.13",
        }
    )
    assert "no market file" in out["error"]


def test_corpus_commands_report_missing_library(absent):
    """With a pain001 that predates the corpus both commands say so."""
    expected = {"error": lsp_server._CORPUS_MISSING}
    assert lsp_server.corpus_list() == expected
    assert (
        lsp_server.corpus_get({"scenario_id": "x", "version": "y"}) == expected
    )


def test_command_glue_passes_the_first_dict_argument(stub):
    """The executeCommand handlers unwrap ``arguments[0]`` and tolerate none."""
    ls = object()
    assert lsp_server.corpus_list_command(ls)["count"] == 4
    assert (
        lsp_server.corpus_list_command(ls, {"kind": "coverage"})["count"] == 1
    )
    assert lsp_server.corpus_list_command(ls, "not-a-dict")["count"] == 4
    got = lsp_server.corpus_get_command(
        ls,
        {"scenario_id": "se.bankgiro.supplier", "version": "pain.001.001.09"},
    )
    assert got["xml"].startswith("<Document>")


def test_commands_are_registered_with_pygls():
    """Both command names are part of the server's registered commands."""
    names = set()
    for attr in ("_features", "commands", "_commands"):
        reg = getattr(lsp_server.server, attr, None)
        if isinstance(reg, dict):
            names |= set(reg)
    lsp_features = getattr(
        getattr(lsp_server.server, "protocol", None), "fm", None
    )
    if lsp_features is not None:
        names |= set(getattr(lsp_features, "commands", {}))
    assert {
        lsp_server.CORPUS_LIST_COMMAND,
        lsp_server.CORPUS_GET_COMMAND,
    } <= names


def test_real_corpus_when_available():
    """Against a pain001 that ships the corpus the commands return real data."""
    if lsp_server._corpus_api() is None:
        pytest.skip("installed pain001 has no example corpus")
    files = lsp_server.corpus_list({"kind": "market", "country": "GB"})
    assert files["count"] > 0
    first = files["files"][0]
    got = lsp_server.corpus_get(
        {
            "scenario_id": first["scenario_id"],
            "version": first["version"],
            "variant": first["variant"],
        }
    )
    assert got["xml"].startswith("<?xml")
    assert got["provenance"]["validation"]["xsd"]["errors"] == 0
