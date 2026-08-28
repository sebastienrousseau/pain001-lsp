#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""How long the editor waits for diagnostics.

A language server is not measured in throughput. It is measured against a
person typing. The client recomputes diagnostics on every change, so what
matters is a single question: **does the answer come back before the user
notices?**

Two thresholds are worth naming, and the table marks both:

* **~16 ms** — one frame. Under this, diagnostics feel instantaneous;
  squiggles move with the cursor.
* **~100 ms** — the limit of "the system is reacting instantly". Past it
  the editor feels laggy on every keystroke, and past a few hundred
  milliseconds people start turning the extension off.

Measured across document sizes, because a payment-data document is not one
record — a real one is hundreds, and the file only ever grows while
somebody is editing it.

Also measured: **completion and hover**, which are called on demand rather
than on every change but block the UI while they run, and the **malformed
path**, which is the state a document spends most of its life in while
being typed. A linter that is fast on valid input and slow on invalid
input is slow exactly when the editor calls it most.

Run::

    python benches/bench_diagnostics.py
    python benches/bench_diagnostics.py --json
    python benches/bench_diagnostics.py --quick     # what CI runs

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped compiling against the
current API fails the build instead of rotting into a file that reads as
verified and is not.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from functools import partial
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pain001_lsp.server as lsp_server  # noqa: E402

FRAME_MS = 16.0
INSTANT_MS = 100.0

_RECORD = {
    "id": "MSG-0001",
    "date": "2026-01-15T10:30:00",
    "nb_of_txs": 1,
    "ctrl_sum": 100.00,
    "initiator_name": "Acme Embedded Finance Ltd",
    "payment_information_id": "PMT-INFO-0001",
    "payment_method": "TRF",
    "batch_booking": False,
    "service_level_code": "SEPA",
    "requested_execution_date": "2026-01-20",
    "debtor_name": "Acme Embedded Finance Ltd",
    "debtor_account_IBAN": "DE89370400440532013000",
    "debtor_agent_BIC": "DEUTDEFFXXX",
    "charge_bearer": "SLEV",
    "payment_id": "PAY-0001",
    "payment_amount": 100.00,
    "currency": "EUR",
    "creditor_agent_BIC": "NWBKGB2LXXX",
    "creditor_name": "National Westminster Bank",
    "creditor_account_IBAN": "GB29NWBK60161331926819",
    "remittance_information": "Invoice 0001",
}


def build(records: int) -> str:
    """A document carrying ``records`` valid payment records."""
    rows = []
    for i in range(records):
        row = dict(_RECORD)
        row["payment_id"] = f"PAY-{i:05d}"
        rows.append(row)
    return json.dumps(rows, indent=2)


def corrupt(text: str) -> str:
    """The same document mid-edit: a quote not yet closed."""
    return text.replace('"currency"', '"currency', 1)


def diagnose(text: str) -> list:
    return lsp_server.compute_diagnostics(text)


# Passed as callables rather than wrapped in lambdas: CodeQL flags a
# lambda that only forwards to a callable, and it is right -- the wrapper
# adds a frame and says nothing. `hover_text` takes an argument, so it
# gets a partial rather than a lambda for the same reason.
ON_DEMAND = [
    ("completion_items", lsp_server.completion_items),
    ("hover_text", partial(lsp_server.hover_text, "debtor_agent_BIC")),
]


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator here; the mean follows
    whatever else the machine is doing. A language server's worst case
    matters too, but the floor is what tells you whether the design can be
    responsive at all.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def _verdict(ms: float) -> str:
    if ms <= FRAME_MS:
        return "instant"
    if ms <= INSTANT_MS:
        return "fine"
    return "LAGGY"


def measure(size: int, repeats: int) -> dict:
    valid = build(size)
    broken = corrupt(valid)
    good = _best(lambda: diagnose(valid), repeats)
    bad = _best(lambda: diagnose(broken), repeats)
    return {
        "size": size,
        "bytes": len(valid),
        "valid_ms": good * 1e3,
        "malformed_ms": bad * 1e3,
        "verdict": _verdict(good * 1e3),
    }


def run(quick: bool) -> dict:
    sizes = [1, 25] if quick else [1, 25, 100, 500]
    repeats = 3 if quick else 7
    rows = [measure(n, repeats) for n in sizes]
    ondemand = []
    for name, call in ON_DEMAND:
        ondemand.append({"call": name, "ms": _best(call, repeats) * 1e3})
    return {"diagnostics": rows, "on_demand": ondemand}


def render(results: dict) -> None:
    print("diagnostics — what the editor waits for on every keystroke")
    print(
        f"{'records':>10}{'KiB':>8}{'valid ms':>10}"
        f"{'malformed ms':>14}{'verdict':>10}"
    )
    for row in results["diagnostics"]:
        print(
            f"{row['size']:>10}{row['bytes'] / 1024:>8.1f}"
            f"{row['valid_ms']:>10.2f}{row['malformed_ms']:>14.2f}"
            f"{row['verdict']:>10}"
        )
    print(
        f"\n  instant = under {FRAME_MS:.0f} ms (one frame), "
        f"fine = under {INSTANT_MS:.0f} ms, LAGGY above it.\n"
        "  The malformed column is the state a document spends most of its\n"
        "  life in while somebody is typing. If it is much slower than the\n"
        "  valid column, the linter is slowest exactly when the editor\n"
        "  calls it most."
    )
    rows = results["diagnostics"]
    largest = rows[-1]
    if largest["size"] and largest["valid_ms"]:
        per = largest["valid_ms"] / largest["size"]
        budget = int(INSTANT_MS / per) if per else 0
        # Two decimals renders a fast server as "0.00 ms", which reads as
        # a broken measurement rather than a good result.
        shown = f"{per:.2f}" if per >= 0.01 else f"{per:.4f}"
        print(
            f"\n  Cost is about {shown} ms per record, so the editor "
            f"stops feeling instant at roughly **{budget} records** and "
            f"stops feeling attached to the keyboard well before that.\n"
            f"  That number is the one to watch: it is a budget, not a "
            f"score, and it tells you the document size this server is "
            f"actually usable on."
        )
    if largest["valid_ms"] > INSTANT_MS:
        print(
            f"\n  At {largest['size']} the editor waits "
            f"{largest['valid_ms']:.0f} ms per change."
        )

    print("\non demand — called by a keystroke, but not by every keystroke")
    print(f"{'call':>18}{'ms':>10}{'verdict':>10}")
    for row in results["on_demand"]:
        print(f"{row['call']:>18}{row['ms']:>10.3f}{_verdict(row['ms']):>10}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="small sizes, as CI runs"
    )
    args = parser.parse_args()

    results = run(quick=args.quick)
    if args.json:
        json.dump(results, sys.stdout, indent=1)
        print()
    else:
        render(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
