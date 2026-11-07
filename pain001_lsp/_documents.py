# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Decide which documents the server diagnoses, and with which engine.

An editor sends the server every JSON document it opens, not only payment
records: the VS Code extension selected every JSON file, so package.json
and tsconfig.json were told "'id' is a required property". Diagnostics are
published only for a document shaped like payment records; any other is
published with none, which also clears what an earlier version left.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any

from pain001_lsp._parsing import PARSE_ERRORS

#: A quoted key followed by a colon: the keys of text that does not parse.
_KEY = re.compile(r'"(\w+)"\s*:')


def is_csv_uri(uri: str) -> bool:
    """Return whether ``uri`` should be linted as a CSV (vs. JSON)."""
    return uri.lower().endswith(".csv")


def is_payment_document(
    text: str,
    message_type: str,
    load_schema: Callable[[str], dict[str, Any]],
) -> bool:
    """Return whether ``text`` is shaped like pain001 payment records.

    It is when it is a JSON array (of records, however incomplete), or an
    object with at least one field of ``message_type``'s schema as a key.
    Text that does not parse yet counts when it opens an array or quotes
    one of those fields as a key, so a payment file keeps its syntax error
    while being typed. With no schema for ``message_type`` only an array
    counts, and :func:`compute_diagnostics` reports the missing schema.
    """
    try:
        known = set(load_schema(message_type).get("properties", {}))
    except ValueError:
        known = set()
    try:
        parsed = json.loads(text)
    except PARSE_ERRORS:
        if text.lstrip().startswith("["):
            return True
        return any(m.group(1) in known for m in _KEY.finditer(text))
    if isinstance(parsed, list):
        return True
    return isinstance(parsed, dict) and not known.isdisjoint(parsed)
