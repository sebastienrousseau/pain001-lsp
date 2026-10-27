<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

<p align="center">
  <img src="https://cloudcdn.pro/pain001/v1/logos/pain001.svg" alt="pain001-lsp logo" width="128" />
</p>

<h1 align="center">pain001-lsp</h1>

<p align="center">
  A Language Server that checks pain.001 payment-data records as you type them.
</p>

<p align="center">
  <a href="https://github.com/sebastienrousseau/pain001-lsp/actions"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/pain001-lsp/ci.yml?style=for-the-badge&logo=github" alt="Build" height="28" /></a>
  <a href="https://pypi.org/project/pain001-lsp/"><img src="https://img.shields.io/pypi/v/pain001-lsp?style=for-the-badge&color=fc8d62&logo=python" alt="Registry" height="28" /></a>
  <a href="https://sebastienrousseau.com/pain001-lsp/"><img src="https://img.shields.io/badge/docs-pain001--lsp-blue?style=for-the-badge&labelColor=555555&logo=readthedocs" alt="Docs" height="28" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/sebastienrousseau/pain001-lsp"><img src="https://img.shields.io/ossf-scorecard/github.com/sebastienrousseau/pain001-lsp?style=for-the-badge&label=OpenSSF%20Scorecard&logo=openssf" alt="OpenSSF Scorecard" height="28" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0%20OR%20MIT-blue.svg?style=for-the-badge" alt="License: Apache-2.0 OR MIT" height="28" /></a>
  <a href="https://github.com/sebastienrousseau/pain001-lsp/blob/main/docs/POLICIES.md"><img src="https://img.shields.io/badge/Python-3.11%2B-93450a.svg?style=for-the-badge&logo=python" alt="Python 3.11 or newer" height="28" /></a>
</p>

<p align="center">
  <img src=".github/demo.gif" alt="pain001-lsp demo: the diagnostics, completion and hover helpers the server runs on every edit, then the missing-fields quick fix, against sample payment records" width="100%" />
</p>

---

<!-- The manual (docs/readme.md) includes this file from here on. -->

## Contents

**Getting started**

- [Install](#install) — pip, pipx or uv, Docker, the VS Code extension
- [Requirements](#requirements) — toolchain floor, platforms
- [Quick Start](#quick-start) — point your editor at `pain001-lsp`, or call the helpers directly

**The pain001-lsp ecosystem**

- [The pain001-lsp ecosystem](#the-pain001-lsp-ecosystem) — the pain001 core library and its four companion packages

**Library reference**

- [Capabilities at a glance](#capabilities-at-a-glance) — the current surface by theme
- [Ecosystem comparison](#ecosystem-comparison) — short matrix; full table at [`docs/COMPARISON.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/docs/COMPARISON.md)
- [Benchmarks](#benchmarks) — headline numbers; full table at [`docs/BENCHMARKS.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/docs/BENCHMARKS.md)
- [Features](#features) — module-level capability list
- [Configuration](#configuration) — core options
- [Examples](#examples) — runnable example index

**Operational**

- [When not to use pain001-lsp](#when-not-to-use-pain001-lsp) — limitations
- [Development](#development) — make targets, fuzzing, CI
- [Security](#security) — guarantees and compliance
- [Documentation](#documentation) — all reference docs
- [Stability guarantees](#stability-guarantees) — SemVer axis, output stability, minimum toolchain discipline
- [License](#license)

---

## Install

### As a Python library

```sh
python -m pip install pain001-lsp
```

> **Latest release: v0.0.75**: the family's 0.0.75 release on the
> pain001 0.0.75 floor. Python 3.11 is now the minimum (3.10 reaches end
> of life in October 2026), and no requirements tree installs an advised
> filelock, virtualenv, dulwich, certifi or `@azure/msal-node`.
> [See what's new →][release]

The package installs a `pain001-lsp` console command and pulls in the core
[`pain001`][pain001] library, [`pygls`][pygls] and `jsonschema`. To keep the
command on your `PATH` without touching a project environment:

```sh
pipx install pain001-lsp
uv tool install pain001-lsp
```

Check the install:

```sh
python -c "import pain001_lsp; print(pain001_lsp.__version__)"
```

### As a container

```sh
docker pull ghcr.io/sebastienrousseau/pain001-lsp:latest
```

The image (linux/amd64 and linux/arm64) runs `pain001-lsp` over stdio as a
non-root user; an editor launches it with `docker run -i --rm
ghcr.io/sebastienrousseau/pain001-lsp`.

### As a VS Code extension

Every [release](https://github.com/sebastienrousseau/pain001-lsp/releases)
attaches `pain001-lsp-json-<version>.vsix`. In VS Code choose *Extensions*,
the `...` menu, *Install from VSIX...*. The extension starts the
`pain001-lsp` command, so install the Python package as well. Its source is
in [`editors/vscode/`](https://github.com/sebastienrousseau/pain001-lsp/tree/main/editors/vscode/).

---

## Requirements

- Python 3.11 or newer, tested in CI on 3.11, 3.12, 3.13 and 3.14 on
  Linux ([toolchain policy](https://github.com/sebastienrousseau/pain001-lsp/blob/main/docs/POLICIES.md)). The package is pure Python
  and runs wherever its dependencies do: macOS, Linux and Windows.
- `pain001` 0.0.74 or newer (below 1.0), `pygls` 2.1 or newer (below 3) and
  `jsonschema` 4.17 or newer (below 5), installed automatically.
- An editor with a Language Server Protocol client (Neovim, VS Code, Helix,
  Emacs, Sublime Text LSP and others).

---

## Quick Start

```lua
-- Neovim 0.11+, built-in LSP client
vim.lsp.config["pain001"] = {
  cmd = { "pain001-lsp" },
  filetypes = { "json" },
  root_markers = { ".git" },
  init_options = { messageType = "pain.001.001.09" },
}
vim.lsp.enable("pain001")
```

Open a JSON array of payment records. The server validates every record on
open and on each change, completes field names and message types, shows
schema descriptions on hover, offers a quick fix that inserts the record's
missing required fields, formats the document and outlines it by record.
`pain001-lsp` speaks LSP on stdin and stdout, so any editor that can spawn a
command over stdio can use it: register `pain001-lsp` as the command for
JSON files, with the same `initializationOptions`.

The same logic is importable, without an editor:

```python
import json

from pain001_lsp.server import compute_diagnostics, missing_required_fields

doc = json.dumps([{"id": "MSG-0001", "debtor_account_IBAN": "INVALID"}])
for diagnostic in compute_diagnostics(doc)[:2]:
    print(diagnostic["severity"], diagnostic["message"])
print(missing_required_fields({"id": "MSG-0001"})[:3])
```

---

## The pain001-lsp ecosystem

`pain001-lsp` is one of five packages built around the [`pain001`][pain001]
library for ISO 20022 customer credit transfer initiation (`pain.001`)
files. They release together at one version, the core first, and every
interface calls the core's validators and schemas, so the editor, the
command line, the REST API and an AI agent apply the same rules.

| Component | Purpose | Use case |
| :--- | :--- | :--- |
| [`pain001`](https://github.com/sebastienrousseau/pain001) | Core library, CLI and REST API: generate and validate ISO 20022 payment files from CSV, JSON and other data | You produce payment files in code, scripts or a service |
| [`pain001-lsp`](#install) | Language Server for the payment-data records that drive generation | You author or review those records in an editor: **this package** |
| [`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp) | Model Context Protocol server exposing the library as agent tools | You work with payment data from an AI assistant |
| [`pain001-loader-mt101`](https://github.com/sebastienrousseau/pain001-loader-mt101) | SWIFT MT101 requests for transfer to `pain.001` flat records | Your transfers still arrive as MT101 |
| [`pain001-loader-xlsx`](https://github.com/sebastienrousseau/pain001-loader-xlsx) | Excel `.xlsx` reader for flat-record payment data | Finance teams keep payments in a spreadsheet |

---

## Capabilities at a glance

| Area | Capability | Status |
| :--- | :--- | :--- |
| Diagnostics | Each record checked against the message type's input JSON Schema; IBAN and BIC fields checked with the core validators | Released |
| Diagnostics (CSV) | `.csv` documents checked by the core's CSV diagnostic engine, with per-cell ranges | Released |
| Completion | Every input field with its schema description, plus every supported message type by name | Released |
| Hover | The schema description of the field under the cursor | Released |
| Code actions | Quick fix inserting the missing required fields of the record under the cursor | Released |
| Outline | One document symbol per record, named by `id` | Released |
| Formatting | Whole-document pretty-print, 2-space indent, idempotent | Released |
| Example corpus | `pain001.corpus.list` and `pain001.corpus.get` commands | Released |
| Targeted fixes per diagnostic, code lenses | See [`ROADMAP.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/ROADMAP.md) | Planned |

---

## Ecosystem comparison

The alternatives to this server are a JSON Schema alone, in any
schema-aware editor, and calling the `pain001` library from a script after
saving.

| Project | Feedback while typing | IBAN check digits | Quick fix for missing fields |
| :--- | :---: | :---: | :---: |
| **pain001-lsp** | Yes | Yes | Yes |
| A JSON Schema alone | Yes | No | No |
| `pain001` library from a script | No | Yes | No |

See [`docs/COMPARISON.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/docs/COMPARISON.md) for the evidence and complete matrix.

---

## Benchmarks

Diagnostics run on every keystroke, so the number that matters is how large
a document stays interactive. Measured with `benches/bench_diagnostics.py`.

| Scenario | Result | Environment |
| :--- | ---: | :--- |
| Diagnostics, cost per record | 0.08 ms | recorded for 0.0.64 (2026-08-29) |
| Interactive budget (under 100 ms per change) | ~1,200 records | recorded for 0.0.64 (2026-08-29) |
| Malformed document | 0.01 ms | Apple A18 Pro, Python 3.12.15, load average above 30 (2026-10-21) |

See [`docs/BENCHMARKS.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/docs/BENCHMARKS.md) for methodology and full results.

---

## Features

For payment-data files: a JSON array of flat payment records, or a single
record object treated as one record. Documents whose URI ends in `.csv` go
to the core's CSV engine instead.

- **Diagnostics**: schema validation reports missing required fields, wrong
  types, and pattern or length violations. `debtor_account_IBAN`,
  `creditor_account_IBAN`, `charge_account_IBAN` and the `*_agent_BIC`
  fields are also checked as IBAN or BIC (warnings). A document that does
  not parse gets one error: at JSON's position for a syntax error, at the
  top for nesting too deep or an integer too long.
- **Completion**: every input field for the message type, with its schema
  description as the detail, plus every supported message type with its
  name (`pain.001.001.09`: Customer Credit Transfer Initiation V09).
- **Hover**: the schema `description` of the field under the cursor.
- **Code actions**: "Add missing required fields" on the record under the
  cursor, inserting type-appropriate placeholders (`""`, `0`, `false`, `[]`,
  `{}`) before its closing brace.
- **Document symbols**: one symbol per top-level record, named by its `id`
  (or `<record N>`), with `payment_id` as the detail.
- **Formatting**: two-space JSON with a trailing newline as one
  whole-document edit; no edit when already formatted or when the JSON does
  not parse.
- **Corpus commands**: `pain001.corpus.list` lists the validated example
  files the core ships (filter by `kind`, `country`, `version`);
  `pain001.corpus.get` returns one file's XML with its provenance.

The logic lives in pure helpers in `pain001_lsp.server`:
`compute_diagnostics`, `compute_diagnostics_csv`, `completion_items`,
`hover_text`, `missing_required_fields`, `build_insert_text`, `corpus_list`
and `corpus_get`. The LSP handlers map their plain dicts to `lsprotocol`
types. Each diagnostic is
`{"line": int, "character": int, "severity": "error" | "warning", "message": str}`.

---

## Configuration

| Setting | Where | Description |
| --- | --- | --- |
| `messageType` | `initializationOptions` | Message type to validate against at startup (default `pain.001.001.09`). |
| `pain001.messageType` (or `messageType`) | `workspace/didChangeConfiguration` | Switch the message type without a restart. |
| `pain001.serverCommand` | VS Code setting | Command that starts the server (default `pain001-lsp`). |
| `pain001.messageType` | VS Code setting | Message type, one of the thirteen the core supports. |

`pain001-lsp` takes no command-line options: it speaks LSP over stdio from
the first byte. A message type the core does not support is ignored, and
the previous one stays active.

---

## Examples

One runnable script per surface in [`examples/`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/examples/README.md), each
run in CI and by `make examples`:

| Example | Demonstrates |
| :--- | :--- |
| [`01_lsp_helpers.py`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/examples/01_lsp_helpers.py) | Diagnostics, completion and hover on sample records |
| [`02_quick_fix.py`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/examples/02_quick_fix.py) | The missing-fields quick fix and the snippet it inserts |
| [`03_configure_message_type.py`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/examples/03_configure_message_type.py) | Overriding the message type through `initializationOptions` |
| [`04_corpus_commands.py`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/examples/04_corpus_commands.py) | The example-corpus commands |

```sh
git clone https://github.com/sebastienrousseau/pain001-lsp.git && cd pain001-lsp
poetry install
poetry run python examples/01_lsp_helpers.py
```

---

## When not to use pain001-lsp

- **You have no LSP-capable editor.** Scripts and CI are better served by
  `pain001 validate` and the core's REST API.
- **You are authoring `pain.001` XML.** Completion, hover and the quick fix
  target the JSON records that drive generation, not XML; use an XSD-aware
  XML language server.
- **Your documents run to thousands of records.** Diagnostics re-validate
  the whole document on every change (see [Benchmarks](#benchmarks)), so
  very large files lag on each keystroke.
- **You want agent tools, not editor diagnostics.** Use
  [`pain001-mcp`](https://github.com/sebastienrousseau/pain001-mcp).

---

## Development

```bash
git clone https://github.com/sebastienrousseau/pain001-lsp.git && cd pain001-lsp
poetry install
make check         # lint, mypy, bandit, complexity, tests, docstrings, examples
make test          # pytest, 100% line and branch coverage enforced
make complexity    # per-function ceilings against complexity-baseline.json
make mutate        # mutation testing of the handlers, 85% floor
make demo          # re-render .github/demo.gif with VHS
```

CI installs from hash-pinned `requirements/*.txt` (compiled from
`requirements/*.in` with `uv pip compile --generate-hashes`, through
`scripts/ci-install.sh`) and runs the test matrix on Python 3.11 to 3.14,
ruff, black, mypy in strict mode, bandit, interrogate (100% docstrings), the
complexity ceilings, the version-source check, pip-audit over `poetry.lock`
and every requirements file, mutation testing, Atheris fuzzing, CodeQL and
OpenSSF Scorecard. See [`CONTRIBUTING.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/CONTRIBUTING.md) and
[`RELEASING.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/RELEASING.md).

---

## Security

The server reads only the document text the editor sends over stdio. It
opens no network socket, executes nothing from the document, takes no file
path from the client, and parses JSON with the standard library; a document
that does not parse yields one diagnostic, never an exception. The document
handlers are fuzzed with [Atheris][atheris] on every change and weekly (see
[`fuzz/`](https://github.com/sebastienrousseau/pain001-lsp/tree/main/fuzz/)). Actions are pinned by SHA, the container base image by
digest, every `pip` install is hash-pinned, workflow tokens are
least-privilege, and releases carry SLSA provenance, PEP 740 attestations,
cosign signatures and SPDX and CycloneDX SBOMs.

Report vulnerabilities according to [`SECURITY.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/SECURITY.md).

---

## Documentation

[User manual](https://sebastienrousseau.com/pain001-lsp/) ·
[API reference: the helpers](#features) ·
[Developer guide](https://github.com/sebastienrousseau/pain001-lsp/blob/main/CONTRIBUTING.md) ·
[Family map](#the-pain001-lsp-ecosystem) ·
[Architecture](https://github.com/sebastienrousseau/pain001-lsp/blob/main/ARCHITECTURE.md) · [Releasing](https://github.com/sebastienrousseau/pain001-lsp/blob/main/RELEASING.md) ·
[Changelog](https://github.com/sebastienrousseau/pain001-lsp/blob/main/CHANGELOG.md) · [Roadmap](https://github.com/sebastienrousseau/pain001-lsp/blob/main/ROADMAP.md) ·
[Security policy](https://github.com/sebastienrousseau/pain001-lsp/blob/main/SECURITY.md) · [Support](https://github.com/sebastienrousseau/pain001-lsp/blob/main/SUPPORT.md) ·
[What is pain.001?](https://pain001.com/pain-001/)

---

## Stability guarantees

The project is pre-1.0 and versions advance in `0.0.1` steps, in lockstep
with the rest of the pain001 suite. The breaking axis is what an editor
receives: the capabilities the server advertises, and the diagnostics,
completion items, code actions, symbols and edits it returns, including the
plain-dict shapes of the public helpers. A change to what the server
reports for the same document is breaking even when no Python signature
moves, and is called out in the [changelog](https://github.com/sebastienrousseau/pain001-lsp/blob/main/CHANGELOG.md). The Python floor
moves only as described in the [toolchain policy](https://github.com/sebastienrousseau/pain001-lsp/blob/main/docs/POLICIES.md).

---

## License

This project is dual-licensed under either:

* Apache License, Version 2.0 ([`LICENSE-APACHE`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
* MIT License ([`LICENSE-MIT`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/LICENSE-MIT) or <https://opensource.org/licenses/MIT>)

at your option. Any contribution submitted for inclusion is licensed the same
way, without additional terms. Dependencies keep their own licences. Built on
[pygls][pygls] and [lsprotocol](https://github.com/microsoft/lsprotocol).

[atheris]: https://github.com/google/atheris
[pain001]: https://github.com/sebastienrousseau/pain001
[pygls]: https://github.com/openlawlibrary/pygls
[release]: https://github.com/sebastienrousseau/pain001-lsp/releases/tag/v0.0.75
