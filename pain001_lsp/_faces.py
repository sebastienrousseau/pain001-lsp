# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Faces commands: a pain.001 document projected into another standard.

``pain001.faces.list`` names each face, its target and the binding keys
it accepts; ``pain001.faces.project`` takes the document as XML text
(the editor sends the buffer) and returns the target payload with a
loss report of every source element not carried. Both delegate to
:mod:`pain001.faces` (pain001 >= 0.0.78) through
:func:`pain001.faces.project_face_text`, which never reads a path and
refuses entity declarations. With an older pain001 they answer with an
error payload, like the corpus commands.
"""

from __future__ import annotations

import importlib
from typing import Any

from pygls.lsp.server import LanguageServer

from pain001_lsp._commands import command_options

FACES_LIST_COMMAND = "pain001.faces.list"
FACES_PROJECT_COMMAND = "pain001.faces.project"
FACES_MISSING = (
    "faces need pain001 >= 0.0.78; the installed pain001 has no "
    "pain001.faces.project_face_text"
)


def _faces_api() -> Any | None:
    """Return :mod:`pain001.faces`, or ``None`` when the library predates it."""
    try:
        faces = importlib.import_module("pain001.faces")
    except ImportError:
        return None
    return faces if hasattr(faces, "project_face_text") else None


def faces_list() -> dict[str, Any]:
    """List the faces, their targets and the binding keys each accepts.

    Pure helper behind :data:`FACES_LIST_COMMAND`.

    Returns:
        ``{"count", "faces": [{"name", "description", "bindings"}, ...]}``
        or ``{"error": ...}`` when the installed pain001 has no faces.
    """
    faces = _faces_api()
    if faces is None:
        return {"error": FACES_MISSING}
    entries = faces.list_supported_faces()
    return {"count": len(entries), "faces": entries}


def faces_project(options: dict[str, Any] | None = None) -> dict[str, Any]:
    """Project a pain.001 document into a face, with its loss report.

    Pure helper behind :data:`FACES_PROJECT_COMMAND`. An editor sends the
    open buffer's text, so a payment file can be checked against the
    request body a UK Open Banking or Berlin Group API expects, and
    against what that body leaves out, without leaving the editor.

    Args:
        options: ``xml`` (the document text) and ``face`` (required), an
            optional ``version`` and optional ``bindings`` (an object of
            the keys :func:`faces_list` names for the face).

    Returns:
        ``{"face", "version", "payload", "loss_report"}`` or
        ``{"error": ...}`` when the arguments are incomplete, the face
        refuses the document or a binding, or the installed pain001 has
        no faces.
    """
    faces = _faces_api()
    if faces is None:
        return {"error": FACES_MISSING}
    options = options or {}
    xml = options.get("xml")
    face = options.get("face")
    if not isinstance(xml, str) or not isinstance(face, str) or not face:
        return {"error": "xml and face are required strings"}
    try:
        result = faces.project_face_text(
            xml,
            face,
            version=options.get("version") or None,
            bindings=options.get("bindings"),
        )
    except faces.FaceError as exc:
        return {"error": str(exc)}
    projection: dict[str, Any] = result.to_dict()
    return projection


def faces_list_command(ls: LanguageServer, *args: Any) -> dict[str, Any]:
    """``workspace/executeCommand`` glue for :func:`faces_list`.

    Args:
        ls: The language server (unused; pygls passes it first).
        *args: The command arguments (none are read).

    Returns:
        The :func:`faces_list` payload.
    """
    return faces_list()


def faces_project_command(ls: LanguageServer, *args: Any) -> dict[str, Any]:
    """``workspace/executeCommand`` glue for :func:`faces_project`.

    Args:
        ls: The language server (unused; pygls passes it first).
        *args: The command arguments; the first is the request dict.

    Returns:
        The :func:`faces_project` payload.
    """
    return faces_project(command_options(args))
