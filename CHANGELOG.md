<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.0.88] - 2026-11-14

### Changed

- Release 0.0.88 in lockstep with the pain001 suite.
- Requires pain001 0.0.88 (floor `>=0.0.88,<1`), the suite version.
- Suite Consistency pins the core's ecosystem check at `404ebb9`, the
  pain001 0.0.88 release, which audits the five SDK repositories with
  the rest of the family; the job is now named "Every family
  publication agrees". Regenerated from pain001's
  `scripts/render_ecosystem_workflows.py`.
- The README's ecosystem table lists the fourteen suite repositories:
  the Go, Java, Rust, .NET and C++ SDKs joined the family at 0.0.88.

### Security

- The docs toolchain requires soupsieve 4.0 or newer: earlier versions
  have a polynomial-time denial of service in the descendant combinator
  (GHSA-mmhr-3c5m-f64f). Only the hash-pinned docs set contained it, so
  the published package is unaffected. The docs set now compiles from
  Python 3.11.5, the oldest version soupsieve 4 supports.

## [0.0.87] - 2026-11-12

### Changed

- Release 0.0.87 in lockstep with the pain001 suite.
- Requires pain001 0.0.87 (floor `>=0.0.87,<1`), the suite version.
- Suite Consistency no longer runs on another workflow's completion
  (`workflow_run`). It audits the family daily and on dispatch, as the
  core's does, since that trigger runs with the default branch's trust
  whatever started it. Regenerated from pain001's
  `scripts/render_ecosystem_workflows.py`.

### Added

- The README's Security section names the project's
  [OpenSSF Best Practices passing badge](https://www.bestpractices.dev/projects/15786),
  meeting the OpenSSF Best Practices silver criterion
  `documentation_achievements`.

### Fixed

- Suite Consistency pins the core's ecosystem check at `febcd0a`, which
  accepts the five pain001 SDK repositories as known members not yet
  released. From the 0.0.86 release until this change every scheduled
  run failed on them as undeclared repositories.

## [0.0.86] - 2026-11-11

### Added

- Add a code of conduct (adapted from Contributor Covenant 2.1, the
  suite's shared text) and a markdownlint CI job (`docs-lint.yml`,
  configured in `.markdownlint-cli2.jsonc`); fix the Markdown it
  flagged.
- Run every Python block in the README as part of the test suite, so
  the Quick Start cannot drift from the helpers it calls.
- Add `DEVELOPMENT.md`, mapping every CI job to the local command that
  reproduces it, and a devcontainer that installs the project and runs
  `make check`.
- Spell-check the tree with codespell in the docs-lint workflow, the
  pre-commit hooks and `make check` (`make spelling`, configured in
  `pyproject.toml`).
- A Docs check workflow (`docs-check.yml`) builds the manual with every
  Sphinx warning an error and runs Sphinx's link check on every push
  and pull request (`make docs`, `make linkcheck`); the deploy build in
  `docs.yml` uses the same warnings-as-errors flags. Links into this
  repository's `main` are skipped by the link check and checked offline
  instead, for `README.md`, `ARCHITECTURE.md` and `DEVELOPMENT.md`, by
  `tests/test_readme.py`.
- The manual includes `ARCHITECTURE.md` and `DEVELOPMENT.md`, and its API
  reference documents the faces helpers (`faces_list`,
  `faces_project`).
- `KEYS.asc`: the maintainer's SSH signing keys in allowed-signers
  format, the same keys the core, MCP server and mockbank publish, so
  a signed commit or tag can be checked with
  `git config gpg.ssh.allowedSignersFile KEYS.asc`.

### Changed

- Release 0.0.86 in lockstep with the pain001 suite and require core
  pain001 0.0.86; the locks resolve its published artifacts.
- Align the pre-commit ruff and black hooks with the locked versions,
  drop the `ruff-format` hook that fought black, and keep black off the
  vendored `tests/test_suite_conformance.py`, which the old hooks
  rewrote.
- `CONTRIBUTING.md` points at `make check` and `DEVELOPMENT.md`, asks for
  the DCO sign-off, and states the dual Apache-2.0 OR MIT licence.
- README: the ecosystem table lists all nine suite repositories, the
  Examples table lists `05_faces_commands.py`, and Documentation links
  the manual's API reference and `DEVELOPMENT.md`; `tests/test_readme.py`
  now checks both tables' sources and the four documentation links.
- `ARCHITECTURE.md` described pygls 1.x (`pygls >=1.3,<2`) and a
  six-helper, single-module server; it now states the pygls 2.x range
  the package requires, maps every module, the formatting, symbol and
  workspace commands, and links ADR 0003 on explicit handler
  registration.
- The record walkers behind diagnostics, the quick fix and the outline
  (`_record_line_offsets`, `_record_close_positions`) share one brace
  scan, `_braces`, which skips strings with a regular expression. Both
  are within every complexity ceiling and leave the baseline; their
  output is unchanged on 300,000 random documents and pinned by
  `tests/test_record_scanning.py`.
- `server.py` (976 lines) is split under the 500-line ceiling: the
  schema loader (`_schema.py`), the record checks and their `lsprotocol`
  mapping (`_diagnostics.py`), the record walkers (`_records.py`),
  formatting and the outline (`_layout.py`), the corpus commands
  (`_corpus.py`) and `compute_diagnostics_csv` (into `_csv.py`) move
  out, and `server.py` imports them back, so every name it exposed is
  still importable from `pain001_lsp.server`. `complexity-baseline.json`
  is now empty.
- The README demo is served from `raw.githubusercontent.com` on
  `main` instead of a relative path, which PyPI does not resolve;
  `tests/test_readme.py` fails on any relative README image.

### Removed

- `CODE-OF-CONDUCT.md`, a second copy of the code of conduct;
  `CODE_OF_CONDUCT.md` is the one GitHub and `GOVERNANCE.md` link to.

## [0.0.85] - 2026-11-10

### Changed

- Release 0.0.85 in lockstep with the pain001 suite and require core
  pain001 0.0.85; the locks resolve its published artifacts.
- Point usage questions at this repository's GitHub issues: SUPPORT.md, SECURITY.md, GOVERNANCE.md, CODEOWNERS and the issue-template contact link no longer send them to GitHub Discussions, which the suite does not use.

## [0.0.84] - 2026-11-09

### Added

- Audit all nine suite repositories and their publication channels daily and after publishing workflows, using the shared checker pinned to a core commit.


### Changed

- Release 0.0.84 with the suite and require core pain001 0.0.84. Regenerate dependency locks from the published core artifacts.


### Fixed

- Include the declared licence files and README in the container build context before package installation.

- Emit the existing Apache-2.0 OR MIT licence as a PEP 639 expression. Remove the erroneous proprietary classifier produced by legacy Poetry metadata.

## [0.0.83] - 2026-11-09

The pain001 family's 0.0.83 release, on the pain001 0.0.83 floor
(`pyproject.toml` and `requirements/runtime.in`). Nothing in the
language server changed beyond the version and the floor: the core
functions it calls (`pain001.lsp.diagnostics`, `validate_iban`,
`validate_bic`) did not change in [pain001 0.0.83](https://github.com/sebastienrousseau/pain001/releases/tag/v0.0.83),
whose work is XML signing and signature verification.

### Changed

- Requires `pain001 >= 0.0.83, < 1`; `poetry.lock` and the hash-pinned
  runtime, ci, docs and fuzz sets move pain001 to 0.0.83.
- Build and audit tools: virtualenv 21.15.6, dulwich 1.2.21, anyio
  4.16.0 and pip 26.3 (Dependabot #95, #97, #98 and #99).
- CI actions: github/codeql-action 4.39.3, docker/login-action 4.8.0,
  sigstore/cosign-installer 4.1.3 and softprops/action-gh-release 3.0.4
  (Dependabot #102).

## [0.0.82] - 2026-11-09

The pain001 family's 0.0.82 release, on the pain001 0.0.82 floor
(`pyproject.toml` and `requirements/runtime.in`). Nothing in the
language server changed beyond the version and the floor: the core
functions it calls (`pain001.lsp.diagnostics`, `validate_iban`,
`validate_bic`) behave the same in [pain001 0.0.82](https://github.com/sebastienrousseau/pain001/releases/tag/v0.0.82).

### Changed

- Requires `pain001 >= 0.0.82, < 1`; `poetry.lock` and the hash-pinned
  runtime, ci, docs and fuzz sets move pain001 to 0.0.82.
- Development tools: ruff 0.17.4 and filelock 4.2.9 (Dependabot #93
  and #94).

## [0.0.81] - 2026-11-08

The pain001 family's 0.0.81 release, on the pain001 0.0.81 floor
(`pyproject.toml` and `requirements/runtime.in`). Nothing in the
language server changed beyond the version and the floor: the core
functions it calls (`pain001.lsp.diagnostics`, `validate_iban`,
`validate_bic`) are the same in [pain001 0.0.81](https://github.com/sebastienrousseau/pain001/releases/tag/v0.0.81).

### Changed

- Requires `pain001 >= 0.0.81, < 1`; `poetry.lock` and the hash-pinned
  runtime, ci, docs and fuzz sets move pain001 to 0.0.81.

## [0.0.80] - 2026-11-07

The pain001 family's 0.0.80 release, on the pain001 0.0.80 floor
(`pyproject.toml` and `requirements/runtime.in`). pain001 0.0.80 is a
security release of the core's REST API
([GHSA-vv3x-jpvc-w468](https://github.com/sebastienrousseau/pain001/security/advisories/GHSA-vv3x-jpvc-w468)).
Nothing in the language server changed beyond the version and the
floor.

### Changed

- Requires `pain001 >= 0.0.80, < 1`; `poetry.lock` and the hash-pinned
  runtime, ci, docs and fuzz sets move pain001 to 0.0.80.

## [0.0.79] - 2026-11-07

The pain001 family's 0.0.79 release, on the pain001 0.0.79 floor
(`pyproject.toml` and `requirements/runtime.in`).

### Fixed

- Only payment documents get diagnostics. The VS Code extension sends
  every JSON file to the server, and the server read every non-CSV
  document as payment records, so `package.json` and `tsconfig.json`
  were told "'id' is a required property". A JSON document is now
  diagnosed only when it is an array, or an object with at least one
  field of the active message type's schema as a key; text that does
  not parse yet counts when it opens an array or quotes one of those
  fields as a key. Any other document is published with no
  diagnostics, which clears what an earlier version left.
  `compute_diagnostics` itself is unchanged. The check is
  `is_payment_document` in `pain001_lsp._documents`, where
  `is_csv_uri` (formerly `server._is_csv_uri`) also moved.
- The README still called the faces commands unreleased; they shipped
  in 0.0.78.

### Added

- VS Code: a `pain001.filePattern` setting, the glob of JSON files sent
  to the server. The default, `**/*.json`, keeps the files reached
  before; set it to, for example, `**/*.pain.json` to stop completion,
  hover and formatting in other JSON files too.

### Changed

- Requires `pain001 >= 0.0.79, < 1`; `poetry.lock` and the hash-pinned
  runtime, ci, docs and fuzz sets move pain001 to 0.0.79.
- The release page is written by the release workflow in the suite's
  shape. A last `release-notes` job, once the SBOMs and the `.vsix`
  are attached, runs `scripts/release_notes.py publish`: the title is
  `pain001-lsp X.Y.Z`, the Highlights come from `releases/vX.Y.Z.md`,
  What's Changed lists the pull requests merged since the previous
  release, and Checksums gives the SHA-256 of every asset. The 0.0.77
  and 0.0.78 pages had to be rewritten by hand.
- Release notes live in `releases/vX.Y.Z.md`, starting with
  `releases/v0.0.78.md` (the published 0.0.78 Highlights).
  `tests/test_release_notes.py` fails a pull request whose CHANGELOG
  dates the version while that note is missing or has other than 2 to
  4 highlights. Both files are vendored byte-identical from `pain001`.

## [0.0.78] - 2026-11-07

The pain001 family's 0.0.78 release, on the pain001 0.0.78 floor
(`pyproject.toml` and `requirements/runtime.in`), which adds faces.

### Added

- Faces commands (pain001 >= 0.0.78): `pain001.faces.list` names each
  face, its target and the binding keys it accepts;
  `pain001.faces.project` takes a pain.001 document as XML text (the
  editor's buffer) with a `face`, an optional `version` and optional
  `bindings`, and returns the payload for UK Open Banking v4.0.1,
  Berlin Group NextGenPSD2 v1.3.16 or ISO 20022 element names with a
  loss report of every source element not carried. A refusal, a file
  path instead of XML or an entity declaration is an `{"error": ...}`
  payload; with an older pain001 both commands say which version they
  need. The pure helpers are `faces_list` and `faces_project` in
  `pain001_lsp._faces`.
- `examples/05_faces_commands.py`, run by `make examples` and CI.

### Changed

- The `executeCommand` argument helper moved to
  `pain001_lsp/_commands.py`, shared by the corpus and faces commands;
  `server.py` shrinks from 983 to 979 lines.

## [0.0.77] - 2026-11-06

The pain001 family's 0.0.77 release, on the pain001 0.0.77 floor.
0.0.76 was prepared on 2026-11-05 but never tagged or published, so
its changes ship here.

### Security

- The VS Code extension overrides minimatch to `^11.0.1`
  (GHSA-g3hv-75wg-m249): vscode-languageclient 9.0.1 resolved 5.1.9.
- `requirements/build.txt` floors dulwich at 1.2.20 and virtualenv at
  21.15.1.

### Changed

- Requires `pain001 >= 0.0.77, < 1` (`pyproject.toml` and
  `requirements/runtime.in`); `poetry.lock` and the hash-pinned runtime,
  ci, docs and fuzz sets move pain001 to 0.0.77.
- Development tools: ruff 0.17.3, complexipy 8.3.0, pytest 9.2.0,
  pytest-benchmark 5.3.1, mypy 2.4.1 and mutmut 3.8.1.
- CI: one stable required check per versioned matrix.

## [0.0.75] - 2026-10-27

The pain001 family's 0.0.75 release, on the pain001 0.0.75 floor, and
the first on Python 3.11 or newer.

### Security

- No advised filelock installs from any requirements tree
  (GHSA-9vhv-jxww-xfm5, GHSA-567q-5qvw-pf92, GHSA-v4x8-3wr5-3wq8;
  `audit.txt`, `build.txt` and `ci.txt` pinned 4.1.0 on Python 3.10,
  which pip-audit on 3.12 skips). filelock 4.2.1 needs Python 3.11:
  `build.txt` and `audit.txt`, installed only on 3.12, are compiled for
  3.12 with `filelock >= 4.2.1`; `ci.in` installs pip-audit, which pulls
  filelock in, only on 3.11+.
- `build.in` floors `virtualenv >= 21.14.13` (GHSA-cx6f-vjhg-g3cc; was
  21.14.12) and `dulwich >= 1.2.19` (was 1.2.17), in place of Dependabot
  #67 and #68, whose recompiles dropped the per-Python markers.
- The VS Code extension's dev tooling overrides `@azure/msal-node` to
  7.1.0 (GHSA-xcx6-jx8p-x3h5; the lock held 6.0.1). `@vscode/vsce` pulls
  it in through `@azure/identity`, whose every release still requires
  msal-node 6.x, and all of 6.x is affected; the extension's publish step
  signs in with `VSCE_PAT`, not an Azure credential.
- `certifi >= 2026.10.23` in the audit, build, CI and docs requirement
  sets (Dependabot #73 and #74, recompiled with each file's own command
  so the per-Python markers stay).
- The VS Code extension's dev lockfile takes `qs` 6.17.0
  (GHSA-6pq8-jhm2-2vcw; the lock held 6.16.0), Dependabot #76, which
  arrived after the release PR merged.

### Removed

- Python 3.10 support. The floor is 3.11 (`python = ">=3.11,<4.0"`),
  the pain001 suite's decision for 0.0.75: 3.10 reaches end of life in
  October 2026, and current hypothesis releases need 3.11, which broke
  Dependabot's resolver for siblings on a 3.10 floor. CI tests 3.11 to
  3.14; ruff, black and mypy target 3.11; the `tomli` backport and the
  3.10 branches in `scripts/check_suite_consistency.py` and the tests
  are gone, and `poetry.lock` and the 3.11 requirement sets are
  re-locked (only the packages for 3.10 leave). pip keeps 3.10 users
  on pain001-lsp 0.0.74.

### Changed

- Dependabot's weekly pip run splits by Python. It resolved the "/" job
  on Python 3.10, then the floor in `pyproject.toml`, and since
  `requirements/audit.in` and `build.in` floor `filelock >= 4.2.1`
  (Python 3.11+), any update touching them would end in
  `dependency_file_not_resolvable`, as it already did in camt053-mcp and
  acmt001-mcp. "/" now leaves the 3.12 sets (audit, build, fuzz) to a
  second pip entry for `/requirements`, which runs on Dependabot's
  newest Python.

## [0.0.74] - 2026-10-21

The pain001 family's 0.0.74 release, on the pain001 0.0.74 floor. The
family skips 0.0.73, which pain001-mcp published on its own.

### Fixed

- A document `json.loads` rejects without a `JSONDecodeError` no longer
  raises out of the handlers. Nesting deeper than the recursion limit
  (about ten thousand open brackets) and an integer longer than 4300
  digits used to leave the editor with stale diagnostics; diagnostics
  now report one `Invalid JSON: ...` error at the top of the document,
  and formatting, the outline and the quick fix offer nothing, as they
  do for a syntax error.
- Completion names `pain.001.001.13` (Customer Credit Transfer
  Initiation V13) and `pain.008.001.08` (Customer Direct Debit
  Initiation V08) instead of showing the bare id, and the VS Code
  extension's `pain001.messageType` setting lists both.
- The GitHub release is titled `pain001-lsp X.Y.Z`, and the VS Code
  extension job waits for the release before attaching the `.vsix`
  (v0.0.72 was published without it).
- The scheduled suite-consistency check compares this tree with
  pain001-lsp's own PyPI release, not the core's.
- The Docker image installed `pain001>=0.0.52,<0.0.54` before this
  package by default and was labelled Apache-2.0 only.

### Changed

- `pain001` floor raised to `>=0.0.74,<1`. The 0.0.72 entry below says
  the floor moved to 0.0.72, but `pyproject.toml` still said `>=0.0.71`.
- Every `pip install` in CI, the release job and the Dockerfile installs
  from hash-pinned `requirements/*.txt`, through `scripts/ci-install.sh`
  in CI; the base image is pinned by digest. OpenSSF Scorecard's
  Pinned-Dependencies check goes from 2 to 10.
- The VS Code extension is packaged with `@vscode/vsce` 4 on Node.js 22,
  which drops braces (GHSA-vfj7-8cjw-p6xm, no fixed release) and
  markdown-it (GHSA-gfr2-rv44-r23c, GHSA-vfgh-jcmw-g37q) from its
  lockfile.
- Hash-pinned build, docs and audit sets floor certifi at 2026.10.19
  (GHSA-6q48-6c7w-9gw2), urllib3 at 2.8.0 and virtualenv at 21.14.8.
- The README follows the portfolio template, with a VHS demo, and the
  manual adds `docs/COMPARISON.md`, `docs/BENCHMARKS.md` and
  `docs/POLICIES.md`; it builds without warnings and links the author
  on every page.
- `CITATION.cff` lists the licence as Apache-2.0 and MIT, the form CFF
  1.2.0 accepts; `Apache-2.0 OR MIT` failed schema validation.

### Added

- `scripts/check_complexity.py` holds every function to the portfolio
  ceilings against `complexity-baseline.json`, which may only shrink:
  three offenders, down from four, after `compute_diagnostics` was
  split into helpers within every ceiling.
- `fuzz/fuzz_documents.py`, an Atheris harness over every document
  handler, run on each change and weekly.
- The Security workflow audits the `poetry.lock` environment and every
  `requirements/*.txt` with pip-audit.
- `scripts/verify_versions.py` checks every version source and fails
  when the pain001 floor differs from the release version; the
  "Version sources agree" workflow runs it on each pull request.
- ruff and black cover `scripts/`, `fuzz/` and `examples/`.

## [0.0.72] - 2026-09-28

Aligns on pain001 0.0.72: ISO 20022 schemas and Schematron validation
rules, enhanced CI provenance attestations, and dependency updates.

### Changed

- `pain001` floor raised to `>=0.0.72`.
- Version aligned to `0.0.72` across all `pain001` suite packages.
- The README and the documentation index link
  [What is pain.001?](https://pain001.com/pain-001/), an explainer of the
  message's structure, versions and a schema-valid example.

## [0.0.71] - 2026-09-26

Aligns on pain001 0.0.71: request-local CEL policy rules, review-only
correction suggestions, explicit SFTP delivery, and release artifact
inspection.

### Changed

- `pain001` floor raised to `>=0.0.71`.
- Version aligned to `0.0.71` across all five `pain001` packages.

## [0.0.70] - 2026-09-13

Aligns on pain001 0.0.70: importing the core no longer loads its CLI,
which makes the server start faster; the rail rules read the CSV
pipeline's column names as well as the short ones.

### Changed

- `pain001` floor raised to `>=0.0.70`.
- Version aligned to `0.0.70` across all five `pain001` packages.

## [0.0.69] - 2026-09-12

Aligns on pain001 0.0.69, the third example-corpus release: the tier 2
and 3 market packs reach `pain001.corpus.list` unchanged.

### Changed

- `pain001` floor raised to `>=0.0.69`.
- Version aligned to `0.0.69` across all five `pain001` packages.

## [0.0.68] - 2026-09-12

Aligns on pain001 0.0.68, the second example-corpus release: the
`pain001.corpus.list` command now sees the tier-1 market packs and the
coverage files named by recipe and focus.

### Changed

- `pain001` floor raised to `>=0.0.68`.
- Version aligned to `0.0.68` across all five `pain001` packages.

## [0.0.67] - 2026-09-12

The example corpus reaches the editor: the validated pain.001 files
pain001 0.0.67 ships, with their provenance, are listable and readable
through workspace commands.

### Added

- **Example corpus commands.** `workspace/executeCommand` gains
  `pain001.corpus.list` (the validated example files pain001 ships:
  market scenarios per country and rail with bank variants, and the
  schema coverage sets, filterable by kind, country and message type)
  and `pain001.corpus.get` (one file's XML with its provenance sidecar),
  backed by the pure helpers `corpus_list` and `corpus_get`. They
  delegate to `pain001.corpus`, which shipped in pain001 0.0.67; the
  dependency floor is now 0.0.67, and with an older library they still
  return an `error` payload rather than failing at import.

### Changed

- `pain001` floor raised to `>=0.0.67`, the first release with
  `pain001.corpus`.
- Version aligned to `0.0.67` across all five `pain001` packages.
- Dev tools: `ruff` 0.16.6, `packaging` 26.3, `pytest-benchmark` 5.3.0;
  GitHub Actions group bumped; the vendored conformance file refreshed
  to the canonical copy.

## [0.0.66] - 2026-09-12

Aligns the `pain001` suite on `0.0.66`, the core release that adds
cross-record duplicate detection, the `/api/v1/ui` dashboard, GPG
flags and OpenTelemetry spans. Nothing in this package changed.

### Changed

- Version aligned to `0.0.66` across all five `pain001` packages.

## [0.0.65] - 2026-08-29

Aligns the `pain001` suite on one version number, and adds the scheduled
drift check this repository was missing.

### Added

- `scripts/check_suite_consistency.py` and a scheduled `Suite
  Consistency` workflow compare this tree, and every published member of
  the suite, against PyPI. A member left a release behind still installs
  and still passes its own tests; only the index disagrees, and only if
  somebody looks.

### Changed

- Version aligned to `0.0.65` across all five `pain001` packages, which
  had drifted to `0.0.62`, `0.0.64`, `0.0.63`, `0.0.62` and `0.0.63`.
- Refreshed the vendored `tests/test_suite_conformance.py` to the
  current canonical copy. Its drift-check probe now matches the bare
  word `pypi` rather than the hostname, which CodeQL read as an
  incomplete URL sanitisation.

## [0.0.64] - 2026-08-29

Brings this repository onto the **suite conformance gate**.

### Added

- **`benches/bench_diagnostics.py`** — how long the editor waits.

  A language server is not measured in throughput. It is measured against
  a person typing: the client recomputes diagnostics on every change, so
  the only question is whether the answer arrives before the user
  notices. The table marks two thresholds — **16 ms** (one frame, feels
  instantaneous) and **100 ms** (the limit of "reacting instantly").

  The number to read is the **budget**: how large a document stays
  interactive. It is a budget, not a score.

  For comparison across the three language servers in the suite, all
  doing the same shape of work:

  | Server | Cost | Interactive budget |
  |---|---|---|
  | `bankstatementparser-lsp` | 0.0018 ms/entry | ~56,000 entries |
  | `pain001-lsp` | 0.08 ms/record | ~1,200 records |
  | `camt053-lsp` | **0.86 ms/record** | **~116 records** |

  The malformed column matters too: that is the state a document spends
  most of its life in while somebody is typing. A linter fast on valid
  input and slow on invalid input is slowest exactly when the editor
  calls it most.

  Nothing asserts a timing threshold — wall-clock is not comparable
  between machines, and a flaky performance gate teaches people to
  ignore red. CI runs `--quick`, so a benchmark that stops compiling
  fails the build rather than rotting.

  This server sits comfortably inside the interactive band — 0.08 ms per
  record, a budget of roughly 1,200 records — and returns immediately on
  malformed input rather than doing partial work.

- **`tests/test_suite_conformance.py`** — invariants shared by every
  repository in the suite, vendored from one canonical copy and
  checksummed by its own test.

### Changed

- CI lints, formats and runs `benches/` alongside everything else.
- `tests/test_suite_conformance.py` is excluded from black: it is
  generated, and the suite uses three different line lengths.

## [0.0.63] - 2026-08-28

### Changed

- **A plain `pytest` now enforces the same 100% coverage floor CI does.**
  `--cov`, `--cov-branch` and `--cov-report=term-missing` move into
  `[tool.pytest.ini_options] addopts`. Before this, running `pytest`
  locally measured no coverage at all: the developer saw green and learned
  otherwise from the build.

  The gate itself was never missing — CI has always run
  `--cov-fail-under=100`, so nothing could regress onto `main` unnoticed.
  What was missing was the local half of it.

- **The floor is stated once.** It was in two places, the
  `--cov-fail-under` flag in `ci.yml` and `fail_under` under
  `[tool.coverage.report]`, which is how two numbers meant to be equal stop
  being equal. pytest-cov honours `fail_under` from the coverage config, so
  the flag is gone from both `addopts` and the workflow and the number lives
  in exactly one place.

  CI now runs `pytest tests/ --cov-report=xml -v`; only the XML report is
  CI-specific.

### Verification

Coverage was already 100% and remains so. The gate was mutation-tested:
adding a function no test calls drops coverage below the floor and fails
the run, locally as well as in CI.

## [0.0.62] - 2026-08-21

### Performance

- **The bundled JSON Schema is cached.** Every interactive entry point
  goes through `_load_schema`, which re-read and re-parsed it from disk
  on each call — a file read and a JSON parse per keystroke, to answer
  from data that ships read-only inside the package and cannot change
  at runtime.

  | call | before | after |
  |---|---|---|
  | `completion_items` | 0.0805ms | **0.0029ms** (28x) |
  | `hover_text` | 0.0794ms | **0.0002ms** (478x) |
  | `missing_required_fields` | 0.0816ms | **0.0004ms** (196x) |

  Not user-visible — 0.08ms is imperceptible — so this is waste removed
  rather than latency fixed. It surfaced from benchmarking: three
  functions measuring identically to three decimal places were not three
  measurements, they were the same file read three times.

### Added

- **Benchmarks for completion, hover and the missing-field check**, the
  per-keystroke paths the 0.0.61 set did not cover. The guard is a
  property rather than a threshold — at microsecond scale any wall-clock
  bound loose enough for CI would not notice the cache being removed, so
  the test asserts the schema is not re-read across 150 interactive
  calls.

- **A `locked` CI job** that installs from `poetry.lock` and runs the
  suite against the pinned set. 0.0.61 added `poetry check --lock` after
  finding the lock silently stale, but nothing installed from it — so it
  proved the lock matched `pyproject.toml` and nothing about whether the
  pinned versions worked. The pip-based jobs still install against the
  live range; the two answer different questions.

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

[0.0.80]: https://github.com/sebastienrousseau/pain001-lsp/compare/v0.0.79...v0.0.80
[0.0.79]: https://github.com/sebastienrousseau/pain001-lsp/compare/v0.0.78...v0.0.79
[0.0.78]: https://github.com/sebastienrousseau/pain001-lsp/compare/v0.0.77...v0.0.78
[0.0.77]: https://github.com/sebastienrousseau/pain001-lsp/compare/v0.0.75...v0.0.77
[0.0.75]: https://github.com/sebastienrousseau/pain001-lsp/compare/v0.0.74...v0.0.75
[0.0.74]: https://github.com/sebastienrousseau/pain001-lsp/compare/v0.0.72...v0.0.74
[0.0.52]: https://github.com/sebastienrousseau/pain001-lsp/releases/tag/v0.0.52
