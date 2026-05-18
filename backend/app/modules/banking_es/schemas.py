import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class BankConnectionCreate(BaseModel):
    bank_name: str = Field(..., min_length=1, max_length=100)
    account_id: uuid.UUID     # the accounts table entry


class BankConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    bank_name: str
    account_id: uuid.UUID
    status: str
    last_sync_at: str | None
    consent_expires_at: str | None


class CSVImportOut(BaseModel):
    imported_count: int
    skipped_duplicates: int
    needs_categorization: int
    message: str


class CategoryRuleCreate(BaseModel):
    category_id: uuid.UUID
    match_field: Literal["description", "counterpart", "amount_range"]
    match_pattern: str = Field(..., max_length=200)
    priority: int = Field(10, ge=1, le=100)
