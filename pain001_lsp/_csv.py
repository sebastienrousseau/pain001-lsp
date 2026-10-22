# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Lint a payment CSV document into the server's plain-dict diagnostics.

The core's :func:`pain001.lsp.diagnostics.diagnostics_for_csv` reads the
text with the ``csv`` module, which raises ``csv.Error`` on text it cannot
read: a bare carriage return inside an unquoted field, or, before Python
3.11, a NUL byte. Editor text can hold either, so that ends as one
diagnostic, never as an exception escaping a keystroke.
"""

from __future__ import annotations

import csv

from pain001.lsp.diagnostics import Severity, diagnostics_for_csv

from pain001_lsp._parsing import _diagnostic

_CSV_SEVERITY_TO_STR = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.INFORMATION: "information",
    Severity.HINT: "hint",
}


def csv_diagnostics(text: str, message_type: str) -> list[dict]:
    """Return the core's CSV diagnostics as plain dicts, or one read error."""
    try:
        found = diagnostics_for_csv(text, message_type)
    except csv.Error as exc:
        return [_diagnostic(0, f"Invalid CSV: {exc}")]
    return [
        {
            "line": diag.line,
            "character": diag.col_start,
            "col_start": diag.col_start,
            "col_end": diag.col_end,
            "severity": _CSV_SEVERITY_TO_STR.get(diag.severity, "error"),
            "message": diag.message,
            "code": diag.code,
        }
        for diag in found
    ]
