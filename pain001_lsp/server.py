# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator
from lsprotocol import types as lsp
from pain001.constants import SCHEMAS_DIR, valid_xml_types
from pain001.lsp.diagnostics import Severity, diagnostics_for_csv
from pain001.validation import validate_bic, validate_iban
from pygls.server import LanguageServer

from pain001_lsp import __version__

DEFAULT_MESSAGE_TYPE = "pain.001.001.09"

# Flat-record fields whose values are financial identifiers, mapped to the
# identifier kind understood by the pain001 validators.
_IDENTIFIER_FIELDS = {
    "debtor_account_IBAN": "iban",
    "creditor_account_IBAN": "iban",
    "charge_account_IBAN": "iban",
    "debtor_agent_BIC": "bic",
    "creditor_agent_BIC": "bic",
    "forwarding_agent_BIC": "bic",
}

_HUMAN_NAMES = {
    "pain.001.001.03": "Customer Credit Transfer Initiation V03",
    "pain.001.001.04": "Customer Credit Transfer Initiation V04",
    "pain.001.001.05": "Customer Credit Transfer Initiation V05",
    "pain.001.001.06": "Customer Credit Transfer Initiation V06",
    "pain.001.001.07": "Customer Credit Transfer Initiation V07",
    "pain.001.001.08": "Customer Credit Transfer Initiation V08",
    "pain.001.001.09": "Customer Credit Transfer Initiation V09",
    "pain.001.001.10": "Customer Credit Transfer Initiation V10",
    "pain.001.001.11": "Customer Credit Transfer Initiation V11",
    "pain.001.001.12": "Customer Credit Transfer Initiation V12",
    "pain.008.001.02": "Customer Direct Debit Initiation V02",
}

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
def _load_schema(message_type: str) -> dict[str, Any]:
    """Load the bundled JSON schema for ``message_type``.

    Raises ``ValueError`` if the message type is unsupported or no schema
    file is bundled (for example, ``pain.001.001.12`` and
    ``pain.008.001.02`` are listed but only ship XML templates).
    """
    if message_type not in valid_xml_types:
        raise ValueError(f"Invalid XML message type: {message_type}")
    path = Path(SCHEMAS_DIR) / f"{message_type}.schema.json"
    if (
        not path.is_file()
    ):  # pragma: no cover - all bundled types ship a schema
        raise ValueError(f"No JSON Schema bundled for {message_type}")
    with path.open("r", encoding="utf-8") as fh:
        loaded: dict[str, Any] = json.load(fh)
        return loaded


def _normalise_records(parsed: Any) -> list[dict[str, Any]]:
    """Coerce parsed JSON into a list of record dicts.

    A single dict is treated as one record; a list is returned as-is.
    """
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return parsed
    return []


def _record_line_offsets(text: str) -> list[int]:
    """Best-effort mapping of record index -> line number.

    Uses the position of each top-level ``{`` opening brace. This is a
    heuristic (stdlib ``json`` does not expose offsets), but it lets
    diagnostics point at roughly the right record. Falls back to line 0
    when a record cannot be located.
    """
    offsets: list[int] = []
    depth = 0
    in_string = False
    escaped = False
    line = 0
    for ch in text:
        if escaped:
            escaped = False
        elif ch == "\\" and in_string:
            escaped = True
        elif ch == '"':
            in_string = not in_string
        elif not in_string:
            if ch == "\n":
                line += 1
                continue
            if ch == "{":
                if depth == 0:
                    offsets.append(line)
                depth += 1
            elif ch == "}":
                depth = max(0, depth - 1)
        if ch == "\n":
            line += 1
    return offsets


def _identifier_valid(kind: str, value: str) -> bool:
    """Return whether ``value`` is a valid IBAN or BIC."""
    if kind == "iban":
        ok, _ = validate_iban(value, strict=False)
    elif kind == "bic":
        ok, _ = validate_bic(value, strict=False)
    else:
        return True
    return bool(ok)


def compute_diagnostics(
    text: str, message_type: str = DEFAULT_MESSAGE_TYPE
) -> list[dict]:
    """Compute diagnostics for a pain.001 payment-data JSON document.

    Parses ``text`` as JSON (a list of record dicts, or a single dict
    treated as one record). On a JSON syntax error, returns a single
    diagnostic at the offending position. For valid JSON, runs schema
    validation against the bundled JSON Schema and additionally checks any
    present identifier fields with the IBAN / BIC validators.

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
    except json.JSONDecodeError as exc:
        return [
            {
                "line": max(0, exc.lineno - 1),
                "character": max(0, exc.colno - 1),
                "severity": "error",
                "message": f"Invalid JSON: {exc.msg}",
            }
        ]

    records = _normalise_records(parsed)
    if not records:
        return [
            {
                "line": 0,
                "character": 0,
                "severity": "error",
                "message": (
                    "Expected a JSON array of record objects "
                    "(or a single record object)."
                ),
            }
        ]

    try:
        schema = _load_schema(message_type)
    except ValueError as exc:
        return [
            {
                "line": 0,
                "character": 0,
                "severity": "error",
                "message": str(exc),
            }
        ]

    line_offsets = _record_line_offsets(text)

    def line_for(row: int) -> int:
        """Map a record index to a line number (falls back to 0)."""
        if 0 <= row < len(line_offsets):
            return line_offsets[row]
        return 0

    diagnostics: list[dict] = []

    validator = Draft7Validator(schema)
    for row, record in enumerate(records):
        if not isinstance(record, dict):
            diagnostics.append(
                {
                    "line": line_for(row),
                    "character": 0,
                    "severity": "error",
                    "message": "Expected a record object (got non-object).",
                }
            )
            continue
        for err in sorted(
            validator.iter_errors(record), key=lambda e: list(e.path)
        ):
            path = ".".join(str(p) for p in err.path)
            prefix = f"{path}: " if path else ""
            diagnostics.append(
                {
                    "line": line_for(row),
                    "character": 0,
                    "severity": "error",
                    "message": f"{prefix}{err.message}",
                }
            )

    # Identifier validation (IBAN / BIC) for any present values.
    for row, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        for field, kind in _IDENTIFIER_FIELDS.items():
            value = record.get(field)
            if not value or not isinstance(value, str):
                continue
            if not _identifier_valid(kind, value):
                diagnostics.append(
                    {
                        "line": line_for(row),
                        "character": 0,
                        "severity": "warning",
                        "message": (
                            f"{field}: {value!r} is not a valid "
                            f"{kind.upper()}."
                        ),
                    }
                )

    return diagnostics


_CSV_SEVERITY_TO_STR = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.INFORMATION: "information",
    Severity.HINT: "hint",
}


def compute_diagnostics_csv(
    text: str, message_type: str = DEFAULT_MESSAGE_TYPE
) -> list[dict]:
    """Compute diagnostics for a pain.001 payment-data CSV document.

    Wraps :func:`pain001.lsp.diagnostics.diagnostics_for_csv` and returns
    the same plain-dict shape as :func:`compute_diagnostics` so the LSP
    handlers can route by URI suffix without caring which engine ran.

    Args:
        text: The raw CSV document text.
        message_type: The pain message type to validate against.

    Returns:
        A list of plain dicts shaped like the JSON-mode output, with
        ``col_start`` / ``col_end`` keys retained so editors can paint
        per-cell ranges.
    """
    diagnostics: list[dict] = []
    for diag in diagnostics_for_csv(text, message_type):
        diagnostics.append(
            {
                "line": diag.line,
                "character": diag.col_start,
                "col_start": diag.col_start,
                "col_end": diag.col_end,
                "severity": _CSV_SEVERITY_TO_STR.get(diag.severity, "error"),
                "message": diag.message,
                "code": diag.code,
            }
        )
    return diagnostics


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
                "detail": _HUMAN_NAMES.get(mt, mt),
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


_SEVERITY = {
    "error": lsp.DiagnosticSeverity.Error,
    "warning": lsp.DiagnosticSeverity.Warning,
    "information": lsp.DiagnosticSeverity.Information,
    "hint": lsp.DiagnosticSeverity.Hint,
}


def _to_lsp_diagnostics(raw: list[dict]) -> list[lsp.Diagnostic]:
    """Map plain diagnostic dicts to ``lsprotocol`` ``Diagnostic`` objects."""
    diagnostics: list[lsp.Diagnostic] = []
    for item in raw:
        line = item["line"]
        col_start = item.get("col_start", item["character"])
        col_end = item.get("col_end", col_start)
        diagnostics.append(
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=line, character=col_start),
                    end=lsp.Position(line=line, character=col_end),
                ),
                message=item["message"],
                severity=_SEVERITY.get(
                    item["severity"], lsp.DiagnosticSeverity.Error
                ),
                source="pain001-lsp",
                code=item.get("code"),
            )
        )
    return diagnostics


def _is_csv_uri(uri: str) -> bool:
    """Return whether ``uri`` should be linted as a CSV (vs. JSON)."""
    return uri.lower().endswith(".csv")


def _validate_and_publish(ls: LanguageServer, uri: str) -> None:
    """Compute diagnostics for ``uri`` and publish them to the client.

    Routes to :func:`compute_diagnostics_csv` for ``.csv`` files and to
    :func:`compute_diagnostics` (the JSON engine) for everything else.
    """
    document = ls.workspace.get_text_document(uri)
    message_type = _current_message_type()
    if _is_csv_uri(uri):
        raw = compute_diagnostics_csv(document.source, message_type)
    else:
        raw = compute_diagnostics(document.source, message_type)
    ls.publish_diagnostics(uri, _to_lsp_diagnostics(raw))


@server.feature(lsp.INITIALIZE)
def on_initialize(ls: LanguageServer, params: lsp.InitializeParams) -> None:
    """Honour ``initializationOptions.messageType`` when the client sets it."""
    global _message_type
    options = getattr(params, "initialization_options", None) or {}
    message_type = None
    if isinstance(options, dict):
        message_type = options.get("messageType")
    if message_type and message_type in valid_xml_types:
        _message_type = message_type


@server.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(
    ls: LanguageServer, params: lsp.DidOpenTextDocumentParams
) -> None:
    """Publish diagnostics when a document is opened."""
    _validate_and_publish(ls, params.text_document.uri)


@server.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def did_change(
    ls: LanguageServer, params: lsp.DidChangeTextDocumentParams
) -> None:
    """Publish diagnostics when a document changes."""
    _validate_and_publish(ls, params.text_document.uri)


@server.feature(lsp.TEXT_DOCUMENT_COMPLETION)
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


@server.feature(lsp.TEXT_DOCUMENT_HOVER)
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


def _record_close_position(text: str) -> lsp.Position | None:
    """Locate the closing ``}`` of the first top-level record object.

    The quick-fix inserts placeholders just before this position, which
    keeps the document syntactically valid after the edit.
    """
    positions = _record_close_positions(text)
    return positions[0] if positions else None


def _record_close_positions(text: str) -> list[lsp.Position]:
    """Locate the closing ``}`` of every top-level record object.

    Used by the multi-record code action so the quick-fix can be offered
    on the record under the cursor, not just the first one.
    """
    line = 0
    char = 0
    depth = 0
    in_string = False
    escaped = False
    positions: list[lsp.Position] = []
    record_close: lsp.Position | None = None
    for ch in text:
        if escaped:
            escaped = False
        elif ch == "\\" and in_string:
            escaped = True
        elif ch == '"':
            in_string = not in_string
        elif not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                if depth == 1:
                    record_close = lsp.Position(line=line, character=char)
                depth = max(0, depth - 1)
                if record_close is not None and depth == 0:
                    positions.append(record_close)
                    record_close = None
        if ch == "\n":
            line += 1
            char = 0
        else:
            char += 1
    return positions


def _record_index_at_position(text: str, position: lsp.Position | None) -> int:
    """Return the top-level record index covering ``position``.

    Used by the multi-record code action to know which record the user
    is editing. Falls back to ``0`` when the position is missing or no
    record covers it.
    """
    if position is None:
        return 0
    line_offsets = _record_line_offsets(text)
    if not line_offsets:
        return 0
    target = position.line
    chosen = 0
    for idx, offset in enumerate(line_offsets):
        if offset <= target:
            chosen = idx
        else:
            break
    return chosen


@server.feature(lsp.TEXT_DOCUMENT_CODE_ACTION)
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
    except json.JSONDecodeError:
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


@server.feature(lsp.WORKSPACE_DID_CHANGE_CONFIGURATION)
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


@server.feature(lsp.TEXT_DOCUMENT_FORMATTING)
def formatting(
    ls: LanguageServer, params: lsp.DocumentFormattingParams
) -> list[lsp.TextEdit]:
    """Pretty-print the document as a JSON array of records.

    Re-serialises with two-space indentation and a trailing newline so
    diffs against the previously-saved version stay minimal. Malformed
    JSON is left untouched (no edits returned) - the diagnostics
    handler already surfaces the syntax error.

    Args:
        ls: The active language server instance.
        params: The LSP formatting parameters identifying the document.

    Returns:
        A single ``TextEdit`` replacing the document with its formatted
        text, or an empty list when the document is malformed or
        already formatted.
    """
    document = ls.workspace.get_text_document(params.text_document.uri)
    try:
        parsed = json.loads(document.source)
    except json.JSONDecodeError:
        return []
    formatted = json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"
    if formatted == document.source:
        return []
    lines = document.source.splitlines(keepends=True)
    end_line = max(0, len(lines) - 1)
    end_char = len(lines[-1]) if lines else 0
    return [
        lsp.TextEdit(
            range=lsp.Range(
                start=lsp.Position(line=0, character=0),
                end=lsp.Position(line=end_line, character=end_char),
            ),
            new_text=formatted,
        )
    ]


@server.feature(lsp.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
def document_symbol(
    ls: LanguageServer, params: lsp.DocumentSymbolParams
) -> list[lsp.DocumentSymbol]:
    """Return an outline of every top-level record in the document.

    Each record becomes one ``DocumentSymbol`` whose name is the
    record's ``id`` field (or ``<record N>`` when absent) and whose
    detail is the ``payment_id`` field (or empty when absent). The
    range covers the record's opening ``{`` through its closing ``}``
    so editors can jump-to / collapse on the record under the cursor.

    Args:
        ls: The active language server instance.
        params: The LSP document-symbol parameters.

    Returns:
        One ``DocumentSymbol`` per top-level record, or an empty list
        when the document is malformed or has no records.
    """
    document = ls.workspace.get_text_document(params.text_document.uri)
    try:
        parsed = json.loads(document.source)
    except json.JSONDecodeError:
        return []
    records = _normalise_records(parsed)
    if not records:
        return []
    line_offsets = _record_line_offsets(document.source)
    close_positions = _record_close_positions(document.source)
    symbols: list[lsp.DocumentSymbol] = []
    for index, record in enumerate(records):
        if index >= len(line_offsets) or index >= len(close_positions):
            break
        start_line = line_offsets[index]
        close_position = close_positions[index]
        if isinstance(record, dict):
            name = str(record.get("id") or f"<record {index + 1}>")
            detail = str(record.get("payment_id") or "")
        else:
            name = f"<record {index + 1}>"
            detail = ""
        record_range = lsp.Range(
            start=lsp.Position(line=start_line, character=0),
            end=lsp.Position(
                line=close_position.line,
                character=close_position.character + 1,
            ),
        )
        symbols.append(
            lsp.DocumentSymbol(
                name=name,
                detail=detail,
                kind=lsp.SymbolKind.Object,
                range=record_range,
                selection_range=record_range,
            )
        )
    return symbols


def main() -> None:
    """Start the ``pain001-lsp`` language server over stdio."""
    server.start_io()


if __name__ == "__main__":
    main()
