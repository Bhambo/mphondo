import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TransactionStatus = Literal["pending", "confirmed", "cancelled", "reconciled"]
EntryDirection = Literal["debit", "credit"]
ModuleContext = Literal["mz", "es"]
CurrencyCode = Literal["EUR", "MZN"]


class EntryIn(BaseModel):
    account_id: uuid.UUID
    direction: EntryDirection
    amount: Decimal = Field(..., gt=0, decimal_places=4)
    notes: str | None = None


class TransactionCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    occurred_at: str                          # ISO8601 datetime string
    module: ModuleContext
    currency: CurrencyCode
    category_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    fx_rate_id: uuid.UUID | None = None
    fx_rate_snapshot: Decimal | None = None
    reference: str | None = Field(None, max_length=100)
    notes: str | None = None
    entries: list[EntryIn] = Field(..., min_length=2)

    @model_validator(mode="after")
    def validate_double_entry(self) -> "TransactionCreate":
        total = sum(
            e.amount if e.direction == "credit" else -e.amount
            for e in self.entries
        )
        if total != 0:
            raise ValueError(
                f"Entries must balance to zero (got {total}). "
                "Every credit must have a matching debit."
            )
        return self


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    direction: str
    amount: Decimal
    notes: str | None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    description: str
    occurred_at: str
    status: str
    module: str
    currency: str
    is_transfer: bool
    category_id: uuid.UUID | None
    contact_id: uuid.UUID | None
    fx_rate_snapshot: Decimal | None = None
    reference: str | None = None
    notes: str | None = None
    entries: list[EntryOut] = []


class TransactionListParams(BaseModel):
    module: Literal["mz", "es"] | None = None
    account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    from_date: str | None = None
    to_date: str | None = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
