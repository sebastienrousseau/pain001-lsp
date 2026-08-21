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

A note on the ratio, because its shape changed. Diagnostics used to
measure *sublinear* over this range — 4x the rows cost about 2.4x the
time — which looked like a fixed per-call cost dominating. It was not:
`pain001.lsp.diagnostics._cell_span` in the core recomputed each cell's
span by re-splitting the line and re-summing every preceding cell, once
per cell, so the per-row work was quadratic in the column count and
swamped the row count entirely.

pain001 0.0.61 fixed that, and the numbers moved accordingly:

    500 rows    43.4ms -> 7.6ms   (5.7x)
    2000 rows  102.0ms -> 32.1ms  (3.2x)

The ratio is now 4.23x for 4x the rows, which is what linear looks like.
The ceiling below stays at 8: it is set against the quadratic case
(~16x), not against the current measurement, so it keeps room for a
noisy runner.
"""

from __future__ import annotations

import time

import pytest

from pain001_lsp.server import (
    _load_schema,
    completion_items,
    compute_diagnostics_csv,
    hover_text,
    missing_required_fields,
)

HEADER = (
    "id,date,nb_of_txs,initiator_name,payment_information_id,"
    "payment_method,batch_booking,requested_execution_date,debtor_name,"
    "debtor_account_IBAN,debtor_agent_BIC,charge_bearer,payment_id,"
    "payment_amount,currency,ctrl_sum,creditor_agent_BIC,creditor_name,"
    "creditor_account_IBAN,remittance_information"
)

#: Ratio ceiling for a 4x increase in row count. Measured behaviour is
#: linear (~4.2x) since pain001 0.0.61; quadratic would be ~16x.
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
        f"behaviour is linear at ~4.2x, so this suggests per-row work "
        f"that rescans the document"
    )


class TestInteractivePaths:
    """Completion, hover and the missing-field check.

    These are the per-keystroke paths. Diagnostics get recomputed on
    change; these get called while someone is typing, so what matters is
    that they do no avoidable work at all rather than that they finish
    within some budget.

    All three go through ``_load_schema``, which used to read and parse
    the bundled JSON schema from disk on every call. That was ~97% of
    each of them, and made all three measure identically at ~0.08ms —
    they were really measuring the same file read. Caching it took them
    to 0.003ms, 0.0002ms and 0.0004ms respectively (28x, 478x, 196x).
    """

    @pytest.mark.benchmark
    def test_completion_items(self, benchmark) -> None:
        """Benchmark building the completion list."""
        items = benchmark(completion_items)

        assert items
        assert all("label" in item for item in items)

    @pytest.mark.benchmark
    def test_missing_required_fields(self, benchmark) -> None:
        """Benchmark the missing-field check on a sparse record."""
        record = {"id": "1", "payment_amount": "100.00", "currency": "EUR"}

        missing = benchmark(missing_required_fields, record)

        assert missing, "a near-empty record must report missing fields"

    @pytest.mark.benchmark
    def test_the_schema_is_not_reread_per_call(self) -> None:
        """The schema load must stay cached.

        A wall-clock threshold is the wrong guard here: these calls are
        now microseconds, so any threshold loose enough to survive CI
        would not notice the cache being removed. The property that
        actually matters is that repeated calls do not touch the disk
        again, and ``lru_cache`` reports that directly.

        Written because removing the decorator is an easy, invisible
        regression: nothing would fail, editors would just get slower.
        """
        _load_schema.cache_clear()

        hover_text("debtor_account_IBAN")
        first = _load_schema.cache_info()

        for _ in range(50):
            hover_text("debtor_account_IBAN")
            completion_items()
            missing_required_fields({"id": "1"})

        later = _load_schema.cache_info()

        assert later.misses == first.misses, (
            f"_load_schema went to disk {later.misses - first.misses} extra "
            f"times across 150 interactive calls — the cache is gone, and "
            f"every keystroke is paying a file read and a JSON parse"
        )
        assert later.hits > first.hits
