import uuid
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AccountType = Literal[
    "mpesa", "bank_es", "cash_mz", "cash_es",
    "xitiqui", "virtual_income", "virtual_expense",
]
CurrencyCode = Literal["EUR", "MZN"]
ModuleContext = Literal["mz", "es"]


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    account_type: AccountType
    currency: CurrencyCode
    module_context: ModuleContext
    iban: str | None = Field(None, max_length=34)
    phone: str | None = Field(None, max_length=20)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = Field(None, max_length=40)


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    account_type: str
    currency: str
    module_context: str
    balance: Decimal
    iban: str | None = None
    phone: str | None = None
    color: str | None = None
    icon: str | None = None
    is_active: bool


class AccountUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=120)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = Field(None, max_length=40)
    is_active: bool | None = None
