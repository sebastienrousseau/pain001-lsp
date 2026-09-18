<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# 0003. Register handlers explicitly, not with decorators

- **Status:** Accepted
- **Date:** 2026-09-18 (practised since the first release; written down today)
- **Deciders:** maintainer

## Context

pygls handlers are conventionally declared with `@server.feature(...)`
and `@server.command(...)`. mutmut 3 never mutates a decorated
function, so the eleven handlers were outside mutation testing; a first
run produced no mutants for them.

## Options considered

1. Keep the decorators and accept that the handlers are untested by
   mutation; the score describes the helpers only.
2. Register the same functions by explicit calls after the definitions;
   the registered object, name, signature and order are identical.

## Decision

Option 2. The handlers are what the editor calls; a mutation score
that excludes them measures the wrong thing. The first honest run
scored 76.5 percent and exposed that no test pinned the diagnostics'
positions or messages; sixteen tests now do, and the score is gated.

## Consequences

A new handler is added as a plain function plus one registration line
in the block before `main()`. `mutation.yml` fails a pull request
below the floor in the Makefile. The stdio end-to-end test proves the
registrations still serve every feature.
