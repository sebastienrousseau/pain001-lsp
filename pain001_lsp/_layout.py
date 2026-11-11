# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Whole-document handlers: formatting and the record outline."""

from __future__ import annotations

import json

from lsprotocol import types as lsp
from pygls.lsp.server import LanguageServer

from pain001_lsp._parsing import PARSE_ERRORS
from pain001_lsp._records import (
    _normalise_records,
    _record_close_positions,
    _record_line_offsets,
)


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
        formatted = json.dumps(parsed, indent=2, ensure_ascii=False) + "\n"
    except PARSE_ERRORS:
        return []
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
    except PARSE_ERRORS:
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
