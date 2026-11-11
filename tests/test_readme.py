# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The README keeps the portfolio template's shape.

Every repository in the family shares one README layout: the same
second-level headings in the same order, a badge row of 28-pixel
for-the-badge shields, the demo under it, and no template placeholder
left unfilled.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"

HEADINGS = [
    "Contents",
    "Install",
    "Requirements",
    "Quick Start",
    "The pain001-lsp ecosystem",
    "Capabilities at a glance",
    "Ecosystem comparison",
    "Benchmarks",
    "Features",
    "Configuration",
    "Examples",
    "When not to use pain001-lsp",
    "Development",
    "Security",
    "Documentation",
    "Stability guarantees",
    "License",
]


def _text() -> str:
    return README.read_text(encoding="utf-8")


def test_headings_follow_the_template_order():
    found = re.findall(r"^## (.+)$", _text(), re.MULTILINE)
    assert found == HEADINGS


def test_no_template_placeholder_is_left():
    assert "{{" not in _text()


def test_badges_are_28_pixel_shields_then_the_demo():
    text = _text()
    badges = re.findall(r'<img src="([^"]+)"[^>]*height="(\d+)"', text)
    assert len(badges) >= 6
    assert {height for _, height in badges} == {"28"}
    assert all("style=for-the-badge" in src for src, _ in badges)
    assert text.index(f'src="{RAW}.github/demo.gif"') > text.index("height=")
    assert (ROOT / ".github" / "demo.gif").is_file()


RAW = "https://raw.githubusercontent.com/sebastienrousseau/pain001-lsp/main/"


def test_every_image_is_an_absolute_https_url():
    """PyPI does not resolve relative image paths in the README."""
    sources = re.findall(r'<img src="([^"]+)"', _text())
    assert sources
    assert [src for src in sources if not src.startswith("https://")] == []
    for src in sources:
        if src.startswith(RAW):
            assert (ROOT / src.removeprefix(RAW)).is_file(), src


def _python_snippets() -> list[str]:
    return re.findall(r"^```python\n(.*?)^```$", _text(), re.M | re.S)


def test_python_snippets_run(capsys):
    """Every Python block in the README runs as written.

    The Quick Start promises code a reader can paste; running it here
    means a renamed helper or a changed return shape fails the suite
    instead of leaving the README wrong.
    """
    snippets = _python_snippets()
    assert snippets
    for snippet in snippets:
        exec(compile(snippet, "README.md", "exec"), {})
    assert capsys.readouterr().out.strip()


def test_every_example_is_listed():
    """The Examples table names every runnable script in examples/."""
    text = _text()
    scripts = sorted(p.name for p in (ROOT / "examples").glob("[0-9]*.py"))
    assert scripts
    missing = [name for name in scripts if f"examples/{name})" not in text]
    assert not missing, missing


def test_documentation_links_the_four_entry_points():
    """User manual, API reference, developer docs and the family map."""
    section = _text().split("## Documentation", 1)[1].split("\n## ", 1)[0]
    for target in (
        "https://sebastienrousseau.com/pain001-lsp/)",
        "https://sebastienrousseau.com/pain001-lsp/api.html)",
        "/DEVELOPMENT.md)",
        "(#the-pain001-lsp-ecosystem)",
    ):
        assert target in section, target


#: Root Markdown the manual includes from docs/, so its links are absolute.
INCLUDED = ["README.md", "ARCHITECTURE.md", "DEVELOPMENT.md"]


@pytest.mark.parametrize("name", INCLUDED)
def test_repository_links_resolve(name):
    """Every link into this repository's main branch names a real path.

    Links are absolute so they work on PyPI and in the Sphinx manual,
    which includes these files from docs/; a renamed file must not leave
    one dangling. The manual's link check skips these URLs (a file added
    on a branch is not on main yet), so this test is their check.
    """
    base = "https://github.com/sebastienrousseau/pain001-lsp/"
    text = (ROOT / name).read_text(encoding="utf-8")
    paths = re.findall(
        re.escape(base) + r"(?:blob|tree)/main/([^)\"#\s]+)", text
    )
    assert paths
    missing = [p for p in paths if not (ROOT / p).exists()]
    assert not missing, missing
