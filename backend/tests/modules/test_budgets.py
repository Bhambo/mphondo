"""Budget schema validation and endpoint routing tests."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.modules.budgets.schemas import BudgetCreate, BudgetOut

# ── Schema tests ────────────────────────────────────────────────────────────


def test_budget_create_valid():
    data = BudgetCreate(
        category_id=uuid.uuid4(),
        amount=Decimal("500.00"),
        currency="EUR",
        period_year=2026,
        period_month=5,
    )
    assert data.amount == Decimal("500.00")
    assert data.alert_threshold == Decimal("0.80")


def test_budget_create_custom_alert():
    data = BudgetCreate(
        category_id=uuid.uuid4(),
        amount=Decimal("200"),
        currency="MZN",
        period_year=2026,
        period_month=1,
        alert_threshold=Decimal("0.90"),
    )
    assert data.alert_threshold == Decimal("0.90")


def test_budget_create_invalid_amount():
    with pytest.raises(ValidationError):
        BudgetCreate(
            category_id=uuid.uuid4(),
            amount=Decimal("-50"),
            currency="EUR",
            period_year=2026,
            period_month=5,
        )


def test_budget_out_with_spending():
    b = BudgetOut(
        id=uuid.uuid4(),
        category_id=uuid.uuid4(),
        amount=Decimal("500"),
        currency="EUR",
        period_year=2026,
        period_month=5,
        alert_threshold=Decimal("0.80"),
        spent=Decimal("320"),
        remaining=Decimal("180"),
    )
    assert b.remaining == Decimal("180")


# ── Endpoint routing tests ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_budgets_empty(client):
    with patch("app.modules.budgets.service.list_budgets", new=AsyncMock(return_value=[])):
        resp = await client.get("/api/v1/budgets?year=2026&month=5")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_budgets_with_data(client):
    cat_id = uuid.uuid4()
    budget_id = uuid.uuid4()
    fake = [
        {
            "id": str(budget_id),
            "category_id": str(cat_id),
            "amount": "500.0000",
            "currency": "EUR",
            "period_year": 2026,
            "period_month": 5,
            "alert_threshold": "0.80",
            "spent": "200.0000",
            "remaining": "300.0000",
        }
    ]
    with patch("app.modules.budgets.service.list_budgets", new=AsyncMock(return_value=fake)):
        resp = await client.get("/api/v1/budgets?year=2026&month=5&currency=EUR")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_delete_budget_not_found(client):
    with patch("app.modules.budgets.service.delete_budget", new=AsyncMock(return_value=False)):
        resp = await client.delete(f"/api/v1/budgets/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_budget_ok(client):
    with patch("app.modules.budgets.service.delete_budget", new=AsyncMock(return_value=True)):
        resp = await client.delete(f"/api/v1/budgets/{uuid.uuid4()}")
    assert resp.status_code == 204
