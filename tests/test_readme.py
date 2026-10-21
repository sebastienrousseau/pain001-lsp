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
    assert text.index('src=".github/demo.gif"') > text.index("height=")
    assert (ROOT / ".github" / "demo.gif").is_file()


def test_local_links_resolve():
    """Every relative link in the README points at a tracked path."""
    targets = re.findall(r"\]\((?!https?:|#|mailto:)([^)#\s]+)", _text())
    missing = [t for t in targets if not (ROOT / t).exists()]
    assert not missing, missing
