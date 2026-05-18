import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.deps import DB, CurrentUser
from app.modules.accounts import service
from app.modules.accounts.schemas import AccountCreate, AccountOut, AccountUpdate

router = APIRouter()


@router.get("", response_model=list[AccountOut])
async def list_accounts(db: DB, current_user: CurrentUser):
    return await service.list_accounts(db, current_user)


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(data: AccountCreate, db: DB, current_user: CurrentUser):
    return await service.create_account(db, current_user, data)


@router.patch("/{account_id}", response_model=AccountOut)
async def update_account(
    account_id: uuid.UUID, data: AccountUpdate, db: DB, current_user: CurrentUser
):
    row = await service.update_account(db, current_user, account_id, data)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return row
