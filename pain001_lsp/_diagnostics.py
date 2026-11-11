# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""Record-level diagnostics and their ``lsprotocol`` form.

Each record is validated against the message type's JSON Schema, and
every present IBAN or BIC field with the pain001 validators; the results
are plain dicts, which :func:`_to_lsp_diagnostics` maps to
``lsprotocol`` diagnostics for publishing.
"""

from __future__ import annotations

from typing import Any

from jsonschema import Draft7Validator
from lsprotocol import types as lsp
from pain001.validation import validate_bic, validate_iban

from pain001_lsp._parsing import _diagnostic

# Flat-record fields whose values are financial identifiers, mapped to the
# identifier kind understood by the pain001 validators.
_IDENTIFIER_FIELDS = {
    "debtor_account_IBAN": "iban",
    "creditor_account_IBAN": "iban",
    "charge_account_IBAN": "iban",
    "debtor_agent_BIC": "bic",
    "creditor_agent_BIC": "bic",
    "forwarding_agent_BIC": "bic",
}


def _identifier_valid(kind: str, value: str) -> bool:
    """Return whether ``value`` is a valid IBAN or BIC."""
    if kind == "iban":
        ok, _ = validate_iban(value, strict=False)
    elif kind == "bic":
        ok, _ = validate_bic(value, strict=False)
    else:
        return True
    return bool(ok)


def _schema_diagnostics(
    records: list[Any], schema: dict[str, Any], line_for: Any
) -> list[dict]:
    """Validate each record against ``schema``, in record order."""
    diagnostics: list[dict] = []
    validator = Draft7Validator(schema)
    for row, record in enumerate(records):
        if not isinstance(record, dict):
            diagnostics.append(
                _diagnostic(
                    line_for(row),
                    "Expected a record object (got non-object).",
                )
            )
            continue
        for err in sorted(
            validator.iter_errors(record), key=lambda e: list(e.path)
        ):
            path = ".".join(str(p) for p in err.path)
            prefix = f"{path}: " if path else ""
            diagnostics.append(
                _diagnostic(line_for(row), f"{prefix}{err.message}")
            )
    return diagnostics


def _identifier_diagnostics(records: list[Any], line_for: Any) -> list[dict]:
    """Warn about every present IBAN or BIC value that does not validate."""
    diagnostics: list[dict] = []
    for row, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        for field, kind in _IDENTIFIER_FIELDS.items():
            value = record.get(field)
            if not value or not isinstance(value, str):
                continue
            if not _identifier_valid(kind, value):
                diagnostics.append(
                    _diagnostic(
                        line_for(row),
                        f"{field}: {value!r} is not a valid {kind.upper()}.",
                        severity="warning",
                    )
                )
    return diagnostics


_SEVERITY = {
    "error": lsp.DiagnosticSeverity.Error,
    "warning": lsp.DiagnosticSeverity.Warning,
    "information": lsp.DiagnosticSeverity.Information,
    "hint": lsp.DiagnosticSeverity.Hint,
}


def _to_lsp_diagnostics(raw: list[dict]) -> list[lsp.Diagnostic]:
    """Map plain diagnostic dicts to ``lsprotocol`` ``Diagnostic`` objects."""
    diagnostics: list[lsp.Diagnostic] = []
    for item in raw:
        line = item["line"]
        col_start = item.get("col_start", item["character"])
        col_end = item.get("col_end", col_start)
        diagnostics.append(
            lsp.Diagnostic(
                range=lsp.Range(
                    start=lsp.Position(line=line, character=col_start),
                    end=lsp.Position(line=line, character=col_end),
                ),
                message=item["message"],
                severity=_SEVERITY.get(
                    item["severity"], lsp.DiagnosticSeverity.Error
                ),
                source="pain001-lsp",
                code=item.get("code"),
            )
        )
    return diagnostics
