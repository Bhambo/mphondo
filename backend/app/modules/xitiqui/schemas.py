import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

XitiqueRole = Literal["organizer", "member"]


class XitiqueGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    account_id: uuid.UUID  # xitiqui virtual account
    contribution_amount: Decimal = Field(..., gt=0, decimal_places=4)
    currency: Literal["MZN", "EUR"] = "MZN"
    frequency_days: int = Field(30, ge=7, le=365)
    notes: str | None = None


class XitiqueGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    account_id: uuid.UUID
    contribution_amount: Decimal
    currency: str
    frequency_days: int
    is_active: bool
    notes: str | None


class XitiqueCycleCreate(BaseModel):
    group_id: uuid.UUID
    start_date: str
    total_rounds: int = Field(..., ge=2, le=50)


class XitiqueCycleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    group_id: uuid.UUID
    cycle_number: int
    start_date: str
    end_date: str | None
    status: str


class XitiqueContributionCreate(BaseModel):
    cycle_id: uuid.UUID
    member_user_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=4)
    paid_at: str
    notes: str | None = None
