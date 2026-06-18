# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in pain001-lsp, please email
**security@pain001.com** instead of using the issue tracker.

Please include:
1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if available)

We will acknowledge receipt within 48 hours and provide updates on
remediation timeline.

## Threat Model

`pain001-lsp` is a Language Server Protocol server. It runs locally over
stdio under the user's editor process, so its security surface is:

- **Document contents** - JSON payment-data files an editor sends via
  `textDocument/didOpen` and `textDocument/didChange`.
- **`initializationOptions`** - the editor can pass arbitrary
  configuration at startup; the server consumes one key (`messageType`).
- **Schema loading** - `_load_schema()` reads JSON Schema files bundled
  with `pain001` from a known directory; no caller-supplied paths.

There is **no network listener, no caller-supplied filesystem path, and
no shell-out**. The server's behaviour is bounded by what the editor
chooses to send.

## Hardening

- **Defensive parsing** - `json.loads` is wrapped in `try/except`; a
  malformed document yields a single LSP diagnostic, not an exception.
- **Bounded configuration** - `messageType` is validated against
  `pain001.constants.valid_xml_types` before it takes effect; non-dict
  `initializationOptions` is ignored.
- **No code execution from documents** - diagnostics, completion, hover,
  and code actions are pure functions of the document text.
- **Type-appropriate placeholders only** - the "Add missing required
  fields" quick-fix inserts `""`/`0`/`false`-style values from a fixed
  table, never values derived from the document.
- **Errors don't leak tracebacks** - schema-loading failures fall back to
  empty lists/`None`, surfaced as plain diagnostics with no stack frame.

## Continuous Integration

- `ci.yml` runs the full quality matrix (ruff, mypy, pytest with the
  100% coverage gate, interrogate).
- `security.yml` runs `bandit` against the package on every push and
  weekly via cron.
- `codeql.yml` runs GitHub's CodeQL Python analysis weekly.

## Cryptography Status

`pain001-lsp` does not perform cryptographic operations.

## Contact

- **Email**: security@pain001.com
- **GitHub Advisories**: https://github.com/sebastienrousseau/pain001-lsp/security/advisories
- **GitHub Discussions**: https://github.com/sebastienrousseau/pain001/discussions
