import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    category_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=4)
    currency: Literal["EUR", "MZN"]
    period_year: int = Field(..., ge=2020, le=2100)
    period_month: int = Field(..., ge=1, le=12)
    alert_threshold: Decimal = Field(Decimal("0.80"), ge=0, le=1)


class BudgetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal
    currency: str
    period_year: int
    period_month: int
    alert_threshold: Decimal
    spent: Decimal | None = None      # computed field — filled by service
    remaining: Decimal | None = None
