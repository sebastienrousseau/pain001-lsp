<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# AGENTS.md

Invariants for AI-assisted contributions to `pain001-lsp`. Read this before changing anything.

Everything here applies equally to humans and automated agents. It is addressed to agents because agents can make breaking changes across multiple files before anyone notices.

## What this repository is

`pain001-lsp` is the Language Server of the pain001 suite: diagnostics, completion, hover, the missing-fields quick fix, formatting and document symbols for the JSON payment-data records that drive ISO 20022 `pain.001` generation, plus the example-corpus commands. It holds no validation rules of its own: records are checked against the core's bundled JSON Schemas, identifiers with `pain001.validation`, and CSV documents with the core's CSV engine, so the editor reports what the CLI, REST API and MCP server would. Its core value is that feedback arrives while someone types, and never disagrees with the core.

## 1. Core Invariants

1. **Versioning**: releases stay on the `0.0.x` line and increment strictly by `0.0.1`. Version work happens on `feat/v<next-version>` only. `v0.1.0` follows `v0.0.999`.
2. **Suite lockstep**: every member ships the core's version, and the core releases first. `scripts/check_suite_consistency.py` is the family's shared copy (the same file in pain001-mcp); change it in every member or not at all. The `pain001` floor in `pyproject.toml` and `requirements/runtime.in` is the release version.
3. **Single source of truth**: `pain001_lsp/__init__.py` must agree with `pyproject.toml`, the dated `CHANGELOG.md` heading, `CITATION.cff`, the README's latest-release line and the VS Code extension's `package.json`, lockfile and changelog (checked by `scripts/verify_versions.py`).
4. **The core decides**: do not reimplement a schema, identifier or CSV rule here; fix it in the core.
5. **Output is the contract**: a change to the diagnostics, completion items, code actions, symbols or edits the server returns for the same document, or to the plain-dict shapes of the helpers in `pain001_lsp.server`, is breaking even when no signature moves.
6. **Every keystroke re-parses the document**: work per change stays linear in its length (`tests/test_benchmarks.py` guards the scaling), and nothing the editor can type may raise out of a handler (`fuzz/fuzz_documents.py`).
7. **Stdout is the transport**: never print to stdout from the server.
8. **Dual licensing**: Apache-2.0 OR MIT.

## 2. Before You Claim To Be Done

```console
make check
```

It runs ruff, black, mypy `--strict`, bandit, the complexity gate, the version-source check, pytest (100% line and branch coverage), interrogate (100% docstrings) and the examples; CI also runs `pip-audit`, mutation testing (85% floor), Atheris, CodeQL and Scorecard. Every function stays within cyclomatic 10, cognitive 15, Halstead difficulty 30 and 60 lines, every file within 500 lines; existing offenders are in `complexity-baseline.json`, which may only shrink.

## 3. Hygiene First

Before any feature, fix or release work: open Dependabot PRs and alerts, code-scanning and secret-scanning alerts, open issues, `pip-audit`, and a red CI on `main` are cleared first. A dependency with an advisory is floored in `pyproject.toml` (and the `requirements/*.in` it appears in) so no affected version resolves.

## 4. Leave Alone

- `tests/test_suite_conformance.py` is a vendored, checksummed copy shared across the suite; it is excluded from black for that reason.
- `poetry.lock` and `requirements/*.txt` are generated (`poetry lock`, and the `uv pip compile` command in each file's header); never hand-edit them.
- `.github/demo.gif` is rendered from `.github/demo.tape` by `make demo`; never edit it by hand.
