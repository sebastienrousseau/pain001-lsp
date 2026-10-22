# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Coverage-guided fuzzing of the document handlers with Atheris.

The server re-reads the whole document on every keystroke, so anything an
editor can hold reaches these functions. Each input becomes a message type
and a document, either raw text or a JSON array built from fuzzed
records, and goes through the JSON and CSV diagnostics, the record
locators, formatting, the outline and the quick-fix. Each must answer with
a list and never raise; anything else is a crash libFuzzer reports and
minimises.

Run (Linux x86_64, Python 3.12)::

    pip install --require-hashes -r requirements/fuzz.txt
    pip install --no-deps -e .
    python fuzz/fuzz_documents.py -max_total_time=60
"""

import json
import sys
from types import SimpleNamespace

import atheris

with atheris.instrument_imports():
    import pain001_lsp.server as srv

# Real message types, so validation is reached as well as rejected.
MESSAGE_TYPES = ("pain.001.001.03", "pain.001.001.09", "pain.008.001.02", "")
FIELDS = ("id", "payment_id", "debtor_account_IBAN", "creditor_agent_BIC")


class _Workspace:
    """The one document every handler asks for."""

    def __init__(self, source: str) -> None:
        self._document = SimpleNamespace(source=source)

    def get_text_document(self, uri: str) -> SimpleNamespace:
        return self._document


def _records(fdp: atheris.FuzzedDataProvider) -> list[object]:
    out: list[object] = []
    for _ in range(fdp.ConsumeIntInRange(0, 3)):
        record: dict[str, object] = {}
        for _ in range(fdp.ConsumeIntInRange(0, 5)):
            key = fdp.PickValueInList(list(FIELDS))
            key += fdp.ConsumeUnicodeNoSurrogates(4)
            record[key] = fdp.PickValueInList(
                [
                    None,
                    fdp.ConsumeBool(),
                    fdp.ConsumeInt(8),
                    fdp.ConsumeUnicodeNoSurrogates(40),
                ]
            )
        out.append(record)
    return out


def _document(fdp: atheris.FuzzedDataProvider) -> str:
    if fdp.ConsumeBool():
        return fdp.ConsumeUnicodeNoSurrogates(4096)
    return json.dumps(_records(fdp), indent=fdp.PickValueInList([None, 2]))


def test_one_input(data: bytes) -> None:
    """Drive every document handler with one fuzzer input."""
    fdp = atheris.FuzzedDataProvider(data)
    message_type = fdp.PickValueInList(list(MESSAGE_TYPES))
    text = _document(fdp)
    ls = SimpleNamespace(workspace=_Workspace(text))
    params = SimpleNamespace(
        text_document=SimpleNamespace(uri="file:///fuzz.json"),
        range=SimpleNamespace(
            start=SimpleNamespace(line=fdp.ConsumeIntInRange(0, 50))
        ),
    )
    for result in (
        srv.compute_diagnostics(text, message_type),
        srv.compute_diagnostics_csv(text, message_type),
        srv._record_line_offsets(text),
        srv._record_close_positions(text),
        srv.formatting(ls, params),
        srv.document_symbol(ls, params),
        srv.code_action(ls, params),
    ):
        if not isinstance(result, list):
            raise TypeError(f"handler returned {type(result).__name__}")


def main() -> None:
    """Hand the harness to libFuzzer."""
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
