#!/usr/bin/env python3
"""Example: switch the LSP server's default message type at runtime.

Usage:
    pip install pain001-lsp     # requires Python 3.10+
    python examples/03_configure_message_type.py

Editors override the default ``pain.001.001.09`` schema by passing
``initializationOptions: {"messageType": "pain.001.001.11"}`` when they
spawn the language server. This example simulates that override locally
and re-checks a record against each schema to highlight differences.
"""

import json

from lsprotocol import types as lsp

from pain001_lsp.server import compute_diagnostics, on_initialize, server

record = [
    {
        "id": "MSG-0001",
        "date": "2026-01-15T10:30:00",
        "nb_of_txs": 1,
        "ctrl_sum": 100.0,
        "debtor_account_IBAN": "DE89370400440532013000",
    }
]
text = json.dumps(record)

print(
    "diagnostics under default pain.001.001.09:",
    len(compute_diagnostics(text)),
)

# Simulate the LSP ``initialize`` request the editor would send.
on_initialize(
    server,
    lsp.InitializeParams(
        capabilities=lsp.ClientCapabilities(),
        initialization_options={"messageType": "pain.001.001.11"},
    ),
)

print(
    "diagnostics under override pain.001.001.11:",
    len(compute_diagnostics(text, "pain.001.001.11")),
)
