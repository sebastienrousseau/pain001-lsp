<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

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
   |   |   |   |   (also: formatting, document_symbol, workspace/executeCommand
   |   |   |   |    for the corpus and faces commands)
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
| **Server** | `pain001_lsp/server.py` | pygls `LanguageServer` instance, feature handlers, the corpus commands, plus the pure helpers |
| **Document routing** | `pain001_lsp/_documents.py` | Which documents get diagnostics, and from which engine (JSON or CSV) |
| **Parse errors** | `pain001_lsp/_parsing.py` | Turns whatever `json.loads` raises on editor text into one diagnostic |
| **CSV** | `pain001_lsp/_csv.py` | Wraps the core's CSV diagnostic engine into the server's plain-dict diagnostics |
| **Faces** | `pain001_lsp/_faces.py` | The `pain001.faces.list` and `pain001.faces.project` commands |
| **Names** | `pain001_lsp/_names.py` | Human-readable names of the message types offered in completion |
| **Command arguments** | `pain001_lsp/_commands.py` | Reads the arguments of a `workspace/executeCommand` request as one dict |
| **Entry point** | `pain001_lsp.server:main` (console script: `pain001-lsp`) | Launches the server over stdio |
| **Version** | `pain001_lsp/__init__.py` | Single source of truth (`__version__`); the LSP reads it for the protocol handshake |
| **Tests** | `tests/` | In-process and end-to-end (subprocess over stdio) regressions; layout in [`DEVELOPMENT.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/DEVELOPMENT.md) |
| **Examples** | `examples/` | One runnable script per usage shape (helpers, quick fix, configuration, corpus and faces commands) |
| **Release helpers** | `scripts/verify_versions.py`, `scripts/release_notes.py` | Every version source agrees; the release page is written from `releases/vX.Y.Z.md` |

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
- **Formatting** - whole-document two-space JSON as one edit.
- **Document symbols** - one symbol per top-level record.
- **Commands** - `pain001.corpus.list` and `pain001.corpus.get` (the
  core's example corpus), `pain001.faces.list` and
  `pain001.faces.project` (another standard's shape of a pain.001
  document, with a loss report).
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
- `corpus_list(options)` and `corpus_get(options)`
- `pain001_lsp._faces.faces_list()` and `faces_project(options)`

Every helper is independently testable; the LSP handlers below them are
thin glue.

## Key design decisions

- **Delegation, not duplication.** Every helper is a thin wrapper over
  the `pain001` public API (schemas, validators, the CSV diagnostic
  engine). New behaviour generally means a new helper that wires up an
  existing pain001 surface.
- **pygls 2.x, the core's range.** `pygls >=2.1,<3` is the range the
  core's `lsp` extra declares, so both install in one environment.
- **Handlers registered by explicit calls**, not decorators, so mutation
  testing reaches them ([ADR 0003](https://github.com/sebastienrousseau/pain001-lsp/blob/main/docs/adr/0003-register-handlers-explicitly.md)).
- **URI-suffix dispatch.** `.csv` URIs run the CSV engine; everything
  else runs the JSON engine. No file content sniffing.
- **Coverage enforced at 100%** line+branch and docstring; only the
  defensive "no schema bundled" guards (unreachable since every valid
  message type ships a schema in pain001) are `# pragma: no cover`.

## Extension points

- **Add a diagnostic rule:** extend `compute_diagnostics()` (for JSON
  records) or add to the upstream
  `pain001.lsp.diagnostics.diagnostics_for_csv()` (for CSV cells).
- **Add a code action:** extend `code_action()` to return another
  `lsp.CodeAction` with a `WorkspaceEdit`.
- **Add a command:** write a pure helper returning a plain dict and a
  thin `*_command` wrapper, then register it with `server.command(...)`
  beside the others at the end of `server.py`.
- **Surface a new pain001 helper:** once it lands in
  `pain001.constants` / `pain001.validation` / `pain001.lsp.diagnostics`,
  expose it through a new pure helper here.

## Where to look first

- Runnable examples: [`examples/`](https://github.com/sebastienrousseau/pain001-lsp/tree/main/examples/)
- Development and CI gates: [`DEVELOPMENT.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/DEVELOPMENT.md)
- Roadmap: [`ROADMAP.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/ROADMAP.md)
- Release process: [`RELEASING.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/RELEASING.md)
- Parent library: [`pain001`](https://github.com/sebastienrousseau/pain001)
