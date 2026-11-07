# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Arguments of a ``workspace/executeCommand`` request, as one dict."""

from __future__ import annotations

from typing import Any


def command_options(args: tuple[Any, ...]) -> dict[str, Any]:
    """The first ``executeCommand`` argument as a dict, else empty."""
    if args and isinstance(args[0], dict):
        return dict(args[0])
    return {}
