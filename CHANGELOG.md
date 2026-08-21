# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.61] - 2026-08-20

Suite release with `pain001` 0.0.61. No change in this package; the
improvement comes from the core.

### Performance

- **Diagnostics are 3-6x faster**, because `pain001` 0.0.61 fixed a
  quadratic in `pain001.lsp.diagnostics`. Each cell's character span was
  computed by re-splitting the line and summing the lengths of every
  preceding cell, once per cell — and eagerly, before knowing whether
  there was anything to report, so a clean document paid the whole cost
  to produce no diagnostics. That is the common case in an editor, on
  every keystroke.

  | rows | before | after |
  |---|---|---|
  | 500 | 43.4ms | **7.6ms** (5.7x) |
  | 2000 | 102.0ms | **32.1ms** (3.2x) |

  Diagnostics output is unchanged. This package's benchmark had recorded
  the pre-fix behaviour as "sublinear (~2.4x)", which was the quadratic
  per-row cost swamping the row count rather than a fixed overhead; the
  ratio is now 4.23x for 4x the rows, which is what linear looks like.
  The benchmark's documentation is corrected accordingly.

## [0.0.60] - 2026-08-20

Lockstep release with `pain001` 0.0.60. No functional change in this
package.

`pain001-lsp` is a lockstep member of the suite: its version tracks the
core so an editor integration can pair `pain001-lsp==X` with
`pain001==X` without consulting a table. `pain001.suite` records which
members follow that rule, and the core enforces it daily.

The `pain001>=0.0.55` floor is deliberately unchanged, which is worth
stating because the core's 0.0.60 does contain a pygls 1.x -> 2.x
migration and this package requires `pygls>=2.1,<3`. That migration is
confined to `pain001.lsp.server`, the core's own language-server entry
point. This package does not import it — it imports
`pain001.lsp.diagnostics`, which has no pygls dependency at all, plus
`pain001.validation` and `pain001.constants`. `pain001.lsp.__init__`
re-exports only from `diagnostics`, so importing the package does not
pull the migrated module in either. Checked rather than assumed, because
a floor that is too low here would surface as an import error in a
user's editor rather than at install time.

## [0.0.59] - 2026-08-20

Rejoins lockstep with `pain001`. This package sat at 0.0.54 while the
core reached 0.0.59 — five releases of silent drift, which is what
`pain001`'s suite-consistency check now reports rather than leaving a
user to notice.

The version jumps 0.0.54 -> 0.0.59 with no intervening releases. The
numbers in between were never published for this package; they exist
so that a user reading `pain001==0.0.59` and `pain001-lsp==0.0.59` can
trust the two belong together, which is the point of lockstep
versioning.

### Changed

- Migrated to `pygls` 2.x (#13).
- Dependency updates: `mypy` 2.3.0, `ruff` 0.16.2, and the grouped
  GitHub Actions bump (#9, #10, #12).
- Dependabot config repaired — an invalid key meant github-actions
  updates were never grouped (#8).

## [0.0.54] - 2026-07-18

### Changed

- Require `pain001 >= 0.0.55` to pick up the upstream security fix
  shipped in that release (security-fix propagation across the pain001
  suite). No LSP-surface behaviour changes.

## [0.0.53] - 2026-06-19

### Added

Two new editor features that surface previously-missing IDE
ergonomics for pain.001 payment-data JSON files:

- `textDocument/formatting` - pretty-print the document as a
  two-space-indented JSON array with a trailing newline. The handler
  re-serialises via `json.dumps(parsed, indent=2)`, leaves malformed
  JSON untouched (diagnostics already flag the syntax error), and
  returns no edits when the document is already formatted (so the
  editor's "format on save" stays idempotent).
- `textDocument/documentSymbol` - return one `DocumentSymbol` per
  top-level record so editors can populate the outline pane, jump
  to a specific payment, and code-fold individual records. Each
  symbol uses the record's `id` field as its name (falling back to
  `<record N>`) and `payment_id` as its detail; the range spans the
  record's opening `{` through its closing `}`.

### Changed

- Pinned to `pain001 >= 0.0.53` so the new public-API symbols
  (`sanitize_to_charset`, the SEPA B2B profile) are available.
- Mypy: added an `ignore_missing_imports` override for the
  `jsonschema.*` module so `poetry run mypy pain001_lsp` is clean
  out of the box (no `types-jsonschema` install needed).

### Quality gates

- pytest: **81 tests**, 100% line + branch coverage (was 79, +2 new
  feature handlers exercised by 13 new tests).
- interrogate: 100% docstring coverage.
- ruff + mypy all clean.

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
