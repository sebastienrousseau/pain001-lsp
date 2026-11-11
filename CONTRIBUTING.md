<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Contributing to pain001-lsp

Thank you for your interest in contributing to **pain001-lsp**, the Language
Server Protocol server for the [pain001](https://github.com/sebastienrousseau/pain001)
suite. This guide covers the development workflow and standards.

## Development Setup

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)
- Git with SSH commit signing configured

### Setup

```bash
# Clone and install
git clone git@github.com:sebastienrousseau/pain001-lsp.git
cd pain001-lsp
poetry install --all-extras

# Verify: every gate CI runs on each push
make check
```

[DEVELOPMENT.md](DEVELOPMENT.md) maps each CI job to the local command
that reproduces it.

The package depends on the core `pain001` library and `pygls`; both are
installed automatically by `poetry install`.

### On macOS

```bash
brew install python@3.12 poetry
```

### On Linux (Debian/Ubuntu)

```bash
sudo apt install python3 python3-pip
pip install poetry
```

### On WSL

```bash
sudo apt install python3 python3-pip
pip install poetry
# Ensure ~/.local/bin is in PATH
```

## Workflow

1. **Fork** the repository
2. **Create a branch** from `main`:

   ```bash
   git checkout -b feat/my-feature
   ```

3. **Make changes** - follow the coding standards below
4. **Run every gate** (lint, types, bandit, complexity, version
   sources, tests at 100 % line and branch coverage, docstrings,
   examples, spelling):

   ```bash
   make check
   ```

5. **Sign off and sign the commit**:

   ```bash
   git commit -s -S -m "feat: add my feature"
   ```

6. **Push** and open a pull request

## Commit Signing (Required)

All commits **must** be signed with SSH or GPG.

### SSH Signing

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519
git config --global commit.gpgsign true
```

### Commit Message Format

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add hover support for optional charge-account fields
fix: handle malformed JSON offsets in diagnostics
docs: update README with editor wiring examples
test: cover the bad-identifier diagnostic path
refactor: simplify the record line-offset heuristic
```

## Coding Standards

- **Line length:** 79 characters (enforced by Black + Ruff)
- **Type hints:** Required on all public functions (mypy strict)
- **Docstrings:** Required on all public classes and functions
- **Tests:** Every new feature must include tests

## Testing

```bash
# Full suite
poetry run pytest tests/ -v

# Single file
poetry run pytest tests/test_lsp_server.py -v
```

## Pull Request Checklist

- [ ] `make check` passes
- [ ] Commits are signed and carry a `Signed-off-by` trailer (DCO)
- [ ] PR title follows conventional commit format
- [ ] New features include tests and documentation

## License

By contributing, you agree that your contributions will be dual-licensed
under the [Apache License 2.0](LICENSE-APACHE) or the
[MIT License](LICENSE-MIT), at the user's option, as the project is.
