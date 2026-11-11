# Copyright (C) 2023-2026 Sebastien Rousseau.
# SPDX-License-Identifier: Apache-2.0 OR MIT

"""Language Server Protocol (LSP) server for pain001 payment-data files.

This server helps developers author **pain.001 payment-data JSON files** -
a JSON array of flat record objects (the same records that drive XML
generation). It provides four editor features, all backed by the pain001
public API so they behave identically to the CLI, REST API, and MCP server:

* **Diagnostics** - each record is validated against a message type's input
  JSON Schema, and any ``debtor_account_IBAN`` / ``creditor_account_IBAN`` /
  ``charge_account_IBAN`` / ``debtor_agent_BIC`` / ``creditor_agent_BIC`` /
  ``forwarding_agent_BIC`` values are additionally checked with the
  dedicated IBAN / BIC validators.
* **Completion** - every input field (with its description) plus the list
  of supported message types are offered as completion items.
* **Hover** - hovering a field name shows its schema description.
* **Code actions** - when the document is missing required fields, the
  server offers a single "Add missing required fields" quick-fix that
  inserts placeholder values for each missing field on the affected
  record.

The intended message type defaults to ``pain.001.001.09`` (Customer Credit
Transfer Initiation V09); the pure helpers accept a ``message_type``
argument so a different type can be configured. Editors can override the
default per-workspace by passing ``initializationOptions`` of the form
``{"messageType": "pain.001.001.11"}``.

Launching
---------
The package installs a ``pain001-lsp`` console entry point (declared in
``pyproject.toml`` as ``pain001_lsp.server:main``) which starts the server
over stdio::

    pain001-lsp

Editor wiring
-------------
Point your editor's LSP client at the ``pain001-lsp`` command for JSON
files. For Neovim (``nvim-lspconfig`` / the built-in ``vim.lsp.config`` API)
register a server whose ``cmd`` is ``{ "pain001-lsp" }`` and ``filetypes``
includes ``"json"``. VS Code clients spawn the same command over stdio.

The business logic lives in pure, testable helper functions
(:func:`compute_diagnostics`, :func:`completion_items`, :func:`hover_text`,
:func:`missing_required_fields`, :func:`build_insert_text`); the LSP
handlers below are thin glue that map those plain dicts to ``lsprotocol``
types.
"""

from __future__ import annotations

import json
from typing import Any

from lsprotocol import types as lsp
from pain001.constants import valid_xml_types
from pygls.lsp.server import LanguageServer

from pain001_lsp import __version__, _faces
from pain001_lsp._corpus import _CORPUS_MISSING as _CORPUS_MISSING
from pain001_lsp._corpus import (
    CORPUS_GET_COMMAND,
    CORPUS_LIST_COMMAND,
    corpus_get_command,
    corpus_list_command,
)
from pain001_lsp._corpus import _corpus_api as _corpus_api
from pain001_lsp._corpus import corpus_get as corpus_get
from pain001_lsp._corpus import corpus_list as corpus_list
from pain001_lsp._csv import compute_diagnostics_csv
from pain001_lsp._diagnostics import _IDENTIFIER_FIELDS as _IDENTIFIER_FIELDS
from pain001_lsp._diagnostics import _SEVERITY as _SEVERITY
from pain001_lsp._diagnostics import (
    _identifier_diagnostics,
    _schema_diagnostics,
    _to_lsp_diagnostics,
)
from pain001_lsp._diagnostics import _identifier_valid as _identifier_valid
from pain001_lsp._documents import is_csv_uri, is_payment_document
from pain001_lsp._layout import document_symbol, formatting
from pain001_lsp._names import HUMAN_NAMES
from pain001_lsp._parsing import (
    PARSE_ERRORS,
    _diagnostic,
    _parse_error_diagnostic,
)
from pain001_lsp._records import (
    _line_mapper,
    _normalise_records,
    _record_close_positions,
    _record_index_at_position,
)
from pain001_lsp._records import (
    _record_close_position as _record_close_position,
)
from pain001_lsp._records import _record_line_offsets as _record_line_offsets
from pain001_lsp._schema import DEFAULT_MESSAGE_TYPE, _load_schema

# Placeholders used by ``build_insert_text`` when offering a "fill in missing
# required fields" quick-fix. Values map to JSON Schema ``type`` keys.
_PLACEHOLDERS: dict[str, Any] = {
    "string": "",
    "integer": 0,
    "number": 0,
    "boolean": False,
    "array": [],
    "object": {},
}


# ---------------------------------------------------------------------------
# Pure helpers (no LSP/server I/O - directly unit-testable)
# ---------------------------------------------------------------------------
def compute_diagnostics(
    text: str, message_type: str = DEFAULT_MESSAGE_TYPE
) -> list[dict]:
    """Compute diagnostics for a pain.001 payment-data JSON document.

    Parses ``text`` as JSON (a list of record dicts, or a single dict
    treated as one record). When the text does not parse (a syntax error,
    an integer too long to convert, or nesting too deep), returns a single
    diagnostic, at the offending position when JSON reports one. For valid
    JSON, runs schema validation against the bundled JSON Schema and
    additionally checks any present identifier fields with the IBAN / BIC
    validators.

    Args:
        text: The raw document text.
        message_type: The pain message type to validate against.

    Returns:
        A list of plain dicts::

            {"line": int, "character": int,
             "severity": "error" | "warning", "message": str}
    """
    try:
        parsed = json.loads(text)
    except PARSE_ERRORS as exc:
        return [_parse_error_diagnostic(exc)]

    records = _normalise_records(parsed)
    if not records:
        return [
            _diagnostic(
                0,
                "Expected a JSON array of record objects "
                "(or a single record object).",
            )
        ]

    try:
        schema = _load_schema(message_type)
    except ValueError as exc:
        return [_diagnostic(0, str(exc))]

    line_for = _line_mapper(text)
    return _schema_diagnostics(
        records, schema, line_for
    ) + _identifier_diagnostics(records, line_for)


def completion_items(
    message_type: str = DEFAULT_MESSAGE_TYPE,
) -> list[dict]:
    """Return completion items for a pain.001 payment-data document.

    Offers every input field for ``message_type`` (with its schema
    description as the detail) plus every supported message type.

    Args:
        message_type: The pain message type whose fields are offered.

    Returns:
        A list of ``{"label": str, "detail": str, "kind": "field"}`` dicts.
    """
    items: list[dict] = []
    try:
        schema = _load_schema(message_type)
    except ValueError:  # pragma: no cover - all valid types ship a schema
        schema = {}
    properties = schema.get("properties", {})
    for field, spec in properties.items():
        items.append(
            {
                "label": field,
                "detail": (spec or {}).get("description", "") or "",
                "kind": "field",
            }
        )
    for mt in valid_xml_types:
        items.append(
            {
                "label": mt,
                "detail": HUMAN_NAMES.get(mt, mt),
                "kind": "field",
            }
        )
    return items


def hover_text(
    field: str, message_type: str = DEFAULT_MESSAGE_TYPE
) -> str | None:
    """Return the schema description for ``field``, or ``None``.

    Args:
        field: An input field name.
        message_type: The pain message type whose schema is consulted.

    Returns:
        The field's ``description`` string, or ``None`` if the field is
        unknown or has no description.
    """
    try:
        schema = _load_schema(message_type)
    except ValueError:  # pragma: no cover - all valid types ship a schema
        return None
    properties = schema.get("properties", {})
    spec = properties.get(field)
    if not spec:
        return None
    description = spec.get("description")
    return description or None


def missing_required_fields(
    record: dict[str, Any], message_type: str = DEFAULT_MESSAGE_TYPE
) -> list[str]:
    """List required field names absent from ``record``.

    Returns an empty list if no schema is bundled for ``message_type`` or
    the record already satisfies the required list (so callers can keep a
    single short-circuit check on ``not missing_required_fields(...)``).

    Args:
        record: A flat payment record.
        message_type: The pain message type whose required list applies.

    Returns:
        A list of field names from the schema's ``required`` array that
        are missing from ``record``.
    """
    try:
        schema = _load_schema(message_type)
    except ValueError:  # pragma: no cover - all valid types ship a schema
        return []
    required: list[str] = list(schema.get("required", []))
    return [field for field in required if field not in record]


def build_insert_text(
    missing: list[str], message_type: str = DEFAULT_MESSAGE_TYPE
) -> str:
    """Render JSON-Object fragments for the ``missing`` required fields.

    The returned string is a comma-prefixed sequence of
    ``"field": placeholder`` lines that can be inserted **just before** a
    record object's closing ``}``. Placeholders are type-appropriate
    defaults (``""`` for strings, ``0`` for numbers, ``false`` for
    booleans, ``[]`` for arrays, ``{}`` for objects).

    Args:
        missing: Required field names to insert.
        message_type: The pain message type whose schema supplies types.

    Returns:
        A multi-line snippet, or the empty string if no fields are missing
        or the schema is not bundled.
    """
    if not missing:
        return ""
    try:
        schema = _load_schema(message_type)
    except ValueError:  # pragma: no cover - all valid types ship a schema
        return ""
    properties = schema.get("properties", {})
    parts: list[str] = []
    for field in missing:
        spec = properties.get(field) or {}
        field_type = spec.get("type", "string")
        placeholder = _PLACEHOLDERS.get(field_type, "")
        parts.append(f'  "{field}": {json.dumps(placeholder)}')
    return ",\n" + ",\n".join(parts)


# ---------------------------------------------------------------------------
# LSP glue (thin - maps plain dicts to lsprotocol types)
# ---------------------------------------------------------------------------
server = LanguageServer("pain001-lsp", f"v{__version__}")

# Editor-provided override for the default message type. Populated on
# ``initialize`` if the client sends ``initializationOptions``.
_message_type: str = DEFAULT_MESSAGE_TYPE


def _current_message_type() -> str:
    """Return the currently configured message type."""
    return _message_type


def _validate_and_publish(ls: LanguageServer, uri: str) -> None:
    """Compute diagnostics for ``uri`` and publish them to the client.

    Routes to :func:`compute_diagnostics_csv` for ``.csv`` files and to
    :func:`compute_diagnostics` (the JSON engine) for payment records;
    any other JSON document is published with no diagnostics.
    """
    document = ls.workspace.get_text_document(uri)
    message_type = _current_message_type()
    if is_csv_uri(uri):
        raw = compute_diagnostics_csv(document.source, message_type)
    elif is_payment_document(document.source, message_type, _load_schema):
        raw = compute_diagnostics(document.source, message_type)
    else:
        raw = []
    ls.text_document_publish_diagnostics(
        lsp.PublishDiagnosticsParams(
            uri=uri, diagnostics=_to_lsp_diagnostics(raw)
        )
    )


def on_initialize(ls: LanguageServer, params: lsp.InitializeParams) -> None:
    """Honour ``initializationOptions.messageType`` when the client sets it."""
    global _message_type
    options = getattr(params, "initialization_options", None) or {}
    message_type = None
    if isinstance(options, dict):
        message_type = options.get("messageType")
    if message_type and message_type in valid_xml_types:
        _message_type = message_type


def did_open(
    ls: LanguageServer, params: lsp.DidOpenTextDocumentParams
) -> None:
    """Publish diagnostics when a document is opened."""
    _validate_and_publish(ls, params.text_document.uri)


def did_change(
    ls: LanguageServer, params: lsp.DidChangeTextDocumentParams
) -> None:
    """Publish diagnostics when a document changes."""
    _validate_and_publish(ls, params.text_document.uri)


def completion(
    ls: LanguageServer, params: lsp.CompletionParams
) -> lsp.CompletionList:
    """Offer input-field and message-type completions."""
    items = [
        lsp.CompletionItem(
            label=item["label"],
            detail=item["detail"],
            kind=lsp.CompletionItemKind.Field,
        )
        for item in completion_items(_current_message_type())
    ]
    return lsp.CompletionList(is_incomplete=False, items=items)


def hover(ls: LanguageServer, params: lsp.HoverParams) -> lsp.Hover | None:
    """Show the schema description for the field under the cursor."""
    document = ls.workspace.get_text_document(params.text_document.uri)
    word = document.word_at_position(params.position)
    if not word:
        return None
    text = hover_text(word, _current_message_type())
    if text is None:
        return None
    return lsp.Hover(contents=text)


def code_action(
    ls: LanguageServer, params: lsp.CodeActionParams
) -> list[lsp.CodeAction]:
    """Offer a "fill in missing required fields" quick-fix.

    Active when the record under the cursor (or the first record, if
    the params don't specify one) is missing schema-required fields.
    Inserts JSON ``"field": placeholder`` lines just before that
    record's closing ``}``.
    """
    document = ls.workspace.get_text_document(params.text_document.uri)
    try:
        parsed = json.loads(document.source)
    except PARSE_ERRORS:
        return []
    records = _normalise_records(parsed)
    if not records:
        return []
    cursor = getattr(getattr(params, "range", None), "start", None)
    index = _record_index_at_position(document.source, cursor)
    if index >= len(records) or not isinstance(records[index], dict):
        return []
    message_type = _current_message_type()
    missing = missing_required_fields(records[index], message_type)
    if not missing:
        return []
    close_positions = _record_close_positions(document.source)
    if index >= len(close_positions):
        return []
    close_position = close_positions[index]
    snippet = build_insert_text(missing, message_type)
    if not snippet:
        return []
    edit = lsp.TextEdit(
        range=lsp.Range(start=close_position, end=close_position),
        new_text=snippet,
    )
    return [
        lsp.CodeAction(
            title=(
                f"Add {len(missing)} missing required field(s) "
                f"for {message_type}"
            ),
            kind=lsp.CodeActionKind.QuickFix,
            edit=lsp.WorkspaceEdit(changes={params.text_document.uri: [edit]}),
        )
    ]


def on_did_change_configuration(
    ls: LanguageServer, params: lsp.DidChangeConfigurationParams
) -> None:
    """Live-switch the active message type when the client reconfigures.

    Editors that wire `workspace/didChangeConfiguration` can push
    ``{"pain001": {"messageType": "pain.001.001.11"}}`` (or a top-level
    ``{"messageType": ...}``) and have every subsequent diagnostic /
    completion / hover / code-action call use the new schema, with no
    restart required.
    """
    global _message_type
    settings = getattr(params, "settings", None)
    if not isinstance(settings, dict):
        return
    candidate: str | None = None
    section = settings.get("pain001")
    if isinstance(section, dict):
        candidate = section.get("messageType")
    if candidate is None:
        candidate = settings.get("messageType")
    if candidate and candidate in valid_xml_types:
        _message_type = candidate


# Handlers are registered here, in definition order, rather than with
# decorators on each function: mutmut 3 never mutates a decorated function,
# so the decorator form left every handler outside mutation testing. pygls
# registers the same function, name and signature either way.
server.feature(lsp.INITIALIZE)(on_initialize)
server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)(did_open)
server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)(did_change)
server.feature(lsp.TEXT_DOCUMENT_COMPLETION)(completion)
server.feature(lsp.TEXT_DOCUMENT_HOVER)(hover)
server.feature(lsp.TEXT_DOCUMENT_CODE_ACTION)(code_action)
server.feature(lsp.WORKSPACE_DID_CHANGE_CONFIGURATION)(
    on_did_change_configuration
)
server.feature(lsp.TEXT_DOCUMENT_FORMATTING)(formatting)
server.feature(lsp.TEXT_DOCUMENT_DOCUMENT_SYMBOL)(document_symbol)
server.command(CORPUS_LIST_COMMAND)(corpus_list_command)
server.command(CORPUS_GET_COMMAND)(corpus_get_command)
server.command(_faces.FACES_LIST_COMMAND)(_faces.faces_list_command)
server.command(_faces.FACES_PROJECT_COMMAND)(_faces.faces_project_command)


def main() -> None:
    """Start the ``pain001-lsp`` language server over stdio."""
    server.start_io()


if __name__ == "__main__":
    main()
