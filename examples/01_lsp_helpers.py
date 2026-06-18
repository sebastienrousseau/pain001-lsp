#!/usr/bin/env python3
"""Example: the LSP server's editor-feature helpers.

Usage:
    pip install pain001-lsp     # requires Python 3.10+
    python examples/lsp_helpers.py

The pain001 language server (launched as `pain001-lsp` over stdio) powers
editor features for payment-data JSON files. Its logic lives in pure
helpers that you can call directly — exactly what the server runs on each
edit.
"""

import json

from pain001_lsp.server import (
    completion_items,
    compute_diagnostics,
    hover_text,
)

# --- Diagnostics: a valid record vs. common mistakes -----------------------
valid_doc = json.dumps(
    [
        {
            "id": "MSG-0001",
            "date": "2026-01-15T10:30:00",
            "nb_of_txs": 1,
            "ctrl_sum": 100.00,
            "initiator_name": "Acme Embedded Finance Ltd",
            "payment_information_id": "PMT-INFO-0001",
            "payment_method": "TRF",
            "batch_booking": False,
            "service_level_code": "SEPA",
            "requested_execution_date": "2026-01-20",
            "debtor_name": "Acme Embedded Finance Ltd",
            "debtor_account_IBAN": "DE89370400440532013000",
            "debtor_agent_BIC": "DEUTDEFFXXX",
            "charge_bearer": "SLEV",
            "payment_id": "PAY-0001",
            "payment_amount": 100.00,
            "currency": "EUR",
            "creditor_agent_BIC": "NWBKGB2LXXX",
            "creditor_name": "National Westminster Bank",
            "creditor_account_IBAN": "GB29NWBK60161331926819",
            "remittance_information": "Invoice 0001",
        }
    ]
)
print("valid document diagnostics:", compute_diagnostics(valid_doc))

missing = json.dumps([{"id": "ONLY-ID"}])
print(
    "missing-fields diagnostics:",
    len(compute_diagnostics(missing)),
    "issue(s)",
)

bad_identifier = json.dumps([{"debtor_account_IBAN": "INVALID"}])
identifier_issues = compute_diagnostics(bad_identifier)
print(
    f"bad-identifier diagnostics: {len(identifier_issues)} issue(s)"
)

print("malformed JSON diagnostics:", compute_diagnostics("{not json"))

# --- Completion and hover --------------------------------------------------
items = completion_items()
print(f"completion items:          {len(items)} (e.g. {items[0]['label']})")
print("hover debtor_account_IBAN:", hover_text("debtor_account_IBAN"))
print("hover unknown field:      ", hover_text("nope"))
