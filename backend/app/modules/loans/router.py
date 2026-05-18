"""Loans module — personal loans, family loans, payment schedule. Sprint 10."""

import uuid

from fastapi import APIRouter, status

from app.core.deps import DB, CurrentUser

router = APIRouter()


@router.get("")
async def list_loans(db: DB, current_user: CurrentUser):
    return []


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_loan(db: DB, current_user: CurrentUser):
    raise NotImplementedError("Loans — Sprint 10")
