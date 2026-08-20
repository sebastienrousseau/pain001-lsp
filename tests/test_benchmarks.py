"""Performance benchmarks for the language server.

Latency here is not a batch concern. An editor recomputes diagnostics on
every change, so the cost of one pass is paid in front of a person
waiting for underlines to update.

``test_diagnostics_typical_document`` is the measurement, recorded so
the number lands in a CI artifact.

``test_diagnostics_scale_linearly`` is the regression guard. It compares
the engine against itself at two sizes rather than using a wall-clock
threshold, so a slow or noisy runner scales both halves equally and the
ratio holds.

A note on what the ratio looks like, because it is not the ~4x that a
4x-size step would suggest. Diagnostics are sublinear over this range
(4x the rows costs about 2.4x the time), because a fixed per-call cost
dominates at typical document sizes. The ceiling is still set against
the quadratic case, which is what would actually hurt: per-row work that
rescans the document.

Profiling this path also found that the dominant per-cell cost lives in
`pain001.lsp.diagnostics._cell_span` in the core, which re-sums the
lengths of preceding cells for every cell -- O(columns^2) per row. That
is a core issue, not one this package can fix, and it is recorded here
so the benchmark's shape is not mistaken for the engine being
intrinsically slow.
"""

from __future__ import annotations

import time

import pytest

from pain001_lsp.server import compute_diagnostics_csv

HEADER = (
    "id,date,nb_of_txs,initiator_name,payment_information_id,"
    "payment_method,batch_booking,requested_execution_date,debtor_name,"
    "debtor_account_IBAN,debtor_agent_BIC,charge_bearer,payment_id,"
    "payment_amount,currency,ctrl_sum,creditor_agent_BIC,creditor_name,"
    "creditor_account_IBAN,remittance_information"
)

#: Ratio ceiling for a 4x increase in row count. Measured behaviour is
#: sublinear (~2.4x); quadratic would be ~16x.
MAX_SCALING_RATIO = 8.0


def build_csv(rows: int) -> str:
    """Build a valid ``rows``-row pain.001 payment CSV."""
    lines = [HEADER]
    for index in range(rows):
        lines.append(
            f"{index},2026-08-20T10:00:00,1,Initiator,PMT-INFO,TRF,false,"
            f"2026-08-21,Debtor,DE89370400440532013000,BANKDEFFXXX,DEBT,"
            f"TX{index},100.00,EUR,100.00,SPUEDE2UXXX,Creditor,"
            f"GB29NWBK60161331926819,INVOICE {index}"
        )
    return "\n".join(lines) + "\n"


def _best_of(text: str, rounds: int = 5) -> float:
    """Fastest diagnostics pass over ``text`` in seconds."""
    compute_diagnostics_csv(text)
    timings = []
    for _ in range(rounds):
        started = time.perf_counter()
        compute_diagnostics_csv(text)
        timings.append(time.perf_counter() - started)
    return min(timings)


@pytest.mark.benchmark
def test_diagnostics_typical_document(benchmark) -> None:
    """Benchmark one diagnostics pass over a typical document."""
    text = build_csv(200)

    diagnostics = benchmark(compute_diagnostics_csv, text)

    # The document is valid, so a clean pass is the expected result --
    # and asserting it means a benchmark over a document that failed to
    # parse cannot masquerade as a fast one.
    assert diagnostics == []


@pytest.mark.benchmark
def test_diagnostics_scale_linearly() -> None:
    """4x the rows must not cost ~16x the time."""
    small = _best_of(build_csv(500))
    large = _best_of(build_csv(2000))

    ratio = large / small
    assert ratio < MAX_SCALING_RATIO, (
        f"diagnostics over 2000 rows took {ratio:.1f}x the time of 500 "
        f"({large * 1000:.0f}ms vs {small * 1000:.0f}ms); measured "
        f"behaviour is sublinear at ~2.4x, so this suggests per-row work "
        f"that rescans the document"
    )
