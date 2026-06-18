"""Shared fixtures for the pain001-lsp test suite."""

import pytest

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


@pytest.fixture
def sample_record() -> dict:
    """A complete payment record satisfying the pain.001.001.09 schema."""
    return dict(_RECORD)
