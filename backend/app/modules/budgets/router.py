import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import DB, CurrentUser
from app.modules.budgets import service
from app.modules.budgets.schemas import BudgetCreate, BudgetOut

router = APIRouter()


@router.get("", response_model=list[BudgetOut])
async def list_budgets(
    db: DB,
    current_user: CurrentUser,
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    currency: Literal["EUR", "MZN"] = Query("EUR"),
):
    return await service.list_budgets(db, current_user, year, month, currency)


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
async def create_budget(data: BudgetCreate, db: DB, current_user: CurrentUser):
    return await service.create_budget(db, current_user, data)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(budget_id: uuid.UUID, db: DB, current_user: CurrentUser):
    ok = await service.delete_budget(db, current_user, budget_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
