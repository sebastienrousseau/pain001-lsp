<!-- SPDX-License-Identifier: Apache-2.0 -->

# Getting support

Thanks for using pain001-lsp. Here's the fastest way to get help, by
need.

## Questions & how-to

- **Read first:** the [README](README.md), the runnable
  [`examples/`](examples/) (helper walkthrough, quick-fix snippet,
  runtime message-type override), and the parent
  [`pain001`](https://github.com/sebastienrousseau/pain001) repo for
  message-type / scheme background.
- **Still stuck?** Open a
  [GitHub Discussion](https://github.com/sebastienrousseau/pain001/discussions)
  on the parent repo (shared with pain001 and pain001-mcp) or a question
  issue here. Include your Python version, `pain001-lsp` version
  (`python -c "import pain001_lsp; print(pain001_lsp.__version__)"`), your
  editor + LSP client, and a minimal reproducer.

## Bugs

Open a bug report at
<https://github.com/sebastienrousseau/pain001-lsp/issues/new> with a
minimal reproducer, the file type you're editing (JSON record array or
CSV), and what you saw vs what you expected.

## Feature requests

Open a feature request at
<https://github.com/sebastienrousseau/pain001-lsp/issues/new>. Editor
features that surface more of the
[`pain001`](https://github.com/sebastienrousseau/pain001) public API are
especially welcome - see [ARCHITECTURE.md](ARCHITECTURE.md) for the
extension points and [ROADMAP.md](ROADMAP.md) for what's planned.

## Security

**Do not** open public issues for vulnerabilities. Follow the private
disclosure process in [SECURITY.md](SECURITY.md).

## Contributing & maintaining

See [CONTRIBUTING.md](CONTRIBUTING.md) and [GOVERNANCE.md](GOVERNANCE.md).

## Supported versions

Fixes land on the latest release line. See [SECURITY.md](SECURITY.md)
for the supported-version policy. pain001-lsp requires Python 3.10+.
