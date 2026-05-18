import uuid
from typing import Literal

from fastapi import APIRouter, Query, status

from app.core.deps import DB, CurrentUser
from app.modules.budgets.schemas import BudgetCreate, BudgetOut

router = APIRouter()


@router.get("", response_model=list[BudgetOut])
async def list_budgets(
    db: DB,
    current_user: CurrentUser,
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    currency: Literal["EUR", "MZN"] = Query("EUR"),
):
    # Sprint 10
    return []


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
async def create_budget(data: BudgetCreate, db: DB, current_user: CurrentUser):
    raise NotImplementedError("Budgets — Sprint 10")


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(budget_id: uuid.UUID, db: DB, current_user: CurrentUser):
    raise NotImplementedError("Budgets — Sprint 10")
