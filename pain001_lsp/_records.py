# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Find the top-level records of a payment-data JSON document in its text.

``json`` gives values but not offsets, so diagnostics, the quick fix and
the outline locate each top-level record object by walking the raw text
for braces outside strings: the line each record opens on, the position
of its closing brace, and the record a cursor sits in. The walk is a
heuristic that tolerates half-typed documents.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from lsprotocol import types as lsp


def _normalise_records(parsed: Any) -> list[dict[str, Any]]:
    """Coerce parsed JSON into a list of record dicts.

    A single dict is treated as one record; a list is returned as-is.
    """
    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        return parsed
    return []


# A whole string (to its closing quote, or to the end of the text when it
# never closes, with a backslash escaping any next character, newlines
# included), or one brace outside a string.
_STRING_OR_BRACE = re.compile(r'"[^"\\]*(?:\\.[^"\\]*)*"?|[{}]', re.DOTALL)


def _braces(text: str) -> Iterator[tuple[str, int, int]]:
    """Yield ``(brace, line, character)`` for each brace outside a string.

    The one walk behind the record helpers below. Strings are skipped
    whole, so a brace inside one is not structure; lines count every
    newline before the brace, in a string or not. The scan and the
    newline counts run in C, and each newline is counted once, so the
    walk stays linear in the length of the text.
    """
    line = 0
    line_start = 0
    scanned = 0
    for match in _STRING_OR_BRACE.finditer(text):
        token = match.group()
        if token not in ("{", "}"):
            continue
        at = match.start()
        newlines = text.count("\n", scanned, at)
        if newlines:
            line += newlines
            line_start = text.rfind("\n", scanned, at) + 1
        scanned = at
        yield token, line, at - line_start


def _record_line_offsets(text: str) -> list[int]:
    """Best-effort mapping of record index -> line number.

    Uses the position of each top-level ``{`` opening brace. This is a
    heuristic (stdlib ``json`` does not expose offsets), but it lets
    diagnostics point at roughly the right record. Falls back to line 0
    when a record cannot be located.
    """
    offsets: list[int] = []
    depth = 0
    for brace, line, _ in _braces(text):
        if brace == "}":
            depth = max(0, depth - 1)
            continue
        if depth == 0:
            offsets.append(line)
        depth += 1
    return offsets


def _line_mapper(text: str) -> Any:
    """Return a function mapping a record index to its line (default 0)."""
    line_offsets = _record_line_offsets(text)

    def line_for(row: int) -> int:
        """Map a record index to a line number (falls back to 0)."""
        if 0 <= row < len(line_offsets):
            return line_offsets[row]
        return 0

    return line_for


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
    depth = 0
    positions: list[lsp.Position] = []
    for brace, line, char in _braces(text):
        if brace == "{":
            depth += 1
            continue
        if depth == 1:
            positions.append(lsp.Position(line=line, character=char))
        depth = max(0, depth - 1)
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
