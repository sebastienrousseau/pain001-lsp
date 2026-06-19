<!-- SPDX-License-Identifier: Apache-2.0 -->

# Pain001-LSP VS Code extension

A Language Server Protocol client that brings the full pain001-lsp
surface to VS Code for payment-data JSON files:

- **Diagnostics** - JSON schema + IBAN / BIC validation
- **Completion** - every input field plus the list of supported
  message types
- **Hover** - schema descriptions for any field
- **Code actions** - "Add missing required fields" quick-fix on the
  record under the cursor
- **Formatting** (`textDocument/formatting`) - two-space, ISO 20022
  Latin-clean pretty-printing
- **Outline** (`textDocument/documentSymbol`) - one entry per record,
  so the symbol pane and code-folding work per-record

The actual engine is the Python `pain001-lsp` server, so the same
checks back the editor, the CLI, and CI.

## Prerequisites

```bash
pip install pain001-lsp   # provides the `pain001-lsp` server on PATH
```

## Run from source

```bash
cd editors/vscode
npm install
npm run compile
# Then press F5 in VS Code to launch an Extension Development Host.
```

Open any pain.001 payment-data `.json` file; diagnostics appear
inline and in the Problems panel. The active message type is
controlled by the `pain001.messageType` setting; the server command
by `pain001.serverCommand`.

## Packaging / publishing

Building a `.vsix` and publishing to the Marketplace is an external,
credentialed step (`vsce package` / `vsce publish`) and is
intentionally left to a maintainer with publisher access - it is
not part of the Python package's automated build.
