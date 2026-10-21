<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Releasing pain001-lsp

This document defines **what merits a release** and **how to cut one**,
so versions are deliberate rather than ad-hoc.

## Versioning scheme

pain001-lsp tracks
[`pain001`](https://github.com/sebastienrousseau/pain001) version-for-
version: when pain001 ships `0.0.X`, pain001-lsp ships a matching
`0.0.X`. This keeps the editor surface aligned with the core library's
public API and lets a user install both at compatible versions with a
single pin. Out-of-band patch releases (e.g. `0.0.X.post1`) are reserved
for LSP-only bug fixes that don't require a pain001 bump.

## What merits a release

Cut a new version when there is user-visible change to ship - bug fixes,
security or dependency patches, new editor features (diagnostics,
completion entries, code actions), or documentation that ships in the
package.

Do **not** cut a release that contains only a version-number bump with
no functional, security, or documentation change.

## Pre-flight checklist

A release is ready only when **all** of the following hold on `main`:

1. `make check` is green (lint + 100% coverage + interrogate + examples).
2. `mypy --strict`, `ruff`, `black` are clean.
3. Zero open Dependabot alerts, code-scanning alerts and issues, and
   bandit and pip-audit are clean. An alert is closed by fixing it; only
   a false positive or a finding that cannot be fixed in code is
   dismissed, by the maintainer, with the reason written on it.
4. `CHANGELOG.md` has a dated section for the new version describing the
   change set (this is the single source of truth for the release).
5. Every version source agrees and the `pain001` floor equals the
   release version (enforced by `scripts/verify_versions.py`, which the
   "Version sources agree" workflow runs on each pull request).
6. `poetry.lock` and the hash-pinned `requirements/*.txt` resolve the
   core's release: the core publishes first, then each file is
   recompiled with the command in its header and `poetry lock`.

## Cutting the release

1. Bump the version in `pyproject.toml`, `pain001_lsp/__init__.py`,
   `CITATION.cff`, the README's latest-release line and
   `editors/vscode/package.json`, raise the `pain001` floor, and add the
   `CHANGELOG.md` section, on `feat/vX.Y.Z` in a single PR.
2. Merge the PR to `main` once CI is green.
3. Push a signed tag:

   ```bash
   git tag -s vX.Y.Z -m "pain001-lsp vX.Y.Z" <merge-commit>
   git push origin vX.Y.Z
   ```

4. The tag triggers the `publish` job in `release.yml`, which fails fast
   if the tag does not match the package version, then builds, runs
   `twine check`, creates the GitHub release from the `CHANGELOG.md`
   section, and publishes to PyPI via OIDC trusted publishing.

## After releasing

- Confirm the version is live on
  [PyPI](https://pypi.org/project/pain001-lsp/) and the GitHub release is
  published (not draft).
- Verify a clean install: `pip install pain001-lsp==X.Y.Z`.

## Optional CI integrations

These are deliberately gated so an empty / un-set secret skips the
step rather than failing the build:

- **Codecov upload** (`pr.yml`): set the `CODECOV_TOKEN` repository
  secret and the PR Gate will start publishing branch coverage to
  [codecov.io](https://about.codecov.io). Without the secret the
  step skips silently; the 100% coverage gate is still enforced
  in-CI by pytest's `--cov-fail-under=100`.
- **PyPI trusted publisher** (`release.yml`): configured at
  <https://pypi.org/manage/account/publishing/>. The publisher claim
  set is `repo:sebastienrousseau/pain001-lsp:environment:pypi` with
  `workflow_ref` pointing at `.github/workflows/release.yml`. A
  Pending Publisher is auto-converted to a permanent Trusted
  Publisher on the first successful publish.
