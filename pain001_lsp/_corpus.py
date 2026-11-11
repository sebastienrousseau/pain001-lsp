# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Example corpus commands (pain001 >= 0.0.67).

``pain001.corpus.list`` lists the validated example files pain001 ships
and ``pain001.corpus.get`` returns one market file's XML with its
provenance sidecar. With an older pain001 both answer with an error
payload instead of failing at import time.
"""

from __future__ import annotations

import importlib
from typing import Any

from pygls.lsp.server import LanguageServer

from pain001_lsp._commands import command_options

CORPUS_LIST_COMMAND = "pain001.corpus.list"
CORPUS_GET_COMMAND = "pain001.corpus.get"
_CORPUS_MISSING = (
    "the example corpus needs pain001 >= 0.0.67; the installed pain001 "
    "has no pain001.corpus module"
)


def _corpus_api() -> Any | None:
    """Return :mod:`pain001.corpus`, or ``None`` when the library predates it.

    The corpus shipped in pain001 0.0.67; older releases remain valid
    peers of this server, so the corpus commands answer with an error
    payload instead of failing at import time.
    """
    try:
        return importlib.import_module("pain001.corpus")
    except ImportError:
        return None


def corpus_list(options: dict[str, Any] | None = None) -> dict[str, Any]:
    """List the validated example files pain001 ships.

    Pure helper behind :data:`CORPUS_LIST_COMMAND`. Market files are
    realistic payments per country and rail, each with a scenario id
    and an optional bank-overlay ``variant``; coverage files exercise
    every element and choice branch of one message type.

    Args:
        options: Optional filters: ``kind`` (``market`` or ``coverage``),
            ``country`` (two letters, any case) and ``version`` (a
            message type such as ``pain.001.001.09``).

    Returns:
        ``{"count", "files": [...]}`` or ``{"error": ...}`` when the
        installed pain001 has no corpus.
    """
    corpus = _corpus_api()
    if corpus is None:
        return {"error": _CORPUS_MISSING}
    options = options or {}
    country = options.get("country")
    wanted_country = str(country).upper() if country else None
    version = options.get("version")
    files = []
    for entry in corpus.list_files(options.get("kind")):
        if wanted_country and entry.country != wanted_country:
            continue
        if version and entry.version != version:
            continue
        files.append(
            {
                "kind": entry.kind,
                "scenario_id": entry.scenario_id,
                "version": entry.version,
                "country": entry.country,
                "family": entry.family,
                "variant": entry.variant,
                "file": entry.path.name,
            }
        )
    return {"count": len(files), "files": files}


def corpus_get(options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return one market file's XML and its provenance sidecar.

    Pure helper behind :data:`CORPUS_GET_COMMAND`. Editors use it to open
    a reference example next to the data file being authored: the XML a
    correct ``scenario_id`` produces in ``version``, and the sidecar
    that says which sources it rests on, how confident the evidence is
    and how every validation rung judged it.

    Args:
        options: ``scenario_id`` and ``version`` (required) and an
            optional ``variant`` overlay id for a bank variant.

    Returns:
        ``{"scenario_id", "version", "variant", "xml", "provenance"}`` or
        ``{"error": ...}`` when the arguments are incomplete, the file
        does not exist, or the installed pain001 has no corpus.
    """
    corpus = _corpus_api()
    if corpus is None:
        return {"error": _CORPUS_MISSING}
    options = options or {}
    scenario_id = options.get("scenario_id")
    version = options.get("version")
    variant = options.get("variant") or None
    if not scenario_id or not version:
        return {"error": "scenario_id and version are required"}
    try:
        xml = corpus.get_file(scenario_id, version, variant)
        record = corpus.provenance(scenario_id, version, variant)
    except FileNotFoundError as exc:
        return {"error": str(exc)}
    return {
        "scenario_id": scenario_id,
        "version": version,
        "variant": variant,
        "xml": xml,
        "provenance": record,
    }


def corpus_list_command(ls: LanguageServer, *args: Any) -> dict[str, Any]:
    """``workspace/executeCommand`` glue for :func:`corpus_list`.

    Args:
        ls: The language server (unused; pygls passes it first).
        *args: The command arguments; the first may be a filter dict.

    Returns:
        The :func:`corpus_list` payload.
    """
    return corpus_list(command_options(args))


def corpus_get_command(ls: LanguageServer, *args: Any) -> dict[str, Any]:
    """``workspace/executeCommand`` glue for :func:`corpus_get`.

    Args:
        ls: The language server (unused; pygls passes it first).
        *args: The command arguments; the first is the request dict.

    Returns:
        The :func:`corpus_get` payload.
    """
    return corpus_get(command_options(args))
