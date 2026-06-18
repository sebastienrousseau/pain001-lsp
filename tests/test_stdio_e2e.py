# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""End-to-end stdio regression for ``pain001-lsp``.

The fast suite drives the LSP handlers in-process via a workspace stub,
but only a real subprocess exercises the LSP JSON-RPC framing and the
``server.start_io`` plumbing. This test sends the minimum traffic an
editor needs (``initialize`` → ``initialized`` → ``shutdown`` →
``exit``) and asserts the server returns capabilities advertising the
features pain001-lsp ships.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

pytest.importorskip("pygls")


def _pain001_pythonpath() -> str:
    """Locate pain001 on disk (sibling repo in dev, site-packages in CI)."""
    sibling = Path(__file__).resolve().parents[2] / "pain001"
    if sibling.is_dir():
        return str(sibling)
    return ""


async def _round_trip_initialize() -> dict:
    """Spawn ``pain001-lsp`` and complete an LSP initialize handshake."""
    env = os.environ.copy()
    repo_root = str(Path(__file__).resolve().parents[1])
    extras = [repo_root]
    sibling = _pain001_pythonpath()
    if sibling:
        extras.append(sibling)
    env["PYTHONPATH"] = os.pathsep.join(extras) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "pain001_lsp.server",
        env=env,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def send(payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        assert proc.stdin is not None
        proc.stdin.write(header + body)
        await proc.stdin.drain()

    async def read_message() -> dict:
        assert proc.stdout is not None
        content_length = 0
        while True:
            line = await proc.stdout.readline()
            if not line or line in (b"\r\n", b"\n"):
                break
            if line.lower().startswith(b"content-length:"):
                content_length = int(line.split(b":", 1)[1].strip())
        body = await proc.stdout.readexactly(content_length)
        return json.loads(body.decode("utf-8"))

    try:
        await send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "processId": None,
                    "rootUri": None,
                    "capabilities": {},
                    "initializationOptions": {
                        "messageType": "pain.001.001.11"
                    },
                },
            }
        )
        init_reply = await asyncio.wait_for(read_message(), timeout=10)
        assert init_reply.get("id") == 1, init_reply

        await send({"jsonrpc": "2.0", "method": "initialized", "params": {}})

        await send(
            {"jsonrpc": "2.0", "id": 2, "method": "shutdown", "params": None}
        )
        shutdown_reply = await asyncio.wait_for(read_message(), timeout=10)
        assert shutdown_reply.get("id") == 2

        await send({"jsonrpc": "2.0", "method": "exit", "params": None})
        return init_reply
    finally:
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()


def test_pain001_lsp_subprocess_advertises_features():
    """Real subprocess + real LSP framing returns the expected capabilities."""
    init_reply = asyncio.run(
        asyncio.wait_for(_round_trip_initialize(), timeout=30)
    )
    capabilities = init_reply["result"]["capabilities"]
    # pygls exposes each registered feature in the capabilities map. We
    # only need to confirm the headline editor features are advertised.
    assert "completionProvider" in capabilities
    assert "hoverProvider" in capabilities
    assert "codeActionProvider" in capabilities
    assert capabilities.get("textDocumentSync") is not None
