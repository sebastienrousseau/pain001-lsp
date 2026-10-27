<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# pain001-lsp Roadmap

This roadmap tracks the next set of capabilities for the LSP companion
of the [pain001](https://github.com/sebastienrousseau/pain001) library.
The versions are **target** windows; releases ship when the gates pass,
not on a calendar.

## Where we are: v0.0.75

- Diagnostics (JSON Schema plus IBAN and BIC), completion, hover, the
  missing-fields quick fix on the record under the cursor, formatting,
  the per-record outline, CSV diagnostics through the core's engine,
  and the example-corpus commands.
- Live message-type switching through `initializationOptions` and
  `workspace/didChangeConfiguration`; all thirteen core message types.
- 100% line, branch and docstring coverage, mutation testing with an
  85% floor, Atheris fuzzing, per-function complexity ceilings against
  a shrinking baseline, hash-pinned CI installs.

## Next

- Targeted code actions per diagnostic (e.g. "remove invalid IBAN",
  "uppercase BIC", "regenerate `ctrl_sum` from `payment_amount`
  totals").
- Shrink the complexity baseline: `_record_close_positions`,
  `_record_line_offsets` and the length of `server.py`.

## After that

- `textDocument/codeLens` showing per-record validation status inline.
- `DiagnosticTag.Information` for purely informational hints (e.g. soft
  recommendations the schema doesn't enforce).

## Out of scope (handled elsewhere)

- **AI-agent surface** - see [`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp).
- **Bank submission / signing** - see the core
  [`pain001`](https://github.com/sebastienrousseau/pain001) library.
