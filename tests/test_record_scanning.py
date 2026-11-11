# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Characterise the record walkers and the server module's surface.

``_record_line_offsets`` and ``_record_close_positions`` walk the raw
text for top-level braces outside strings; diagnostics, the quick fix
and the outline all place themselves with them. These cases pin their
exact output on well-formed, nested, escaped, CRLF and half-typed
documents, and the names ``pain001_lsp.server`` exposes, so the walkers
and the module layout can be restructured without changing either.
"""

from __future__ import annotations

import pytest
from lsprotocol import types as lsp

import pain001_lsp.server as lsp_server

# (text, record start lines, record close (line, character) positions)
CASES = [
    ("", [], []),
    ("[]", [], []),
    ("{}", [0], [(0, 1)]),
    ("[{}]", [0], [(0, 2)]),
    ('[{"a": 1}, {"b": 2}]', [0, 0], [(0, 8), (0, 18)]),
    (
        '[\n  {"a": "x\\"y", "b": "line\\nbreak"},\n  {}\n]',
        [1, 2],
        [(1, 34), (2, 3)],
    ),
    (
        '[\n  {"a": {"b": {"c": 1}}},\n  {"d": [1, {"e": 2}]}\n]',
        [1, 2],
        [(1, 23), (2, 21)],
    ),
    ('[\n  {"a": "}{"},\n  {"b": "\\\\"}\n]', [1, 2], [(1, 12), (2, 12)]),
    ('[\r\n  {"a": 1},\r\n  {"b": 2}\r\n]', [1, 2], [(1, 9), (2, 9)]),
    ('}}[{"a": 1}]', [0], [(0, 10)]),
    ('[{"a": 1}}}, {"b": 2}]', [0, 0], [(0, 8), (0, 20)]),
    ('[{"a": "unterminated}\n, {"b": 2}]', [0], []),
    ('\\{"a": 1}', [0], [(0, 8)]),
    ('{"a": "first\nsecond"}\n{"b": 1}', [0, 2], [(1, 7), (2, 7)]),
    ('[{"a": 1},\n\n\n  {"b": "\\u007b"}]', [0, 3], [(0, 8), (3, 16)]),
    ("[{", [0], []),
    ('[{"a": [}]', [0], [(0, 8)]),
]


@pytest.mark.parametrize(("text", "starts", "closes"), CASES)
def test_record_walkers(text, starts, closes):
    """Start lines and close positions match, case by case."""
    assert lsp_server._record_line_offsets(text) == starts
    positions = lsp_server._record_close_positions(text)
    assert [(p.line, p.character) for p in positions] == closes
    first = lsp_server._record_close_position(text)
    assert first == (positions[0] if positions else None)


@pytest.mark.parametrize(
    ("position", "two_records", "no_records"),
    [
        (None, 0, 0),
        ((0, 0), 0, 0),
        ((1, 0), 0, 0),
        ((2, 5), 1, 0),
        ((9, 0), 1, 0),
    ],
)
def test_record_index_at_position(position, two_records, no_records):
    """The record under a position is the last one starting at or above."""
    cursor = None if position is None else lsp.Position(*position)
    text = '[\n  {"a": 1},\n  {"b": 2}\n]'
    assert lsp_server._record_index_at_position(text, cursor) == two_records
    assert lsp_server._record_index_at_position("[]", cursor) == no_records


SURFACE = [
    "CORPUS_GET_COMMAND",
    "CORPUS_LIST_COMMAND",
    "DEFAULT_MESSAGE_TYPE",
    "_CORPUS_MISSING",
    "_IDENTIFIER_FIELDS",
    "_PLACEHOLDERS",
    "_SEVERITY",
    "_corpus_api",
    "_current_message_type",
    "_identifier_diagnostics",
    "_identifier_valid",
    "_line_mapper",
    "_load_schema",
    "_normalise_records",
    "_record_close_position",
    "_record_close_positions",
    "_record_index_at_position",
    "_record_line_offsets",
    "_schema_diagnostics",
    "_to_lsp_diagnostics",
    "_validate_and_publish",
    "build_insert_text",
    "code_action",
    "completion",
    "completion_items",
    "compute_diagnostics",
    "compute_diagnostics_csv",
    "corpus_get",
    "corpus_get_command",
    "corpus_list",
    "corpus_list_command",
    "did_change",
    "did_open",
    "document_symbol",
    "formatting",
    "hover",
    "hover_text",
    "main",
    "missing_required_fields",
    "on_did_change_configuration",
    "on_initialize",
    "server",
]


@pytest.mark.parametrize("name", SURFACE)
def test_server_module_surface(name):
    """Every helper, handler and constant stays importable from server."""
    assert hasattr(lsp_server, name)
