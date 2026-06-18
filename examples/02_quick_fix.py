#!/usr/bin/env python3
"""Example: render the quick-fix snippet for missing required fields.

Usage:
    pip install pain001-lsp     # requires Python 3.10+
    python examples/02_quick_fix.py

Shows what the LSP server's "Add missing required fields" code action
would insert into an editor buffer for an incomplete record.
"""

import json

from pain001_lsp.server import build_insert_text, missing_required_fields

incomplete_record = {
    "id": "MSG-0001",
    "date": "2026-01-15T10:30:00",
    "debtor_account_IBAN": "DE89370400440532013000",
}

missing = missing_required_fields(incomplete_record)
print(f"missing required fields ({len(missing)}):", missing)

snippet = build_insert_text(missing)
print("\nquick-fix snippet that the LSP code action would insert:\n")
print(json.dumps(incomplete_record, indent=2)[:-2] + snippet + "\n}")
