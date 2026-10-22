<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Scope comparison

The comparison that matters for this server is with the two things it
replaces when someone edits payment-data records: a JSON Schema alone (in
any schema-aware editor), and calling the `pain001` library from a script
after saving. No competitor ranking or comparative performance claim is
made.

| Capability | **pain001-lsp** | A JSON Schema alone | `pain001` library from a script |
| :--- | :---: | :---: | :---: |
| Feedback while typing | Yes | Yes | No, on each run |
| Required fields, types, patterns, lengths | Yes | Yes | Yes (`jsonschema` with the bundled schema) |
| IBAN check digits and BIC structure | Yes | No | Yes (`pain001.validation`) |
| Same schemas and validators as the CLI, REST API and MCP server | Yes | No | Yes |
| Quick fix that inserts missing required fields | Yes | No | No |
| Message type switched without a restart | Yes | Depends on the editor | Not applicable |
| CSV payment data | Yes, through the core's CSV engine | No | Yes |

Why the middle column says no: the bundled schema gives
`debtor_account_IBAN` a pattern (`^[A-Z]{2}[0-9]{2}[A-Z0-9]+$`) and a
length, but JSON Schema has no keyword that computes the ISO 13616 mod-97
check digits, so `DE00370400440532013000` passes the schema while
`pain001.validation.validate_iban` rejects it ("IBAN checksum validation
failed"). This server sends every IBAN and BIC field through that
validator.

Every row for pain001-lsp is exercised by the test suite
(`tests/test_lsp_server.py`, `tests/test_diagnostic_shapes.py`) and by the
runnable scripts in [`examples/`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/examples/README.md).
