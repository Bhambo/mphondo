"""Xitiqui (rotating savings group) module — Sprint 5-6."""

import uuid

from fastapi import APIRouter, status

from app.core.deps import DB, CurrentUser
from app.modules.xitiqui.schemas import (
    XitiqueCycleCreate,
    XitiqueCycleOut,
    XitiqueContributionCreate,
    XitiqueGroupCreate,
    XitiqueGroupOut,
)

router = APIRouter()


@router.get("/groups", response_model=list[XitiqueGroupOut])
async def list_groups(db: DB, current_user: CurrentUser):
    # Sprint 5
    return []


@router.post("/groups", response_model=XitiqueGroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(data: XitiqueGroupCreate, db: DB, current_user: CurrentUser):
    raise NotImplementedError("Xitiqui groups — Sprint 5")


@router.get("/groups/{group_id}/cycles", response_model=list[XitiqueCycleOut])
async def list_cycles(group_id: uuid.UUID, db: DB, current_user: CurrentUser):
    return []


@router.post("/cycles", response_model=XitiqueCycleOut, status_code=status.HTTP_201_CREATED)
async def create_cycle(data: XitiqueCycleCreate, db: DB, current_user: CurrentUser):
    raise NotImplementedError("Xitiqui cycles — Sprint 5")


@router.post("/contributions", status_code=status.HTTP_201_CREATED)
async def record_contribution(data: XitiqueContributionCreate, db: DB, current_user: CurrentUser):
    raise NotImplementedError("Xitiqui contributions — Sprint 6")
