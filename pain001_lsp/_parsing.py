# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Turn a document that ``json.loads`` rejects into one diagnostic.

Every handler parses the whole document on each request, so whatever
``json.loads`` can raise on editor text has to end as a diagnostic or an
empty answer, never as an exception escaping a keystroke.
"""

from __future__ import annotations

import json

#: What ``json.loads`` raises on text it cannot turn into a value. A syntax
#: error is a ``json.JSONDecodeError`` (a ``ValueError``); an integer longer
#: than ``sys.get_int_max_str_digits()`` is a plain ``ValueError``; nesting
#: deeper than the interpreter's recursion limit is a ``RecursionError``.
PARSE_ERRORS = (ValueError, RecursionError)


def _diagnostic(
    line: int, message: str, severity: str = "error", character: int = 0
) -> dict:
    """Build one plain-dict diagnostic."""
    return {
        "line": line,
        "character": character,
        "severity": severity,
        "message": message,
    }


def _parse_error_diagnostic(exc: Exception) -> dict:
    """Describe why ``json.loads`` rejected the document."""
    if isinstance(exc, json.JSONDecodeError):
        return _diagnostic(
            max(0, exc.lineno - 1),
            f"Invalid JSON: {exc.msg}",
            character=max(0, exc.colno - 1),
        )
    if isinstance(exc, RecursionError):
        return _diagnostic(0, "Invalid JSON: nested too deeply to parse")
    return _diagnostic(0, f"Invalid JSON: {exc}")
