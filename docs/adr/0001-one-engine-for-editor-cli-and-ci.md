<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# 0001. One engine for the editor, the CLI and CI

- **Status:** Accepted
- **Date:** 2026-09-18 (practised since the first release; written down today)
- **Deciders:** maintainer

## Context

An editor could get its own validation rules, tuned for speed and
incremental checking. The core library already carries the JSON Schema,
the identifier checks and the scheme rulebooks.

## Options considered

1. A separate rule set in the server, fast and incremental, drifting
   from the core with every release.
2. Delegate every check to the core's public API and accept its cost;
   the editor never disagrees with the CLI or the CI gate.

## Decision

Option 2. A diagnostic the editor shows and the CLI does not is worse
than a slower diagnostic; the server is a thin adapter over the same
engine the rest of the suite uses.

## Consequences

The server pins the core at its own version (the suite's lockstep
floor). Benchmarks guard that diagnostics still scale linearly on large
batches; the schema is loaded once per message type and cached.
