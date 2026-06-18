# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.52] - 2026-06-18

### Added

- Initial release of `pain001-lsp`, a [pygls](https://github.com/openlawlibrary/pygls)-based
  Language Server Protocol (LSP) server for authoring pain001 payment-data
  JSON files (Python 3.10+)
- A `pain001-lsp` console entry point that starts the language server over
  stdio for editor LSP clients
- **Diagnostics** - schema validation of each record against a message
  type's input JSON Schema (missing required fields, types, patterns) plus
  IBAN / BIC validation of identifier fields
- **Completion** - every input field (with its schema description) and the
  full list of supported pain message types
- **Hover** - schema descriptions for the field under the cursor
- **Code actions** - multi-record "Add missing required fields"
  quick-fix backed by `missing_required_fields(...)` and
  `build_insert_text(...)`; uses the cursor's line to pick the target
  record (falls back to the first one) and inserts JSON placeholder
  lines (`""` for strings, `0` for numbers, `false` for booleans)
  before that record's closing brace.
- **Workspace configuration** - editors override the default message
  type either at startup (`initializationOptions: {"messageType": ...}`)
  or **live** via `workspace/didChangeConfiguration` (accepting either a
  nested `{"pain001": {"messageType": ...}}` payload or a flat
  `{"messageType": ...}` payload).
- Pure, importable helper functions (`compute_diagnostics`,
  `completion_items`, `hover_text`, `missing_required_fields`,
  `build_insert_text`) backed by the `pain001` public API, so editor
  behaviour matches the CLI, REST API, and MCP server
- Three runnable examples (`examples/01_lsp_helpers.py`,
  `examples/02_quick_fix.py`, `examples/03_configure_message_type.py`)
- Part of the **pain001 suite** alongside the core `pain001` library and
  the `pain001-mcp` Model Context Protocol server
- Versioning aligned with `pain001` and `pain001-mcp`: the three packages
  in the suite ship under matching release numbers
- **Quality gates pinned at 100%** from the initial release:
  - `pytest --cov=pain001_lsp --cov-branch --cov-fail-under=100`
    (68 tests exercising every line, branch, and LSP handler in
    `pain001_lsp/server.py`, including the multi-record code action,
    workspace configuration paths, brace-walker fall-through, and an
    end-to-end stdio handshake against a real subprocess)
  - `interrogate --fail-under=100` for module and function docstring
    coverage
  - Every example script is also exercised by pytest so breakage is
    caught at the test-suite level
- **Quality workflows** - `ci.yml` enforces ruff, mypy, the 100% pytest
  coverage gate, the 100% docstring gate, and the example scripts on
  Python 3.10/3.11/3.12; `security.yml` runs bandit + pip-audit;
  `codeql.yml` runs GitHub's CodeQL Python analysis weekly.
- **Security policy** (`SECURITY.md`) describing the (small) threat
  model: stdio-only, bounded configuration, no caller-supplied
  filesystem paths.
- `scripts/verify_versions.py` - pre-release script asserting
  `__version__`, `pyproject.toml`, and `CHANGELOG.md` agree.

[0.0.52]: https://github.com/sebastienrousseau/pain001-lsp/releases/tag/v0.0.52
