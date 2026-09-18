<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# 0002. Speak stdio only

- **Status:** Accepted
- **Date:** 2026-09-18 (practised since the first release; written down today)
- **Deciders:** maintainer

## Context

LSP servers can listen on TCP or WebSocket as well as stdio. Editors
launch a stdio server as a child process; a listening socket is a
network surface on a payments workstation.

## Options considered

1. Offer TCP as well, for remote or containerised editors; a socket to
   harden, TLS to manage, a port to document.
2. stdio only through pygls; the editor owns the process lifetime.

## Decision

Option 2. No listener, no port, no TLS; the editor starts and stops
the server, and the same binary works in every LSP client that can
spawn a process.

## Consequences

`main()` calls `server.start_io()` and nothing else. The stdio
end-to-end test spawns the real server as a subprocess and completes
the initialize handshake; a remote-editing setup uses the editor's own
remote mechanism, not a server socket.
