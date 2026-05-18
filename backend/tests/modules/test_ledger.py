"""Ledger double-entry validation tests."""

import pytest
from pydantic import ValidationError

from app.modules.ledger.schemas import EntryIn, TransactionCreate


def _tx(entries):
    return TransactionCreate(
        description="Test",
        occurred_at="2026-01-01T12:00:00",
        module="mz",
        currency="MZN",
        entries=entries,
    )


def test_balanced_entries_pass():
    import uuid

    account_a = uuid.uuid4()
    account_b = uuid.uuid4()
    tx = _tx(
        [
            EntryIn(account_id=account_a, direction="debit", amount="100.0000"),
            EntryIn(account_id=account_b, direction="credit", amount="100.0000"),
        ]
    )
    assert tx.entries[0].amount + tx.entries[1].amount > 0


def test_unbalanced_entries_raise():
    import uuid

    with pytest.raises(ValidationError, match="balance"):
        _tx(
            [
                EntryIn(account_id=uuid.uuid4(), direction="debit", amount="100.0000"),
                EntryIn(account_id=uuid.uuid4(), direction="credit", amount="50.0000"),
            ]
        )


def test_single_entry_raise():
    with pytest.raises(ValidationError):
        _tx([EntryIn(account_id=__import__("uuid").uuid4(), direction="debit", amount="100.0000")])


def test_health_endpoint():
    """Smoke test — verifies the app imports without errors."""
    from app.main import app

    assert app.title == "Mphondo API"
