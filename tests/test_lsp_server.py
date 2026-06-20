# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the pain001 Language Server Protocol server.

These exercise the pure helper functions directly (no server I/O required)
plus the thin LSP handler glue via a workspace stub, so the suite covers
every branch of ``pain001_lsp.server`` without touching a real client.
"""

import json
from types import SimpleNamespace
from typing import Any

import pytest

pytest.importorskip("pygls")

from lsprotocol import types as lsp  # noqa: E402

import pain001_lsp.server as lsp_server  # noqa: E402


# ---------------------------------------------------------------------------
# Test doubles: a workspace + language-server stub that records publishes
# ---------------------------------------------------------------------------
class _StubDoc:
    """In-memory ``TextDocument`` replacement for handler tests."""

    def __init__(self, source: str, word: str | None = None) -> None:
        """Initialise with the document ``source`` and a hover-test ``word``."""
        self.source = source
        self._word = word

    def word_at_position(self, position: Any) -> str | None:
        """Return the canned word the test supplied (or ``None``)."""
        return self._word


class _StubWorkspace:
    """Minimal ``Workspace`` replacement returning a single document."""

    def __init__(self, source: str, word: str | None = None) -> None:
        """Wrap ``source`` and the optional hover ``word`` into a stub doc."""
        self._doc = _StubDoc(source, word)

    def get_text_document(self, uri: str) -> _StubDoc:
        """Return the wrapped stub document regardless of ``uri``."""
        return self._doc


class _StubLS:
    """Stand-in for ``pygls.lsp.server.LanguageServer`` used by handlers."""

    def __init__(self, source: str, word: str | None = None) -> None:
        """Initialise the stub workspace and the published-diagnostic log."""
        self.workspace = _StubWorkspace(source, word)
        self.published: list[tuple[str, list[lsp.Diagnostic]]] = []

    def publish_diagnostics(
        self, uri: str, diagnostics: list[lsp.Diagnostic]
    ) -> None:
        """Record the diagnostic batch the handler tried to publish."""
        self.published.append((uri, diagnostics))


def _did_open_params(uri: str = "file:///x.json") -> SimpleNamespace:
    """Build a minimal ``DidOpenTextDocumentParams`` stand-in."""
    return SimpleNamespace(text_document=SimpleNamespace(uri=uri))


def _did_change_params(uri: str = "file:///x.json") -> SimpleNamespace:
    """Build a minimal ``DidChangeTextDocumentParams`` stand-in."""
    return SimpleNamespace(text_document=SimpleNamespace(uri=uri))


def _hover_params(
    uri: str = "file:///x.json", line: int = 0, character: int = 0
) -> SimpleNamespace:
    """Build a minimal ``HoverParams`` stand-in."""
    return SimpleNamespace(
        text_document=SimpleNamespace(uri=uri),
        position=SimpleNamespace(line=line, character=character),
    )


def _code_action_params(
    uri: str = "file:///x.json", line: int | None = None
) -> SimpleNamespace:
    """Build a minimal ``CodeActionParams`` stand-in.

    When ``line`` is set, the params include a ``range.start.line``
    pointing at the cursor (used by the multi-record code action to
    pick which record to fix).
    """
    range_obj = None
    if line is not None:
        range_obj = SimpleNamespace(
            start=SimpleNamespace(line=line, character=0)
        )
    return SimpleNamespace(
        text_document=SimpleNamespace(uri=uri), range=range_obj
    )


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def test_valid_records_produce_no_diagnostics(sample_record):
    """A complete, valid record yields no diagnostics."""
    text = json.dumps([sample_record])
    diagnostics = lsp_server.compute_diagnostics(text)
    assert diagnostics == []


def test_single_dict_is_treated_as_one_record(sample_record):
    """A single record object (not wrapped in a list) is accepted."""
    text = json.dumps(sample_record)
    assert lsp_server.compute_diagnostics(text) == []


def test_missing_required_fields_produce_error(sample_record):
    """A record missing required fields produces at least one error."""
    record = dict(sample_record)
    record.pop("id", None)
    record.pop("debtor_account_IBAN", None)
    text = json.dumps([record])
    diagnostics = lsp_server.compute_diagnostics(text)
    errors = [d for d in diagnostics if d["severity"] == "error"]
    assert len(errors) >= 1


def test_bad_identifier_produces_diagnostic(sample_record):
    """A record with an invalid IBAN/BIC is flagged."""
    record = dict(sample_record)
    record["debtor_account_IBAN"] = "INVALID!"
    text = json.dumps([record])
    diagnostics = lsp_server.compute_diagnostics(text)
    assert any("debtor_account_IBAN" in d["message"] for d in diagnostics)
    assert len(diagnostics) >= 1


def test_malformed_json_produces_single_diagnostic():
    """Malformed JSON yields exactly one syntax diagnostic."""
    diagnostics = lsp_server.compute_diagnostics("[{not json}]")
    assert len(diagnostics) == 1
    assert diagnostics[0]["severity"] == "error"
    assert "Invalid JSON" in diagnostics[0]["message"]


def test_unsupported_message_type_diagnostic_only():
    """Passing an unsupported message type returns a single error."""
    diagnostics = lsp_server.compute_diagnostics(
        json.dumps([{}]), message_type="pain.999.999.99"
    )
    assert len(diagnostics) == 1
    assert "Invalid XML message type" in diagnostics[0]["message"]


# ---------------------------------------------------------------------------
# Completion + hover
# ---------------------------------------------------------------------------
def test_completion_items_include_field_and_message_type():
    """Completion includes a known field and at least one message type."""
    labels = {item["label"] for item in lsp_server.completion_items()}
    assert "id" in labels
    assert any(label.startswith("pain.") for label in labels)


def test_hover_text_known_and_unknown():
    """Hover returns a description for a known field and None otherwise."""
    text = lsp_server.hover_text("debtor_account_IBAN")
    assert text
    assert isinstance(text, str)
    assert lsp_server.hover_text("nope") is None


# ---------------------------------------------------------------------------
# Quick-fix helpers
# ---------------------------------------------------------------------------
def test_missing_required_fields_lists_absent_keys(sample_record):
    """A record missing two required fields surfaces both names."""
    record = dict(sample_record)
    record.pop("id", None)
    record.pop("debtor_account_IBAN", None)
    missing = lsp_server.missing_required_fields(record)
    assert "id" in missing
    assert "debtor_account_IBAN" in missing


def test_missing_required_fields_empty_when_complete(sample_record):
    """A complete record reports no missing fields."""
    assert lsp_server.missing_required_fields(sample_record) == []


def test_build_insert_text_emits_json_fragments(sample_record):
    """Generated snippet uses type-appropriate placeholders."""
    snippet = lsp_server.build_insert_text(
        ["id", "nb_of_txs", "batch_booking", "ctrl_sum"]
    )
    assert snippet.startswith(",\n")
    assert '"id": ""' in snippet
    assert '"nb_of_txs": 0' in snippet
    assert '"batch_booking": false' in snippet
    assert '"ctrl_sum": 0' in snippet


def test_build_insert_text_empty_for_no_fields():
    """No missing fields yields the empty string."""
    assert lsp_server.build_insert_text([]) == ""


def test_record_close_position_locates_outer_brace():
    """``_record_close_position`` walks past nested braces."""
    text = '[\n  {\n    "id": "x",\n    "nested": {"k": "v"}\n  }\n]'
    pos = lsp_server._record_close_position(text)
    assert pos is not None
    # The first top-level record's closing brace lives on the line with
    # only ``  }``; column 2 is the brace itself.
    assert pos.line == 4
    assert pos.character == 2


# ---------------------------------------------------------------------------
# Server module wiring
# ---------------------------------------------------------------------------
def test_server_and_main_exist():
    """The module exposes a ``server`` object and a callable ``main``."""
    assert lsp_server.server is not None
    assert callable(lsp_server.main)


def test_initialize_honours_message_type_override():
    """``initializationOptions.messageType`` overrides the default type."""
    from lsprotocol import types as lsp

    original = lsp_server._message_type
    try:
        params = lsp.InitializeParams(
            capabilities=lsp.ClientCapabilities(),
            initialization_options={"messageType": "pain.001.001.11"},
        )
        lsp_server.on_initialize(lsp_server.server, params)
        assert lsp_server._current_message_type() == "pain.001.001.11"
    finally:
        lsp_server._message_type = original


def test_initialize_ignores_unknown_message_type():
    """An unsupported override leaves the default in place."""
    original = lsp_server._message_type
    try:
        params = lsp.InitializeParams(
            capabilities=lsp.ClientCapabilities(),
            initialization_options={"messageType": "pain.999.999.99"},
        )
        lsp_server.on_initialize(lsp_server.server, params)
        assert lsp_server._current_message_type() == original
    finally:
        lsp_server._message_type = original


def test_initialize_ignores_non_dict_initialization_options():
    """Non-dict ``initializationOptions`` is tolerated (and left untouched)."""
    original = lsp_server._message_type
    try:
        params = lsp.InitializeParams(
            capabilities=lsp.ClientCapabilities(),
            initialization_options=[1, 2, 3],
        )
        lsp_server.on_initialize(lsp_server.server, params)
        assert lsp_server._current_message_type() == original
    finally:
        lsp_server._message_type = original


def test_initialize_handles_missing_initialization_options():
    """No ``initializationOptions`` at all -> default message type."""
    original = lsp_server._message_type
    try:
        params = lsp.InitializeParams(
            capabilities=lsp.ClientCapabilities(),
            initialization_options=None,
        )
        lsp_server.on_initialize(lsp_server.server, params)
        assert lsp_server._current_message_type() == original
    finally:
        lsp_server._message_type = original


# ---------------------------------------------------------------------------
# Pure-helper edge cases (private fallbacks + brace walker)
# ---------------------------------------------------------------------------
def test_identifier_valid_returns_true_for_unknown_kind():
    """``_identifier_valid`` treats unknown kinds as a pass-through."""
    assert lsp_server._identifier_valid("lei", "5493001KJTIIGC8Y1R12") is True


def test_normalise_records_returns_empty_for_scalar():
    """A scalar (neither dict nor list) is normalised to an empty list."""
    assert lsp_server._normalise_records(42) == []
    assert lsp_server._normalise_records("string") == []


def test_record_line_offsets_handles_escaped_chars_and_strings():
    """Walker tracks line numbers around escapes and newlines in strings."""
    text = '[\n  {"a": "x\\"y", "b": "line\\nbreak"},\n  {}\n]'
    offsets = lsp_server._record_line_offsets(text)
    # Two top-level records starting on lines 1 and 2 (zero-indexed).
    assert offsets == [1, 2]


def test_record_line_offsets_handles_nested_objects():
    """Nested ``{`` does not get registered as a new top-level record."""
    text = '[\n  {"a": {"b": 1}},\n  {}\n]'
    offsets = lsp_server._record_line_offsets(text)
    assert offsets == [1, 2]


def test_record_line_offsets_handles_literal_newline_in_string():
    """A literal newline inside a string advances the line counter."""
    # JSON disallows literal newlines, but the walker is heuristic and is
    # asked to tolerate the kind of in-flight edits an editor sees.
    text = '[\n  {"a": "first\nsecond"}\n]'
    offsets = lsp_server._record_line_offsets(text)
    assert offsets == [1]


def test_record_close_position_returns_none_when_no_close():
    """Documents without a closing brace fall through to the final return."""
    assert lsp_server._record_close_position("[{") is None


def test_record_close_position_handles_escapes_and_unclosed_string():
    """Walker handles escape sequences inside the record."""
    # Closing brace is at the end of line 0, just before the trailing ']'.
    text = '[{"x": "a\\"b"}]'
    pos = lsp_server._record_close_position(text)
    assert pos is not None
    assert pos.line == 0


def test_compute_diagnostics_flags_non_object_record_in_list():
    """A list whose element isn't an object yields a typed diagnostic."""
    diagnostics = lsp_server.compute_diagnostics(json.dumps([42]))
    assert any("non-object" in d["message"] for d in diagnostics)


def test_compute_diagnostics_handles_empty_list():
    """An explicit empty list yields the "expected JSON array" error."""
    diagnostics = lsp_server.compute_diagnostics("[]")
    assert len(diagnostics) == 1
    assert "Expected a JSON array" in diagnostics[0]["message"]


def test_compute_diagnostics_handles_scalar_root():
    """A scalar JSON value is treated as an empty record list."""
    diagnostics = lsp_server.compute_diagnostics('"hello"')
    assert len(diagnostics) == 1
    assert "Expected a JSON array" in diagnostics[0]["message"]


def test_completion_items_handle_field_without_description(monkeypatch):
    """A schema property with no ``description`` falls back to ``""``."""

    def fake_load(_mt: str) -> dict:
        return {"properties": {"weird_field": {}}}

    monkeypatch.setattr(lsp_server, "_load_schema", fake_load)
    items = lsp_server.completion_items()
    weird = next(item for item in items if item["label"] == "weird_field")
    assert weird["detail"] == ""


def test_hover_text_returns_none_for_field_without_description(monkeypatch):
    """A bundled field with no ``description`` produces no hover text."""

    def fake_load(_mt: str) -> dict:
        return {"properties": {"empty_field": {}}}

    monkeypatch.setattr(lsp_server, "_load_schema", fake_load)
    assert lsp_server.hover_text("empty_field") is None


def test_build_insert_text_unknown_type_defaults_to_string(monkeypatch):
    """A field with a non-standard JSON Schema ``type`` falls back to ``""``."""

    def fake_load(_mt: str) -> dict:
        return {"properties": {"odd": {"type": "geo"}}}

    monkeypatch.setattr(lsp_server, "_load_schema", fake_load)
    snippet = lsp_server.build_insert_text(["odd"])
    assert '"odd": ""' in snippet


def test_to_lsp_diagnostics_maps_severity_with_default():
    """Unknown severity strings fall back to ``Error``."""
    out = lsp_server._to_lsp_diagnostics(
        [
            {
                "line": 0,
                "character": 0,
                "severity": "info",
                "message": "x",
            }
        ]
    )
    assert out[0].severity == lsp.DiagnosticSeverity.Error


# ---------------------------------------------------------------------------
# LSP handler glue (via the stub workspace)
# ---------------------------------------------------------------------------
def test_did_open_publishes_diagnostics(sample_record):
    """``did_open`` invokes the validation+publish pipeline."""
    ls = _StubLS(json.dumps([sample_record]))
    lsp_server.did_open(ls, _did_open_params())
    assert len(ls.published) == 1
    _uri, diagnostics = ls.published[0]
    assert diagnostics == []


def test_did_change_publishes_diagnostics_for_broken_doc():
    """``did_change`` re-validates and reports schema errors as diagnostics."""
    ls = _StubLS(json.dumps([{}]))
    lsp_server.did_change(ls, _did_change_params())
    assert ls.published
    _uri, diagnostics = ls.published[0]
    assert diagnostics
    assert diagnostics[0].source == "pain001-lsp"


def test_completion_returns_field_and_message_type_items():
    """The completion handler surfaces both fields and message types."""
    ls = _StubLS("")
    result = lsp_server.completion(ls, SimpleNamespace())
    labels = {item.label for item in result.items}
    assert "id" in labels
    assert any(label.startswith("pain.") for label in labels)


def test_hover_returns_description_for_known_field():
    """Hovering a known field surfaces its schema description."""
    ls = _StubLS("doc", word="debtor_account_IBAN")
    result = lsp_server.hover(ls, _hover_params())
    assert result is not None
    assert isinstance(result.contents, str)


def test_hover_returns_none_when_no_word_under_cursor():
    """Hover bails when the workspace reports no word at the position."""
    ls = _StubLS("doc", word=None)
    assert lsp_server.hover(ls, _hover_params()) is None


def test_hover_returns_none_for_unknown_field():
    """A word that isn't a schema field yields no hover."""
    ls = _StubLS("doc", word="nope")
    assert lsp_server.hover(ls, _hover_params()) is None


def test_code_action_returns_empty_for_invalid_json():
    """Malformed JSON yields no quick-fix (the diagnostic alone is enough)."""
    ls = _StubLS("{not json}")
    assert lsp_server.code_action(ls, _code_action_params()) == []


def test_code_action_returns_empty_for_empty_array():
    """An empty array has no first record to fix."""
    ls = _StubLS("[]")
    assert lsp_server.code_action(ls, _code_action_params()) == []


def test_code_action_returns_empty_for_non_object_record():
    """A list of scalars has no first record to fix."""
    ls = _StubLS("[42]")
    assert lsp_server.code_action(ls, _code_action_params()) == []


def test_code_action_returns_empty_for_complete_record(sample_record):
    """A complete record exposes no missing fields and so no quick-fix."""
    ls = _StubLS(json.dumps([sample_record]))
    assert lsp_server.code_action(ls, _code_action_params()) == []


def test_code_action_offers_quick_fix_for_incomplete_record():
    """An incomplete record yields a single "Add missing fields" action."""
    ls = _StubLS(json.dumps([{"id": "x"}]))
    actions = lsp_server.code_action(ls, _code_action_params())
    assert len(actions) == 1
    action = actions[0]
    assert action.kind == lsp.CodeActionKind.QuickFix
    assert "missing required field" in action.title
    edits = action.edit.changes["file:///x.json"]
    assert len(edits) == 1
    assert '"date":' in edits[0].new_text


def test_code_action_returns_empty_when_close_position_missing(monkeypatch):
    """An unfindable close position aborts the quick-fix.

    A real JSON document that parses cleanly will always have a closing
    brace, so the only realistic way to reach this defensive branch is to
    monkeypatch the brace walker.
    """
    ls = _StubLS(json.dumps([{"id": "x"}]))
    monkeypatch.setattr(lsp_server, "_record_close_positions", lambda _src: [])
    assert lsp_server.code_action(ls, _code_action_params()) == []


def test_code_action_returns_empty_when_snippet_empty(monkeypatch):
    """A no-op snippet (empty placeholders) suppresses the quick-fix."""
    ls = _StubLS('[{"id": "x"}]')
    monkeypatch.setattr(
        lsp_server, "missing_required_fields", lambda *_a, **_k: ["id"]
    )
    monkeypatch.setattr(lsp_server, "build_insert_text", lambda *_a, **_k: "")
    assert lsp_server.code_action(ls, _code_action_params()) == []


# ---------------------------------------------------------------------------
# Multi-record quick-fix
# ---------------------------------------------------------------------------
def test_code_action_targets_second_record_when_cursor_is_on_it(
    sample_record,
):
    """A cursor on record #2 fixes record #2, not record #1."""
    incomplete = {"id": "second-only"}
    source = json.dumps([sample_record, incomplete], indent=2)
    # Find the line where the second record opens.
    second_line = next(
        idx
        for idx, line in enumerate(source.splitlines())
        if "second-only" in line
    )
    ls = _StubLS(source)
    actions = lsp_server.code_action(ls, _code_action_params(line=second_line))
    assert len(actions) == 1
    edit = actions[0].edit.changes["file:///x.json"][0]
    # The edit's anchor is on a line at or below the second record's
    # opening, never on line 0 (which would be the first record).
    assert edit.range.start.line >= second_line


def test_code_action_falls_back_to_first_record_without_cursor(
    sample_record,
):
    """Without a ``range`` on the params, the first record is the target."""
    incomplete = {"id": "second-only"}
    ls = _StubLS(json.dumps([sample_record, incomplete], indent=2))
    # First record is complete -> no missing fields -> no actions.
    assert lsp_server.code_action(ls, _code_action_params()) == []


def test_code_action_returns_empty_when_cursor_index_overflows(
    sample_record,
):
    """A cursor past the last record yields no quick-fix."""
    ls = _StubLS(json.dumps([sample_record], indent=2))
    actions = lsp_server.code_action(ls, _code_action_params(line=9_999))
    # Single record is complete -> no missing fields anyway.
    assert actions == []


def test_code_action_returns_empty_when_close_index_overflows(monkeypatch):
    """An index past the close-position list aborts the quick-fix."""
    ls = _StubLS(json.dumps([{"id": "x"}]))
    monkeypatch.setattr(lsp_server, "_record_close_positions", lambda _src: [])
    monkeypatch.setattr(
        lsp_server, "missing_required_fields", lambda *_a, **_k: ["x"]
    )
    assert lsp_server.code_action(ls, _code_action_params()) == []


def test_record_index_at_position_returns_zero_for_empty_text():
    """An empty document maps any cursor to record 0."""
    assert (
        lsp_server._record_index_at_position(
            "", lsp.Position(line=10, character=0)
        )
        == 0
    )


def test_record_index_at_position_breaks_when_offset_exceeds_target():
    """The walker stops as soon as a record offset overshoots the cursor."""
    text = "[\n  {},\n  {},\n  {}\n]"
    # Cursor on line 2 means record #2 (zero-indexed: index=1). The walker
    # must enter the ``else: break`` branch when it sees record #3.
    idx = lsp_server._record_index_at_position(
        text, lsp.Position(line=2, character=0)
    )
    assert idx == 1


def test_record_index_at_position_returns_zero_for_no_records():
    """A document with no top-level records maps any cursor to 0."""
    assert (
        lsp_server._record_index_at_position(
            "[]", lsp.Position(line=0, character=0)
        )
        == 0
    )


def test_record_index_at_position_returns_zero_for_no_cursor():
    """A missing cursor defaults to the first record."""
    text = "[\n  {},\n  {}\n]"
    assert lsp_server._record_index_at_position(text, None) == 0


def test_record_close_positions_collects_every_record():
    """The multi-record walker returns one close brace per top-level record."""
    text = '[\n  {"a": 1},\n  {"b": 2}\n]'
    closes = lsp_server._record_close_positions(text)
    assert len(closes) == 2


# ---------------------------------------------------------------------------
# workspace/didChangeConfiguration
# ---------------------------------------------------------------------------
def test_workspace_did_change_configuration_with_nested_section():
    """A ``{"pain001": {"messageType": ...}}`` payload switches the type."""
    original = lsp_server._message_type
    try:
        params = SimpleNamespace(
            settings={"pain001": {"messageType": "pain.001.001.11"}}
        )
        lsp_server.on_did_change_configuration(lsp_server.server, params)
        assert lsp_server._current_message_type() == "pain.001.001.11"
    finally:
        lsp_server._message_type = original


def test_workspace_did_change_configuration_with_flat_payload():
    """A top-level ``{"messageType": ...}`` payload is also honoured."""
    original = lsp_server._message_type
    try:
        params = SimpleNamespace(settings={"messageType": "pain.001.001.10"})
        lsp_server.on_did_change_configuration(lsp_server.server, params)
        assert lsp_server._current_message_type() == "pain.001.001.10"
    finally:
        lsp_server._message_type = original


def test_workspace_did_change_configuration_ignores_unknown_type():
    """An unsupported override is silently ignored."""
    original = lsp_server._message_type
    try:
        params = SimpleNamespace(settings={"messageType": "pain.999.999.99"})
        lsp_server.on_did_change_configuration(lsp_server.server, params)
        assert lsp_server._current_message_type() == original
    finally:
        lsp_server._message_type = original


def test_workspace_did_change_configuration_ignores_non_dict_settings():
    """Non-dict ``settings`` falls through without raising."""
    original = lsp_server._message_type
    try:
        params = SimpleNamespace(settings=["wrong", "shape"])
        lsp_server.on_did_change_configuration(lsp_server.server, params)
        assert lsp_server._current_message_type() == original
    finally:
        lsp_server._message_type = original


def test_workspace_did_change_configuration_ignores_non_dict_section():
    """A ``pain001`` key with a non-dict value is tolerated."""
    original = lsp_server._message_type
    try:
        params = SimpleNamespace(settings={"pain001": "pain.001.001.11"})
        lsp_server.on_did_change_configuration(lsp_server.server, params)
        assert lsp_server._current_message_type() == original
    finally:
        lsp_server._message_type = original


# ---------------------------------------------------------------------------
# Examples kept honest
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# CSV linting (ported from pain001.lsp.diagnostics)
# ---------------------------------------------------------------------------
def test_compute_diagnostics_csv_clean_input_yields_no_diagnostics():
    """A header-only CSV with all required columns produces no diagnostics."""
    header = (
        "id,date,nb_of_txs,ctrl_sum,payment_amount,currency,"
        "debtor_name,debtor_account_IBAN,creditor_name,"
        "creditor_account_IBAN"
    )
    assert lsp_server.compute_diagnostics_csv(header + "\n") == []


def test_compute_diagnostics_csv_flags_missing_required_column():
    """Missing a required column surfaces a ``missing-column`` diagnostic."""
    header = "id,currency,debtor_name,creditor_name\n"
    diagnostics = lsp_server.compute_diagnostics_csv(header)
    assert diagnostics
    assert any(d["code"] == "missing-column" for d in diagnostics)
    assert all("col_start" in d and "col_end" in d for d in diagnostics)


def test_compute_diagnostics_csv_empty_input_returns_empty_list():
    """An empty document yields no diagnostics."""
    assert lsp_server.compute_diagnostics_csv("") == []


def test_is_csv_uri_dispatches_by_suffix():
    """The dispatcher recognises ``.csv`` (case-insensitive)."""
    assert lsp_server._is_csv_uri("file:///x.csv") is True
    assert lsp_server._is_csv_uri("file:///x.CSV") is True
    assert lsp_server._is_csv_uri("file:///x.json") is False


def test_did_open_routes_csv_uri_to_csv_engine():
    """A ``.csv`` URI runs the CSV engine, not the JSON one."""
    csv_text = "id,currency,debtor_name,creditor_name\n"
    ls = _StubLS(csv_text)
    lsp_server.did_open(ls, _did_open_params(uri="file:///x.csv"))
    assert ls.published
    _uri, diagnostics = ls.published[0]
    # The CSV engine reports ``missing-column`` codes; the JSON engine
    # never sets a code, so the presence of one proves the dispatch.
    assert any(
        getattr(d, "code", None) == "missing-column" for d in diagnostics
    )


@pytest.mark.parametrize(
    "module_path",
    [
        "examples/01_lsp_helpers.py",
        "examples/02_quick_fix.py",
        "examples/03_configure_message_type.py",
    ],
)
def test_example_scripts_run_without_error(module_path, capsys):
    """Each example script imports and runs end-to-end."""
    import importlib.util
    import sys
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / module_path
    spec = importlib.util.spec_from_file_location(
        f"_example_{path.stem}", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    original_default = lsp_server._message_type
    try:
        spec.loader.exec_module(module)
        main_fn = getattr(module, "main", None)
        if callable(main_fn):
            main_fn()
    finally:
        sys.modules.pop(spec.name, None)
        lsp_server._message_type = original_default
    assert capsys.readouterr().out


# ---------------------------------------------------------------------------
# Formatting (textDocument/formatting)
# ---------------------------------------------------------------------------
def _formatting_params(uri: str = "file:///x.json") -> SimpleNamespace:
    """Build a minimal ``DocumentFormattingParams`` stand-in."""
    return SimpleNamespace(text_document=SimpleNamespace(uri=uri))


def test_formatting_reflows_compact_json_into_pretty_form(sample_record):
    """A compact one-liner gets re-emitted as indented JSON + newline."""
    source = json.dumps([sample_record])
    ls = _StubLS(source)
    edits = lsp_server.formatting(ls, _formatting_params())
    assert len(edits) == 1
    formatted = edits[0].new_text
    assert formatted.endswith("\n")
    assert "\n  " in formatted  # contains the two-space indent.
    assert json.loads(formatted) == [sample_record]


def test_formatting_returns_empty_list_for_already_formatted_doc(
    sample_record,
):
    """No edit is offered when the document is already pretty-printed."""
    source = json.dumps([sample_record], indent=2, ensure_ascii=False) + "\n"
    ls = _StubLS(source)
    assert lsp_server.formatting(ls, _formatting_params()) == []


def test_formatting_returns_empty_list_for_malformed_json():
    """Malformed JSON is left untouched - diagnostics surface the error."""
    ls = _StubLS("[{not json}]")
    assert lsp_server.formatting(ls, _formatting_params()) == []


def test_formatting_handles_empty_document():
    """An empty document yields no edits (malformed JSON path)."""
    ls = _StubLS("")
    assert lsp_server.formatting(ls, _formatting_params()) == []


def test_formatting_edit_range_spans_entire_document(sample_record):
    """The edit range covers the document end so the replace overwrites all."""
    source = json.dumps([sample_record])
    ls = _StubLS(source)
    edits = lsp_server.formatting(ls, _formatting_params())
    assert edits[0].range.start.line == 0
    assert edits[0].range.start.character == 0
    assert edits[0].range.end.line == 0
    assert edits[0].range.end.character == len(source)


# ---------------------------------------------------------------------------
# Document symbols (textDocument/documentSymbol)
# ---------------------------------------------------------------------------
def _document_symbol_params(
    uri: str = "file:///x.json",
) -> SimpleNamespace:
    """Build a minimal ``DocumentSymbolParams`` stand-in."""
    return SimpleNamespace(text_document=SimpleNamespace(uri=uri))


def test_document_symbol_returns_one_per_record(sample_record):
    """Each top-level record becomes one ``DocumentSymbol``."""
    record_b = dict(sample_record)
    record_b["id"] = "MSG-0002"
    record_b["payment_id"] = "PAY-0002"
    source = json.dumps([sample_record, record_b], indent=2)
    ls = _StubLS(source)
    symbols = lsp_server.document_symbol(ls, _document_symbol_params())
    assert len(symbols) == 2
    assert {s.name for s in symbols} == {"MSG-0001", "MSG-0002"}
    assert {s.detail for s in symbols} == {"PAY-0001", "PAY-0002"}


def test_document_symbol_uses_placeholder_when_id_missing(sample_record):
    """Records without an ``id`` get a positional placeholder name."""
    record = dict(sample_record)
    record.pop("id", None)
    record.pop("payment_id", None)
    source = json.dumps([record], indent=2)
    ls = _StubLS(source)
    symbols = lsp_server.document_symbol(ls, _document_symbol_params())
    assert len(symbols) == 1
    assert symbols[0].name == "<record 1>"
    assert symbols[0].detail == ""


def test_document_symbol_returns_empty_for_malformed_json():
    """Malformed JSON yields no symbols - diagnostics handle the error."""
    ls = _StubLS("[{not json}]")
    assert lsp_server.document_symbol(ls, _document_symbol_params()) == []


def test_document_symbol_returns_empty_for_empty_array():
    """An empty array yields no symbols."""
    ls = _StubLS("[]")
    assert lsp_server.document_symbol(ls, _document_symbol_params()) == []


def test_document_symbol_marks_non_dict_records_with_placeholder(
    monkeypatch,
):
    """Non-dict records (e.g. lists) still get a positional placeholder."""
    # The real scanner only tracks ``{`` / ``}``, so non-dict records
    # never produce a close-position naturally. Inject one via the
    # helpers to exercise the placeholder branch end-to-end.
    monkeypatch.setattr(
        lsp_server, "_normalise_records", lambda parsed: [[1, 2, 3]]
    )
    monkeypatch.setattr(lsp_server, "_record_line_offsets", lambda text: [0])
    monkeypatch.setattr(
        lsp_server,
        "_record_close_positions",
        lambda text: [lsp.Position(line=0, character=8)],
    )
    ls = _StubLS("[[1, 2, 3]]")
    symbols = lsp_server.document_symbol(ls, _document_symbol_params())
    assert len(symbols) == 1
    assert symbols[0].name == "<record 1>"
    assert symbols[0].detail == ""
    assert symbols[0].kind == lsp.SymbolKind.Object


def test_document_symbol_range_spans_full_record(sample_record):
    """The symbol range covers the record opening through its closing brace."""
    source = json.dumps([sample_record], indent=2)
    ls = _StubLS(source)
    symbols = lsp_server.document_symbol(ls, _document_symbol_params())
    # Pretty-printed JSON wraps the array, so the record itself starts
    # on line 1 (after the opening ``[``); the close brace is later.
    assert symbols[0].range.start.line >= 0
    assert symbols[0].range.end.line > symbols[0].range.start.line
    assert symbols[0].selection_range == symbols[0].range


def test_document_symbol_stops_when_close_positions_missing(
    sample_record, monkeypatch
):
    """If close-position scanning drops a record, the loop bails gracefully."""
    monkeypatch.setattr(lsp_server, "_record_close_positions", lambda text: [])
    source = json.dumps([sample_record], indent=2)
    ls = _StubLS(source)
    assert lsp_server.document_symbol(ls, _document_symbol_params()) == []


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------
def test_main_starts_the_pygls_server(monkeypatch):
    """``main()`` is a thin wrapper around ``server.start_io``."""
    calls: list[tuple] = []

    def fake_start_io(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(lsp_server.server, "start_io", fake_start_io)
    lsp_server.main()
    assert calls == [((), {})]
