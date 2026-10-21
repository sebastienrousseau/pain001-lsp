<!-- SPDX-License-Identifier: Apache-2.0 OR MIT -->

# Benchmarks

The client recomputes diagnostics on every change, so the measure is how
long the editor waits, against two thresholds: 16 ms (one frame) and
100 ms (the limit of "reacting instantly"). The number to read is the
budget: how many records a document can hold and still stay under 100 ms.

## Method

`benches/bench_diagnostics.py` times `compute_diagnostics` on valid
documents of 1, 25, 100 and 500 records and on a malformed document, and
times the on-demand calls (completion, hover, `pain001.corpus.list`):

```sh
python benches/bench_diagnostics.py           # the table
python benches/bench_diagnostics.py --json    # machine-readable
python benches/bench_diagnostics.py --quick   # what CI runs
```

Nothing asserts a threshold: wall-clock time is not comparable between
machines. CI runs `--quick` so the benchmark keeps working against the
current API.

## Results

Recorded for 0.0.64 (2026-08-29): 0.08 ms per record, a budget of roughly
1,200 records.

Run on 2026-10-21 for 0.0.74 (Apple A18 Pro, Python 3.12.15, pain001
0.0.72) on a machine with a load average above 30, so the absolute numbers
are inflated; the shape is what carries over:

| Records | KiB | Valid document | Malformed document |
| ---: | ---: | ---: | ---: |
| 1 | 0.8 | 0.27 ms | 0.01 ms |
| 25 | 19.2 | 4.85 ms | 0.01 ms |
| 100 | 76.9 | 16.91 ms | 0.01 ms |
| 500 | 384.3 | 113.85 ms | 0.01 ms |

| On-demand call | Time |
| :--- | ---: |
| `completion_items` | 0.013 ms |
| `hover_text` | under 0.001 ms |
| `pain001.corpus.list` (market) | 16.2 ms |

Cost grows linearly with the number of records, and a document that does
not parse returns at once, which matters because that is the state a
document is in for most of the time someone is typing.
