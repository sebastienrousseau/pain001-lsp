<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Toolchain policy

Python 3.10 is the floor (`python = ">=3.10,<4.0"` in `pyproject.toml`),
with Linux CI on 3.10, 3.11, 3.12, 3.13 and 3.14. The floor matches the
`pain001` core library and moves with the rest of the pain001 suite.
Raising it is a maintainer decision, recorded in the changelog. No
distro-system Python is supported.

The VS Code extension in `editors/vscode/` is built with Node.js 22, the
minimum `@vscode/vsce` 4 accepts, and targets VS Code 1.75 or newer.
