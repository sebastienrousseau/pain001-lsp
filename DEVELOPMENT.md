<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Development

The single entry point for working on `pain001-lsp`: toolchain, how to
reproduce every CI gate locally, where tests live, and how a release
happens. [CONTRIBUTING.md](https://github.com/sebastienrousseau/pain001-lsp/blob/main/CONTRIBUTING.md)
covers the etiquette (DCO, commit format, review); this file covers the
mechanics.

## Toolchain

| Tool | Version | Where it is pinned |
| :--- | :--- | :--- |
| Python | 3.11 is the floor; CI runs 3.11 to 3.14 | `pyproject.toml` `python = ">=3.11,<4.0"`, the `ci.yml` matrix, [`docs/POLICIES.md`](https://github.com/sebastienrousseau/pain001-lsp/blob/main/docs/POLICIES.md) |
| Poetry | 2.x | `poetry.lock` is committed; `requirements/build.txt` pins Poetry for CI |
| Node.js | 22 | only for the VS Code extension (`editors/vscode/`) and `markdownlint-cli2` |
| Docker | any | only for the container image (`Dockerfile`) |

```bash
git clone https://github.com/sebastienrousseau/pain001-lsp
cd pain001-lsp
poetry install --all-extras
make check
```

`pre-commit install` (with [pre-commit](https://pre-commit.com) on your
`PATH`) runs the hygiene hooks, ruff, black, codespell and mypy on each
commit; `.pre-commit-config.yaml` pins every hook by exact release.

The [devcontainer](https://github.com/sebastienrousseau/pain001-lsp/blob/main/.devcontainer/devcontainer.json)
does the same in a Codespace or VS Code container: it installs Poetry
and pre-commit, installs the project and finishes by running
`make check`.

## Reproducing every CI gate

Each CI job maps onto a local command, so a red job can be reproduced
without reading YAML. `make check` runs every gate in the first block.

| Gate | Local command | CI workflow |
| :--- | :--- | :--- |
| Lint (ruff, black) | `make lint` | `ci.yml`, `pr.yml`, `nightly.yml` |
| Types (mypy `--strict`) | `make type-check` | `ci.yml`, `pr.yml` |
| Security lint (bandit) | `make security` | `security.yml` |
| Complexity ceilings (cyclomatic 10, cognitive 15, Halstead difficulty 30, 60 lines per function, 500 per file) against `complexity-baseline.json`, which may only shrink | `make complexity` | `ci.yml` |
| Version sources agree | `make versions` | `versions.yml` |
| Tests with the 100 % line and branch coverage floor | `make test` | `ci.yml` (matrix), `pr.yml` |
| Docstring coverage (interrogate, 100 %) | `make doc-coverage` | `ci.yml`, `pr.yml` |
| Examples run | `make examples` | `ci.yml` |
| Spelling (codespell) | `make spelling` | `docs-lint.yml` |
| Markdown style | `npx markdownlint-cli2@0.23.3 "**/*.md"` | `docs-lint.yml` |
| Locked dependency set | `poetry install && poetry run pytest -q` | `ci.yml` (`locked`) |
| Lockfile matches `pyproject.toml` | `poetry check --lock` | `ci.yml` (`lockfile`) |
| Benchmarks (kept running, not asserted) | `poetry run python benches/bench_diagnostics.py --quick` | `ci.yml` |
| Dependency advisories | `pip-audit` over the Poetry environment and each `requirements/*.txt` (commands in `security.yml`) | `security.yml` |
| Fuzzing (Atheris) | `python fuzz/fuzz_documents.py -max_total_time=60` after `pip install --require-hashes -r requirements/fuzz.txt` | `fuzz.yml` |
| Mutation testing (85 % floor) | `make mutate` | `mutation.yml` |
| Docs build | `cd docs && make html` after `pip install --require-hashes -r requirements/docs.txt` and `pip install --no-deps -e .` | `docs.yml` |
| VS Code extension | `cd editors/vscode && npm ci && npm run compile` | `vscode-extension.yml` |
| Container image | `docker build .` | `docker.yml` |
| Sign-off on every commit | `git commit -s` | `dco.yml` |

The coverage floor is 100 % line and branch, set once in
`[tool.coverage.report]` in `pyproject.toml`, so a plain `pytest`
enforces it too. `# pragma: no cover` is kept for the defensive guards
that no valid message type can reach (see
[ARCHITECTURE.md](https://github.com/sebastienrousseau/pain001-lsp/blob/main/ARCHITECTURE.md)).

## Test layout

```text
tests/
  test_lsp_server.py            the pure helpers and the in-process handlers
  test_stdio_e2e.py             the server as a subprocess over stdio
  test_diagnostic_shapes.py     positions and shapes of the diagnostics
  test_corpus_commands.py       the example-corpus workspace commands
  test_faces_commands.py        the faces workspace commands
  test_benchmarks.py            the linear-scaling guard
  test_fuzz_harness.py          the Atheris harness runs on fixed inputs
  test_vscode_extension.py      the extension offers what the server accepts
  test_readme.py                README shape, links and Python snippets
  test_check_*.py, test_verify_versions.py, test_release_notes.py
                                the release and CI helpers under scripts/
  test_workflow_pinning.py      every CI install is hash-pinned
  test_headers.py               SPDX headers
  test_suite_conformance.py     the family-wide rules; vendored, do not edit here
examples/                       numbered scripts; every one runs in CI
benches/                        the diagnostics benchmark
fuzz/                           Atheris harness for the document handlers
```

## Versioning and release

- One version number, restated in `pyproject.toml`,
  `pain001_lsp/__init__.py`, `CITATION.cff`, the README's latest-release
  line and the VS Code extension; `scripts/verify_versions.py` fails
  when they disagree.
- The line is `0.0.x`, every release is one step up, and the package
  ships the same number as the core `pain001` library, which releases
  first.
- Releases are cut by a signed tag on `main`; `release.yml` builds,
  publishes to PyPI with trusted publishing and writes the release page.
  [RELEASING.md](https://github.com/sebastienrousseau/pain001-lsp/blob/main/RELEASING.md)
  is the checklist.
