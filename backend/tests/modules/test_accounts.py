"""Account schema validation and endpoint routing tests."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.accounts.schemas import AccountCreate, AccountOut, AccountUpdate

# ── Schema tests ────────────────────────────────────────────────────────────


def test_account_create_valid():
    data = AccountCreate(
        name="Cuenta Corriente",
        account_type="bank_es",
        currency="EUR",
        module_context="es",
    )
    assert data.name == "Cuenta Corriente"
    assert data.currency == "EUR"


def test_account_create_mpesa():
    data = AccountCreate(
        name="M-Pesa",
        account_type="mpesa",
        currency="MZN",
        module_context="mz",
        phone="+258841234567",
    )
    assert data.phone == "+258841234567"


def test_account_update_partial():
    update = AccountUpdate(name="Renamed")
    dumped = update.model_dump(exclude_none=True)
    assert dumped == {"name": "Renamed"}
    assert "currency" not in dumped


def test_account_out_serialization():
    acc = AccountOut(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test",
        account_type="bank_es",
        currency="EUR",
        module_context="es",
        balance=Decimal("1234.56"),
        is_active=True,
    )
    assert acc.balance == Decimal("1234.56")


# ── Endpoint routing tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_accounts_returns_empty(client):
    with patch("app.modules.accounts.service.list_accounts", new=AsyncMock(return_value=[])):
        resp = await client.get("/api/v1/accounts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_account_calls_service(client):
    account_id = uuid.uuid4()
    fake = {
        "id": str(account_id),
        "user_id": str(uuid.uuid4()),
        "name": "M-Pesa",
        "account_type": "mpesa",
        "currency": "MZN",
        "module_context": "mz",
        "balance": "0.0000",
        "iban": None,
        "phone": "+258841234567",
        "color": None,
        "icon": None,
        "is_active": True,
    }
    with patch("app.modules.accounts.service.create_account", new=AsyncMock(return_value=fake)):
        resp = await client.post(
            "/api/v1/accounts",
            json={
                "name": "M-Pesa",
                "account_type": "mpesa",
                "currency": "MZN",
                "module_context": "mz",
                "phone": "+258841234567",
            },
        )
    assert resp.status_code == 201
    assert resp.json()["name"] == "M-Pesa"


@pytest.mark.asyncio
async def test_update_account_not_found(client):
    with patch("app.modules.accounts.service.update_account", new=AsyncMock(return_value=None)):
        resp = await client.patch(
            f"/api/v1/accounts/{uuid.uuid4()}",
            json={"name": "Renamed"},
        )
    assert resp.status_code == 404
