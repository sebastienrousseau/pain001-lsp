# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Load the input JSON Schema the core bundles for a message type."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pain001.constants import SCHEMAS_DIR, valid_xml_types

DEFAULT_MESSAGE_TYPE = "pain.001.001.09"


@lru_cache(maxsize=16)
def _load_schema(message_type: str) -> dict[str, Any]:
    """Load the bundled JSON schema for ``message_type``.

    Cached. The schemas ship inside the installed package and are
    read-only, so re-reading and re-parsing them cannot pick up a
    change — it only repeats work. That mattered because every
    interactive entry point here goes through this function, and an
    editor calls them on each keystroke: completion, hover and the
    missing-field check were each paying a disk read plus a JSON parse
    to answer from data that never changes.

    ``pain001.xml.validate_via_xsd`` caches its compiled XSD the same
    way and for the same reason.

    Raises ``ValueError`` if the message type is unsupported or no schema
    file is bundled (for example, ``pain.001.001.12`` and
    ``pain.008.001.02`` are listed but only ship XML templates).
    """
    if message_type not in valid_xml_types:
        raise ValueError(f"Invalid XML message type: {message_type}")
    path = Path(SCHEMAS_DIR) / f"{message_type}.schema.json"
    if (
        not path.is_file()
    ):  # pragma: no cover - all bundled types ship a schema
        raise ValueError(f"No JSON Schema bundled for {message_type}")
    with path.open("r", encoding="utf-8") as fh:
        loaded: dict[str, Any] = json.load(fh)
        return loaded
