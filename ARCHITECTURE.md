<!-- SPDX-License-Identifier: Apache-2.0 -->

# pain001-lsp Architecture

A map of the codebase for new contributors and maintainers. The goal is
that anyone can navigate, extend, and reason about pain001-lsp without
prior context.

## The pipeline

```
Editor LSP client (Neovim, VS Code, Helix, ...)
        |  stdio (LSP JSON-RPC)
        v
pain001_lsp/server.py
   |   |   |   |
   |   |   |   `-- code_action     -> multi-record "Add missing required fields" quick-fix
   |   |   `------ hover            -> hover_text()           -> pain001 schema descriptions
   |   `---------- completion       -> completion_items()     -> pain001 schema + supported types
   `-------------- did_open/change  -> _validate_and_publish() -> compute_diagnostics() (JSON)
                                                              \-> compute_diagnostics_csv() (CSV via
                                                                  pain001.lsp.diagnostics)
```

Helpers are pure (no LSP / pygls dependency); the LSP feature handlers
are thin glue that maps the helpers' plain-dict diagnostics into
`lsprotocol` types.

## Module map

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Server** | `pain001_lsp/server.py` | pygls `LanguageServer` instance, feature handlers, plus the pure helpers |
| **Entry point** | `pain001_lsp.server:main` (console script: `pain001-lsp`) | Launches the server over stdio |
| **Version** | `pain001_lsp/__init__.py` | Single source of truth (`__version__`); the LSP reads it for the protocol handshake |
| **Tests** | `tests/test_lsp_server.py`, `tests/test_stdio_e2e.py` | In-process + end-to-end-via-subprocess regressions |
| **Examples** | `examples/` | One runnable script per usage shape (helpers, quick-fix, configuration) |
| **Release helpers** | `scripts/verify_versions.py` | Asserts `__version__`, `pyproject.toml`, and `CHANGELOG.md` agree |

## Editor features

The current LSP surface:

- **Diagnostics (JSON mode)** - schema validation + IBAN/BIC checks for
  the identifier fields on every record.
- **Diagnostics (CSV mode)** - wraps
  `pain001.lsp.diagnostics.diagnostics_for_csv` (per-cell column ranges,
  ISO 20022 charset, required columns).
- **Completion** - every input field for the message type + every
  supported pain.001 / pain.008 message type.
- **Hover** - schema description for the field under the cursor.
- **Code actions** - multi-record "Add missing required fields"
  quick-fix.
- **Workspace configuration** - `initializationOptions.messageType`
  override at startup; `workspace/didChangeConfiguration` for live
  switching.

## Pure helpers (the public Python surface)

- `compute_diagnostics(text, message_type=...)`
- `compute_diagnostics_csv(text, message_type=...)`
- `completion_items(message_type=...)`
- `hover_text(field, message_type=...)`
- `missing_required_fields(record, message_type=...)`
- `build_insert_text(missing, message_type=...)`

Every helper is independently testable; the LSP handlers below them are
thin glue.

## Key design decisions

- **Delegation, not duplication.** Every helper is a thin wrapper over
  the `pain001` public API (schemas, validators, the CSV diagnostic
  engine). New behaviour generally means a new helper that wires up an
  existing pain001 surface.
- **Pygls 1.x for runtime parity.** Pinned to `pygls >=1.3,<2` so the
  standalone server can coexist with the in-tree `pain001[lsp]` server
  in the same environment.
- **URI-suffix dispatch.** `.csv` URIs run the CSV engine; everything
  else runs the JSON engine. No file content sniffing.
- **Coverage enforced at 100%** line+branch and docstring; only the
  defensive "no schema bundled" guards (unreachable since every valid
  message type ships a schema in pain001) are `# pragma: no cover`.

## Extension points

- **Add a diagnostic rule:** extend `compute_diagnostics()` (for JSON
  records) or add to the upstream
  `pain001.lsp.diagnostics.diagnostics_for_csv()` (for CSV cells).
- **Add a code action:** add an `@server.feature(lsp.TEXT_DOCUMENT_CODE_ACTION)`
  branch that returns a `lsp.CodeAction` with a `WorkspaceEdit`.
- **Surface a new pain001 helper:** once it lands in
  `pain001.constants` / `pain001.validation` / `pain001.lsp.diagnostics`,
  expose it through a new pure helper here.

## Where to look first

- Runnable examples: [`examples/`](examples/)
- Roadmap: [`ROADMAP.md`](ROADMAP.md)
- Release process: [`RELEASING.md`](RELEASING.md)
- Parent library: [`pain001`](https://github.com/sebastienrousseau/pain001)
