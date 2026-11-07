# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The VS Code extension offers what the server accepts.

Kept out of tests/test_lsp_server.py: mutation testing copies only the
package, its examples and the handler tests into its working tree, and
this test reads the extension's manifest.
"""

import json
from pathlib import Path

import pain001_lsp.server as lsp_server


def test_vscode_setting_offers_every_supported_message_type():
    """The extension's messageType enum matches what the server accepts."""
    manifest = (
        Path(__file__).resolve().parents[1]
        / "editors"
        / "vscode"
        / "package.json"
    )
    setting = json.loads(manifest.read_text(encoding="utf-8"))["contributes"][
        "configuration"
    ]["properties"]["pain001.messageType"]
    assert setting["enum"] == list(lsp_server.valid_xml_types)


def test_vscode_selects_files_by_the_configured_pattern():
    """Users can narrow the JSON files the extension sends to the server.

    The selector used to be every JSON file; the server now skips
    documents that are not payment records, and ``pain001.filePattern``
    lets a workspace narrow the selection further (``**/*.pain.json``).
    """
    root = Path(__file__).resolve().parents[1] / "editors" / "vscode"
    manifest = json.loads((root / "package.json").read_text(encoding="utf-8"))
    setting = manifest["contributes"]["configuration"]["properties"][
        "pain001.filePattern"
    ]
    assert setting["type"] == "string"
    assert setting["default"] == "**/*.json"
    source = (root / "src" / "extension.ts").read_text(encoding="utf-8")
    assert 'config.get<string>("filePattern", "**/*.json")' in source
    assert '{ scheme: "file", language: "json", pattern }' in source
