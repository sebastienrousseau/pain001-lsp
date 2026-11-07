# Copyright (C) 2023-2026 Pain001. All rights reserved.
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The two faces commands, called through their pure helpers.

pain001 0.0.78 projects a pain.001 document into another standard's
JSON shape (UK Open Banking, Berlin Group NextGenPSD2, ISO 20022 element
names) with a loss report of what the target cannot carry. An editor
reaches it through ``workspace/executeCommand`` with
``pain001.faces.list`` and ``pain001.faces.project``, sending the open
buffer's text as ``xml``.

With a pain001 that predates faces the commands answer with an
``error`` payload, and this script shows that path too.

Run::

    python examples/05_faces_commands.py
"""

from __future__ import annotations

from pain001_lsp import _faces
from pain001_lsp.server import corpus_get


def main() -> None:
    """List the faces, project a corpus file, and show a refusal."""
    listed = _faces.faces_list()
    if "error" in listed:
        print("faces unavailable:", listed["error"])
        return
    print(
        f"{_faces.FACES_LIST_COMMAND} ->",
        ", ".join(face["name"] for face in listed["faces"]),
    )

    xml = corpus_get(
        {"scenario_id": "de.sepa.sct-salary", "version": "pain.001.001.09"}
    )["xml"]
    result = _faces.faces_project({"xml": xml, "face": "berlin_group"})
    report = result["loss_report"]
    print(
        f"{_faces.FACES_PROJECT_COMMAND} (berlin_group) -> "
        f"{report['mapped_count']} of {report['total_source_elements']} "
        "source elements carried"
    )

    refused = _faces.faces_project({"xml": xml, "face": "uk_open_banking"})
    print("refused:", refused["error"])
    print("Faces commands example completed.")


if __name__ == "__main__":
    main()
