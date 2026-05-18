"""Analytics module — monthly summaries, net worth, top categories."""

from typing import Literal

from fastapi import APIRouter, Query

from app.core.deps import DB, CurrentUser

router = APIRouter()


@router.get("/summary")
async def monthly_summary(
    db: DB,
    current_user: CurrentUser,
    module: Literal["mz", "es", "all"] = Query("all"),
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
):
    """Returns income, expense, net, and top categories for the period."""
    # Sprint 9 — consolidado EUR+MZN
    return {"module": module, "year": year, "month": month, "data": []}


@router.get("/net-worth")
async def net_worth(db: DB, current_user: CurrentUser):
    """Returns current balance across all accounts, converted to EUR."""
    # Sprint 9
    return {"eur_total": 0, "mzn_total": 0, "eur_equivalent_mzn": 0}


@router.get("/top-categories")
async def top_categories(
    db: DB,
    current_user: CurrentUser,
    module: Literal["mz", "es"] = Query("es"),
    limit: int = Query(5, ge=1, le=20),
    months: int = Query(1, ge=1, le=12),
):
    # Sprint 9
    return []
