<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Changelog

The extension ships at the pain001 suite's version.

## 0.0.80

- Version aligned with the suite (pain001 0.0.80, a security release
  of the core's REST API; nothing in the extension changed).

## 0.0.79

- Version aligned with the suite.
- New `pain001.filePattern` setting (default `**/*.json`): the glob of
  JSON files sent to the language server, for example `**/*.pain.json`.
- With pain001-lsp 0.0.79, files such as `package.json` and
  `tsconfig.json` no longer get payment diagnostics.

## 0.0.78

- Version aligned with the suite.

## 0.0.77

- Version aligned with the suite. 0.0.76 was prepared but never
  published; its changes ship in 0.0.77.

## 0.0.76 (not published)

- Version aligned with the suite.
- minimatch is overridden to 11 (GHSA-g3hv-75wg-m249); the
  language client's 5.1.9 is gone from the bundle.

## 0.0.75

- Version aligned with the suite.

## 0.0.74

- Packaged with `@vscode/vsce` 4 on Node.js 22; the lockfile no longer
  carries braces or markdown-it, which had open advisories.
- The `pain001.messageType` setting offers `pain.001.001.13` and
  `pain.008.001.08`, the two types the server supported but the
  setting did not list.
- Version aligned with the suite.

## 0.0.72

- Version aligned with the suite.

## 0.0.71

- Version aligned with the suite.

## 0.0.70

- Packaged as a `.vsix` on every release of pain001-lsp; installable
  from the release page without the Marketplace.
- Version aligned with the suite.
