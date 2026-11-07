# Copyright (C) 2023-2026 Sebastien Rousseau.
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""The exact shape and position of what the editor is told.

Mutation testing showed the diagnostics' keys, positions and messages
were never pinned: a mutant that reported a JSON error one line off, or
renamed ``"line"`` to ``"LINE"``, passed every test. An editor would
have underlined the wrong row or nothing. These tests pin the contract
the editor reads: keys, line and character, severity, message wording,
LSP range conversion, record offsets through strings that contain
braces and escaped quotes, and completion detail text.
"""

from __future__ import annotations

import json

import pytest

pytest.importorskip("pygls")

from lsprotocol import types as lsp  # noqa: E402

import pain001_lsp.server as server  # noqa: E402

MT = server.DEFAULT_MESSAGE_TYPE
KEYS = {"line", "character", "severity", "message"}


def _record(**overrides: object) -> dict:
    base = {
        "id": "MSG-1",
        "date": "2026-09-18T09:00:00",
        "initiator_name": "Acme GmbH",
        "payment_information_id": "PMT-1",
        "payment_method": "TRF",
        "batch_booking": False,
        "requested_execution_date": "2026-09-19",
        "debtor_name": "Acme GmbH",
        "debtor_account_IBAN": "DE89370400440532013000",
        "debtor_agent_BIC": "COBADEFFXXX",
        "charge_bearer": "SLEV",
        "payment_id": "E2E-1",
        "payment_amount": 100.0,
        "currency": "EUR",
        "creditor_agent_BIC": "DEUTDEFFXXX",
        "creditor_name": "Beta AG",
        "creditor_account_IBAN": "DE02120300000000202051",
        "remittance_information": "Invoice 1",
    }
    base.update(overrides)
    return base


class TestJsonErrors:
    """A syntax error is reported once, at the character the parser stopped."""

    def test_position_and_message_are_exact(self):
        text = '[\n  {"id": 1,\n   "x": }\n]'
        assert server.compute_diagnostics(text) == [
            {
                "line": 2,
                "character": 8,
                "severity": "error",
                "message": "Invalid JSON: Expecting value",
            }
        ]

    def test_an_error_on_the_first_character_is_not_negative(self):
        (diag,) = server.compute_diagnostics("")
        assert set(diag) == KEYS
        assert (diag["line"], diag["character"]) == (0, 0)
        assert diag["severity"] == "error"
        assert diag["message"].startswith("Invalid JSON: ")

    def test_an_empty_batch_is_one_error_at_the_origin(self):
        assert server.compute_diagnostics("[]") == [
            {
                "line": 0,
                "character": 0,
                "severity": "error",
                "message": (
                    "Expected a JSON array of record objects "
                    "(or a single record object)."
                ),
            }
        ]

    def test_an_unknown_message_type_is_one_error_naming_it(self):
        (diag,) = server.compute_diagnostics("[{}]", "pain.999.001.01")
        assert set(diag) == KEYS
        assert (diag["line"], diag["character"], diag["severity"]) == (
            0,
            0,
            "error",
        )
        assert "pain.999.001.01" in diag["message"]


class TestRecordPositions:
    """Each diagnostic sits on the line its record opens on."""

    def test_schema_errors_carry_the_records_line_and_path(self):
        import json

        good = _record()
        bad = _record()
        del bad["creditor_name"]
        text = "[\n" + json.dumps(good) + ",\n\n" + json.dumps(bad) + "\n]"
        diags = server.compute_diagnostics(text)
        assert diags, "the second record is missing a required field"
        for d in diags:
            assert set(d) == KEYS
            assert d["line"] == 3
            assert d["character"] == 0
            assert d["severity"] == "error"
        assert any("creditor_name" in d["message"] for d in diags)

    def test_braces_and_escaped_quotes_inside_strings_do_not_shift_lines(self):
        text = (
            "[\n"
            '  {"remittance_information": "brace { and \\" quote } here",\n'
            '   "note": "backslash \\\\ then \\"{\\""},\n'
            '  {"id": "second"},\n'
            "\n"
            '  {"id": "third"}\n'
            "]"
        )
        assert server._record_line_offsets(text) == [1, 3, 5]

    def test_close_positions_name_the_closing_brace_of_each_record(self):
        text = '[\n  {"a": "x}y"},\n  {"b": {"nested": 1}}\n]'
        positions = server._record_close_positions(text)
        assert [(p.line, p.character) for p in positions] == [(1, 13), (2, 21)]

    def test_a_non_object_record_is_reported_on_its_own_line(self):
        text = "[\n  42\n]"
        (diag,) = server.compute_diagnostics(text)
        assert diag == {
            "line": 0,
            "character": 0,
            "severity": "error",
            "message": "Expected a record object (got non-object).",
        }


class TestIdentifierWarnings:
    """Identifier checks are warnings, worded with the field and the value."""

    def test_invalid_iban_message_is_exact(self):
        import json

        text = json.dumps(
            [_record(debtor_account_IBAN="DE00000000000000000000")]
        )
        warnings = [
            d
            for d in server.compute_diagnostics(text)
            if d["severity"] == "warning"
        ]
        assert warnings == [
            {
                "line": 0,
                "character": 0,
                "severity": "warning",
                "message": (
                    "debtor_account_IBAN: 'DE00000000000000000000' "
                    "is not a valid IBAN."
                ),
            }
        ]

    def test_a_valid_batch_produces_nothing(self):
        import json

        assert server.compute_diagnostics(json.dumps([_record()])) == []


class TestLspConversion:
    """The raw dicts become LSP diagnostics with exact ranges."""

    def test_column_span_is_honoured(self):
        (d,) = server._to_lsp_diagnostics(
            [
                {
                    "line": 4,
                    "character": 0,
                    "col_start": 7,
                    "col_end": 19,
                    "severity": "warning",
                    "message": "m",
                    "code": "E42",
                }
            ]
        )
        assert (d.range.start.line, d.range.start.character) == (4, 7)
        assert (d.range.end.line, d.range.end.character) == (4, 19)
        assert d.severity is lsp.DiagnosticSeverity.Warning
        assert d.message == "m"
        assert d.source == "pain001-lsp"
        assert d.code == "E42"

    def test_without_a_span_the_range_is_a_point_at_the_character(self):
        (d,) = server._to_lsp_diagnostics(
            [{"line": 2, "character": 5, "severity": "error", "message": "m"}]
        )
        assert (d.range.start.line, d.range.start.character) == (2, 5)
        assert (d.range.end.line, d.range.end.character) == (2, 5)
        assert d.severity is lsp.DiagnosticSeverity.Error
        assert d.code is None

    def test_an_unknown_severity_word_falls_back_to_error(self):
        (d,) = server._to_lsp_diagnostics(
            [{"line": 0, "character": 0, "severity": "loud", "message": "m"}]
        )
        assert d.severity is lsp.DiagnosticSeverity.Error


class TestCompletionItems:
    """Field completions carry the schema's own description."""

    def test_a_described_field_carries_its_description(self):
        items = {i["label"]: i for i in server.completion_items(MT)}
        assert items["id"] == {
            "label": "id",
            "detail": "Message identification",
            "kind": "field",
        }

    def test_message_types_carry_their_human_names(self):
        items = {i["label"]: i for i in server.completion_items(MT)}
        assert items[MT]["detail"] == server.HUMAN_NAMES[MT]
        assert items[MT]["detail"] != MT
        assert items[MT]["kind"] == "field"

    def test_every_item_has_exactly_the_three_keys(self):
        for item in server.completion_items(MT):
            assert set(item) == {"label", "detail", "kind"}
            assert isinstance(item["detail"], str)


class _Doc:
    def __init__(self, source: str) -> None:
        self.source = source


class _Server:
    """Records what the publish path tells the editor about one document."""

    def __init__(self, source: str) -> None:
        self.workspace = self
        self._doc = _Doc(source)
        self.published: list[list[lsp.Diagnostic]] = []

    def get_text_document(self, uri: str) -> _Doc:
        return self._doc

    def text_document_publish_diagnostics(self, params) -> None:
        self.published.append(list(params.diagnostics))


def _published(text: str) -> list[lsp.Diagnostic]:
    ls = _Server(text)
    server._validate_and_publish(ls, "file:///w/doc.json")
    (diagnostics,) = ls.published
    return diagnostics


class TestOnlyPaymentDocumentsAreDiagnosed:
    """Editors send every JSON file; only payment records get diagnostics.

    The VS Code extension selected every JSON document, so package.json
    and tsconfig.json were told "'id' is a required property". A document
    that is neither an array of records nor an object naming a payment
    field is published with no diagnostics, which also clears old ones.
    """

    @pytest.mark.parametrize(
        "text",
        [
            '{"name": "x", "version": "1.0.0", "private": true}',
            '{"compilerOptions": {"strict": true}}',
            "{}",
            '"hello"',
            "42",
            "null",
            "",
            '{"name": "x",',
            '{"compilerOptions": {',
        ],
        ids=[
            "package-json",
            "tsconfig-json",
            "empty-object",
            "string",
            "number",
            "null",
            "empty-text",
            "broken-package-json",
            "broken-tsconfig-json",
        ],
    )
    def test_other_json_gets_no_diagnostics(self, text):
        assert _published(text) == []

    @pytest.mark.parametrize(
        "text",
        [
            "[{}]",
            "[]",
            "[42]",
            '{"id": "MSG-1"}',
            '{"name": "x", "currency": "EUR"}',
            '[{"id": ',
            '  {"id": "MSG-1",',
            '{"x": 1, "debtor_name": "A"',
        ],
        ids=[
            "empty-record",
            "empty-array",
            "array-of-non-records",
            "single-record",
            "one-payment-field-is-enough",
            "broken-array",
            "broken-single-record",
            "broken-record-later-field",
        ],
    )
    def test_payment_records_are_still_diagnosed(self, text):
        assert _published(text) != []

    def test_a_valid_record_object_is_clean(self):
        assert _published(json.dumps(_record())) == []

    def test_a_record_object_is_validated_like_an_array(self):
        text = json.dumps({"id": "MSG-1"})
        assert [d.message for d in _published(text)] == [
            d["message"] for d in server.compute_diagnostics(text, MT)
        ]

    def test_csv_documents_are_not_shape_checked(self):
        ls = _Server("not,a,payment\n")
        server._validate_and_publish(ls, "file:///w/doc.csv")
        (diagnostics,) = ls.published
        assert diagnostics != []

    def test_the_helper_never_raises_on_unparseable_text(self):
        assert _shape("[" * 100_000) is True
        assert _shape("{" * 100_000) is False

    def test_the_helper_reads_only_object_keys(self):
        assert _shape('{"x": "id"}') is False
        assert _shape('{"x": "id",') is False
        assert _shape('{"id" : 1') is True
        assert _shape('{"ID": 1}') is False

    def test_the_fields_come_from_the_message_type_schema(self):
        seen: list[str] = []

        def load(message_type: str) -> dict:
            seen.append(message_type)
            return {"properties": {"amount": {}}}

        assert server.is_payment_document('{"amount": 1}', "t", load)
        assert not server.is_payment_document('{"id": 1}', "t", load)
        assert seen == ["t", "t"]

    def test_without_a_schema_only_an_array_counts(self):
        def load(message_type: str) -> dict:
            raise ValueError(f"No JSON Schema bundled for {message_type}")

        assert server.is_payment_document("[{}]", "t", load) is True
        assert server.is_payment_document('{"id": 1}', "t", load) is False
        assert server.is_payment_document('{"id": 1', "t", load) is False

    def test_a_schema_without_properties_names_no_fields(self):
        def load(message_type: str) -> dict:
            return {}

        assert server.is_payment_document("[{}]", "t", load) is True
        assert server.is_payment_document('{"id": 1}', "t", load) is False

    def test_an_indented_broken_array_still_counts(self):
        assert _shape('\n  [{"x": ') is True


def _shape(text: str) -> bool:
    return server.is_payment_document(
        text, "t", lambda _mt: {"properties": {"id": {}}}
    )
