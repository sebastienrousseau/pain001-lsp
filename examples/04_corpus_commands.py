# Copyright (C) 2023-2026 Pain001. All rights reserved.
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The example-corpus commands an editor can execute.

pain001 ships a corpus of validated example files from 0.0.67. The
language server exposes it through ``workspace/executeCommand``:
``pain001.corpus.list`` lists the files (filter by kind, country and
message type) and ``pain001.corpus.get`` returns one file's XML with its
provenance record, so an editor can open a reference example beside the
data file being authored. The pure helpers ``corpus_list`` and
``corpus_get`` do the work; the command handlers are thin glue.

With a pain001 that predates the corpus the commands answer with an
``error`` payload instead of failing, and this script shows that path
too, so it runs against either library.

Run::

    python examples/04_corpus_commands.py
"""

from __future__ import annotations

from pain001_lsp.server import (
    CORPUS_GET_COMMAND,
    CORPUS_LIST_COMMAND,
    corpus_get,
    corpus_get_command,
    corpus_list,
    corpus_list_command,
)


def main() -> None:
    """Call the helpers and the command glue and print the results."""
    print("commands:", CORPUS_LIST_COMMAND, CORPUS_GET_COMMAND)
    listed = corpus_list({"kind": "market"})
    if "error" in listed:
        print("corpus unavailable:", listed["error"])
        assert "error" in corpus_get({"scenario_id": "x", "version": "y"})
        assert "error" in corpus_list_command(None)
        print("both commands return the same error payload; nothing raised")
        return

    print(f"corpus.list(kind=market) -> {listed['count']} files")
    first = listed["files"][0]
    print("  first:", first["scenario_id"], first["version"], first["country"])

    gb = corpus_list_command(None, {"kind": "market", "country": "gb"})
    assert all(f["country"] == "GB" for f in gb["files"])
    print(f"corpus.list(country=gb) via executeCommand -> {gb['count']} files")

    got = corpus_get_command(
        None,
        {"scenario_id": first["scenario_id"], "version": first["version"]},
    )
    assert got["xml"].startswith("<?xml")
    assert got["provenance"]["validation"]["xsd"]["errors"] == 0
    print(
        f"corpus.get -> {len(got['xml'])} characters of {first['version']}, "
        f"confidence {got['provenance']['provenance']['confidence']}"
    )

    missing = corpus_get({"version": first["version"]})
    assert "required" in missing["error"]
    print("corpus.get (no scenario_id) ->", missing["error"])
    print("Corpus commands example completed.")


if __name__ == "__main__":
    main()
