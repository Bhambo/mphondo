"""Banking ES module — Enable Banking PSD2 + CSV import + category rules.

Enable Banking OAuth flow:
  1. POST /banking-es/connect  → returns redirect_url to bank
  2. Bank redirects back to SITE_URL/callback?code=...
  3. POST /banking-es/callback  → exchanges code, stores token, triggers sync
"""

import uuid

from fastapi import APIRouter, File, Form, UploadFile, status

from app.core.deps import DB, CurrentUser
from app.modules.banking_es.schemas import (
    BankConnectionCreate,
    BankConnectionOut,
    CategoryRuleCreate,
    CSVImportOut,
)

router = APIRouter()


@router.get("/connections", response_model=list[BankConnectionOut])
async def list_connections(db: DB, current_user: CurrentUser):
    # Sprint 7 — Enable Banking PSD2 implementation
    return []


@router.post("/connections", response_model=BankConnectionOut, status_code=status.HTTP_201_CREATED)
async def create_connection(data: BankConnectionCreate, db: DB, current_user: CurrentUser):
    # Sprint 7 — returns Enable Banking OAuth redirect URL
    raise NotImplementedError("Enable Banking PSD2 — Sprint 7")


@router.post("/import/csv", response_model=CSVImportOut)
async def import_csv(
    account_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: DB = ...,
    current_user: CurrentUser = ...,
):
    # Sprint 7 — CSV import with duplicate detection
    raise NotImplementedError("CSV import — Sprint 7")


@router.get("/rules")
async def list_category_rules(db: DB, current_user: CurrentUser):
    # Sprint 7 — return category auto-categorization rules
    return []


@router.post("/rules", status_code=status.HTTP_201_CREATED)
async def create_category_rule(data: CategoryRuleCreate, db: DB, current_user: CurrentUser):
    # Sprint 7
    raise NotImplementedError("Category rules — Sprint 7")
