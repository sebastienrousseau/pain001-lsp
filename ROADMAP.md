# pain001-lsp Roadmap

This roadmap tracks the next set of capabilities for the LSP companion
of the [pain001](https://github.com/sebastienrousseau/pain001) library.
The versions are **target** windows; releases ship when the gates pass,
not on a calendar.

## v0.0.52 - Initial release (current)

- Four LSP features: diagnostics, completion, hover, code actions.
- Workspace-level message-type override via `initializationOptions`.
- 100% line+branch coverage gate, 100% docstring coverage gate, signed
  conventional commits.
- Three runnable examples covering helpers, quick-fix snippets, and
  runtime configuration.

## v0.0.53 - Live configuration + formatting

- `workspace/didChangeConfiguration` - live-switch the active message
  type without restarting the server.
- `textDocument/formatting` - pretty-print payment-data JSON in place,
  reusing the existing JSON syntax check.
- Multi-record quick-fix - extend the "Add missing required fields"
  code action to act on the record under the cursor, not just the first
  one.

## v0.1.0 - Authoring-grade UX

- Targeted code actions per diagnostic (e.g. "remove invalid IBAN",
  "uppercase BIC", "regenerate `ctrl_sum` from `payment_amount` totals").
- `textDocument/documentSymbol` so editors can outline each record by
  `id`.
- `textDocument/codeLens` showing per-record validation status inline.
- `DiagnosticTag.Information` for purely informational hints (e.g. soft
  recommendations the schema doesn't enforce).

## Out of scope (handled elsewhere)

- **AI-agent surface** - see [`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp).
- **Bank submission / signing** - see the core
  [`pain001`](https://github.com/sebastienrousseau/pain001) library.
