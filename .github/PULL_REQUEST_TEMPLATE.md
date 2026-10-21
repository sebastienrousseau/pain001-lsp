<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->
<!--
Pull request description for pain001-lsp. The shape follows the shared
PR template (section order, Highlights, fenced Checksums block, Full
Changelog line), aligned with the release page format at
https://github.com/sebastienrousseau/passmcp/releases/tag/v0.0.5.

- Title: a Conventional Commit, e.g. "fix: keep hover on escaped keys".
- Open with a two-line BLUF: line 1 begins "This PR " and says what it
  does; line 2 says why it matters or the outcome. Put a blank line
  between them, and no paragraph above.
- Write like a person: direct, concrete, no filler. No em dash
  characters anywhere; use commas, colons, parentheses or a spaced
  hyphen. No tool-attribution footer.
- Keep the sections and their order. Fill every placeholder from real
  evidence: commands that ran and what they printed.
- Every commit is signed and carries a Signed-off-by from its author.
-->

This PR <what it does, in one plain line>.

<why it matters or the outcome, in one plain line>

## Highlights ⭐️

* **<Headline>**: <one or two plain sentences on what changed for the user>.
* **<Headline>**: <one or two plain sentences>.

## What's Changed

* `<commit subject>` by @<author>

<optional: a few detail bullets naming files and the concrete change>

## Validation

* `make check`: <N passed, coverage 100% line and branch, every gate's result>.
* `python scripts/check_complexity.py` and `python scripts/verify_versions.py`: <result>.
* `python -m build` and `twine check --strict dist/*`: <result>.

## Checksums

SHA-256 of the artifacts produced by `python -m build` on this branch:

```text
<sha256>  dist/pain001_lsp-<version>-py3-none-any.whl
<sha256>  dist/pain001_lsp-<version>.tar.gz
```

**Full Changelog**: https://github.com/sebastienrousseau/pain001-lsp/compare/<base>...<head>
